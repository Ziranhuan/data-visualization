import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import matplotlib.pyplot as plt
from matplotlib import font_manager

# -------------------------- 1. 环境配置 --------------------------
# 设置 API 客户端
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# 设置 Matplotlib 中文显示
def set_chinese_font():
    system_fonts = {f.name for f in font_manager.fontManager.ttflist}
    font_candidates = ["SimHei", "Microsoft YaHei", "PingFang SC", "WenQuanYi Micro Hei"]
    for font in font_candidates:
        if font in system_fonts:
            plt.rcParams['font.sans-serif'] = [font]
            plt.rcParams['axes.unicode_minus'] = False
            return
    print("警告: 未找到中文字体，图表可能显示乱码")

set_chinese_font()

# -------------------------- 2. 数据获取 --------------------------
# 定义城市坐标
cities = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "南昌": (28.6762, 115.8922)
}

# API 请求参数
url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": [coord[0] for coord in cities.values()],
    "longitude": [coord[1] for coord in cities.values()],
    "daily": ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean", "precipitation_sum", "wind_speed_10m_max"],
    "start_date": "2025-03-01",
    "end_date": "2025-03-31",
    "timezone": "Asia/Shanghai"
}

# 发起请求并解析数据
responses = openmeteo.weather_api(url, params=params)
all_data = []
city_names = list(cities.keys())

for i, response in enumerate(responses):
    daily = response.Daily()
    daily_data = {
        "城市": city_names[i],
        "日期": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        ).strftime('%Y-%m-%d'),
        "最高温(°C)": daily.Variables(0).ValuesAsNumpy().round(1),
        "最低温(°C)": daily.Variables(1).ValuesAsNumpy().round(1),
        "平均温(°C)": daily.Variables(2).ValuesAsNumpy().round(1),
        "降水量(mm)": daily.Variables(3).ValuesAsNumpy().round(1),
        "最大风速(km/h)": daily.Variables(4).ValuesAsNumpy().round(1)
    }
    all_data.append(pd.DataFrame(daily_data))

df = pd.concat(all_data, ignore_index=True)

# -------------------------- 3. 数据分析与报告 --------------------------

print("\n" + "="*60)
print("【数据分析报告】2025年3月 四城市气象数据")
print("="*60)

# --- 任务 1: 比较四个城市3月份的平均温度 ---
print("\n四城市3月平均温度对比 (从高到低)")
print("-" * 40)
monthly_temp_avg = df.groupby("城市")["平均温(°C)"].mean().round(2).sort_values(ascending=False)
for city, temp in monthly_temp_avg.items():
    print(f"  {city}: {temp} °C")

# --- 任务 2: 找出降水量最多的城市和日期 ---
print("\n降水量最多的单日记录")
print("-" * 40)
max_precip_row = df.loc[df["降水量(mm)"].idxmax()]
print(f"  城市: {max_precip_row['城市']}")
print(f"  日期: {max_precip_row['日期']}")
print(f"  降水量: {max_precip_row['降水量(mm)']} mm")

# 额外计算：每个城市的最大单日降水量（用于绘图对比）
city_max_precip = df.groupby("城市")["降水量(mm)"].max().round(1)

# --- 任务 3: 计算每个城市的风速平均值 ---
print("\n四城市3月平均风速")
print("-" * 40)
monthly_wind_avg = df.groupby("城市")["最大风速(km/h)"].mean().round(2).sort_values(ascending=False)
for city, wind in monthly_wind_avg.items():
    print(f"  {city}: {wind} km/h")

print("\n" + "="*60)

# -------------------------- 4. 绘制统计图 (数据标签改为3位小数) --------------------------

# 统一绘图风格
colors = ['#73A6AD', '#D9B38C', '#8FAF8F', '#C9A0A0']

# === 图表 1: 四城市3月平均温度 ===
plt.figure(figsize=(10, 5), dpi=100)
bars1 = plt.bar(monthly_temp_avg.index, monthly_temp_avg.values, color=colors, width=0.6)
plt.title("2025年3月 四城市平均温度对比", fontsize=14, pad=15)
plt.ylabel("平均温度 (°C)")
plt.ylim(0, monthly_temp_avg.max() + 3)
for bar in bars1:
    height = bar.get_height()
    # 修改：保留3位小数
    plt.text(bar.get_x() + bar.get_width()/2, height + 0.3, f'{height:.3f}°C', ha='center', fontweight='bold')
plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.tight_layout()

# === 图表 2: 四城市3月单日最大降水量 ===
plt.figure(figsize=(10, 5), dpi=100)
# 确保顺序和之前一致
city_order = monthly_temp_avg.index.tolist()
precip_values = [city_max_precip[city] for city in city_order]

bars2 = plt.bar(city_order, precip_values, color=colors, width=0.5)
plt.title("2025年3月 四城市单日最大降水量对比", fontsize=14, pad=15)
plt.ylabel("降水量 (mm)")
plt.ylim(0, 25)

# 高亮显示全局最大值的柱子
max_val = max_precip_row['降水量(mm)']
for bar in bars2:
    height = bar.get_height()
    if height == max_val:
        bar.set_color('#FF4757') # 高亮色
        # 修改：保留3位小数
        plt.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'最高\n{height:.3f}mm', ha='center', fontweight='bold', color='#FF4757')
    else:
        # 修改：保留3位小数
        plt.text(bar.get_x() + bar.get_width()/2 , height + 0.5, f'{height:.3f}mm', ha='center')

plt.grid(axis='y', linestyle='--', alpha=0.2)
plt.tight_layout()

# === 图表 3: 四城市3月平均风速 ===
plt.figure(figsize=(10, 5), dpi=100)
bars3 = plt.bar(monthly_wind_avg.index, monthly_wind_avg.values, color=colors, width=0.6)
plt.title("2025年3月 四城市平均风速对比", fontsize=14, pad=15)
plt.ylabel("平均风速 (km/h)")
plt.ylim(0, monthly_wind_avg.max() + 3)
for bar in bars3:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, height + 0.3, f'{height:.3f}', ha='center', fontweight='bold')
plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.tight_layout()

# 显示所有图表
plt.show()