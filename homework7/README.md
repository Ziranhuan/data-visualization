# Homework 7 - Plotly 高级数据可视化

## 📊 项目概述

本次实验通过 **Plotly** 库深入学习高级数据可视化技术，包括交互式图表、仪表板、地图可视化和动画效果。

## 🎯 学习内容

### Part 1: 基础图表和散点图
- 温度与湿度的散点图分析
- 城市温度变化趋势线图

### Part 2: 多维分析与仪表板
- 城市间对比柱状图
- 综合数据仪表板展示
- 风玫瑰图（南昌风向分析）

### Part 3: 地理可视化与动画
- 地图快照和地理分散散点图
- 温度动画时间序列展示

## 🛠️ 技术栈

- **语言**: Python 3.x
- **主库**: Plotly（交互式可视化）
- **数据处理**: Pandas
- **地理数据**: GeoJSON

## 📁 文件结构

```
homework7/
├── 数据可视化W7.py          # 主程序代码
├── README.md               # 本文件
├── 报告/                   # 实验报告
│   ├── 实验七.docx
│   └── 实验七_报告.pdf
└── output/                 # 输出结果
    ├── part1_temperature_line.html
    ├── part1_temp_humidity_scatter.html
    ├── part2_city_compare_bar.html
    ├── part2_city_dashboard.html
    ├── part2_wind_rose_nanchang.html
    ├── part3_map_snapshot.html
    ├── part3_temperature_animation.html
    └── assets/
        ├── china_provinces.geojson
        └── [其他资源文件]
```

## 🚀 运行方式

```bash
# 安装依赖
pip install plotly pandas

# 执行主程序
python 数据可视化W7.py
```

## 📈 输出说明

所有输出文件均为交互式HTML格式，可在浏览器中打开，支持缩放、平移、悬停等交互功能。

## ✅ 完成日期

2026年4月16日

## 📝 关键要点

- ✨ 掌握 Plotly 的多种图表类型
- ✨ 理解交互式可视化设计原理
- ✨ 学会创建数据仪表板
- ✨ 掌握地理数据可视化技巧
