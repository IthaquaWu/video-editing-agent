# 智能视频编辑代理系统 (Video Editing Agent)

一个基于 AI 的智能视频编辑代理系统，使用 Vision LLM 进行视频内容理解，结合 FFmpeg 和 Blender 实现自动化视频剪辑。系统采用多代理协作架构，实现 Render-Critique 循环机制，确保输出视频质量。

## 🎯 核心功能

- **智能场景分析**：通过 Vision LLM 自动识别和定位视频中的特定场景
- **自动化剪辑**：基于用户指令生成专业的视频剪辑
- **质量评审**：实现 Render-Critique 循环，确保输出视频质量
- **多代理协作**：分析代理、编辑代理、评审代理协同工作
- **支持多种视频格式**：MP4、MKV 等常见视频格式

## 🏗️ 系统架构

### 多代理协作架构

```
用户指令 → Orchestrator (主控代理) → 多代理协作流程
    ↓
Analysis Agent (分析代理) → 场景定位
    ↓  
Editor Agent (编辑代理) → 脚本生成
    ↓
Blender Runner → 视频渲染
    ↓
Critic Agent (评审代理) → 质量检查
    ↓
Render-Critique 循环 (最多3次迭代)
（机制：这是一种质量保证范式，特别适用于生成视觉内容(如视频、PPT、图像)的场景。
工作流程：Editor Agent 生成代码 → 渲染执行 → Critic Agent 使用 Vision LLM 分析渲染结果 → 提出改进建议 → Editor Agent 调整代码 → 重新渲染，如此迭代直到质量达标。
核心思想：Agent 生成代码或配置后，无法直接判断最终渲染效果是否符合预期，必须通过实际渲染并使用 Vision LLM 检查视觉输出。
```

## 📁 项目结构详解

```
智能视频编辑代理系统/
├── agents/                 # AI 代理模块
│   ├── analysis_agent.py   # 视频分析代理 - 场景识别和定位
│   ├── editor_agent.py     # 视频编辑代理 - Blender脚本生成
│   └── critic_agent.py     # 质量评审代理 - Render-Critique机制
├── tools/                  # 工具模块
│   ├── ffmpeg_tools.py     # FFmpeg 工具封装 - 视频处理
│   ├── blender_runner.py   # Blender 执行器 - 脚本运行
│   └── vision_utils.py     # 视觉处理工具 - Vision LLM集成
├── templates/              # 模板文件
│   └── blender_base.py     # Blender 基础脚本模板
├── workspace/              # 工作空间
│   ├── frames/             # 提取的视频帧
│   ├── scripts/            # 生成的编辑脚本
│   └── output/             # 输出视频文件
├── frontend/               # 前端界面 (React + Vite)
│   ├── src/
│   │   ├── app/            # React组件
│   │   ├── services/       # API服务层
│   │   └── styles/         # 样式文件
│   └── package.json        # 前端依赖
├── main.py                 # 主入口文件 - Orchestrator
├── config.py               # 配置管理
├── example_usage.py        # 使用示例
├── requirements.txt        # Python依赖
├── develop_plan.md         # 开发计划
└── README.md              # 项目说明
```

## 🔧 详细功能模块说明

### 1. 主控模块 (Orchestrator)

