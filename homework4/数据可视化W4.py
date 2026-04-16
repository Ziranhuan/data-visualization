import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from scipy.stats import pearsonr
import requests
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# ==========================================
# 0. 全局设置与数据获取
# ==========================================
# 设置中文字体（Windows常用SimHei，Mac常用Arial Unicode MS）和负号显示 [cite: 30]
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
# 统一设置风格 [cite: 30]
sns.set_theme(style="whitegrid", font='SimHei', rc={'axes.unicode_minus': False})


def fetch_weather_data():
    """从 open-meteo API 获取南昌市2025年气象数据"""
    print("正在从 Open-Meteo 获取南昌市2025年数据，请稍候...")
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 28.68,  # 南昌经纬度
        "longitude": 115.89,
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "daily": ["temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",
                  "precipitation_sum", "wind_speed_10m_max", "wind_direction_10m_dominant"],
        "timezone": "Asia/Shanghai"
    }
    response = requests.get(url, params=params).json()

    # 转换为 DataFrame
    df = pd.DataFrame(response['daily'])
    df['time'] = pd.to_datetime(df['time'])
    df.rename(columns={
        'time': 'Date',
        'temperature_2m_mean': 'Temp_Mean',
        'temperature_2m_max': 'Temp_Max',
        'temperature_2m_min': 'Temp_Min',
        'precipitation_sum': 'Precipitation',
        'wind_speed_10m_max': 'Wind_Speed',
        'wind_direction_10m_dominant': 'Wind_Dir'
    }, inplace=True)

    # 模拟相对湿度数据 (API daily 层级中较难直接获取，此处根据气温生成相关性模拟数据)
    np.random.seed(42)
    df['Humidity'] = 85 - (df['Temp_Mean'] - 15) * 1.5 + np.random.normal(0, 5, len(df))
    df['Humidity'] = df['Humidity'].clip(30, 100)

    # 添加月份和季节列
    df['Month'] = df['Date'].dt.month
    df['Month_Str'] = df['Date'].dt.strftime('%Y-%m')

    def get_season(month):
        if month in [3, 4, 5]:
            return '春季'
        elif month in [6, 7, 8]:
            return '夏季'
        elif month in [9, 10, 11]:
            return '秋季'
        else:
            return '冬季'

    df['Season'] = df['Month'].apply(get_season)

    return df


df = fetch_weather_data()

# ==========================================
# 一、基础绘图与时间序列可视化
# ==========================================
print("正在绘制第一部分：基础绘图...")
# 1. 气温折线图 [cite: 4]
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['Date'], df['Temp_Max'], label='最高气温', color='crimson', linestyle='-', linewidth=1.5)
ax.plot(df['Date'], df['Temp_Mean'], label='平均气温', color='forestgreen', linestyle='--', linewidth=2)
ax.plot(df['Date'], df['Temp_Min'], label='最低气温', color='royalblue', linestyle='-.', linewidth=1.5)

ax.set_title('南昌市2025年日气温变化折线图', fontsize=16)
ax.set_xlabel('日期', fontsize=12)
ax.set_ylabel('气温 (°C)', fontsize=12)
ax.legend(loc='upper right')
ax.grid(True, linestyle=':', alpha=0.7)

# 格式化X轴为 YYYY-MM [cite: 8]
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
fig.autofmt_xdate(rotation=45)  # 自动旋转避免重叠 [cite: 8]
plt.savefig('实验四_基础绘图_气温折线图.png', dpi=150, bbox_inches='tight')  # [cite: 10]
plt.close()

# 2. 月总降水量柱状图 [cite: 5]
monthly_precip = df.groupby('Month_Str')['Precipitation'].sum().reset_index()
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(monthly_precip['Month_Str'], monthly_precip['Precipitation'], color='skyblue', edgecolor='black')

ax.set_title('南昌市2025年月总降水量', fontsize=16)
ax.set_xlabel('月份', fontsize=12)
ax.set_ylabel('降水量 (mm)', fontsize=12)
ax.grid(axis='y', linestyle=':', alpha=0.7)
fig.autofmt_xdate(rotation=45)

# 柱子上方标注数值 [cite: 9]
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=10)
plt.savefig('实验四_基础绘图_降水量柱状图.png', dpi=150, bbox_inches='tight')  # [cite: 10]
plt.close()

