# Intelligent Video Editing System Development Constitution & Plan

（Qwen2-VL + Render-Critique · Low-Cost & High-Reliability）

⸻

0. 项目定位（Project Positioning）

本项目旨在构建一个跨平台（macOS / Windows）、低成本、高可靠性的智能视频剪辑系统。
系统以 Render-Critique 机制 为核心，通过“生成 → 渲染 → 视觉验收 → 迭代修正”的闭环，显著降低对单次模型推理准确性的依赖，从而在使用中等规模、低成本模型的前提下，仍能稳定输出高质量视频结果。

⸻

1. 最高原则（Supreme Principles｜不可违背）

以下原则优先级高于一切实现细节，任何违反都视为架构失败。

P1. Render Is Ground Truth（渲染即真值）
	•	系统不信任任何模型的中间推理
	•	最终判断只基于真实渲染画面
	•	一切质量保证必须来自 Render-Critique

P2. 模型可错，系统不可失控
	•	允许模型误判
	•	必须有纠错、回退、上限、终止条件
	•	不允许“无限迭代”或“无结果卡死”

P3. 低成本优先于强模型
	•	默认使用 免费 / 低价模型
	•	只有在明确触发条件下才升级模型
	•	不允许“全量强模型覆盖”

P4. 一切输出必须结构化
	•	Agent 之间只通过 JSON 通信
	•	不允许依赖“自然语言理解正确性”

⸻

2. 系统架构总览（System Architecture）

2.1 Agent 分工（不可合并）

1️⃣ Editor Agent（主控）
	•	职责：
	•	解析用户自然语言需求
	•	调度 Sub-Agent
	•	生成 / 修改 Blender Python 剪辑脚本
	•	禁止：
	•	直接判断视频效果好坏
	•	直接接触视觉真值

2️⃣ Video Analysis Sub-Agent（工作流 Agent）
	•	职责：
	•	ffmpeg 抽帧
	•	Vision LLM 问答
	•	输出场景时间边界
	•	特点：
	•	无决策权
	•	无状态
	•	可重复调用

3️⃣ Critic Agent（视觉验收 Agent）
	•	职责：
	•	读取渲染预览
	•	抽取关键帧
	•	判断是否达标
	•	输出可执行修正补丁
	•	唯一有资格说“通过/不通过”的 Agent

⸻

3. 模型宪法（Model Constitution｜已冻结）

3.1 Vision 模型（OpenRouter）

Tier 0（默认，0 成本）
	•	qwen/qwen-2.5-vl-7b-instruct:free
	•	用途：粗粒度场景定位 / 精细边界定位 / Render-Critique 视觉验收

Tier 1（回退升级，低成本）
	•	qwen/qwen-2.5-vl-7b-instruct
	•	升级触发条件（任一满足即升级）：
	•	同一问题两次回答边界差 > 2 秒
	•	Critic 无法给出 evidence frame
	•	OCR / 字幕可读性判断不稳定

❌ 禁止默认使用更强 Vision 模型

3.2 Text / Code 模型
	•	默认：qwen/qwen2.5-coder-7b-instruct
	•	用途：Blender Python 脚本生成 / Patch 应用 / 结构化日志输出

⸻

4. Render-Critique 机制宪法（核心）

4.1 Render-Critique 标准流程（不可简化）

Editor 生成脚本
→ Blender 低质量预览渲染
→ 抽取关键帧
→ Critic 视觉分析
→ JSON Patch
→ Editor 修改脚本
→ 循环

4.2 Critic 输出强制 Schema（示例）

{
  "pass": false,
  "issues": [
    {
      "type": "boundary_start_late",
      "severity": "high",
      "suggestion": { "delta_start_sec": -1.5 },
      "evidence_frame": "frame_00003.jpg"
    }
  ],
  "summary": "起始点偏晚，字幕可读性不足"
}

❌ 不允许 Critic 只给自然语言建议
✅ 必须给可直接执行的参数修改

⸻

5. 两步定位策略宪法（效率保证）

Step 1：粗粒度定位
	•	抽帧频率：1 帧 / 10 秒
	•	范围：全视频
	•	输出：一个或多个候选时间区间

