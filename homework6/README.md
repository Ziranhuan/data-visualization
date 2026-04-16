# Homework 6 - Pyecharts数据可视化实验

## 作业概述
基于 Open-Meteo 天气 API 的真实气象数据，使用 `Pyecharts` 完成多城市天气可视化实验。作业围绕历史天气趋势、城市间综合指标对比、实时天气空间分布以及未来 24 小时温度预测四个方向展开，重点练习组合图、雷达图、热力图、Geo 地理图和 Timeline 时间轴图的实现与版式优化。

## 目录结构
```text
homework6/
├── README.md                         # 本作业说明
├── 数据可视化W6.py                    # 完整代码实现
├── 图表输出/
│   ├── part1_nanchang_past7days.html # 南昌过去7天温度+降水组合图
│   ├── part2_radar_heatmap.html      # 五城市雷达图+热力图联动页
│   ├── part3_geo_scatter.html        # 五城市实时天气地理分布图
│   ├── part3_forecast_timeline.html  # 五城市未来24小时温度Timeline
│   ├── city_summary_metrics.csv      # 五城市统计指标汇总
│   ├── city_daily_metrics.csv        # 五城市日尺度明细数据
│   └── assets/                       # 本地图表依赖资源
└── 报告/
    ├── 实验六_Pyecharts数据可视化实验报告.docx
    └── 实验六_Pyecharts数据可视化实验报告.pdf
```

## 实验内容
### 1. 基本图表绘制
- 南昌过去 7 天逐小时温度与降水变化
- 使用双轴叠加方式展示温度折线与降水柱状图

### 2. 多城市气象指标对比与关联分析
- 对南昌、长沙、武汉、南京、上海五城市 2025 年 8 月气象指标进行统计
- 计算平均最高温、总降水量、平均风速、高温日占比
- 使用 Z-score 标准化后绘制雷达图
- 通过热力图展示各城市内部指标相关性，并实现点击联动

### 3. 多城市实时天气与预测趋势展示
- 绘制五城市实时天气地理散点图
- 点大小表示风速，颜色表示温度
- 使用 Timeline 展示五城市未来 24 小时温度预测
- 标注平均温度、最高温和最低温

## 使用方法
### 快速开始
```bash
pip install requests pandas numpy pyecharts
python 数据可视化W6.py
```

运行后会自动在 `图表输出/` 中生成 HTML 图表和 CSV 数据文件。

## 核心技术栈
- **数据获取**: Open-Meteo Forecast API / Archive API
- **数据处理**: Pandas, NumPy
- **可视化**: Pyecharts
- **文档整理**: python-docx

## 数据来源
所有实验数据均来自 [Open-Meteo](https://open-meteo.com/) 开源天气 API，包括：
- 南昌过去 7 天逐小时温度与降水数据
- 五城市 2025 年 8 月历史气象数据
- 五城市实时天气数据
- 五城市未来 24 小时逐小时温度预测数据

## 文件说明
| 文件名 | 说明 |
|------|------|
| `数据可视化W6.py` | 完整实验代码，可直接运行生成图表与数据 |
| `图表输出/part1_nanchang_past7days.html` | 组合图结果 |
| `图表输出/part2_radar_heatmap.html` | 雷达图与热力图联动结果 |
| `图表输出/part3_geo_scatter.html` | 地理散点图结果 |
| `图表输出/part3_forecast_timeline.html` | Timeline 动态折线图结果 |
| `报告/实验六_Pyecharts数据可视化实验报告.docx` | 实验报告 Word 版 |
| `报告/实验六_Pyecharts数据可视化实验报告.pdf` | 实验报告 PDF 版 |

## 学习成果
通过本作业，掌握了：
- ✅ Pyecharts 多种核心图表的实现方法
- ✅ 天气 API 数据获取与清洗流程
- ✅ 多城市指标标准化与相关性分析
- ✅ 地理分布图与时间轴动态图表设计
- ✅ 交互式图表排版和可读性优化

## 相关资源
- [Pyecharts 文档](https://pyecharts.org/)
- [Open-Meteo API](https://open-meteo.com/)
- [Pandas 文档](https://pandas.pydata.org/)

---
**完成日期**: 2026年4月9日
