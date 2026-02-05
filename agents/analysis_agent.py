"""
视频分析 Sub-Agent
负责通过视觉理解定位视频中的目标场景
采用粗粒度 + 精细粒度的两步定位策略
"""
import os
from typing import Dict, List, Tuple, Optional
from tools.ffmpeg_tools import FFmpegTools
from tools.vision_utils import VisionLLM


class AnalysisAgent:
    """视频分析 Agent - 通过 Vision LLM 定位场景"""
    
    def __init__(
        self,
        vision_llm: VisionLLM,
        ffmpeg_tools: FFmpegTools,
        workspace_dir: str
    ):
        """
        初始化分析 Agent
        
        Args:
            vision_llm: Vision LLM 实例
            ffmpeg_tools: FFmpeg 工具实例
            workspace_dir: 工作空间目录
        """
        self.vision_llm = vision_llm
        self.ffmpeg_tools = ffmpeg_tools
        self.workspace_dir = workspace_dir
        self.frames_dir = os.path.join(workspace_dir, "frames")
    
    def analyze_video(
        self,
        video_path: str,
        query: str,
        coarse_interval: int = 10,
        fine_interval: float = 1.0
    ) -> Dict[str, float]:
        """
        分析视频并定位目标场景
        使用两步定位策略：粗粒度 -> 精细粒度
        
        Args:
            video_path: 视频文件路径
            query: 用户查询（如"找出冲浪场景"）
            coarse_interval: 粗粒度扫描间隔（秒）
            fine_interval: 精细粒度扫描间隔（秒）
            
        Returns:
            包含 start_time 和 end_time 的字典
        """
        print(f"\n[Analysis Agent] 开始分析视频: {video_path}")
        print(f"[Analysis Agent] 目标场景: {query}")
        
        # 第一步：粗粒度定位
        print("\n[第一步] 粗粒度扫描...")
        rough_range = self._coarse_localization(video_path, query, coarse_interval)
        
        print(f"[粗定位结果] 场景大致范围: {rough_range['start']:.1f}s - {rough_range['end']:.1f}s")
        
        # 第二步：精细粒度定位
        print("\n[第二步] 精细粒度扫描...")
        exact_range = self._fine_localization(
            video_path,
            query,
            rough_range['start'],
            rough_range['end'],
            fine_interval
        )
        
        print(f"[精定位结果] 精确时间范围: {exact_range['start']:.2f}s - {exact_range['end']:.2f}s")
        
        return exact_range
    
    def _coarse_localization(
        self,
        video_path: str,
        query: str,
        interval: int
    ) -> Dict[str, float]:
        """
        粗粒度定位：在整个视频中找出目标场景的大致范围
        
        Args:
            video_path: 视频路径
            query: 查询描述
            interval: 扫描间隔
            
        Returns:
            大致的开始和结束时间
        """
        # 提取粗粒度关键帧
        coarse_dir = os.path.join(self.frames_dir, "coarse")
        os.makedirs(coarse_dir, exist_ok=True)
        
        frame_paths = self.ffmpeg_tools.extract_frames_coarse(
            video_path,
            coarse_dir,
            interval=interval
        )
        
        print(f"  - 已提取 {len(frame_paths)} 个粗粒度关键帧")
        
        # 构建 Vision LLM 提示
        prompt = f"""
你是一个视频分析专家。我将给你展示一个视频中按时间顺序提取的关键帧。
每个图片的文件名包含时间信息（格式：frame_coarse_XXXX_tYYYYs.jpg，其中 YYYY 是时间戳，单位秒）。

用户查询: {query}

请仔细分析这些图片，找出用户描述的场景大致出现在哪个时间范围内。

请以 JSON 格式回复，包含以下字段：
{{
    "start": 开始时间（秒，数字）,
    "end": 结束时间（秒，数字）,
    "confidence": 置信度（0-1之间的浮点数）,
    "reasoning": "你的推理过程"
}}

注意：
1. 如果场景在多个不连续的时间段出现，选择最主要或最清晰的一段
2. 适当扩大范围以避免遗漏（前后各扩展 {interval} 秒左右）
3. 如果找不到相关场景，返回 start=0, end=0, confidence=0
"""
        
        # 调用 Vision LLM
        response = self.vision_llm.ask_with_images(prompt, frame_paths)
        
        # 解析响应
        try:
            result = self.vision_llm.parse_json_response(response)
            
            # 验证结果
            if result.get('confidence', 0) < 0.3:
                print(f"  ⚠️  警告: 置信度较低 ({result['confidence']}), 可能未找到目标场景")
            
            return {
                'start': max(0, result['start'] - interval),  # 向前扩展
                'end': result['end'] + interval,  # 向后扩展
                'confidence': result.get('confidence', 0),
                'reasoning': result.get('reasoning', '')
            }
            
        except Exception as e:
            print(f"  ❌ 解析粗定位结果失败: {e}")
            print(f"  原始响应: {response}")
            # 返回整个视频作为后备
            duration = self.ffmpeg_tools.get_video_duration(video_path)
            return {'start': 0, 'end': duration, 'confidence': 0}
    
    def _fine_localization(
        self,
        video_path: str,
        query: str,
        start_rough: float,
        end_rough: float,
        interval: float
    ) -> Dict[str, float]:
        """
        精细粒度定位：在粗定位范围内精确找到边界
        
        Args:
            video_path: 视频路径
            query: 查询描述
            start_rough: 粗定位的开始时间
            end_rough: 粗定位的结束时间
            interval: 扫描间隔
            
        Returns:
            精确的开始和结束时间
        """
        # 提取精细粒度关键帧
        fine_dir = os.path.join(self.frames_dir, "fine")
        os.makedirs(fine_dir, exist_ok=True)
        
        frame_paths = self.ffmpeg_tools.extract_frames_fine(
            video_path,
            fine_dir,
            start_time=start_rough,
            end_time=end_rough,
            interval=interval
        )
        
        print(f"  - 已提取 {len(frame_paths)} 个精细粒度关键帧")
        
        # 构建 Vision LLM 提示
        prompt = f"""
你是一个视频分析专家。我将给你展示一个视频片段中按时间顺序提取的关键帧。
每个图片的文件名包含精确的时间信息（格式：frame_fine_XXXX_tYY.YYs.jpg）。

用户查询: {query}

这些帧已经在粗定位阶段确认包含目标场景。现在请你精确找出：
1. 场景的**真正开始时刻**（目标动作/场景刚刚出现的那一秒）
2. 场景的**真正结束时刻**（目标动作/场景完全结束的那一秒）

请以 JSON 格式回复：
{{
    "start": 精确开始时间（秒，保留2位小数）,
    "end": 精确结束时间（秒，保留2位小数）,
    "start_description": "开始帧的画面描述",
    "end_description": "结束帧的画面描述"
}}

要求：
1. 尽可能精确，误差不超过 1 秒
2. 确保不遗漏关键动作的开始和结束
3. 如果场景有渐入渐出，包含完整的过渡
"""
        
        # 调用 Vision LLM
        response = self.vision_llm.ask_with_images(prompt, frame_paths)
        
        # 解析响应
        try:
            result = self.vision_llm.parse_json_response(response)
            
            return {
                'start': result['start'],
                'end': result['end'],
                'start_description': result.get('start_description', ''),
                'end_description': result.get('end_description', '')
            }
            
        except Exception as e:
            print(f"  ❌ 解析精定位结果失败: {e}")
            print(f"  原始响应: {response}")
            # 返回粗定位结果作为后备
            return {'start': start_rough, 'end': end_rough}