Step 2：精细粒度定位
	•	抽帧频率：1 帧 / 秒
	•	范围：粗定位区间 ± buffer
	•	输出：精确 start / end 秒

❌ 禁止对全视频做 1fps 密集采样

⸻

6. 可靠性与稳定性约束（Mandatory Guards）

6.1 一致性检查
	•	同一定位问题至少 2 次 Vision 判断
	•	若差异 > 2 秒 → 升级 Vision 模型

6.2 迭代上限
	•	Render-Critique 最多 5 轮
	•	超过上限：
	•	输出最佳版本
	•	标记为 PARTIAL_PASS
	•	附带完整问题报告

6.3 修正幅度限制
	•	单轮 start/end 修正 ≤ ±3 秒
	•	防止震荡与过拟合

⸻

7. 成本控制宪法（必须可审计）

7.1 成本来源限制
	•	Vision 调用只允许发生在：
	•	抽帧分析
	•	Critic 验收
	•	禁止对连续视频流直接推理

7.2 成本日志
	•	每次调用必须记录：
	•	模型
	•	token 数
	•	场景阶段
	•	必须可生成 cost report

⸻

8. 跨平台宪法（macOS / Windows）
	•	ffmpeg：命令行统一
	•	Blender：只使用 Python API（VSE）
	•	路径：内部统一使用绝对路径（Python pathlib）
	•	字体：字幕字体随项目打包，不依赖系统字体

⸻

9. 项目阶段划分（Develop Plan）

Phase 1｜基础可运行（MVP）
	•	ffmpeg 抽帧
	•	Qwen2-VL 粗/精定位
	•	Blender 基础剪辑
	•	单轮 Render-Critique

Phase 2｜闭环稳定
	•	多轮 Render-Critique
	•	JSON Patch 自动应用
	•	成本/日志系统

Phase 3｜对比实验与评估
	•	无 Critique vs 有 Critique
	•	边界误差统计
	•	失败率、迭代轮数分析

⸻

10. 成功判定标准（Acceptance Criteria）
	•	场景起止误差 ≤ 3 秒
	•	特效（字幕 / 慢动作 / 转场）可见
	•	至少 1 次 Critic 触发修正
	•	最终视频可播放、格式正确
	•	全流程可复现、有日志

⸻

11. 最终宣言（Design Philosophy）

我们不追求一次推理的完美，
而是构建一个即使推理不完美，也能稳定产出正确结果的系统。

⸻

✅【新增】16. 依赖环境宪法（Environment｜必须冻结）

冻结后不得随意变更版本。任何变更必须走“架构变更提案（RFC）”。

E1. 运行时版本锁定（必须）
	•	Python：3.11.x（允许 3.10–3.12，但 CI 以 3.11 为准）
	•	Blender：固定一个版本（建议 3.6 LTS 或 4.0.x），写入 BLENDER_VERSION
	•	FFmpeg：固定 major（例如 ffmpeg 6.x），必须包含 ffprobe

E2. 环境分发方式（必须二选一）
	•	方案 A：environment.yml（Conda）
	•	方案 B：requirements.txt + python -m venv

项目必须提供 bootstrap 脚本，一键检查环境

E3. 必须存在的环境变量
	•	OPENROUTER_API_KEY
	•	BLENDER_BIN（blender 可执行文件路径）
	•	FFMPEG_BIN（可选，找不到系统 ffmpeg 时使用）

E4. Bootstrap 自检（必须）

启动前必须检查并输出：
	•	blender 版本、ffmpeg 版本、python 版本
	•	:free 模型是否可用（一次轻量 ping）
失败则立即退出并给出可操作错误信息（不得进入主流程）

E5. Blender 调用模式锁定（必须）
	•	MUST NOT：禁止在外部 Python 代码中 import bpy（作为模块使用）。
	•	MUST：必须通过 subprocess 调用 Blender 可执行文件。
	•	唯一合法命令模式：
	  blender -b -P <generated_script.py>
	•	原因：确保 Windows/macOS 行为一致，隔离 Blender 内部 Python 环境与系统环境，保证脚本可复现性。

