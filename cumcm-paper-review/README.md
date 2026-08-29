# cumcm-paper-review 技能包

数学建模竞赛论文**分章自查工作流**:1 个编排技能 + 7 个分章检查技能,跑完输出一份 Markdown 总报告。

**不绑定特定 agent 软件**:遵循 Agent Skills 规范的软件(如 ZCode、Claude Code、Codex CLI 等)按技能方式安装;任何能读写文件的 agent 即使没有技能机制,也能按路径直读运行(见安装方式 B)。

## 包内容

| 文件夹 | 说明 | 来源 |
|---|---|---|
| `cumcm-paper-review` | 编排技能(本包新增):材料盘点 → 调度 7 个检查器 → 汇总总报告 | 新写 |
| `abstract-checker` | 摘要检查(独立可读性第一道门) | 数学建模技能合集原样拷贝(仅去前缀改名) |
| `problem-restatement` | 问题重述生成/自查 | 同上 |
| `problem-analysis-checker` | 问题分析章检查 | 同上 |
| `model-assumption-checker` | 模型假设章检查 | 同上 |
| `symbol-notation-checker` | 符号说明表检查 | 同上 |
| `model-solution-checker` | 模型建立与求解各章检查 | 同上 |
| `reference-appendix-checker` | 参考文献/附录/支撑材料检查 | 同上(已修复原包的嵌套目录打包事故) |

每个技能都含 `SKILL.md`(Agent Skills 规范)与 `agents/openai.yaml`(OpenAI 系界面元数据);7 个检查技能除名称外保持原样、可独立使用、可单独升级,编排技能不修改它们的任何规则。

## 安装(本包未自动安装,三种方式任选)

### 方式 A:按技能规范安装(推荐,支持技能的软件)

把本目录下全部 **8 个技能文件夹**复制到所用软件的技能目录,然后重启会话/重新加载技能。常见位置:

| 软件 | 用户级技能目录(常见) |
|---|---|
| ZCode | `C:\Users\<你>\.zcode\skills\` |
| Claude Code | `~/.claude/skills/` |
| Codex CLI | `~/.codex/skills/`(以该软件官方文档为准) |
| 其他遵循 Agent Skills 规范 | 该软件的 skills 目录 |

项目级目录同理(如 `<项目>\.zcode\skills\`、`<项目>/.claude/skills/`)。8 个文件夹必须装齐;缺任何一个,工作流前置检查会列出缺失项,经你确认后可跳过该章检查。

### 方式 B:无技能机制的 agent,按路径直读运行

把整个包拷到任意位置(保持 8 个文件夹同级),对 agent 说:

> 读取 `<包路径>/cumcm-paper-review/SKILL.md`,严格按其执行,对以下赛题和论文做分章自查:……

工作流内部会按路径读取各分章技能的 SKILL.md 与 references,不依赖任何技能发现机制;该软件没有子代理能力时,工作流会自动降级为主对话串行执行,结果不变。

### 方式 C:OpenAI 系界面

包内各技能带 `agents/openai.yaml`,支持该元数据的软件可直接识别 `$cumcm-paper-review` 与各分章技能的调用名(如 `$abstract-checker`)。

## 使用

1. 提供材料:完整赛题(含附件说明)、论文全文或各章文本,可选的代码/数据/当届官方规则;
2. 触发:支持技能的软件中输入 `cumcm-paper-review`、`论文分章自查` 或 `分章体检`;无技能机制的软件按方式 B 的话术直读运行;
3. 工作流自动按 摘要 → 问题重述 → 问题分析 → 模型假设 → 符号说明 → 模型求解 → 参考文献/附录 的顺序调度 7 个检查器(有子代理能力时两波并行);
4. 结束后在论文目录的 `review_out/` 下查看总报告 `cumcm-paper-review-report.md`、7 份分章片段与任务基准。

## 定位与边界

- **纯诊断**:不修改论文、代码、数据;所有产出只写入 `review_out/`。
- **不打分排名**:不估计奖项;打分排位类技能有意不收入本包。
- **默认静态检查**:不运行你的代码;确需运行时会在第 07 项单独请求授权。
- **与 paper-review 互补**:已有的 `paper-review`(9 维整体审查)管整体印象,本工作流管逐章精查;两者可先后使用。

## 卸载

方式 A/C:删除所装技能目录下对应的 8 个文件夹;方式 B:直接删除拷贝出的整个目录。