**文件**: [main.py](file:///e:/DHU/2026寒假/AI%20Agent%202026/video_editing_agent/main.py)

**功能**:
- 协调整个视频剪辑流程
- 实现 Render-Critique 循环机制
- 管理多代理协作和状态流转
- 控制最大迭代次数，防止无限循环

**核心方法**:
- `process_video()`: 主处理流程
- `_run_render_critique_loop()`: Render-Critique 循环
- `_cleanup_workspace()`: 工作空间清理

### 2. AI 代理模块 (Agents)

#### 2.1 分析代理 (Analysis Agent)
**文件**: [agents/analysis_agent.py](file:///e:/DHU/2026寒假/AI%20Agent%202026/video_editing_agent/agents/analysis_agent.py)

**功能**:
- 使用 Vision LLM 分析视频内容
- 采用粗粒度 + 精细粒度的两步定位策略
- 识别和定位用户指定的场景
- 返回精确的时间戳信息

**核心方法**:
- `analyze_video()`: 视频分析主方法
- `_coarse_scan()`: 粗粒度扫描
- `_fine_scan()`: 精细粒度扫描

#### 2.2 编辑代理 (Editor Agent)
**文件**: [agents/editor_agent.py](file:///e:/DHU/2026寒假/AI%20Agent%202026/video_editing_agent/agents/editor_agent.py)

**功能**:
- 基于用户指令生成 Blender Python 脚本
- 处理视频剪辑、转场、特效等操作
- 支持模板化脚本生成
- 可扩展的编辑效果库

**核心方法**:
- `generate_script()`: 生成编辑脚本
- `_apply_editing_effects()`: 应用编辑效果

#### 2.3 评审代理 (Critic Agent)
**文件**: [agents/critic_agent.py](file:///e:/DHU/2026寒假/AI%20Agent%202026/video_editing_agent/agents/critic_agent.py)

**功能**:
- 通过 Vision LLM 检查渲染结果质量
- 实现 Render-Critique 机制
- 提供质量评分和改进建议
- 控制迭代终止条件

**核心方法**:
- `review_video()`: 视频质量评审
- `_extract_key_frames()`: 提取关键帧
- `_assess_quality()`: 质量评估

### 3. 工具模块 (Tools)

#### 3.1 FFmpeg 工具
**文件**: [tools/ffmpeg_tools.py](file:///e:/DHU/2026寒假/AI%20Agent%202026/video_editing_agent/tools/ffmpeg_tools.py)

**功能**:
- 视频截帧和元数据提取
- 视频格式转换和处理
- 音频处理和时间戳管理
- 支持多种视频格式

**核心方法**:
- `extract_frames()`: 提取视频帧
- `get_video_info()`: 获取视频信息
- `trim_video()`: 视频剪辑

#### 3.2 Blender 运行器
**文件**: [tools/blender_runner.py](file:///e:/DHU/2026寒假/AI%20Agent%202026/video_editing_agent/tools/blender_runner.py)

**功能**:
- 执行 Blender Python 脚本
- 支持低分辨率预览渲染
- 错误处理和日志记录
- 资源管理和清理

**核心方法**:
- `run_script()`: 运行 Blender 脚本
- `_validate_installation()`: 验证安装

#### 3.3 Vision LLM 工具
**文件**: [tools/vision_utils.py](file:///e:/DHU/2026寒假/AI%20Agent%202026/video_editing_agent/tools/vision_utils.py)

**功能**:
- 封装多种 Vision LLM API 调用
- 支持 OpenAI GPT-4o、Wan-AI、Gemini 等模型
- 图像编码和批量处理
- Mock 模式支持（无 API Key 时）

**核心方法**:
- `analyze_images()`: 分析图像内容
- `_encode_image()`: 图像编码

### 4. 前端界面 (Frontend)

**目录**: [frontend/](file:///e:/DHU/2026寒假/AI%20Agent%202026/video_editing_agent/frontend)

**技术栈**: React + TypeScript + Vite + Tailwind CSS

**功能模块**:
- **视频上传组件**: 拖拽上传、进度显示
- **指令输入组件**: 预设指令、智能提示
- **进度指示器**: 实时进度、步骤状态
- **视频预览组件**: 前后对比、结果展示

**API 集成**:
- 完整的后端 API 服务层
- 实时状态轮询机制
- 错误处理和重试逻辑

### 5. 配置管理

**文件**: [config.py](file:///e:/DHU/2026寒假/AI%20Agent%202026/video_editing_agent/config.py)

**配置项**:
- API 密钥和端点配置
- 工具路径 (Blender, FFmpeg)
- 工作空间目录
- 场景分析参数
- Render-Critique 配置

## 🚀 快速开始

### 环境要求

- **Python**: 3.10+
- **系统工具**: Blender 3.0+, FFmpeg
- **API 密钥**: Wan-AI 或 OpenAI GPT-4o

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd video_editing_agent
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置 API 密钥和工具路径
```

4. **启动前端** (可选)
```bash
cd frontend
npm install
npm run dev
```

5. **运行示例**
```bash
python example_usage.py
```

## 📋 使用示例

### 基本剪辑
```python
from main import VideoEditOrchestrator

orchestrator = VideoEditOrchestrator()
result = orchestrator.process_video(
    video_path="surfing.mp4",
    instruction="剪辑掉视频开始的前五秒",
    output_name="surfing_clip.mp4"
)
```

### 高级编辑
```python
result = orchestrator.process_video(
    video_path="action_scene.mp4",
    instruction="为关键动作添加慢动作效果，并添加转场",
    output_name="action_edited.mp4",
    max_iterations=3  # 最多3次质量迭代
)
```

## 🔄 Render-Critique 机制

系统采用先进的 Render-Critique 循环机制：

1. **生成**: Editor Agent 生成编辑脚本
2. **渲染**: Blender 执行脚本生成预览
3. **评审**: Critic Agent 检查渲染质量
4. **迭代**: 如果不达标，重新生成和改进
5. **终止**: 达到质量阈值或最大迭代次数

## 🛠️ 技术栈

### 后端技术
- **编程语言**: Python 3.10+
- **AI 模型**: Vision LLM (GPT-4o/Wan-AI/Gemini)
- **视频处理**: FFmpeg, OpenCV
- **专业编辑**: Blender Python API
- **配置管理**: dotenv, Python Config

### 前端技术
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **UI 组件**: Radix UI, Lucide Icons
- **状态管理**: React Hooks

### 开发工具
- **代码格式化**: Black
- **测试框架**: pytest
- **依赖管理**: pip, npm
- **版本控制**: Git

## 📊 性能优化

- **智能帧提取**: 粗粒度+精细粒度两级扫描
- **低分辨率预览**: 快速迭代验证
- **缓存机制**: 避免重复处理
- **并行处理**: 多代理协作
- **资源管理**: 自动清理临时文件

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 🙏 致谢

- **Wan-AI**: 提供优秀的 Vision LLM 服务
- **Blender**: 强大的开源视频编辑工具
- **FFmpeg**: 业界标准的多媒体处理工具
- **OpenAI**: GPT-4o Vision 模型支持

---