Technical Note (Implementation Assumption):
本系统的工程实现假设如下：
	•	Orchestrator (External Python)：负责逻辑控制、Agent 调度、文本处理。
	•	Editor Agent：输出纯文本的 Python 代码（Blender API），不执行。
	•	Blender (Headless)：作为一个独立的“渲染引擎”被调用，执行 Editor 生成的脚本。
	•	Isolation：外部 Python 环境与 Blender 内部 Python 环境完全隔离，互不干扰。

⸻

✅【新增】17. 工程边界宪法（Engineering Boundaries｜必须补齐）

B1. Policy 唯一裁决

升档/重试/上限/震荡处理必须集中在 policy.py：
	•	Orchestrator 只能执行状态机，不得分散业务判断
	•	Agent 内不得自行决定升档或循环策略

B2. 性能护栏（帧数/窗口上限必须写死）
	•	coarse 最大抽帧数：MAX_COARSE_FRAMES = 600
	•	fine 最大窗口长度：MAX_FINE_WINDOW_SEC = 60
	•	critic 最大抽帧数：MAX_CRITIC_FRAMES = 120
超限必须自动收缩窗口或降采样，并写入日志

B3. runs/ 证据链必须完整

每轮必须落盘：
	•	edit_script.py
	•	preview.mp4
	•	preview_frames/
	•	critic_report.json
缺一则该轮无效并视为错误

⸻

✅【新增】18. 可复现性宪法（Reproducibility｜必须固定）

（保持你原 R1–R3，不改语义，补一个 R4）

R4. 元信息必须写入 run_summary

每次运行必须记录：
	•	input 视频：duration / fps / resolution / codec（ffprobe）
	•	blender 版本、ffmpeg 版本、模型 tier 使用情况
用于复现与审计

⸻

✅【新增】19. 风险登记表（Risk Register｜可执行优化建议）

这部分用于项目管理与实施，不是“概念描述”。每条必须包含优化动作。

RISK-01：Blender 版本差异导致 VSE 行为不一致
	•	触发迹象：同脚本不同机输出剪辑点/特效不同
	•	影响：不可复现，验收失效
	•	优化建议：
	1.	固定 Blender 版本（E1）
	2.	bootstrap 打印版本并强校验
	3.	给 blender_tool.py 添加 --version 检查
	•	优先级：P0

RISK-02：FPS / Timebase 不一致导致边界偏移
	•	触发迹象：start/end 总偏差 1–5 秒
	•	影响：误差超标、Critic 反复震荡
	•	优化建议：
	1.	强制 ffprobe 读取 fps/duration 写入 run_summary（R2/R4）
	2.	全项目只能调用 sec_to_frame()
	3.	在 CI 加单测：给定 fps=29.97 的 case 也必须正确
	•	优先级：P0

RISK-03：免费 VLM 抖动/不一致
	•	触发迹象：两次定位差 > 2 秒，或 evidence frame 缺失
	•	影响：边界不稳、迭代次数上升
	•	优化建议：
	1.	一致性检查 + 自动升 Tier1（6.1/3.1）
	2.	“证据优先”提示词：必须输出首次/末次出现帧
	3.	对同一窗口重复推理时缓存结果（节省成本）
	•	优先级：P0

RISK-04：Critic 输出 JSON 不合规（schema fail）
	•	触发迹象：jsonschema 校验失败、字段缺失
	•	影响：无法自动 patch，流程中断
	•	优化建议：
	1.	强制 schema 校验（S1）
	2.	“自修复重试”一次（同模型）
	3.	再失败 → 升 Tier1
	4.	仍失败 → 终止并输出失败报告（包含原始输出）
	•	优先级：P0

RISK-05：5 轮内不收敛（震荡）
	•	触发迹象：start/end 来回改（+2s/-2s）
	•	影响：卡死或 PARTIAL_PASS
	•	优化建议：
	1.	震荡检测 + 步长衰减（C2）
	2.	强制 Tier1 Critic（更稳定）
	3.	细定位窗口收缩（从 60s 缩到 30s）
	•	优先级：P0