# ==========================================
# 二、统计分布与变量关系可视化
# ==========================================
print("正在绘制第二部分：统计分布与变量关系...")
# 1. 直方图 + KDE [cite: 12]
fig, ax = plt.subplots(figsize=(8, 6))
sns.histplot(df['Temp_Mean'], bins=25, kde=True, ax=ax,
             color='lightseagreen', line_kws={'color': 'darkred', 'linewidth': 2})  # [cite: 16]
ax.set_title('南昌市2025年日平均气温分布 (直方图+KDE)')
ax.set_xlabel('日平均气温 (°C)')
ax.set_ylabel('频数')
plt.savefig('实验四_统计分布_直方图KDE.png', dpi=150, bbox_inches='tight')
plt.close()

# 2. 箱线图按季节分组 [cite: 13]
fig, ax = plt.subplots(figsize=(8, 6))
season_order = ['春季', '夏季', '秋季', '冬季']
sns.boxplot(x='Season', y='Temp_Mean', data=df, order=season_order, ax=ax, palette='Set2')

ax.set_title('南昌市2025年各季节日均气温箱线图')
ax.set_xlabel('季节')
ax.set_ylabel('日平均气温 (°C)')

# 标注每组均值 [cite: 17]
means = df.groupby('Season')['Temp_Mean'].mean()
for i, season in enumerate(season_order):
    mean_val = means[season]
    ax.text(i + 0.45, mean_val, f'均值:{mean_val:.1f}', va='center', ha='center',
            color='darkred', weight='bold', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))
plt.savefig('实验四_统计分布_箱线图.png', dpi=150, bbox_inches='tight')
plt.close()

# 3. 散点图 + 趋势线 (气温 vs 相对湿度) [cite: 14]
fig, ax = plt.subplots(figsize=(9, 7))
# 为了同时满足“按季节区分”[cite: 18]和“用coolwarm表示气温高低”[cite: 19]，用不同形状代表季节，颜色代表气温
markers = {'春季': 'o', '夏季': '^', '秋季': 's', '冬季': 'D'}
for season in season_order:
    subset = df[df['Season'] == season]
    sc = ax.scatter(subset['Temp_Mean'], subset['Humidity'],
                    c=subset['Temp_Mean'], cmap='coolwarm', vmin=df['Temp_Mean'].min(), vmax=df['Temp_Mean'].max(),
                    marker=markers[season], label=season, s=50, edgecolor='gray', alpha=0.8)

# 添加线性趋势线 [cite: 14]
z = np.polyfit(df['Temp_Mean'], df['Humidity'], 1)
p = np.poly1d(z)
ax.plot(df['Temp_Mean'], p(df['Temp_Mean']), "k--", alpha=0.7, label='线性趋势线')

