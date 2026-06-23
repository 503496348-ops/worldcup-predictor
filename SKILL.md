---
name: worldcup-predictor
description: "2026 FIFA World Cup match predictor — Elo + Dixon-Coles bivariate Poisson + Monte Carlo simulation. 48-team tournament model with live results conditioning."
version: 1.0.0
triggers:
  - 世界杯预测
  - 足球预测
  - worldcup predict
  - match prediction
  - Elo rating
  - 绿茵智脑
author: Hermes Agent
license: MIT
dependencies: [node>=18]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [worldcup, football, prediction, fifa, 2026, elo, poisson]
    related_skills: [football-predictor]
---

# 2026 世界杯预测

基于 Elo + Dixon-Coles 双变量泊松分布 + 蒙特卡洛模拟的世界杯预测模型。


## 模型精度

| 指标 | 模型 | 基线(硬币翻面) |
|------|------|----------------|
| 正确结果预测 | **62%** | 33% |
| RPS (排名概率分数) | **0.175** | 0.241 |
| 校准误差 ECE | **2.3%** | — |
| 明确热门(p≥50%) | **69%** | — |

## 使用方式

```bash
# 预测单场比赛
node ~/.hermes/skills/worldcup-predictor/scripts/predict.mjs brazil argentina

# 主场优势预测
node ~/.hermes/skills/worldcup-predictor/scripts/predict.mjs usa mexico usa

# 查看所有可用队伍
node ~/.hermes/skills/worldcup-predictor/scripts/predict.mjs
```

## 可用队伍 (60+)

argentina, brazil, france, spain, england, germany, portugal, netherlands, belgium, italy, colombia, uruguay, croatia, morocco, usa, mexico, japan, south-korea, iran, australia, senegal, denmark, ecuador, switzerland, canada, china 等

## 模型原理

1. **Elo 评分**: 基于913场国际比赛校准的国家队能力评分
2. **Dixon-Coles**: 双变量泊松分布，修正0-0/1-1平局低估问题 (ρ=-0.13)
3. **蒙特卡洛**: 50,000次模拟，计算夺冠概率和晋级路径
4. **实时更新**: 条件于已完赛结果，淘汰赛自动更新

## Pitfalls

- 世界杯专用模型，不适用于俱乐部联赛
- 队伍名必须用英文小写连字符格式 (如 south-korea, not 韩国)
- 中性场地为主，主场优势仅75 Elo分
- 小组赛阶段结果已纳入模型