RISK-06：字幕/字体跨平台异常
	•	触发迹象：mac 缺字、字体替换导致布局变化
	•	影响：视觉验收失败
	•	优化建议：
	1.	字体随项目打包（R3）
	2.	Blender 脚本只引用 assets/fonts 路径
	3.	CI 加“字体文件存在”检查
	•	优先级：P1

RISK-07：ffmpeg 不可用或路径问题（Windows 常见）
	•	触发迹象：找不到 ffmpeg/ffprobe
	•	影响：抽帧失败，系统无法运行
	•	优化建议：
	1.	bootstrap 检查 + 友好报错（E4）
	2.	支持 FFMPEG_BIN 指定路径
	3.	README 写清安装步骤
	•	优先级：P0（因为会直接阻塞运行）

RISK-08：成本不可控（帧数过多/窗口过大）
	•	触发迹象：抽帧数量激增，token/call 数超预期
	•	影响：成本爆炸，free 额度更容易触发限制
	•	优化建议：
	1.	帧数上限（B2）
	2.	fine 窗口最大 60 秒，超限必须收缩
	3.	Critic 只抽关键帧+边界附近加密
	•	优先级：P1

RISK-09：Render 太慢影响演示
	•	触发迹象：preview 或 final 渲染时间过长
	•	影响：demo 体验差、迭代慢
	•	优化建议：
	1.	preview 固定低分辨率 + 高压缩（必须）
	2.	final 允许质量档（fast/medium/high）
	3.	先把“剪对”跑通，再追求画质
	•	优先级：P2

⸻

✅【新增】20. Freeze Checklist（冻结清单｜TRAE 可直接执行）
	•	提供 environment.yml 或 requirements.txt
	•	提供 bootstrap 脚本（mac: .sh / win: .ps1），能检查 blender/ffmpeg/python/ENV
	•	固定并记录 BLENDER_VERSION、FFmpeg major、默认 Python 版本
	•	schemas/ 完整且在启动时/CI 中校验
	•	policy.py 为唯一裁决点（升档/重试/上限/震荡）
	•	orchestrator.py 只执行状态机，不写业务判断
	•	runs/ 证据链目录结构固定，必须产出 run_summary.json + cost_report.json
	•	端到端 demo：输入视频 + 指令 → 至少 1 轮 Critic → final.mp4
	•	baseline（no-critique）可运行并产出 final，用于对比
	•	输出对比指标：边界误差、迭代轮数、是否 pass/partial_pass

很好，这一步正好是“把架构从可用推进到可规模化”的关键补丁。
下面我给你的是可直接追加到宪法文档末尾的正式条款，语气、严谨度与你现有 0–20 章保持一致，可冻结、可执行、可分发。

我会分三部分给你：
	1.	新增章节正文（可直接复制进宪法）
	2.	长视频处理的强制工程护栏（Policy 级）
	3.	不同视频类型的预设参数表（Preset Profiles）

⸻

⸻

21. 长视频处理补充宪法（Long Video Addendum｜必须遵守）

21.1 适用范围（Scope）

本系统必须支持 长达数十分钟至数小时的视频（如旅行 Vlog、运动录像、会议录制、影视素材等）。
在长视频场景下，系统的首要目标是稳定性、可控成本与可终止性，而非一次性精确剪辑。

⸻

21.2 分层定位宪法（Hierarchical Localization｜必须）

在处理 ≥ 20 分钟的视频 时，系统 必须 启用三级定位策略：

Step 0｜超粗粒度定位（Hour-Level）
	•	抽帧频率：1 帧 / 60 秒
	•	扫描范围：全视频
	•	目的：
	•	快速排除无关大段内容
	•	仅标记“可能相关”的时间区间
	•	输出：
	•	候选时间段列表（可多个）

❌ 禁止直接对小时级视频进入 Step 1 或 Step 2

⸻

Step 1｜粗粒度定位（Segment-Level）
	•	抽帧频率：1 帧 / 10 秒
	•	扫描范围：Step 0 命中的时间段
	•	目的：
	•	确定目标事件/场景的大致出现区间
	•	输出：
	•	精炼后的候选时间区间（分钟级）

⸻

