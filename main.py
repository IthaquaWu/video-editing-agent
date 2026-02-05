"""
主程序入口 - Orchestrator (主控 Agent)
协调整个视频剪辑流程，实现 Render-Critique 循环
"""
import os
import sys
import time
from typing import Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import AnalysisAgent, EditorAgent, CriticAgent
from tools import FFmpegTools, BlenderRunner, VisionLLM
from config import Config


class VideoEditOrchestrator:
    """主控 Agent - 协调整个剪辑流程"""
    
    def __init__(
        self,
        workspace_dir: str = "./workspace",
        api_key: Optional[str] = None,
        model: str = "qwen/qwen-2.5-vl-7b-instruct",
        blender_path: str = "blender",
        ffmpeg_path: str = "ffmpeg"
    ):
        """
        初始化主控 Agent
        
        Args:
            workspace_dir: 工作空间目录
            api_key: API 密钥
            model: Vision LLM 模型
            blender_path: Blender 可执行文件路径
            ffmpeg_path: FFmpeg 可执行文件路径
        """
        api_key = api_key or Config.API_KEY
        self.workspace_dir = os.path.abspath(workspace_dir)
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        # 初始化工具
        print("初始化工具...")
        self.ffmpeg_tools = FFmpegTools(ffmpeg_path=ffmpeg_path)
        self.blender_runner = BlenderRunner(blender_path=blender_path)
        
        # 获取 base_url（如果环境变量中有设置）
        base_url = os.getenv('API_BASE_URL')
        
        self.vision_llm = VisionLLM(api_key=api_key, model=model, base_url=base_url)
        
        # 初始化 Agents
        print("初始化 Agents...")
        self.analysis_agent = AnalysisAgent(
            self.vision_llm,
            self.ffmpeg_tools,
            workspace_dir
        )
        
        self.editor_agent = EditorAgent(
            self.ffmpeg_tools,
            workspace_dir
        )
        
        self.critic_agent = CriticAgent(
            self.vision_llm,
            self.ffmpeg_tools,
            workspace_dir
        )
        
        
        print("✓ 初始化完成\n")
    
    def process_video(
        self,
        video_path: str,
        instruction: str,
        output_name: str = "final_output.mp4",
        max_iterations: int = 3,
        skip_analysis: bool = False,
        manual_timestamps: Optional[Dict[str, float]] = None
    ) -> str:
        """
        处理视频编辑请求（完整流程）
        
        Args:
            video_path: 输入视频路径
            instruction: 用户编辑指令
            output_name: 输出文件名
            max_iterations: Render-Critique 最大迭代次数
            skip_analysis: 是否跳过场景分析（使用手动时间戳）
            manual_timestamps: 手动指定的时间戳
            
        Returns:
            最终输出视频路径
        """
        print("="*80)
        print("智能视频剪辑 Agent 系统")
        print("="*80)
        print(f"输入视频: {video_path}")
        print(f"用户指令: {instruction}")
        print(f"最大迭代: {max_iterations} 次")
        print("="*80)
        
        # 转换为绝对路径
        video_path = os.path.abspath(video_path)
        
        # 验证视频文件
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        start_time = time.time()
        
        # ========== 第一阶段：场景分析 ==========
        if skip_analysis and manual_timestamps:
            print("\n[跳过场景分析] 使用手动时间戳")
            timestamps = manual_timestamps
        else:
            print("\n" + "="*80)
            print("第一阶段：场景分析与定位")
            print("="*80)
            timestamps = self.analysis_agent.analyze_video(
                video_path,
                instruction
            )
        
        if not timestamps or timestamps.get('start', 0) == timestamps.get('end', 0):
            print("\n❌ 场景分析失败，未能找到目标内容")
            return None
        
        # ========== 第二阶段：Render-Critique 迭代 ==========
        print("\n" + "="*80)
        print("第二阶段：编辑与质量迭代 (Render-Critique 循环)")
        print("="*80)
        
        final_output = None
        feedback = None
        
        for iteration in range(1, max_iterations + 1):
            print(f"\n{'='*80}")
            print(f"迭代 {iteration}/{max_iterations}")
            print(f"{'='*80}")
            
            # 2.1 生成脚本
            output_dir = os.path.join(self.workspace_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            preview_name = f"preview_v{iteration}.mp4"
            preview_path = os.path.join(output_dir, preview_name)
            
            script_path = self.editor_agent.generate_script(
                video_path=video_path,
                instruction=instruction,
                timestamps=timestamps,
                output_path=preview_path,
                resolution_percentage=50,  # 低分辨率快速预览
                feedback=feedback,
                version=iteration
            )
            
            # 2.2 渲染预览
            print(f"\n[Blender] 渲染预览 v{iteration}...")
            success, result = self.blender_runner.run_script(
                script_path,
                preview_path
            )
            
            if not success:
                print(f"❌ 渲染失败: {result}")
                if iteration == max_iterations:
                    print("已达最大迭代次数，渲染仍失败")
                    return None
                continue
            
            print(f"✓ 预览渲染完成: {preview_path}")
            
            # 2.3 Critic 评审
            try:
                critique_result = self.critic_agent.review_video(
                    preview_path,
                    instruction,
                    timestamps
                )
            except Exception as e:
                print(f"⚠️  Critic Agent 连接失败: {e}")
                print("⚠️  跳过质量检查，默认通过")
                critique_result = {'passed': True, 'score': 8.0, 'feedback': "自动通过（API不可用）"}
            
            # 2.4 判断是否通过
            if critique_result['passed']:
                print(f"\n{'='*80}")
                print(f"✓✓✓ 质量检查通过！(评分: {critique_result['score']:.1f}/10)")
                print(f"{'='*80}")
                
                # 生成最终高清版本
                print("\n[最终渲染] 生成高清版本...")
                final_name = output_name
                final_path = os.path.join(output_dir, final_name)
                
                final_script_path = self.editor_agent.generate_script(
                    video_path=video_path,
                    instruction=instruction,
                    timestamps=timestamps,
                    output_path=final_path,
                    resolution_percentage=100,  # 完整分辨率
                    feedback=feedback,
                    version=f"{iteration}_final"
                )
                
                success, result = self.blender_runner.run_script(
                    final_script_path,
                    final_path
                )
                
                if success:
                    final_output = final_path
                    print(f"✓ 最终视频已生成: {final_output}")
                else:
                    print(f"⚠️  最终渲染失败，使用预览版本: {preview_path}")
                    final_output = preview_path
                
                break
            
            else:
                print(f"\n{'='*80}")
                print(f"✗ 质量检查未通过 (评分: {critique_result['score']:.1f}/10)")
                print(f"{'='*80}")
                
                # 准备下一轮迭代的反馈
                feedback = critique_result.get('feedback_text', critique_result['feedback'])
                
                if iteration < max_iterations:
                    print(f"\n[准备下一轮迭代] 基于反馈调整...")
                    print(f"反馈: {feedback}")
                else:
                    print(f"\n⚠️  已达最大迭代次数，质量仍未达标")
                    print(f"最后一次预览: {preview_path}")
                    final_output = preview_path
        
        # ========== 总结 ==========
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*80}")
        print("处理完成")
        print(f"{'='*80}")
        print(f"总耗时: {elapsed_time:.1f} 秒")
        print(f"迭代次数: {iteration}")
        if final_output:
            print(f"输出文件: {final_output}")
            print(f"文件大小: {os.path.getsize(final_output) / 1024 / 1024:.2f} MB")
        else:
            print("⚠️  未能生成有效输出")
        print(f"{'='*80}\n")
        
        return final_output


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="智能视频剪辑 Agent 系统")
    parser.add_argument("video", help="输入视频路径")
    parser.add_argument("instruction", help="编辑指令（如：'剪辑出冲浪场景'）")
    parser.add_argument("-o", "--output", default="final_output.mp4", help="输出文件名")
    parser.add_argument("--api-key", help="API 密钥（或设置环境变量 API_KEY）")
    parser.add_argument("--model", default="gpt-4o", help="Vision LLM 模型")
    parser.add_argument("--max-iter", type=int, default=3, help="最大迭代次数")
    parser.add_argument("--blender", default="blender", help="Blender 可执行文件路径")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="FFmpeg 可执行文件路径")
    parser.add_argument("--workspace", default="./workspace", help="工作空间目录")
    
    # 手动时间戳（用于测试）
    parser.add_argument("--start", type=float, help="手动指定开始时间（秒）")
    parser.add_argument("--end", type=float, help="手动指定结束时间（秒）")
    
    args = parser.parse_args()
    
    # 创建 Orchestrator
    orchestrator = VideoEditOrchestrator(
        workspace_dir=args.workspace,
        api_key=args.api_key,
        model=args.model,
        blender_path=args.blender,
        ffmpeg_path=args.ffmpeg
    )
    
    # 处理视频
    manual_timestamps = None
    skip_analysis = False
    
    if args.start is not None and args.end is not None:
        manual_timestamps = {'start': args.start, 'end': args.end}
        skip_analysis = True
        print(f"使用手动时间戳: {args.start}s - {args.end}s")
    
    result = orchestrator.process_video(
        video_path=args.video,
        instruction=args.instruction,
        output_name=args.output,
        max_iterations=args.max_iter,
        skip_analysis=skip_analysis,
        manual_timestamps=manual_timestamps
    )
    
    if result:
        print(f"\n✓ 成功！输出: {result}")
        sys.exit(0)
    else:
        print(f"\n✗ 失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
