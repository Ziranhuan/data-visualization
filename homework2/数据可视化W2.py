import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import zscore
from datetime import datetime

# --- 全局设置：中文显示 ---
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# --- 全局变量：城市坐标与天气代码 ---
CHINA_CITIES = {
    "北京": (39.9042, 116.4074), "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644), "深圳": (22.5431, 114.0579),
    "成都": (30.5728, 104.0668), "杭州": (30.2741, 120.1551),
    "武汉": (30.5928, 114.3055), "西安": (34.3416, 108.9398),
    "重庆": (29.4316, 106.9123), "南京": (32.0603, 118.7969),
    "南昌": (28.6800, 115.8900), "长沙": (28.2000, 112.9388)
}

WEATHER_CODE = {
    0: ('☀️', '晴朗'), 1: ('🌤️', '大部晴'), 2: ('⛅', '局部多云'), 3: ('☁️', '多云'),
    45: ('🌫️', '雾'), 61: ('🌧️', '小雨'), 63: ('🌧️', '中雨'), 65: ('🌧️', '大雨'),
    71: ('🌨️', '小雪'), 80: ('🌦️', '阵雨'), 95: ('⛈️', '雷暴')
}


# ==========================================================================
# 一、数据预处理 (已封装为函数，并增加模拟数据兜底)
# ==========================================================================
def run_data_preprocessing():
    print("\n" + "=" * 60)
    print("第一部分：数据预处理")
    print("=" * 60)

    df = None
    # 1. 尝试下载数据
    try:
        print("正在尝试从 Open-Meteo 下载数据...")
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": 28.68, "longitude": 115.89,
            "start_date": "2025-03-01", "end_date": "2025-03-31",
            "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation"],
            "timezone": "Asia/Shanghai"
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame({
                "time": pd.to_datetime(data["hourly"]["time"]),
                "temp": data["hourly"]["temperature_2m"],
                "humidity": data["hourly"]["relative_humidity_2m"],
                "precip": data["hourly"]["precipitation"]
            }).set_index("time")
            print("真实数据下载成功！")
    except:
        pass

    # 2. 如果下载失败，生成模拟数据
    if df is None:
        print("API 异常，正在生成高质量模拟数据...")
        np.random.seed(42)
        timestamps = pd.date_range(start="2025-03-01", end="2025-03-31 23:00", freq='H')
        # 模拟气温：有日变化的正弦波 + 噪声
        hour_of_day = timestamps.hour
        base_temp = 15 + 10 * np.sin((hour_of_day - 6) * (2 * np.pi / 24))
        noise = np.random.normal(0, 1.5, len(timestamps))
        temps = base_temp + noise

        # 模拟湿度：与温度负相关
        humidity = 80 - (temps - 10) * 1.5 + np.random.normal(0, 5, len(timestamps))
        humidity = np.clip(humidity, 30, 100)

        # 模拟降水：随机几天有雨
        precip = np.zeros(len(timestamps))
        rain_days = [5, 12, 18, 25]
        for d in rain_days:
            mask = (timestamps.day == d) & (np.random.rand(len(timestamps)) > 0.7)
            precip[mask] = np.random.uniform(0.5, 10, size=np.sum(mask))

        df = pd.DataFrame({
            "temp": temps, "humidity": humidity, "precip": precip
        }, index=timestamps)

    # -----------------------------------------------------------
    # 开始处理与绘图
    # -----------------------------------------------------------

    # 1. 缺失值填充
    np.random.seed(42)
    mask = np.random.choice([True, False], size=len(df), p=[0.05, 0.95])
    df['temp_missing'] = df['temp'].where(~mask, np.nan)
    df['temp_ffill'] = df['temp_missing'].ffill()
    df['temp_interp'] = df['temp_missing'].interpolate()

    plt.figure(figsize=(14, 5))
    view_slice = slice(0, 120)
    plt.plot(df.index[view_slice], df['temp'][view_slice], label='原始数据', color='black', linewidth=2, alpha=0.3)
    plt.plot(df.index[view_slice], df['temp_ffill'][view_slice], label='前向填充', color='red', linestyle='--')
    plt.plot(df.index[view_slice], df['temp_interp'][view_slice], label='线性插值', color='blue', linestyle='-.')
    plt.title('图1：缺失值填充方法对比')
    plt.legend()
    plt.show()

    # 2. 异常值检测
    df['precip_zscore'] = np.abs(zscore(df['precip']))
    anomalies = df[df['precip_zscore'] > 3]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
    ax1.plot(df.index, df['precip'], label='降水量', color='gray')
    ax1.scatter(anomalies.index, anomalies['precip'], color='red', label='异常值')
    ax1.set_title('图2：降水量异常值检测')
    ax2.bar(df.index, df['precip_zscore'], color='steelblue')
    ax2.axhline(y=3, color='red', linestyle='--')
    plt.show()

    # 3. 数据切片
    night_df = df.between_time('22:00', '06:00')
    day_df = df.between_time('06:00', '22:00')

    plt.figure(figsize=(12, 6))
    bp = plt.boxplot([day_df['temp'], night_df['temp'], day_df['humidity'], night_df['humidity']],
                     labels=['白天气温', '夜间气温', '白天湿度', '夜间湿度'], patch_artist=True)
    colors = ['#FFD700', '#4682B4', '#90EE90', '#006400']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    plt.title('图3：白天与夜间气候特征对比')
    plt.show()

    # 4. 重采样
    daily_df = df.resample('D').agg(最高温=('temp', 'max'), 最低温=('temp', 'min'), 平均湿度=('humidity', 'mean'))

    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax1.plot(daily_df.index, daily_df['最高温'], color='red', marker='o', label='最高温')
    ax1.plot(daily_df.index, daily_df['最低温'], color='blue', marker='s', label='最低温')
    ax2 = ax1.twinx()
    ax2.plot(daily_df.index, daily_df['平均湿度'], color='green', linestyle='--', label='平均湿度')
    plt.title('图4：每日数据聚合')
    plt.show()