Step 2｜精细粒度定位（Boundary-Level）
	•	抽帧频率：1 帧 / 1 秒
	•	扫描范围：Step 1 区间 ± buffer
	•	目的：
	•	精确确定 start / end 秒
	•	输出：
	•	精确时间边界（秒级）

⸻

21.3 分段扫描宪法（Chunking｜必须）
	•	对 ≥ 30 分钟的视频：
	•	系统必须按 5–10 分钟为单位进行分段扫描
	•	每个分段独立进入 Step 0 / Step 1
	•	仅对 命中目标的分段 进入 Step 2 与 Render-Critique

❌ 禁止对全视频进行连续高密度采样

⸻

21.4 帧预算宪法（Frame Budget｜强制上限）

为保证低成本与可终止性，系统必须实施以下帧数硬上限：

阶段	最大帧数
Step 0（超粗）	≤ 120
Step 1（粗）	≤ 600
Step 2（精）	≤ 120
Critic 验收	≤ 120

	•	超过上限：
	•	必须自动降采样
	•	或收缩时间窗口
	•	并记录于日志

⸻

21.5 长视频缓存宪法（Caching｜必须）
	•	对同一视频文件：
	•	相同抽帧参数（时间范围 + 间隔）
	•	Vision LLM 的定位结果
	•	必须缓存
	•	后续任务：
	•	优先复用缓存
	•	禁止重复调用 Vision LLM

目的：

长视频通常会被多次请求不同精彩片段，缓存是成本控制的核心机制。

⸻
21.6 分段重叠宪法（Chunk Overlap｜必须）

为避免跨段事件在分段边界处被切碎导致漏检，所有分段扫描必须启用重叠窗口。
	•	当启用 Chunking（≥ 30 分钟视频）时：
	•	分段长度：CHUNK_LEN_SEC ∈ [300, 600]（5–10 分钟）
	•	必须重叠：OVERLAP_SEC = 30（默认 30 秒）
	•	分段生成规则：
	•	第 k 段：[k*CHUNK_LEN_SEC - OVERLAP_SEC, (k+1)*CHUNK_LEN_SEC + OVERLAP_SEC]
	•	范围超出视频边界时自动裁剪到 [0, duration]
	•	重叠目的：
	•	确保跨段事件至少在一个分段中呈现完整上下文
	•	降低“半事件被误判为无关”的漏检风险

❌ 禁止对分段做“无重叠硬切”

⸻

21.7 召回优先宪法（High-Recall First｜Step 0 必须保证召回）

Step 0 的任务是高召回，宁可多报候选区间，也不得漏掉短事件。
	•	Step 0 默认采样间隔应满足：
	•	对于 “写实/日常、运动/动作、影视、动漫”：
	•	STEP0_INTERVAL_SEC = 30（默认 1 帧/30 秒）
	•	对于 “景色/风光/延时”：
	•	STEP0_INTERVAL_SEC = 90（允许稀疏）
	•	若用户明确强调“精彩瞬间/短事件/高光”：
	•	Step 0 必须自动提升密度至 1 帧/30 秒（即使是长视频）

❌ 禁止将 Step 0 固定在 1 帧/60 秒而不考虑视频类型与目标事件长度

⸻

21.8 Step 0 自适应预算宪法（Adaptive Budget｜必须）

固定 Step 0 帧预算在超长视频场景会导致降采样过度，必须自适应。
	•	Step 0 帧预算定义为：
	•	B0 = clamp(120, 360, round(60 * sqrt(duration_min)))
	•	其中 duration_min 为视频分钟数
	•	解释：
	•	20–60 分钟：预算适度上升
	•	数小时：预算上升但不线性爆炸（仍可控）
	•	当实际 Step 0 抽帧数 > B0：
	•	优先使用“滑动窗口 Step 0”而非继续降采样：
	•	窗口长度：W = 30 分钟
	•	窗口步长：S = 15 分钟
	•	每个窗口内部按 STEP0_INTERVAL_SEC 抽帧并独立定位
	•	汇总窗口结果形成全局候选区间

✅ 允许 Step 0 输出更多候选段，后续 Step 1/2 负责收敛
⸻

22. 视频类型适配宪法（Video Type Presets）

