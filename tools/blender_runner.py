"""
Blender 运行器模块
封装 Blender 命令行调用逻辑
"""
import subprocess
import os
import json
import shutil
from typing import Optional


class BlenderRunner:
    """封装 Blender 脚本执行"""
    
    def __init__(self, blender_path: str = "blender"):
        """
        初始化 Blender 运行器
        
        Args:
            blender_path: Blender 可执行文件路径
        """
        self.blender_path = blender_path
    
    def run_script(
        self,
        script_path: str,
        output_path: str,
        low_res: bool = True,
        resolution_percentage: int = 50
    ) -> tuple[bool, str]:
        """
        运行 Blender 脚本
        
        Args:
            script_path: Python 脚本路径
            output_path: 输出视频路径
            low_res: 是否使用低分辨率（用于快速预览）
            resolution_percentage: 分辨率百分比（1-100）
            
        Returns:
            (是否成功, 输出路径或错误信息)
        """
        if not os.path.exists(script_path):
            return False, f"Script not found: {script_path}"

        # 如果 Blender 可执行文件不存在，尝试使用 FFmpeg 回退（基于脚本旁的元数据）
        blender_exec = shutil.which(self.blender_path) or (self.blender_path if os.path.exists(self.blender_path) else None)
        if not blender_exec:
            # 查找元数据文件
            meta_path = script_path + '.meta.json'
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as mf:
                        meta = json.load(mf)

                    video = meta.get('video_path')
                    start = float(meta.get('start_time', 0))
                    end = float(meta.get('end_time', 0))
                    fps_meta = float(meta.get('fps', 0)) if meta.get('fps') is not None else 0
                    width_meta = int(meta.get('width')) if meta.get('width') is not None else None
                    height_meta = int(meta.get('height')) if meta.get('height') is not None else None

                    # 优先使用 ffmpeg 做流拷贝以保留原始编码/分辨率/像素格式
                    ffmpeg_exec = shutil.which('ffmpeg')
                    if ffmpeg_exec:
                        # 先尝试 stream copy（remux）以完全保留参数
                        copy_cmd = [
                            ffmpeg_exec,
                            '-y',
                            '-i', video,
                            '-ss', str(start),
                            '-to', str(end),
                            '-c', 'copy',
                            output_path
                        ]
                        copy_res = subprocess.run(copy_cmd, capture_output=True, text=True)
                        if copy_res.returncode == 0 and os.path.exists(output_path):
                            return True, output_path

                        # 如果拷贝失败，使用重新编码并显式设置参数以匹配源视频
                        reencode_cmd = [
                            ffmpeg_exec,
                            '-y',
                            '-i', video,
                            '-ss', str(start),
                            '-to', str(end),
                            '-c:v', 'libx264',
                            '-preset', 'veryfast',
                            '-crf', '18',
                            '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac'
                        ]
                        if fps_meta and fps_meta > 0:
                            reencode_cmd += ['-r', str(int(round(fps_meta)))]
                        if width_meta and height_meta:
                            reencode_cmd += ['-s', f"{width_meta}x{height_meta}"]

                        reencode_cmd += [output_path]
                        re_res = subprocess.run(reencode_cmd, capture_output=True, text=True)
                        if re_res.returncode == 0 and os.path.exists(output_path):
                            return True, output_path

                        # 返回 ffmpeg 的错误信息
                        stderr = re_res.stderr if 're_res' in locals() and re_res.stderr else copy_res.stderr
                        return False, f"FFmpeg fallback failed: {stderr}"

                    # 系统没有 ffmpeg，使用 OpenCV 回退（仅保留分辨率与帧率）
                    try:
                        import cv2

                        cap = cv2.VideoCapture(video)
                        if not cap.isOpened():
                            return False, f"Cannot open video for fallback: {video}"

                        fps = cap.get(cv2.CAP_PROP_FPS) or fps_meta or 25.0
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                        start_frame = int(start * fps)
                        end_frame = int(end * fps)

                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

                        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                        frame_idx = start_frame
                        while frame_idx <= end_frame:
                            ret, frame = cap.read()
                            if not ret:
                                break
                            writer.write(frame)
                            frame_idx += 1

                        writer.release()
                        cap.release()

                        if os.path.exists(output_path):
                            return True, output_path
                        else:
                            return False, "OpenCV fallback failed to create output file"

                    except Exception as e:
                        return False, f"OpenCV fallback exception: {e}"

                except Exception as e:
                    return False, f"FFmpeg fallback exception: {e}"
            else:
                return False, f"Blender not found ({self.blender_path}) and no metadata fallback available"
        
        # 构建 Blender 命令
        cmd = [
            self.blender_path,
            "--background",  # 后台模式
            "--python", script_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=False,  # 不自动解码文本，避免 UnicodeDecodeError
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                if os.path.exists(output_path):
                    return True, output_path
                
                # 检查是否降级为 PNG 序列
                # Blender 文档: 如果输出路径是 /tmp/test.mp4 且格式是 PNG，文件名为 /tmp/test.mp40001.png
                possible_first_frame = f"{output_path}0001.png" # 假设从第1帧开始
                if not os.path.exists(possible_first_frame):
                    # 尝试查找目录下的任意匹配文件
                    dir_name = os.path.dirname(output_path)
                    base_name = os.path.basename(output_path)
                    if os.path.exists(dir_name):
                        for f in os.listdir(dir_name):
                            if f.startswith(base_name) and f.endswith(".png"):
                                possible_first_frame = os.path.join(dir_name, f)
                                break
                
                if os.path.exists(possible_first_frame):
                    print(f"Detected PNG sequence (e.g., {possible_first_frame}), stitching with FFmpeg...")
                    try:
                        # 使用 FFmpeg 合成
                        # 注意：Blender 输出的文件名通常是 output.mp40001.png
                        # FFmpeg 输入 pattern 应该是 output.mp4%04d.png
                        ffmpeg_cmd = [
                            "ffmpeg", "-y",
                            "-framerate", "25", # 假设默认 25fps，理想情况应该从脚本获取，这里做个兜底
                            "-i", f"{output_path}%04d.png",
                            "-c:v", "libx264",
                            "-pix_fmt", "yuv420p",
                            output_path
                        ]
                        
                        stitch_result = subprocess.run(
                            ffmpeg_cmd,
                            capture_output=True,
                            text=False  # Avoid decoding errors
                        )
                        
                        if stitch_result.returncode == 0 and os.path.exists(output_path):
                            # 清理 PNG 序列（可选，这里保留以便调试）
                            return True, output_path
                        else:
                            stderr = stitch_result.stderr.decode('utf-8', errors='replace') if stitch_result.stderr else ""
                            return False, f"FFmpeg stitching failed: {stderr}"
                            
                    except Exception as e:
                        return False, f"Stitching exception: {str(e)}"

            # 如果没有找到输出文件也没有 PNG 序列，报告错误
            # 尝试解码错误信息
                stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""
                if not stderr:
                    stderr = result.stderr.decode('gbk', errors='replace') if result.stderr else ""
                
                # 如果 stderr 为空，尝试读取 stdout（有时错误会输出到 stdout）
                if not stderr:
                    stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ""
                    if not stdout:
                        stdout = result.stdout.decode('gbk', errors='replace') if result.stdout else "Unknown error (no output)"
                    stderr = f"stdout: {stdout[-500:]}" # 只取最后500个字符
                    
                return False, f"Blender execution failed: {stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Blender execution timeout"
        except Exception as e:
            return False, f"Exception during execution: {str(e)}"
    
    def validate_blender_installation(self) -> bool:
        """
        验证 Blender 是否正确安装
        
        Returns:
            是否安装
        """
        try:
            result = subprocess.run(
                [self.blender_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
