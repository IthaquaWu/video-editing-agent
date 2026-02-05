"""
配置管理模块
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """全局配置类"""
    
    # API 配置
    API_KEY = os.getenv('API_KEY', os.getenv('OPENAI_API_KEY', ''))
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://api.wan-ai.com/v1')
    VISION_MODEL = os.getenv('VISION_MODEL', 'Wan-AI/Wan2.2-I2V-A14B')
    
    # 工具路径
    BLENDER_PATH = os.getenv('BLENDER_PATH', 'blender')
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', 'ffmpeg')
    
    # 工作空间
    WORKSPACE_DIR = os.getenv('WORKSPACE_DIR', './workspace')
    
    # 场景分析配置
    COARSE_INTERVAL = int(os.getenv('COARSE_INTERVAL', '10'))  # 粗粒度：每10秒
    FINE_INTERVAL = int(os.getenv('FINE_INTERVAL', '1'))       # 精细粒度：每1秒
    
    # Render-Critique 配置
    MAX_ITERATIONS = int(os.getenv('MAX_ITERATIONS', '3'))     # 最大迭代次数
    PREVIEW_RESOLUTION = int(os.getenv('PREVIEW_RESOLUTION', '50'))  # 预览分辨率百分比
    QUALITY_THRESHOLD = float(os.getenv('QUALITY_THRESHOLD', '7.0'))  # 质量通过阈值
    
    # Blender 渲染配置
    DEFAULT_FPS = int(os.getenv('DEFAULT_FPS', '30'))
    DEFAULT_FORMAT = os.getenv('DEFAULT_FORMAT', 'FFMPEG')
    DEFAULT_CODEC = os.getenv('DEFAULT_CODEC', 'H264')
    
    @classmethod
    def validate(cls):
        """验证配置"""
        errors = []
        
        if not cls.API_KEY:
            errors.append("API_KEY 未设置（请在 .env 文件中配置）")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """打印当前配置（隐藏敏感信息）"""
        print("当前配置:")
        print(f"  Vision Model: {cls.VISION_MODEL}")
        print(f"  API Base URL: {cls.API_BASE_URL}")
        print(f"  API Key: {'*' * 20 if cls.API_KEY else '(未设置)'}")
        print(f"  Blender: {cls.BLENDER_PATH}")
        print(f"  FFmpeg: {cls.FFMPEG_PATH}")
        print(f"  Workspace: {cls.WORKSPACE_DIR}")
        print(f"  Max Iterations: {cls.MAX_ITERATIONS}")
        print(f"  Quality Threshold: {cls.QUALITY_THRESHOLD}")
