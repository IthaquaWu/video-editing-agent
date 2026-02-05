"""
FFmpeg 工具模块
提供视频截帧、获取元数据等功能
"""
import subprocess
import os
import logging
import shutil
from pathlib import Path
from typing import List, Tuple
import json

try:
    # 延迟导入配置以避免循环依赖
    from ..config import Config
except Exception:
    from config import Config


class FFmpegTools:
    """封装 FFmpeg 常用操作"""
    
    def __init__(self, ffmpeg_path: str = None, ffprobe_path: str = None):
        """
        初始化 FFmpeg 工具
        
        Args:
            ffmpeg_path: ffmpeg 可执行文件路径
            ffprobe_path: ffprobe 可执行文件路径
        """
        # 使用 Config 或环境变量中的路径优先
        raw_ffmpeg = ffmpeg_path or os.getenv('FFMPEG_PATH') or getattr(Config, 'FFMPEG_PATH', 'ffmpeg')

        # 解析可执行文件的真实路径（优先使用 PATH）
        resolved_ffmpeg = shutil.which(raw_ffmpeg) or raw_ffmpeg
        self.ffmpeg_path = str(resolved_ffmpeg)

        # ffprobe 寻找顺序：explicit arg -> FFPROBE_PATH env -> same dir as resolved ffmpeg -> which('ffprobe') -> 'ffprobe'
        if ffprobe_path:
            self.ffprobe_path = ffprobe_path
        else:
            env_fp = os.getenv('FFPROBE_PATH')
            if env_fp:
                self.ffprobe_path = env_fp
            else:
                ffmpeg_full = shutil.which(self.ffmpeg_path) or self.ffmpeg_path
                try:
                    ffmpeg_parent = Path(ffmpeg_full).parent
                except Exception:
                    ffmpeg_parent = None

                candidate = None
                if ffmpeg_parent and ffmpeg_parent.exists():
                    candidate_path = ffmpeg_parent / ('ffprobe.exe' if os.name == 'nt' else 'ffprobe')
                    if candidate_path.exists():
                        candidate = str(candidate_path)

                if not candidate:
                    candidate = shutil.which('ffprobe')

                self.ffprobe_path = candidate or 'ffprobe'

        logging.debug("FFmpegTools initialized with ffmpeg=%s ffprobe=%s (raw=%s)", self.ffmpeg_path, self.ffprobe_path, raw_ffmpeg)
    
    def get_video_duration(self, video_path: str) -> float:
        """
        获取视频时长（秒）
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频时长（秒）
        """
        # 检查 ffprobe 是否可用
        ffprobe_exec = shutil.which(self.ffprobe_path) or (Path(self.ffprobe_path).exists() and str(self.ffprobe_path))
        if not ffprobe_exec:
            raise FileNotFoundError(
                f"ffprobe not found. Tried: ffprobe_path={self.ffprobe_path}. "
                f"请确认 FFmpeg/ffprobe 已安装并在 PATH 中，或在 .env 中设置 FFMPEG_PATH/FFPROBE_PATH。"
            )

        cmd = [
            ffprobe_exec,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            video_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except OSError as e:
            logging.exception("运行 ffprobe 出错: %s", e)
            raise FileNotFoundError(f"无法执行 ffprobe: {e}")

        if result.returncode != 0:
            logging.error("ffprobe 返回非零代码 (%s), stderr: %s", result.returncode, result.stderr)
            raise RuntimeError(f"ffprobe failed: {result.stderr}")

        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    
    def get_video_metadata(self, video_path: str) -> dict:
        """
        获取视频元数据
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            包含宽度、高度、帧率、时长等信息的字典
        """
        cmd = [
            self.ffprobe_path,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,duration",
            "-show_entries", "format=duration",
            "-of", "json",
            video_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)

            stream = data['streams'][0]
            fps_parts = stream['r_frame_rate'].split('/')
            fps = int(fps_parts[0]) / int(fps_parts[1])

            duration = float(data['format']['duration']) if 'duration' in data['format'] else 0

            return {
                'width': stream['width'],
                'height': stream['height'],
                'fps': fps,
                'duration': duration
            }
        except Exception:
            # 如果 ffprobe 不可用或解析失败，回退到 OpenCV 获取元数据
            try:
                import cv2

                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    raise RuntimeError("cv2 cannot open video")

                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
                duration = frame_count / fps if fps > 0 else 0
                cap.release()

                return {
                    'width': width,
                    'height': height,
                    'fps': fps,
                    'duration': duration
                }
            except Exception as e:
                raise RuntimeError(f"Failed to get video metadata via ffprobe and OpenCV: {e}")
    
    def extract_frames_coarse(
        self, 
        video_path: str, 
        output_dir: str, 
        interval: int = 10,
        start_time: float = 0,
        end_time: float = None
    ) -> List[str]:
        """
        粗粒度提取关键帧（按时间间隔）
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            interval: 截图间隔（秒）
            start_time: 开始时间（秒）
            end_time: 结束时间（秒），None 表示到视频结束
            
        Returns:
            提取的帧文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取视频总时长
        duration = self.get_video_duration(video_path)
        if end_time is None or end_time > duration:
            end_time = duration
        
        frame_paths = []
        current_time = start_time
        frame_index = 0
        
        while current_time < end_time:
            output_file = os.path.join(output_dir, f"frame_coarse_{frame_index:04d}_t{int(current_time):04d}s.jpg")
            
            cmd = [
                self.ffmpeg_path,
                "-ss", str(current_time),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                "-y",
                output_file
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            if os.path.exists(output_file):
                frame_paths.append(output_file)
            
            frame_index += 1
            current_time += interval
        
        return frame_paths
    
    def extract_frames_fine(
        self,
        video_path: str,
        output_dir: str,
        start_time: float,
        end_time: float,
        interval: float = 1.0
    ) -> List[str]:
        """
        精细粒度提取关键帧（按秒或亚秒级）
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            interval: 截图间隔（秒），可以是小数
            
        Returns:
            提取的帧文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        
        frame_paths = []
        current_time = start_time
        frame_index = 0
        
        while current_time < end_time:
            output_file = os.path.join(
                output_dir, 
                f"frame_fine_{frame_index:04d}_t{current_time:.2f}s.jpg"
            )
            
            cmd = [
                self.ffmpeg_path,
                "-ss", str(current_time),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                "-y",
                output_file
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            if os.path.exists(output_file):
                frame_paths.append(output_file)
            
            frame_index += 1
            current_time += interval
        
        return frame_paths
    
    def extract_key_frames_from_preview(
        self,
        video_path: str,
        output_dir: str,
        num_frames: int = 5
    ) -> List[str]:
        """
        从预览视频中均匀提取关键帧用于 Critic 评审
        
        Args:
            video_path: 预览视频路径
            output_dir: 输出目录
            num_frames: 要提取的帧数
            
        Returns:
            提取的帧文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        
        duration = self.get_video_duration(video_path)
        interval = duration / (num_frames + 1)
        
        frame_paths = []
        
        for i in range(num_frames):
            timestamp = interval * (i + 1)
            output_file = os.path.join(output_dir, f"preview_frame_{i:02d}.jpg")
            
            cmd = [
                self.ffmpeg_path,
                "-ss", str(timestamp),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                "-y",
                output_file
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            if os.path.exists(output_file):
                frame_paths.append(output_file)
        
        return frame_paths