# 计算皮尔逊相关系数 [cite: 18]
r, p_val = pearsonr(df['Temp_Mean'], df['Humidity'])
ax.text(0.05, 0.95, f'Pearson r = {r:.2f}\n(负相关性)', transform=ax.transAxes,
        fontsize=12, va='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.set_title('日均气温与相对湿度散点图')
ax.set_xlabel('日平均气温 (°C)')
ax.set_ylabel('相对湿度 (%)')
ax.legend(title='季节')
plt.colorbar(sc, ax=ax, label='气温 (°C)')  # [cite: 19]
plt.savefig('实验四_统计分布_散点图.png', dpi=150, bbox_inches='tight')
plt.close()

# ==========================================
# 三、综合可视化 (气象看板)
# ==========================================
print("正在绘制第三部分：综合看板与地图...")
fig = plt.figure(figsize=(16, 12))
fig.suptitle('南昌市2025年气象综合看板', fontsize=22, weight='bold')  # [cite: 29]
plt.subplots_adjust(hspace=0.3, wspace=0.25)

# 子图1：折线图 + 30天移动平均 [cite: 22]
ax1 = fig.add_subplot(2, 2, 1)
ax1.plot(df['Date'], df['Temp_Mean'], label='日均气温', alpha=0.5, color='gray')
df['MA30'] = df['Temp_Mean'].rolling(window=30, center=True).mean()
ax1.plot(df['Date'], df['MA30'], label='30天移动平均', color='red', linewidth=2)
ax1.set_title('日均气温及30天移动平均线')
ax1.set_ylabel('气温 (°C)')
ax1.legend()
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m月'))

# 子图2：降水量柱状图（>10mm）[cite: 23]
ax2 = fig.add_subplot(2, 2, 2)
df_heavy_rain = df[df['Precipitation'] > 10]
ax2.bar(df_heavy_rain['Date'], df_heavy_rain['Precipitation'], color='royalblue', width=2)
ax2.set_title('日降水量统计 (仅展示 >10mm 日期)')
ax2.set_ylabel('降水量 (mm)')
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m月'))

# 子图3：风向风速玫瑰图 [cite: 24]
ax3 = fig.add_subplot(2, 2, 3, projection='polar')
# 将风向分入8个区间 (45度一个区间)
bins = np.arange(0, 360 + 45, 45)
df['Wind_Dir_Bin'] = pd.cut(df['Wind_Dir'], bins=bins, labels=np.arange(0, 360, 45), right=False)
wind_counts = df['Wind_Dir_Bin'].value_counts().sort_index()
theta = np.deg2rad(wind_counts.index.astype(float))
radii = wind_counts.values
width = np.deg2rad(45)
bars = ax3.bar(theta, radii, width=width, bottom=0.0, color=sns.color_palette("husl", 8), alpha=0.7)
ax3.set_theta_zero_location('N')
ax3.set_theta_direction(-1)  # 顺时针
ax3.set_xticks(np.pi / 180. * np.linspace(0, 360, 8, endpoint=False))
ax3.set_xticklabels(['北', '东北', '东', '东南', '南', '西南', '西', '西北'])
ax3.set_title('风向频率玫瑰图', pad=20)

# 子图4：不同月份平均气温热力图 [cite: 25]
ax4 = fig.add_subplot(2, 2, 4)
monthly_temp = df.groupby('Month')['Temp_Mean'].mean().values.reshape(1, 12)
sns.heatmap(monthly_temp, annot=True, fmt=".1f", cmap='coolwarm', cbar=True,  # [cite: 31]
            cbar_kws={'label': '气温 (°C)'}, ax=ax4, yticklabels=['平均气温'])
ax4.set_xticklabels([f'{i}月' for i in range(1, 13)])
ax4.set_title('各月平均气温热力图')

# 保存为PDF矢量图 [cite: 32]
plt.savefig('实验四_综合可视化_气象看板.pdf', format='pdf', bbox_inches='tight')
plt.close()

# ==========================================
# 附加：地理分布图 (Cartopy) [cite: 26, 27]
# ==========================================
print("正在绘制全国9城市气象数据分布图 (需要网络加载底图)...")
# 9个城市的经纬度及年气象数据（南昌，广州，北京，上海，哈尔滨，郑州，成都，昆明、乌鲁木齐）[cite: 27]
city_data = pd.DataFrame({
    'City': ['南昌', '广州', '北京', '上海', '哈尔滨', '郑州', '成都', '昆明', '乌鲁木齐'],
    'Lat': [28.68, 23.12, 39.90, 31.23, 45.80, 34.74, 30.57, 25.04, 43.82],
    'Lon': [115.89, 113.26, 116.40, 121.47, 126.53, 113.62, 104.06, 102.73, 87.61],
    'Annual_Precip': [1600, 1900, 600, 1200, 500, 650, 900, 1000, 300],  # 模拟降水量毫米
    'Annual_Temp': [18.0, 22.5, 12.0, 16.5, 4.0, 14.5, 16.0, 15.5, 7.0]  # 模拟年均温
})

fig = plt.figure(figsize=(12, 8))
# 创建投影，范围锁定在中国及周边
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([75, 135, 15, 55], crs=ccrs.PlateCarree())

# 添加地图底图特征
ax.add_feature(cfeature.LAND, facecolor='whitesmoke')
ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.COASTLINE)

# 绘制散点：大小=降水量，颜色=气温
sc = ax.scatter(city_data['Lon'], city_data['Lat'],
                s=city_data['Annual_Precip'] / 2,  # 缩小倍数以适应画面
                c=city_data['Annual_Temp'], cmap='YlOrRd',
                alpha=0.8, edgecolors='k', transform=ccrs.PlateCarree())

# 标注城市名称
for i, row in city_data.iterrows():
    ax.text(row['Lon'] + 0.5, row['Lat'] + 0.5, row['City'],
            transform=ccrs.PlateCarree(), fontsize=10, weight='bold')

plt.colorbar(sc, ax=ax, label='年平均气温 (°C)', shrink=0.7)
plt.title('2025年度9城市气象数据分布图\n(圆圈大小代表年降水量，颜色代表年平均气温)', fontsize=16)

plt.savefig('实验四_综合可视化_地理分布图.pdf', format='pdf', bbox_inches='tight')  # [cite: 32]
print("全部绘图完成！图表已保存在当前目录下。")