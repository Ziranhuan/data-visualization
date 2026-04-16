# Homework 5 - Seaborn数据可视化实验

## 📊 作业概述

基于真实的南昌市气象数据，掌握Seaborn核心绘图函数和高级可视化技巧，包括关系型数据、分类数据、回归分析等多维度的数据探索。

## 📁 目录结构

```
homework5/
├── 数据可视化W5.ipynb             # Jupyter Notebook - 完整代码实现
└── 报告/
    └── Seaborn数据可视化实验报告.docx  # 详细实验报告与分析
```

## 🎯 实验内容

### 1. 关系型数据可视化
- **动态双变量散点图** - 温度 vs 湿度（按时间段分段）
- **矩阵网格对比图** - 多变量配对关系展示
- **热力-折线组合图** - 双轴展示相关指标

### 2. 分类数据可视化  
- **增强箱线图** - 不同天气类型的温度分布
- **分类分面网格** - 风向风速的多维度对比

### 3. 回归分析与综合应用
- **多维度回归网格** - 温度与多变量的线性关系
- **时间序列回归** - 过去30天温度趋势分析
- **自定义PairGrid** - 三维联合可视化

## 🔑 关键发现

✨ **气象规律**
- 温度与相对湿度呈显著负相关
- 不同时段温湿度聚类特征明显
- 降水对温度有明显的抑制作用
- 南昌市风向主要为北向和东向

📈 **数据特征**
- 日周期波动：单日温差可达5°C以上
- 季节变化：孟夏季节南昌气温逐步回暖
- 天气模式：阴天天气占优势(71天)

## 💻 使用方法

### 快速开始

```bash
# 安装依赖
pip install seaborn matplotlib pandas numpy jupyter

# 运行Notebook
jupyter notebook 数据可视化W5.ipynb
```

### 核心技术栈

- **数据处理**: Pandas, NumPy
- **可视化**: Seaborn, Matplotlib
- **时间处理**: datetime, Pandas TimeSeries
- **数据源**: Open-Meteo API (南昌市)

## 📊 数据来源

所有数据来自 [Open-Meteo](https://open-meteo.com/) 开源天气API，涵盖：
- 未来3/7天逐小时气象指标
- 2024年5月-6月历史数据
- 过去30/14天回溯数据

## 📝 文件说明

| 文件名 | 说明 |
|------|------|
| `数据可视化W5.ipynb` | 完整的可视化实现代码，可直接在Jupyter中运行 |
| `报告/Seaborn数据可视化实验报告.docx` | 详细的实验分析报告 |

## 🎓 学习成果

通过本作业，掌握了：
- ✅ Seaborn三大类核心可视化方案
- ✅ 数据预处理与特征工程
- ✅ 高级图表定制与美化
- ✅ 数据驱动的规律发现

## 📚 相关资源

- [Seaborn文档](https://seaborn.pydata.org/)
- [Matplotlib指南](https://matplotlib.org/)
- [Pandas时间序列](https://pandas.pydata.org/docs/user_guide/timeseries.html)

---

**完成日期**: 2026年4月2日