# ==========================================================================
# 二、实时天气查询 (简化文本版，保证能运行)
# ==========================================================================
def get_current_weather(city_name):
    if city_name not in CHINA_CITIES:
        return f"❌ 数据库中暂未收录 [{city_name}]。"

    # 模拟数据生成
    np.random.seed(ord(city_name[0]))
    temp = np.random.randint(10, 28)
    humid = np.random.randint(45, 85)
    wind = np.random.randint(3, 20)
    code = np.random.choice([0, 1, 2, 3, 61])
    _, desc = WEATHER_CODE.get(code, ("❓", "未知"))

    return (f"\n━━━━━━━━ {city_name} 实时天气 (模拟演示) ━━━━━━━━\n"
            f"  温度：{temp}°C\n  天气：{desc}\n  湿度：{humid}%\n  风速：{wind} km/h")


# ==========================================================================
# 三、历史天气绘图
# ==========================================================================
def plot_history_weather(city_name, start_date, end_date):
    if city_name not in CHINA_CITIES:
        print("❌ 不支持的城市")
        return

    print(f"正在生成 {city_name} 的模拟历史数据...")
    # 生成模拟时间序列
    try:
        timestamps = pd.date_range(start=start_date, end=end_date, freq='H')
    except:
        print("日期格式错误，请使用 YYYY-MM-DD")
        return

    np.random.seed(42)
    hour_of_day = timestamps.hour
    base_temp = 12 + 8 * np.sin((hour_of_day - 6) * (2 * np.pi / 24))
    temps = base_temp + np.random.normal(0, 2, len(timestamps))

    df_hist = pd.DataFrame({"temp": temps}, index=timestamps)
    daily_avg = df_hist.resample('D').mean()

    plt.figure(figsize=(14, 5))
    plt.plot(df_hist.index, df_hist['temp'], label='逐小时气温', color='#1f77b4', linewidth=0.5, alpha=0.5)
    plt.plot(daily_avg.index, daily_avg['temp'], label='日平均温', color='#ff4b5c', linewidth=2, marker='o')
    plt.title(f"{city_name} 温度变化 ({start_date} ~ {end_date}) [模拟数据]")
    plt.legend()
    plt.grid(True)
    plt.show()


# ==========================================================================
# 主程序入口 (已修复)
# ==========================================================================
if __name__ == "__main__":
    print("天气数据分析系统启动...")

    # 1. 运行第一部分
    run_data_preprocessing()

    # 2. 第二部分
    print("\n" + "=" * 60)
    print("第二部分：实时天气查询")
    print("=" * 60)
    while True:
        city = input("\n请输入要查询的城市 (输入 q 进入下一模块): ")
        if city.lower() == 'q':
            break
        print(get_current_weather(city))

    # 3. 第三部分
    print("\n" + "=" * 60)
    print("第三部分：历史数据绘图")
    print("=" * 60)
    c = input("请输入城市名: ")
    s = input("请输入开始日期 (如 2025-03-01): ")
    e = input("请输入结束日期 (如 2025-03-10): ")
    if c and s and e:
        plot_history_weather(c, s, e)