"""
Blender 脚本基础模板
提供视频编辑的通用框架代码
"""

BLENDER_SCRIPT_TEMPLATE = """
import bpy
import os

# 清空当前场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 确保使用视频序列编辑器
if not bpy.context.scene.sequence_editor:
    bpy.context.scene.sequence_editor_create()

seq_editor = bpy.context.scene.sequence_editor

# 清空所有现有序列
if seq_editor:
    # 兼容 Blender 新旧版本
    seqs = getattr(seq_editor, 'sequences_all', seq_editor.sequences)
    for seq in list(seqs):  # 使用 list() 创建副本以避免修改迭代器
        seq_editor.sequences.remove(seq)

# 设置场景参数
scene = bpy.context.scene
scene.render.fps = {fps}
scene.render.resolution_x = {width}
scene.render.resolution_y = {height}
scene.render.resolution_percentage = {resolution_percentage}

# 设置渲染输出格式
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
scene.render.ffmpeg.audio_codec = 'AAC'

# 设置输出路径
scene.render.filepath = r'{output_path}'

print("Blender script initialized successfully")
"""

CLIP_VIDEO_TEMPLATE = """
# 导入视频文件
video_path = r'{video_path}'
strip = seq_editor.sequences.new_movie(
    name="video_clip",
    filepath=video_path,
    channel=1,
    frame_start=1
)

# 设置裁剪范围
# 视频 FPS: {fps}
# 开始时间: {start_time}s -> 帧: {start_frame}
# 结束时间: {end_time}s -> 帧: {end_frame}

# 裁剪视频（通过调整 strip 的 frame_final_start 和 frame_final_end）
strip.frame_offset_start = {start_frame}
strip.frame_final_end = {end_frame} - {start_frame} + 1

# 设置场景的渲染帧范围
scene.frame_start = 1
scene.frame_end = {end_frame} - {start_frame} + 1

print(f"Video clip set: {{strip.frame_final_start}} to {{strip.frame_final_end}}")
"""

ADD_EFFECT_TEMPLATE = """
# 添加特效: {effect_type}
{effect_code}
"""

FADE_IN_EFFECT = """
# 淡入效果
fade_duration = {fade_duration}  # 秒
fade_frames = int(fade_duration * {fps})

# 添加淡入淡出序列
fade = seq_editor.sequences.new_effect(
    name="fade_in",
    type='GAMMA_CROSS',
    channel=2,
    frame_start=1,
    frame_end=fade_frames,
    seq1=strip
)
"""

SLOW_MOTION_EFFECT = """
# 慢动作效果
speed_factor = {speed_factor}  # 0.5 = 50% 速度（慢两倍）

# 添加速度控制
speed_strip = seq_editor.sequences.new_effect(
    name="slow_motion",
    type='SPEED',
    channel=2,
    frame_start=strip.frame_final_start,
    frame_end=strip.frame_final_end,
    seq1=strip
)
speed_strip.speed_factor = speed_factor

# 调整场景长度以适应慢动作
original_length = scene.frame_end - scene.frame_start + 1
scene.frame_end = int(original_length / speed_factor)
"""

ADD_TEXT_TEMPLATE = """
# 添加文字
text_content = "{text_content}"
text_duration = {text_duration}  # 秒
text_frames = int(text_duration * {fps})

# 创建文本序列
text_strip = seq_editor.sequences.new_effect(
    name="text_overlay",
    type='TEXT',
    channel=3,
    frame_start={text_start_frame},
    frame_end={text_start_frame} + text_frames
)
text_strip.text = text_content
text_strip.font_size = {font_size}
text_strip.location[0] = {text_x}  # X 位置 (0-1)
text_strip.location[1] = {text_y}  # Y 位置 (0-1)
text_strip.color = ({color_r}, {color_g}, {color_b}, 1.0)
"""

RENDER_COMMAND = """
# 开始渲染
print("Starting render...")
bpy.ops.render.render(animation=True, write_still=False)
print(f"Render complete! Output: {{scene.render.filepath}}")
"""
