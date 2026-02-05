"""
示例使用脚本 - 演示如何使用智能视频剪辑 Agent

运行前请确保：
1. 已安装所有依赖 (pip install -r requirements.txt)
2. 已配置 .env 文件（API Key 等）
3. 系统已安装 Blender 和 FFmpeg
"""
import os
from main import VideoEditOrchestrator
from config import Config


def example_1_basic_clip():
    """示例 1：基本剪辑 - 提取特定场景"""
    print("\n" + "="*80)
    print("示例 1：基本场景剪辑")
    print("="*80)
    
    orchestrator = VideoEditOrchestrator(
        workspace_dir="./workspace",
        api_key=Config.API_KEY,
        model=Config.VISION_MODEL,
        blender_path=Config.BLENDER_PATH,
        ffmpeg_path=Config.FFMPEG_PATH
    )
    
    # 假设你有一个视频文件
    video_path = "surfing.mp4"  # 替换为你的视频路径
    
    if not os.path.exists(video_path):
        print(f"⚠️  视频文件不存在: {video_path}")
        print("请先准备一个测试视频")
        return
    
    result = orchestrator.process_video(
        video_path=video_path,
        instruction="剪辑掉视频开始的前五秒",
        output_name="surfing_clip.mp4",
        max_iterations=3
    )
    
    if result:
        print(f"\n✓ 成功！输出文件: {result}")
    else:
        print(f"\n✗ 剪辑失败")


def example_2_manual_timestamps():
    """示例 2：使用手动时间戳（跳过场景分析）"""
    print("\n" + "="*80)
    print("示例 2：手动指定时间戳")
    print("="*80)
    
    orchestrator = VideoEditOrchestrator(
        workspace_dir="./workspace",
        api_key=Config.API_KEY,
        model=Config.VISION_MODEL,
        blender_path=Config.BLENDER_PATH,
        ffmpeg_path=Config.FFMPEG_PATH
    )
    
    video_path = "example_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"⚠️  视频文件不存在: {video_path}")
        return
    
    # 直接指定时间范围：从 2秒 到 8秒 (适应测试视频)
    result = orchestrator.process_video(
        video_path=video_path,
        instruction="剪辑 2秒 到 8秒 的片段",
        output_name="manual_clip.mp4",
        max_iterations=2,
        skip_analysis=True,
        manual_timestamps={'start': 2, 'end': 8}  # 秒
    )
    
    if result:
        print(f"\n✓ 成功！输出文件: {result}")


def example_3_render_critique_demo():
    """示例 3：演示 Render-Critique 迭代过程"""
    print("\n" + "="*80)
    print("示例 3：Render-Critique 机制演示")
    print("="*80)
    print("此示例将展示系统如何通过多次迭代优化剪辑质量\n")
    
    orchestrator = VideoEditOrchestrator(
        workspace_dir="./workspace",
        api_key=Config.API_KEY,
        model=Config.VISION_MODEL,
        blender_path=Config.BLENDER_PATH,
        ffmpeg_path=Config.FFMPEG_PATH
    )
    
    video_path = "example_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"⚠️  视频文件不存在: {video_path}")
        return
    
    # 更复杂的指令，可能需要多次迭代
    result = orchestrator.process_video(
        video_path=video_path,
        instruction="提取滑雪者跳跃的完整过程，从起跳到落地",
        output_name="skiing_jump_complete.mp4",
        max_iterations=3  # 允许最多 3 次迭代优化
    )
    
    if result:
        print(f"\n✓ 成功！输出文件: {result}")
        print("\n请查看 workspace/output/ 目录，可以看到:")
        print("  - preview_v1.mp4  (第一次尝试)")
        print("  - preview_v2.mp4  (第二次优化，如果有)")
        print("  - preview_v3.mp4  (第三次优化，如果有)")
        print("  - skiing_jump_complete.mp4 (最终高清版本)")


def example_4_test_without_video():
    """示例 4：测试系统配置（不需要视频文件）"""
    print("\n" + "="*80)
    print("示例 4：系统配置测试")
    print("="*80)
    
    # 验证配置
    errors = Config.validate()
    if errors:
        print("配置错误:")
        for error in errors:
            print(f"  ✗ {error}")
        return
    
    print("✓ 配置验证通过\n")
    Config.print_config()
    
    # 测试工具初始化
    try:
        from tools import FFmpegTools, BlenderRunner, VisionLLM
        
        print("\n测试工具初始化...")
        
        ffmpeg = FFmpegTools()
        print("  ✓ FFmpeg 工具初始化成功")
        
        blender = BlenderRunner()
        print("  ✓ Blender 运行器初始化成功")
        
        vision = VisionLLM(api_key=Config.API_KEY, model=Config.VISION_MODEL)
        print("  ✓ Vision LLM 初始化成功")
        
        print("\n✓ 所有工具初始化成功！系统已就绪。")
        
    except Exception as e:
        print(f"\n✗ 工具初始化失败: {e}")


def main():
    """主函数 - 选择要运行的示例"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║          智能视频剪辑 Agent 系统 - 示例脚本                    ║
╚════════════════════════════════════════════════════════════════╝
    
请选择要运行的示例:
    
  1. 基本场景剪辑（需要视频文件）
  2. 手动指定时间戳（需要视频文件）
  3. Render-Critique 迭代演示（需要视频文件）
  4. 系统配置测试（无需视频文件）
  0. 退出
    """)
    
    choice = input("请输入选项 (0-4): ").strip()
    
    examples = {
        '1': example_1_basic_clip,
        '2': example_2_manual_timestamps,
        '3': example_3_render_critique_demo,
        '4': example_4_test_without_video,
    }
    
    if choice == '0':
        print("再见！")
        return
    
    if choice in examples:
        examples[choice]()
    else:
        print("无效选项")


if __name__ == "__main__":
    main()
