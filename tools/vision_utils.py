"""
Vision LLM 工具模块
封装调用 GPT-4o/Gemini/Wan-AI Vision API 的通用接口
"""
import base64
import functools
import logging
from typing import List, Dict, Any
import os
from pathlib import Path


class VisionLLM:
    """封装 Vision LLM 调用"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o", base_url: str = None):
        """
        初始化 Vision LLM
        
        Args:
            api_key: API 密钥（可从环境变量获取）
            model: 使用的模型名称
            base_url: API 基础 URL（用于自定义端点）
        """
        self.api_key = api_key or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url or os.getenv("API_BASE_URL")
        self.mock_mode = False
        # 缓存图片的 base64 编码，避免重复 IO/编码
        self._image_cache: Dict[str, str] = {}
        
        # 启用 Mock 模式（如果未设置 API Key）
        if self.api_key == "your-wan-ai-api-key-here" or not self.api_key:
            logging.warning("未检测到有效 API Key，启用 Mock 模式进行演示")
            self.mock_mode = True
            self.provider = "mock"
            return
        
        # 根据模型选择不同的客户端（归一化判断）
        model_lower = (model or "").lower()
        try:
            if "wan" in model_lower or "wan-ai" in model_lower:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url or "https://api.wan-ai.com/v1"
                )
                self.provider = "wan-ai"
            elif "gpt" in model_lower:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                self.provider = "openai"
            elif "gemini" in model_lower:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key or os.getenv("GOOGLE_API_KEY"))
                self.client = genai.GenerativeModel(model)
                self.provider = "google"
            else:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                self.provider = "custom"
        except Exception as e:
            logging.exception("初始化 VisionLLM 客户端失败，降级为 Mock 模式: %s", e)
            self.mock_mode = True
            self.provider = "mock"
    
    def encode_image(self, image_path: str) -> str:
        """
        将图片编码为 base64
        
        Args:
            image_path: 图片路径
            
        Returns:
            base64 编码的字符串
        """
        # 使用缓存减少重复读取与编码
        if image_path in self._image_cache:
            return self._image_cache[image_path]

        img_path = Path(image_path)
        if not img_path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with img_path.open("rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
            self._image_cache[image_path] = encoded
            return encoded
    
    def ask_with_images(
        self,
        prompt: str,
        image_paths: List[str],
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """
        使用图片和文本提示调用 Vision LLM
        
        Args:
            prompt: 文本提示
            image_paths: 图片路径列表
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            
        Returns:
            模型响应文本
        """
        if self.mock_mode:
            return self._mock_response(prompt, image_paths)

        if self.provider in ["openai", "wan-ai", "custom"]:
            return self._ask_openai(prompt, image_paths, max_tokens, temperature)
        if self.provider == "google":
            return self._ask_google(prompt, image_paths, max_tokens, temperature)

        raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _mock_response(self, prompt: str, image_paths: List[str]) -> str:
        """生成 Mock 响应"""
        import time
        import random
        import json
        
        time.sleep(1.5) # 模拟网络延迟
        
        prompt_lower = prompt.lower()
        
        # 场景分析 - 粗定位 (修复 prompt 匹配逻辑)
        if "coarse" in prompt or "粗定位" in prompt or "coarse_" in str(image_paths):
            print("  [Mock Vision] 模拟粗定位分析...")
            return json.dumps({
                "start": 20, 
                "end": 40, 
                "confidence": 0.95, 
                "reasoning": "在第20秒到40秒的关键帧中清晰地看到了冲浪板和海浪，这是典型的冲浪场景。"
            })
            
        # 场景分析 - 精定位
        if "fine_XXXX" in prompt or "真正开始时刻" in prompt:
            print("  [Mock Vision] 模拟精定位分析...")
            return json.dumps({
                "start": 24.5, 
                "end": 32.0, 
                "start_description": "冲浪者站起", 
                "end_description": "冲浪者落水"
            })
            
        # 质量评审 (Critic)
        if "质量评审" in prompt or "用户原始需求" in prompt:
            print("  [Mock Vision] 模拟质量评审...")
            # 简单的状态机逻辑：通过文件名或随机决定是否通过
            # 但为了演示 render-critique，我们可以根据 "feedback" 历史做判断
            # 这里简化：第一次总是失败，第二次总是成功
            
            # 使用一个简单的类变量或全局变量来追踪状态（由于 VisionLLM 实例可能会被重建，最好检查 prompt 上下文）
            # 或者随机
            # 这里我们假设如果 prompt 里包含某些关键词（这需要 orchestrated flow），或者简单地：
            # 如果是第一次调用（可以通过检查路径是否存在某些文件来判断，或者在内存中存状态）
            
            if not getattr(self, '_mock_critique_passed', False):
                self._mock_critique_passed = True
                return json.dumps({
                    "passed": False,
                    "score": 5.5,
                    "feedback": "主要内容已提取，但开始时间有点晚，导致错过了起跳动作。",
                    "issues": ["开始时间过晚", "前几帧动作不连贯"],
                    "suggestions": ["建议开头向前调整2秒"],
                    "timing_adjustment": {
                        "start_offset": -2.0,
                        "reason": "捕捉完整的起跳动作"
                    }
                })
            else:
                return json.dumps({
                    "passed": True,
                    "score": 9.0,
                    "feedback": "修正后的剪辑非常完美，完整捕捉了动作过程。",
                    "issues": [],
                    "suggestions": [],
                    "timing_adjustment": {}
                })
                
        return "{}"

    def flow_check(self, text: str) -> str:
        """占位助手：后续可扩展为更复杂的流程检查器"""
        return text
    
    def _ask_openai(
        self,
        prompt: str,
        image_paths: List[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """OpenAI GPT-4o 调用（带重试机制和错误处理）"""
        import time
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        # 添加图片
        for img_path in image_paths:
            try:
                if Path(img_path).is_file():
                    base64_image = self.encode_image(img_path)
                    messages[0]["content"].append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    })
            except Exception:
                logging.exception("添加图片时出错：%s", img_path)
        
        # 带重试的API调用
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # 尽量稳健地提取文本
                try:
                    return response.choices[0].message.content
                except Exception:
                    try:
                        return str(response)
                    except Exception:
                        logging.exception("无法解析 OpenAI 响应")
                        return ""
            except Exception as e:
                error_msg = str(e)
                logging.warning(f"OpenAI API 调用失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                
                # 检查是否为SSL错误
                if "SSL" in error_msg or "ConnectError" in error_msg:
                    logging.warning("检测到SSL连接错误，尝试使用备选HTTP客户端...")
                    # 尝试使用备选方案
                    alt_result = self._ask_openai_with_requests(prompt, image_paths, max_tokens, temperature)
                    if alt_result:
                        return alt_result
                
                if attempt < max_retries - 1:
                    logging.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    logging.error("所有重试尝试均失败")
                    return ""
    
    def _ask_openai_with_requests(
        self,
        prompt: str,
        image_paths: List[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """使用requests库作为备选方案调用OpenAI API"""
        try:
            import requests
            
            # 构建请求数据
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # 添加图片
            for img_path in image_paths:
                try:
                    if Path(img_path).is_file():
                        base64_image = self.encode_image(img_path)
                        messages[0]["content"].append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        })
                except Exception:
                    logging.exception("添加图片时出错：%s", img_path)
            
            # 确定API端点
            if self.provider == "wan-ai":
                api_url = self.base_url or "https://api.wan-ai.com/v1/chat/completions"
            else:
                api_url = self.base_url or "https://api.openai.com/v1/chat/completions"
            
            # 发送请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # 禁用SSL验证（仅作为最后手段）
            response = requests.post(
                api_url,
                headers=headers,
                json=data,
                timeout=30,
                verify=False  # 禁用SSL验证以绕过SSL错误
            )
            
            if response.status_code == 200:
                result = response.json()
                try:
                    return result["choices"][0]["message"]["content"]
                except Exception:
                    return str(result)
            else:
                logging.error(f"HTTP 请求失败: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logging.exception("备选HTTP客户端调用失败")
            return ""
    
    def _ask_google(
        self,
        prompt: str,
        image_paths: List[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Google Gemini Vision 调用"""
        try:
            from PIL import Image as PILImage
        except Exception:
            logging.exception("Pillow 未安装或导入失败，无法使用 google provider")
            raise

        contents = [prompt]
        for img_path in image_paths:
            try:
                if Path(img_path).is_file():
                    img = PILImage.open(img_path)
                    contents.append(img)
            except Exception:
                logging.exception("打开图片失败：%s", img_path)

        response = self.client.generate_content(
            contents,
            generation_config={"max_output_tokens": max_tokens, "temperature": temperature}
        )

        try:
            return response.text
        except Exception:
            logging.exception("无法解析 Google 返回内容")
            return str(response)
    
    def parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        从响应中提取 JSON 数据
        
        Args:
            response_text: 模型响应文本
            
        Returns:
            解析后的 JSON 字典
        """
        import json
        import re

        # 尝试直接解析（快速路径）
        try:
            return json.loads(response_text)
        except Exception:
            logging.debug("直接解析 JSON 失败，尝试从文本中抽取")

        # 尝试从 markdown 代码块中提取
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except Exception:
                logging.debug("从```json```提取 JSON 失败")

        # 尝试从文本中提取第一个 JSON 对象（保守匹配）
        json_match = re.search(r'\{[\s\S]*?\}', response_text)
        if json_match:
            candidate = json_match.group(0)
            try:
                return json.loads(candidate)
            except Exception:
                logging.debug("从文本中提取的 JSON 解析失败")

        raise ValueError(f"Cannot parse JSON from response (truncated): {response_text[:200]}")
