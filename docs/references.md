# 外部项目核对：它们分别解决什么？

核对日期：2026-10-05。依据公开 README、相关入口脚本／Skill 文档及论文指定章节；本轮没有安装或运行这些项目。下列采用建议是对本工作流的判断。

## Reproduce Research Paper：组织复现与结果证据

[项目入口](https://github.com/FullFighting/reproduce-research-paper)。其 [Skill 文档](https://github.com/FullFighting/reproduce-research-paper/blob/main/skills/reproduce-research-paper/SKILL.md) 将论文主张、计划、代码状态、运行命令、结果提取和对照报告连接起来，并明确区分失败、部分复现和不确定结果。

适合参考其“围绕具体结果组织证据”的方法。它的公共检查案例与规划试验具有各自范围；README 明示独立人工评估尚未完成，不能由项目自述推断任意复杂论文都能自动复现。是否有官方代码，是准备实现时的重要条件，并不是该工具全部能力的分类边界。

当前做法：借鉴记录格式和核验思路；若以后采用此 Skill，再按当时版本检查运行要求与适配情况。

## Paper2Code／PaperCoder：从论文构建实现

[Paper2Code](https://github.com/going-doer/Paper2Code) 是项目／论文名称，**PaperCoder 是其中提出的系统**。流程是规划、分析、代码生成。[默认 run.sh](https://github.com/going-doer/Paper2Code/blob/master/scripts/run.sh) 的终点是代码生成，不能把运行该入口与完成论文实验画等号。

它适合作为缺少可用代码时的实现起点，也可借鉴其模块规划方法。[论文 v5 的 §4.3、附录 B.6 与 C](https://arxiv.org/html/2504.17192v5) 还报告了执行和结果复现分析，同时说明其主要关注方法实现、环境自动化和可执行性仍有局限。因此不能把它贬成“只有代码评分”，也不能把选定样本的结果理解为所有论文均可直接运行。

当前做法：学习其从论文到模块、配置与依赖的拆解；生成代码之后，仍使用本工作流的运行与结果核验步骤。

## PaperBench：区分实现、执行与结果匹配

[OpenAI PaperBench](https://github.com/openai/frontier-evals/tree/main/project/paperbench) 是评测 AI 论文复现能力的基准，提供数据和评价代码。其[官方介绍](https://openai.com/index/paperbench/)说明，会把论文复现任务拆成具体评分项；它不是把任意 PDF 变成成功实验的一键服务。

[当前 README](https://github.com/openai/frontier-evals/blob/main/project/paperbench/README.md) 区分完整评测与 **Code-Dev**：完整流程包括提交代码、在新容器中执行和评分；Code-Dev 只检查代码开发要求，跳过执行与结果匹配。这一点适合转化为我们自己的验收层次。

当前做法：借鉴清晰的验收项和独立执行方式。本文不移植排行榜，也不把其模型评分当作研究结论本身；数值结果仍应关联实际运行输出。

## CORE-Bench：补充已有代码与数据的复跑场景

[CORE-Bench](https://github.com/siegelz/core-bench) 面向已有研究代码的计算复现：处理依赖、运行代码、读取结果并回答任务问题。它比“从论文生成代码”更贴近官方仓库复跑这一支。

原仓库 README 已提示旧执行框架不再积极维护，推荐改用 [HAL harness](https://github.com/princeton-pli/hal-harness)。这里将它作为任务设计与评测参考；若未来真正接入，再确认维护状态和环境要求。

## 本仓库的组合方式

```text
选定论文与目标结果
    ├─ 有可用代码：核对版本、数据、配置与评价入口
    └─ 缺少实现：从论文重实现，可参考 PaperCoder
                 ↓
        相同的最小运行、核心实验与结果核验
                 ↓
        保留证据，决定扩展、继续排查或换目标
```

Reproduce Research Paper 可提供复现组织方式；PaperBench 与 CORE-Bench 提供不同场景的评测参照。当前没有依据把其中某个项目评为全面“最好”，也无需为了四个阶段各安装一个平台。
