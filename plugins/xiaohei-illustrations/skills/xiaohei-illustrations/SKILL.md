---
name: xiaohei-illustrations
description: 生成中文正文配图。用于用户要求为中文文章、帖子、博客、Notion 文档、工作流文档、方法论、流程、结构、状态、隐喻或观点生成“怪诞”“小黑”“手绘”“正文配图”“文章插图”“配图建议”“shot list”“去标题/改图”等任务；默认使用小黑 IP、纯白手绘、少量红橙蓝批注、简洁清爽但天马行空的视觉风格。
---

# 小黑怪诞正文配图

## 核心定位

为中文文章设计和生成 16:9 横版正文配图。目标不是做商业插画、PPT 信息图或可爱卡通，而是把文章里的关键判断、流程、结构、状态或隐喻，变成一张清爽、怪诞、有创意、可读但不说明书的手绘解释图。

默认视觉 IP 是“小黑”：黑色实心、白点眼、细腿、空表情，认真做一件荒诞但成立的事。小黑必须参与画面的核心动作，不能只是站在旁边当装饰。

## 参考文件

默认只读取 `references/prompt-template.md`。生成后需要检查或迭代时，再读取 `references/qa-checklist.md`。

实际生图使用 skill 自带的 `scripts/draw.py`。该脚本只依赖 Python 标准库，通过 `https://codex.apiz.ai/v1/images/generations` 的 OpenAI 兼容协议生成图片。

## 工作流

### 1. 消化正文

先读用户给的正文、链接、Notion 页面、Markdown 文件或截图内容。提炼：

- 核心观点是什么
- 哪些段落承担认知转折
- 哪些内容适合用图解释
- 哪些地方只适合文字，不需要图

不要平均配图。优先选择“认知锚点”，例如：核心判断、两个断点、输入输出闭环、分流、前后对比、一鱼多吃、承接路径、常见坑、角色状态变化。

### 2. 先出配图策略

如果用户只是说“分析怎么配图 / 思考哪些地方需要配图”，先给 shot list。每张图写清楚：

- 放在哪个段落后
- 图的主题
- 核心意思
- 结构类型
- 小黑在图里做什么
- 建议元素
- 建议中文标注词

默认 1-3 张。文章很短时 1-3 张；长文也不要轻易超过 9 张。够用就好，避免把正文做成画册。

### 3. 单张生成

如果用户明确要求“生成 / 输出 / 做图 / 帮我生成”，不要停下来等确认；按下文“API 生图调用”运行 `scripts/draw.py`，每张单独生成。不要把多张图拼在一张里。

不要使用assets中历史生成的图作为参考图。

### 4. 检查与迭代

生成后检查 `references/qa-checklist.md`。如果出现以下问题，优先重生成或局部编辑：

- 小黑只是装饰
- 画面太满
- 太像流程图/PPT
- 中文太多或错字严重
- 左上角出现“常见坑/流程图/系统架构图”等标题
- 画风太可爱、幼稚、死板
- 背景不是干净白底

### 5. 保存交付

无论用户在哪个 workspace 内工作，最终图都保存到当前 skill 自身的 `assets/` 目录：

```text
<skill-dir>/assets/<article-slug>-illustrations/
```

按顺序命名：

```text
01-topic-name.png
02-topic-name.png
```

保留原始生成文件，不要覆盖已有资产，除非用户明确要求替换。

## API 生图调用

先把当前 `SKILL.md` 所在目录解析为 `<skill-dir>`，再运行其中的脚本。不要引用仓库根目录或用户机器上的绝对脚本路径。

macOS / Linux：

```bash
python3 "<skill-dir>/scripts/draw.py" \
  --prompt "<按 references/prompt-template.md 整理后的完整提示词>" \
  --model gpt-image-2 \
  --size 1280x720 \
  --quality medium \
  --out "<skill-dir>/assets/<article-slug>-illustrations/01-topic-name.png"
```

Windows PowerShell：

```powershell
py "<skill-dir>\scripts\draw.py" --prompt "<完整提示词>" --model gpt-image-2 --size 1280x720 --quality medium --out "<skill-dir>\assets\<article-slug>-illustrations\01-topic-name.png"
```

密钥按以下顺序读取：`OPENAI_API_KEY` 环境变量、`--auth-file` 指定文件、`CODEX_AUTH_FILE`、`CODEX_HOME/auth.json`、当前用户目录的 `.codex/auth.json`。不要把密钥写进 skill、提示词或命令参数。认证文件格式为：

```json
{"OPENAI_API_KEY": "用户自己的密钥"}
```

需要先检查请求但不实际生图时添加 `--dry-run`。目标文件已存在时换用新文件名；只有用户明确要求覆盖时才添加 `--force`。

## 输出口径

生成前的策略输出要短而准。生成后的交付要包含：

- 生成了几张
- 每张图的用途
- 每张最终图必须直接渲染在回复中，使用绝对路径的 Markdown 图片语法：`![简短说明](/绝对/路径/图片.png)`
- 不要使用普通链接语法 `[说明](/绝对/路径/图片.png)` 代替图片，也不要只输出保存路径
- 图片下方可补充保存路径，方便用户复用

不要长篇解释风格理论；让图自己说话。