系统必须支持 按视频类型加载预设参数（Preset Profile），以避免组员各自“拍脑袋调参”。

Preset 仅影响：
	•	分段长度
	•	抽帧密度
	•	Critic 容忍误差
	•	Render-Critique 最大轮次

❌ 不得影响核心架构与权限边界

⸻

22.1 写实 / 日常 Vlog（Realistic / Lifestyle）

适用：旅行、日常记录、城市漫步
特点：场景变化明显，但节奏较慢

参数	推荐值
Step 0 抽帧	1 / 30s
Step 1 抽帧	1 / 10s
Step 2 抽帧	1 / 1s
分段长度	10 分钟
overlap    30s
Critic 误差容忍	±3 秒
Render-Critique	≤ 5 轮


⸻

22.2 运动 / 动作类（Sports / Action）

适用：滑雪、冲浪、篮球、极限运动
特点：动作瞬间短、边界敏感

参数	推荐值
Step 0 抽帧	1 / 30s
Step 1 抽帧	1 / 5s
Step 2 抽帧	1 / 0.5s
分段长度	5 分钟
overlap    30s
Critic 误差容忍	±1–2 秒
Render-Critique	≤ 5 轮


⸻

22.3 景色 / 风光（Scenery / Landscape）

适用：航拍、自然风光、延时摄影
特点：变化慢、边界主观

参数	推荐值
Step 0 抽帧	1 / 90s
Step 1 抽帧	1 / 15s
Step 2 抽帧	1 / 2s
分段长度	15 分钟
overlap    30s
Critic 误差容忍	±4–5 秒
Render-Critique	≤ 3 轮


⸻

22.4 影视 / 剧集（Film / TV）

适用：电影片段、剧集剪辑
特点：镜头语言明确，但节奏复杂

参数	推荐值
Step 0 抽帧	1 / 60s
Step 1 抽帧	1 / 8s
Step 2 抽帧	1 / 1s
分段长度	5–8 分钟
overlap    30s
Critic 误差容忍	±2 秒
Render-Critique	≤ 5 轮


⸻

22.5 动漫 / 二次元（Anime / Animation）

适用：动漫、动画短片
特点：画面变化大但语义夸张

参数	推荐值
Step 0 抽帧	1 / 45s
Step 1 抽帧	1 / 6s
Step 2 抽帧	1 / 1s
分段长度	5 分钟
overlap    30s
Critic 误差容忍	±2–3 秒
Render-Critique	≤ 4 轮


⸻
22.6 会议/课堂/录屏（Meetings & Screen Recordings）

适用：会议、课堂、录屏视频
特点：场景变化明显，但节奏较慢

参数	推荐值
Step 0 抽帧	1 / 60s
Step 1 抽帧	1 / 10s
Step 2 抽帧	1 / 1s
分段长度	10 分钟
overlap    30s
Critic 误差容忍	±3 秒
Render-Critique	≤ 4 轮

为避免“适用范围”与“非目标”矛盾，会议类视频适配范围必须明确限定。
	•	会议/课堂/录屏视频当前仅支持以下类型剪辑：
	•	PPT/白板/屏幕内容明显变化的片段定位与剪辑
	•	画面切换、演示操作、关键视觉事件（举手、上台、展示物体）
	•	当前架构不承诺支持：
	•	仅靠音频语义定位“讨论某话题”的片段
	•	固定镜头且画面几乎不变的长会议内容剪辑

如需支持“按语义剪会议”，必须通过 RFC 引入：
	•	ASR（语音转写）+ 时间戳索引 + 交叉验证机制

⸻
注：Step 0 预算按 21.8 自适应，不再死 120；Overlaps 统一强制 30s。
⸻

23. 适配边界声明（Explicit Non-Goals）

当前架构 不以以下目标为设计优先级：
	•	0.1 秒级音乐卡点
	•	口型对齐
	•	纯音频语义驱动剪辑
	•	长时间画面不变的视频（如纯播客）

如需支持上述能力，必须引入：
	•	音频语义索引（ASR + 时间戳）
	•	或节奏/信号处理模块
并通过 架构变更提案（RFC） 评估，不得私自扩展。

⸻

