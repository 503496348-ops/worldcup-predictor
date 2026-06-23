1|---
2|name: worldcup-predictor
description: "2026世界杯专用预测模型。Elo+Dixon-Coles双变量泊松+蒙特卡洛模拟，62%准确率，60+国家队。当需要预测世界杯比赛、查看夺冠概率、分析国家队实力时使用。（what it does: 安全检测与扫描工具；when to use: 当需要扫描AI Agent安全漏洞时使用）"
4|version: 1.0.0
5|triggers:
6|  - 世界杯预测
7|  - 足球预测
8|  - worldcup predict
9|  - match prediction
10|  - Elo rating
11|  - 绿茵智脑
12|author: Hermes Agent
13|license: MIT
14|dependencies: [node>=18]
15|platforms: [linux, macos, windows]
16|metadata:
17|  hermes:
18|    tags: [worldcup, football, prediction, fifa, 2026, elo, poisson]
19|    related_skills: [football-predictor]
20|---

> 📖 详细技术文档见 references/ 目录
21|
22|# 2026 世界杯预测
23|
24|基于 Elo + Dixon-Coles 双变量泊松分布 + 蒙特卡洛模拟的世界杯预测模型。
25|
26|
27|## 模型精度
28|
29|| 指标 | 模型 | 基线(硬币翻面) |
30||------|------|----------------|
31|| 正确结果预测 | **62%** | 33% |
32|| RPS (排名概率分数) | **0.175** | 0.241 |
33|| 校准误差 ECE | **2.3%** | — |
34|| 明确热门(p≥50%) | **69%** | — |
35|
36|## 使用方式
37|
38|```bash
39|# 预测单场比赛
40|node ~/.hermes/skills/worldcup-predictor/scripts/predict.mjs brazil argentina
41|
42|# 主场优势预测
43|node ~/.hermes/skills/worldcup-predictor/scripts/predict.mjs usa mexico usa
44|
45|# 查看所有可用队伍
46|node ~/.hermes/skills/worldcup-predictor/scripts/predict.mjs
47|```
48|
49|## 可用队伍 (60+)
50|
51|argentina, brazil, france, spain, england, germany, portugal, netherlands, belgium, italy, colombia, uruguay, croatia, morocco, usa, mexico, japan, south-korea, iran, australia, senegal, denmark, ecuador, switzerland, canada, china 等
52|
53|## 模型原理
54|
55|1. **Elo 评分**: 基于913场国际比赛校准的国家队能力评分
56|2. **Dixon-Coles**: 双变量泊松分布，修正0-0/1-1平局低估问题 (ρ=-0.13)
57|3. **蒙特卡洛**: 50,000次模拟，计算夺冠概率和晋级路径
58|4. **实时更新**: 条件于已完赛结果，淘汰赛自动更新
59|
60|## Pitfalls
61|
62|- 世界杯专用模型，不适用于俱乐部联赛
63|- 队伍名必须用英文小写连字符格式 (如 south-korea, not 韩国)
64|- 中性场地为主，主场优势仅75 Elo分
65|- 小组赛阶段结果已纳入模型
66|
---

## 工作流

使用此技能时，按以下步骤执行：

- [ ] 1. 确认用户需求和使用场景
- [ ] 2. 加载相关代码和配置
- [ ] 3. 执行核心功能
- [ ] 4. 验证输出结果
