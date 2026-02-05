"""
Critic Agent
负责通过 Vision LLM 检查渲染结果，实现 Render-Critique 机制
"""
import os
from typing import Dict, List, Optional
from tools.ffmpeg_tools import FFmpegTools
from tools.vision_utils import VisionLLM


class CriticAgent:
    """Critic Agent - 视觉质量评审"""
    
    def __init__(
        self,
        vision_llm: VisionLLM,
        ffmpeg_tools: FFmpegTools,
        workspace_dir: str
    ):
        """
        初始化 Critic Agent
        
        Args:
            vision_llm: Vision LLM 实例
            ffmpeg_tools: FFmpeg 工具实例
            workspace_dir: 工作空间目录
        """
        self.vision_llm = vision_llm
        self.ffmpeg_tools = ffmpeg_tools
        self.workspace_dir = workspace_dir
    
    def review_video(
        self,
        preview_path: str,
        original_instruction: str,
        timestamps: Dict[str, float],
        num_frames: int = 5
    ) -> Dict[str, any]:
        """
        评审渲染的预览视频
        
        Args:
            preview_path: 预览视频路径
            original_instruction: 用户原始指令
            timestamps: 当前使用的时间戳
            num_frames: 要提取用于评审的关键帧数量
            
        Returns:
            评审结果字典，包含 passed, score, feedback, issues 等字段
        """
        print(f"\n[Critic Agent] 开始评审预览视频...")
        print(f"  - 预览文件: {os.path.basename(preview_path)}")
        
        if not os.path.exists(preview_path):
            return {
                'passed': False,
                'score': 0.0,
                'feedback': f"预览文件不存在: {preview_path}",
                'issues': ['文件不存在']
            }
        
        # 提取关键帧
        frames_dir = os.path.join(self.workspace_dir, "frames", "preview")
        os.makedirs(frames_dir, exist_ok=True)
        
        frame_paths = self.ffmpeg_tools.extract_key_frames_from_preview(
            preview_path,
            frames_dir,
            num_frames=num_frames
        )
        
        if not frame_paths:
            return {
                'passed': False,
                'score': 0.0,
                'feedback': "无法从预览视频提取关键帧",
                'issues': ['帧提取失败']
            }
        
        print(f"  - 已提取 {len(frame_paths)} 个关键帧用于评审")
        
        # 构建评审提示
        prompt = self._build_critique_prompt(original_instruction, timestamps)
        
        # 调用 Vision LLM 进行评审
        response = self.vision_llm.ask_with_images(prompt, frame_paths, max_tokens=1500)
        
        # 解析评审结果
        result = self._parse_critique_response(response)
        
        # 输出评审结果
        print(f"\n[评审结果]")
        print(f"  - 是否通过: {'✓ 通过' if result['passed'] else '✗ 未通过'}")
        print(f"  - 质量评分: {result['score']:.1f}/10")
        print(f"  - 反馈意见: {result['feedback']}")
        if result['issues']:
            print(f"  - 发现问题:")
            for issue in result['issues']:
                print(f"    • {issue}")
        
        return result
    
    def _build_critique_prompt(
        self,
        instruction: str,
        timestamps: Dict[str, float]
    ) -> str:
        """
        构建评审提示词
        
        Args:
            instruction: 用户原始指令
            timestamps: 当前时间戳
            
        Returns:
            提示词文本
        """
        prompt = f"""
你是一位专业的视频剪辑质量评审专家。我将向你展示一个视频片段的关键帧序列（按时间顺序排列）。

【用户原始需求】
{instruction}

【当前剪辑参数】
- 开始时间: {timestamps['start']:.2f} 秒
- 结束时间: {timestamps['end']:.2f} 秒
- 片段时长: {timestamps['end'] - timestamps['start']:.2f} 秒

【评审任务】
请基于关键帧仔细检查以下方面，并给出专业评价：

1. **内容完整性**
   - 视频是否完整包含用户要求的场景/动作？
   - 是否有关键内容被遗漏？
   - 是否包含了不相关的内容？

2. **时间点准确性**
   - 开始时间是否合适？（是否太早或太晚）
   - 结束时间是否合适？（动作是否被截断或拖沓）
   - 建议如何调整开始/结束时间（向前/向后移动几秒）

3. **视觉质量**
   - 是否有黑屏、花屏、模糊等问题？
   - 画面是否清晰稳定？
   - 颜色是否正常？

4. **整体评价**
   - 给出 0-10 分的质量评分
   - 评分 >= 7.0 视为通过

【输出格式】
请严格按照以下 JSON 格式回复：

{{
    "passed": true/false,  // 是否通过（评分 >= 7.0）
    "score": 8.5,  // 质量评分 (0-10)
    "feedback": "简要总结你的评审意见（50字以内）",
    "issues": [  // 发现的问题列表
        "问题1描述",
        "问题2描述"
    ],
    "suggestions": [  // 改进建议列表
        "建议1",
        "建议2"
    ],
    "timing_adjustment": {{  // 时间调整建议
        "start_offset": 0,  // 开始时间偏移（秒），正数向后，负数向前
        "end_offset": 0,    // 结束时间偏移（秒），正数向后，负数向前
        "reason": "调整原因"
    }}
}}

【注意事项】
- 要求严格但公正
- 如果只是小瑕疵（不影响整体效果），仍可通过
- 如果有明显问题（如遗漏关键内容、时间点严重不准），必须标记为未通过
- 时间调整建议要具体明确（如"开头延后2秒"应设置 start_offset=2）
"""
        return prompt
    
    def _parse_critique_response(self, response: str) -> Dict[str, any]:
        """
        解析 Vision LLM 的评审响应
        
        Args:
            response: LLM 响应文本
            
        Returns:
            解析后的评审结果
        """
        try:
            result = self.vision_llm.parse_json_response(response)
            
            # 验证必需字段
            if 'passed' not in result:
                result['passed'] = result.get('score', 0) >= 7.0
            
            if 'score' not in result:
                result['score'] = 7.0 if result.get('passed', False) else 5.0
            
            if 'feedback' not in result:
                result['feedback'] = "无具体反馈"
            
            if 'issues' not in result:
                result['issues'] = []
            
            if 'suggestions' not in result:
                result['suggestions'] = []
            
            # 构建文字反馈（用于 Editor Agent）
            feedback_text = result['feedback']
            
            if 'timing_adjustment' in result and result['timing_adjustment']:
                adj = result['timing_adjustment']
                start_offset = adj.get('start_offset', 0)
                end_offset = adj.get('end_offset', 0)
                
                if start_offset != 0:
                    direction = "延后" if start_offset > 0 else "提前"
                    feedback_text += f" 开头{direction}{abs(start_offset)}秒。"
                
                if end_offset != 0:
                    direction = "延长" if end_offset > 0 else "缩短"
                    feedback_text += f" 结尾{direction}{abs(end_offset)}秒。"
                
                if adj.get('reason'):
                    feedback_text += f" 原因：{adj['reason']}"
            
            result['feedback_text'] = feedback_text
            
            return result
            
        except Exception as e:
            print(f"  ⚠️  解析评审响应失败: {e}")
            print(f"  原始响应: {response[:200]}...")
            
            # 返回保守的失败结果
            return {
                'passed': False,
                'score': 5.0,
                'feedback': "评审系统解析失败，建议人工检查",
                'feedback_text': "评审系统解析失败，建议人工检查",
                'issues': ['系统解析错误'],
                'suggestions': [],
                'raw_response': response
            }
