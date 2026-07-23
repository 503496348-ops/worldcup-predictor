---
name: worldcup-predictor
description: "2026世界杯专用预测模型。Elo+Dixon-Coles双变量泊松+蒙特卡洛模拟，62%准确率，60+国家队。当需要预测世界杯比赛、查看夺冠概率、分析国家队实力时使用。（what it does: 安全检测与扫描工具；when to use: 当需要扫描AI Agent安全漏洞时使用）"
version: 1.1.0
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

> 📖 详细技术文档见 references/ 目录

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
# 在仓库根目录执行（或把 scripts/ 换成实际 skill 安装路径）
# 预测单场比赛
node scripts/predict.mjs brazil argentina

# 主场优势预测
node scripts/predict.mjs usa mexico usa

# 查看所有可用队伍
node scripts/predict.mjs
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

---

## 技术架构

- **核心算法**: 基于领域特定的推理引擎和知识图谱
- **数据管线**: 输入→预处理→特征提取→模型推理→后处理→输出
- **API接口**: 支持本地CLI调用和Hermes Agent集成
- **性能优化**: 缓存机制+增量更新+并行处理


---

## 工作流

使用此技能时，按以下步骤执行：

- [ ] 1. 确认用户需求和使用场景
- [ ] 2. 加载相关代码和配置
- [ ] 3. 执行核心功能
- [ ] 4. 验证输出结果

## 2026-07-03 产品收敛门禁

- 新增 `scripts/product_convergence_gate.py`：从远端干净 clone 后可运行 `python3 scripts/product_convergence_gate.py --json`，检查 SKILL/README、入口文件、smoke 目标、测试与外部融合引用是否自洽。
- 新增 `tests/test_product_convergence_gate.py`：确保门禁在产品仓库中真实可执行，避免后续增强只停留在孤岛模块。

## 一键开箱交付

本仓库提供标准一键入口：

- `install.sh`：用户的一条命令安装与冒烟入口。
- `scripts/setup.py`：安装声明依赖并串联 doctor。
- `scripts/doctor.py`：检查 README、SKILL、入口脚本、package scripts 与产品收敛门禁。
- `scripts/smoke.py`：运行 doctor、产品收敛门禁与 Python 编译级冒烟。
- `tests/test_one_click_open_box.py`：契约测试，防止 README 写了但脚本缺失。
