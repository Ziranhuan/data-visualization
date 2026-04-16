import random
import pandas as pd
import matplotlib.pyplot as plt


plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ======================
# 1. 基础数据结构操作
# ======================
# 1.1 创建10个随机温度列表
random.seed(472)  # 可去掉此行，每次运行生成不同随机数
temperature_list = [random.randint(-10, 35) for _ in range(10)]
print("原始温度列表：", temperature_list)

# 1.2 转换为Pandas Series并计算统计量
temp_series = pd.Series(temperature_list)
avg_temp = temp_series.mean()
max_temp = temp_series.max()
min_temp = temp_series.min()
print(f"平均温度：{avg_temp:.2f}℃ | 最高温度：{max_temp}℃ | 最低温度：{min_temp}℃")

# 1.3 创建城市信息字典
city_info = {
    "北京": {"人口(万)": 2154, "面积(平方公里)": 16410},
    "上海": {"人口(万)": 2428, "面积(平方公里)": 6340},
    "广州": {"人口(万)": 1530, "面积(平方公里)": 7434}
}
print("\n=== 城市基本信息 ===")
for city, info in city_info.items():
    print(f"{city}：人口 {info['人口(万)']} 万，面积 {info['面积(平方公里)']} 平方公里")


# ======================
# 2. 条件与循环应用
# ======================
# 2.1 摄氏转华氏函数 & 生成对应表格
def celsius_to_fahrenheit(celsius):
    return celsius * 9/5 + 32

fahrenheit_list = [celsius_to_fahrenheit(temp) for temp in temperature_list]
# 创建温度对应表格（清晰展示）
temp_comparison_df = pd.DataFrame({
    "摄氏温度(℃)": temperature_list,
    "华氏温度(°F)": [f"{f:.2f}" for f in fahrenheit_list]
})
print("\n=== 摄氏温度与华氏温度对应表 ===")
print(temp_comparison_df.to_string(index=False))  # 不显示索引，更整洁

# 2.2 筛选高于20℃的温度
high_temp = [temp for temp in temperature_list if temp > 20]
print("\n高于20℃的温度：", high_temp)

# 2.3 温度分级 & 准备可视化数据（按等级分类索引和温度）
temp_levels = []
cold_idx, cold_temp = [], []   # 寒冷：<0℃
comfort_idx, comfort_temp = [], []  # 舒适：0-20℃
hot_idx, hot_temp = [], []     # 炎热：>20℃

for idx, t in enumerate(temperature_list):
    if t < 0:
        level = "寒冷"
        cold_idx.append(idx)
        cold_temp.append(t)
    elif 0 <= t <= 20:
        level = "舒适"
        comfort_idx.append(idx)
        comfort_temp.append(t)
    else:
        level = "炎热"
        hot_idx.append(idx)
        hot_temp.append(t)
    temp_levels.append(level)

print("\n=== 温度分级详情 ===")
print("寒冷等级（<0℃）：")
if cold_idx:
    for idx, t in zip(cold_idx, cold_temp):
        print(f"  编号：{idx+1}，温度：{t}℃")
else:
    print("  无")

print("\n舒适等级（0-20℃）：")
if comfort_idx:
    for idx, t in zip(comfort_idx, comfort_temp):
        print(f"  编号：{idx+1}，温度：{t}℃")
else:
    print("  无")

print("\n炎热等级（>20℃）：")
if hot_idx:
    for idx, t in zip(hot_idx, hot_temp):
        print(f"  编号：{idx+1}，温度：{t}℃")
else:
    print("  无")

# ======================
# 3. 数据可视化
# ======================
fig, ax = plt.subplots(figsize=(12, 7))

# 绘制基础折线图
ax.plot(temp_series.index, temp_series.values, color='gray', linestyle='-', linewidth=1.5, alpha=0.7, label='温度趋势')
ax.set_xticks(temp_series.index)  # 设置刻度位置为0-9
ax.set_xticklabels(temp_series.index + 1, fontsize=12)
# 绘制不同等级的彩色散点
if cold_idx:
    ax.scatter(cold_idx, cold_temp, color='blue', s=120, zorder=5, label='寒冷 (<0℃)')
if comfort_idx:
    ax.scatter(comfort_idx, comfort_temp, color='green', s=120, zorder=5, label='舒适 (0-20℃)')
if hot_idx:
    ax.scatter(hot_idx, hot_temp, color='red', s=120, zorder=5, label='炎热 (>20℃)')

# 图表标注优化
ax.set_title("随机温度变化折线图", fontsize=16, pad=20)
ax.set_xlabel("样本序号", fontsize=14)
ax.set_ylabel("温度(℃)", fontsize=14)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=12, loc='upper right')

plt.show()