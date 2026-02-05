"""
Editor Agent
负责生成 Blender Python 脚本实现视频编辑
"""
import os
from typing import Dict, List, Optional
from tools.ffmpeg_tools import FFmpegTools


class EditorAgent:
    """Editor Agent - 生成 Blender 编辑脚本"""
    
    def __init__(
        self,
        ffmpeg_tools: FFmpegTools,
        workspace_dir: str,
        llm_client=None  # 可选：用于更智能的代码生成
    ):
        """
        初始化 Editor Agent
        
        Args:
            ffmpeg_tools: FFmpeg 工具实例
            workspace_dir: 工作空间目录
            llm_client: LLM 客户端（可选，用于生成更复杂的效果代码）
        """
        self.ffmpeg_tools = ffmpeg_tools
        self.workspace_dir = workspace_dir
        self.scripts_dir = os.path.join(workspace_dir, "scripts")
        self.llm_client = llm_client
        
        # 加载模板
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates",
            "blender_base.py"
        )
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            self._load_templates(template_content)
    
    def _load_templates(self, content: str):
        """从模板文件加载各个模板"""
        # 简单的模板提取（实际应该更健壮）
        self.base_template = content
    
    def generate_script(
        self,
        video_path: str,
        instruction: str,
        timestamps: Dict[str, float],
        output_path: str,
        resolution_percentage: int = 50,
        feedback: Optional[str] = None,
        version: int = 1
    ) -> str:
        """
        生成 Blender 编辑脚本
        
        Args:
            video_path: 输入视频路径
            instruction: 用户指令
            timestamps: 时间戳信息 (start, end)
            output_path: 输出视频路径
            resolution_percentage: 分辨率百分比（用于快速预览）
            feedback: Critic 的反馈（用于迭代改进）
            version: 脚本版本号
            
        Returns:
            生成的脚本路径
        """
        print(f"\n[Editor Agent] 生成编辑脚本 v{version}...")
        if feedback:
            print(f"[Editor Agent] 基于反馈改进: {feedback}")
        
        # 获取视频元数据
        metadata = self.ffmpeg_tools.get_video_metadata(video_path)
        fps = metadata['fps']
        width = metadata['width']
        height = metadata['height']
        
        # 处理反馈调整时间戳
        adjusted_timestamps = self._adjust_timestamps_based_on_feedback(
            timestamps, feedback, fps
        )
        
        # 计算帧数
        start_frame = int(adjusted_timestamps['start'] * fps)
        end_frame = int(adjusted_timestamps['end'] * fps)
        
        print(f"  - 视频: {os.path.basename(video_path)}")
        print(f"  - 分辨率: {width}x{height} @ {fps} FPS")
        print(f"  - 剪辑范围: {adjusted_timestamps['start']:.2f}s - {adjusted_timestamps['end']:.2f}s")
        print(f"  - 帧范围: {start_frame} - {end_frame}")
        
        # 生成脚本
        script_content = self._build_script(
            video_path=video_path,
            output_path=output_path,
            fps=fps,
            width=width,
            height=height,
            start_time=adjusted_timestamps['start'],
            end_time=adjusted_timestamps['end'],
            start_frame=start_frame,
            end_frame=end_frame,
            resolution_percentage=resolution_percentage,
            instruction=instruction
        )
        
        # 保存脚本
        os.makedirs(self.scripts_dir, exist_ok=True)
        script_path = os.path.join(self.scripts_dir, f"edit_script_v{version}.py")
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"  ✓ 脚本已保存: {script_path}")

        # 保存元数据以便在没有 Blender 时使用 FFmpeg 回退
        try:
            import json
            meta = {
                'video_path': video_path,
                'start_time': adjusted_timestamps['start'],
                'end_time': adjusted_timestamps['end'],
                'fps': fps,
                'width': width,
                'height': height,
                'output_path': output_path
            }
            meta_path = script_path + '.meta.json'
            with open(meta_path, 'w', encoding='utf-8') as mf:
                json.dump(meta, mf)
            print(f"  ✓ 元数据已保存: {meta_path}")
        except Exception:
            pass

        return script_path
    
    def _adjust_timestamps_based_on_feedback(
        self,
        timestamps: Dict[str, float],
        feedback: Optional[str],
        fps: float
    ) -> Dict[str, float]:
        """
        根据 Critic 反馈调整时间戳
        
        Args:
            timestamps: 原始时间戳
            feedback: 反馈文本
            fps: 视频帧率
            
        Returns:
            调整后的时间戳
        """
        if not feedback:
            return timestamps.copy()
        
        adjusted = timestamps.copy()
        feedback_lower = feedback.lower()
        
        # 简单的规则匹配（实际应该用 LLM 解析）
        import re
        
        # 匹配 "开头太早，延后 X 秒" 或 "start +X" 等模式
        start_adjust = re.search(r'(?:开头|开始|起始).*?(?:延后|向后|加|plus|\+)\s*(\d+(?:\.\d+)?)', feedback_lower)
        if start_adjust:
            adjust_seconds = float(start_adjust.group(1))
            adjusted['start'] = timestamps['start'] + adjust_seconds
            print(f"  - 调整开始时间: +{adjust_seconds}s -> {adjusted['start']:.2f}s")
        
        start_adjust_back = re.search(r'(?:开头|开始|起始).*?(?:提前|向前|减|minus|-)\s*(\d+(?:\.\d+)?)', feedback_lower)
        if start_adjust_back:
            adjust_seconds = float(start_adjust_back.group(1))
            adjusted['start'] = max(0, timestamps['start'] - adjust_seconds)
            print(f"  - 调整开始时间: -{adjust_seconds}s -> {adjusted['start']:.2f}s")
        
        # 匹配 "结尾太早，延长 X 秒" 或 "end +X" 等模式
        end_adjust = re.search(r'(?:结尾|结束|末尾).*?(?:延长|向后|加|plus|\+)\s*(\d+(?:\.\d+)?)', feedback_lower)
        if end_adjust:
            adjust_seconds = float(end_adjust.group(1))
            adjusted['end'] = timestamps['end'] + adjust_seconds
            print(f"  - 调整结束时间: +{adjust_seconds}s -> {adjusted['end']:.2f}s")
        
        end_adjust_back = re.search(r'(?:结尾|结束|末尾).*?(?:提前|向前|减|minus|-)\s*(\d+(?:\.\d+)?)', feedback_lower)
        if end_adjust_back:
            adjust_seconds = float(end_adjust_back.group(1))
            adjusted['end'] = timestamps['end'] - adjust_seconds
            print(f"  - 调整结束时间: -{adjust_seconds}s -> {adjusted['end']:.2f}s")
        
        return adjusted
    
    def _build_script(
        self,
        video_path: str,
        output_path: str,
        fps: float,
        width: int,
        height: int,
        start_time: float,
        end_time: float,
        start_frame: int,
        end_frame: int,
        resolution_percentage: int,
        instruction: str
    ) -> str:
        """
        构建完整的 Blender 脚本
        
        Returns:
            完整的 Python 脚本内容
        """
        # 基础初始化代码
        script = f"""import bpy
import os

# 清空当前场景
bpy.ops.wm.read_factory_settings(use_empty=False)

# 清理场景对象
if bpy.context.scene.objects:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

# 确保使用视频序列编辑器
if not bpy.context.scene.sequence_editor:
    bpy.context.scene.sequence_editor_create()

seq_editor = bpy.context.scene.sequence_editor

# 兼容 Blender 5.0+ (strips) 和旧版本 (sequences)
def get_strips(editor):
    return getattr(editor, 'strips', getattr(editor, 'sequences', None))

def get_strips_all(editor):
    # 优先尝试 strips_all, 然后 sequences_all, 都没有则回退到 strips/sequences
    return getattr(editor, 'strips_all', getattr(editor, 'sequences_all', get_strips(editor)))

# 清空所有现有序列
if seq_editor:
    strips_collection = get_strips(seq_editor)
    all_strips = get_strips_all(seq_editor)
    
    if strips_collection and all_strips:
        for seq in list(all_strips):
            try:
                strips_collection.remove(seq)
            except:
                pass  # 忽略已移除的 strip

# 设置场景参数
scene = bpy.context.scene
scene.render.fps = {int(fps)}
scene.render.resolution_x = {width}
scene.render.resolution_y = {height}
scene.render.resolution_percentage = {resolution_percentage}

# 设置渲染输出格式
try:
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.ffmpeg.audio_codec = 'AAC'
except TypeError:
    print("Warning: FFMPEG format not available in Blender, falling back to PNG sequence")
    scene.render.image_settings.file_format = 'PNG'

# 设置输出路径
scene.render.filepath = r'{output_path}'

print("Blender 场景初始化完成")

# 导入视频文件
video_path = r'{video_path}'
strips_api = get_strips(seq_editor)
strip = strips_api.new_movie(
    name="video_clip",
    filepath=video_path,
    channel=1,
    frame_start=1
)

# 设置裁剪范围
# 原始时间: {start_time:.2f}s - {end_time:.2f}s
# 对应帧数: {start_frame} - {end_frame}

# 裁剪视频
strip.frame_offset_start = {start_frame}
strip.frame_final_duration = {end_frame - start_frame}

# 设置场景的渲染帧范围
scene.frame_start = 1
scene.frame_end = {end_frame - start_frame}

print(f"视频剪辑设置完成: {{strip.frame_final_start}} 到 {{strip.frame_final_end}}")

# 检查是否需要添加特效
# 用户指令: {instruction}
"""
        
        # 分析指令添加特效（简化版，实际应该用 LLM）
        instruction_lower = instruction.lower()
        
        if "慢动作" in instruction_lower or "slow motion" in instruction_lower:
            script += self._add_slow_motion_effect(fps)
        
        if "淡入" in instruction_lower or "fade in" in instruction_lower:
            script += self._add_fade_effect(fps, fade_duration=2.0)
        
        # 渲染命令
        script += """
# 开始渲染
print("开始渲染...")
bpy.ops.render.render(animation=True, write_still=False)
print(f"渲染完成! 输出文件: {scene.render.filepath}")
"""
        
        return script
    
    def _add_slow_motion_effect(self, fps: float, speed_factor: float = 0.5) -> str:
        """添加慢动作效果代码"""
        return f"""
# 添加慢动作效果
print("添加慢动作效果...")
speed_strip = seq_editor.sequences.new_effect(
    name="slow_motion",
    type='SPEED',
    channel=2,
    frame_start=1,
    frame_end=scene.frame_end,
    seq1=strip
)
speed_strip.speed_factor = {speed_factor}

# 调整场景长度
original_length = scene.frame_end
scene.frame_end = int(original_length / {speed_factor})
print(f"慢动作效果已添加 (速度: {speed_factor*100}%)")
"""
    
    def _add_fade_effect(self, fps: float, fade_duration: float = 2.0) -> str:
        """添加淡入效果代码"""
        fade_frames = int(fade_duration * fps)
        return f"""
# 添加淡入效果
print("添加淡入效果...")
fade_frames = {fade_frames}

# 使用 Gamma Cross 实现淡入
# 注意：Blender VSE 的淡入淡出需要通过调整透明度实现
strip.blend_alpha = 0.0  # 起始透明
strip.keyframe_insert(data_path="blend_alpha", frame=1)
strip.blend_alpha = 1.0  # 结束不透明
strip.keyframe_insert(data_path="blend_alpha", frame=fade_frames)

print(f"淡入效果已添加 (时长: {fade_duration}秒)")
"""
