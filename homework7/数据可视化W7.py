from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import requests
from dash import Input, Output, dcc, html
from plotly.subplots import make_subplots


TIMEZONE = "Asia/Shanghai"
FORECAST_API = "https://api.open-meteo.com/v1/forecast"
CHINA_GEOJSON_URL = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
ASSET_DIR = BASE_DIR / "assets"
CHINA_GEOJSON_PATH = ASSET_DIR / "china_provinces.geojson"

THREE_CITY_COORDS = {
    "南昌": {"latitude": 28.6829, "longitude": 115.8582},
    "上海": {"latitude": 31.2304, "longitude": 121.4737},
    "广州": {"latitude": 23.1291, "longitude": 113.2644},
}

CAPITAL_COORDS = {
    "北京": (39.9042, 116.4074),
    "天津": (39.3434, 117.3616),
    "上海": (31.2304, 121.4737),
    "重庆": (29.5630, 106.5516),
    "哈尔滨": (45.8038, 126.5349),
    "长春": (43.8171, 125.3235),
    "沈阳": (41.8057, 123.4315),
    "呼和浩特": (40.8426, 111.7492),
    "石家庄": (38.0428, 114.5149),
    "乌鲁木齐": (43.8256, 87.6168),
    "兰州": (36.0611, 103.8343),
    "西宁": (36.6171, 101.7782),
    "西安": (34.3416, 108.9398),
    "银川": (38.4872, 106.2309),
    "郑州": (34.7466, 113.6254),
    "济南": (36.6512, 117.1201),
    "太原": (37.8706, 112.5489),
    "合肥": (31.8206, 117.2272),
    "武汉": (30.5928, 114.3055),
    "南京": (32.0603, 118.7969),
    "成都": (30.5728, 104.0668),
    "贵阳": (26.6470, 106.6302),
    "昆明": (25.0389, 102.7183),
    "南宁": (22.8170, 108.3669),
    "拉萨": (29.6520, 91.1721),
    "杭州": (30.2741, 120.1551),
    "南昌": (28.6829, 115.8582),
    "长沙": (28.2278, 112.9388),
    "福州": (26.0745, 119.2965),
    "广州": (23.1291, 113.2644),
    "海口": (20.0442, 110.1983),
    "台北": (25.0330, 121.5654),
}

WEATHER_COLORS = {
    "晴": "#f59e0b",
    "多云": "#60a5fa",
    "阴": "#475569",
    "雾": "#94a3b8",
    "毛毛雨": "#38bdf8",
    "雨": "#2563eb",
    "雪": "#8b5cf6",
    "雷暴": "#ef4444",
    "其他": "#64748b",
}

DIRECTION_ORDER = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    ASSET_DIR.mkdir(exist_ok=True)


def fetch_json(params: Dict[str, object]) -> Dict[str, object]:
    response = requests.get(FORECAST_API, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def weather_code_to_label(code: int) -> str:
    code = int(code)
    if code == 0:
        return "晴"
    if code in (1, 2):
        return "多云"
    if code == 3:
        return "阴"
    if code in (45, 48):
        return "雾"
    if code in (51, 53, 55, 56, 57):
        return "毛毛雨"
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "雨"
    if code in (71, 73, 75, 77, 85, 86):
        return "雪"
    if code in (95, 96, 99):
        return "雷暴"
    return "其他"


def direction_to_label(angle: float) -> str:
    index = int(((float(angle) % 360) + 22.5) // 45) % 8
    return DIRECTION_ORDER[index]


def load_china_geojson() -> Dict[str, object] | None:
    if CHINA_GEOJSON_PATH.exists():
        return json.loads(CHINA_GEOJSON_PATH.read_text(encoding="utf-8"))

    try:
        response = requests.get(CHINA_GEOJSON_URL, timeout=30)
        response.raise_for_status()
        CHINA_GEOJSON_PATH.write_text(response.text, encoding="utf-8")
        return response.json()
    except Exception:
        return None


def get_nanchang_future_24h() -> pd.DataFrame:
    coord = THREE_CITY_COORDS["南昌"]
    payload = fetch_json(
        {
            "latitude": coord["latitude"],
            "longitude": coord["longitude"],
            "hourly": "temperature_2m,relative_humidity_2m",
            "forecast_hours": 24,
            "timezone": TIMEZONE,
        }
    )
    hourly = payload["hourly"]
    return pd.DataFrame(
        {
            "time": pd.to_datetime(hourly["time"]),
            "temperature_2m": hourly["temperature_2m"],
            "relative_humidity_2m": hourly["relative_humidity_2m"],
        }
    )


def get_three_city_recent_24h() -> Dict[str, pd.DataFrame]:
    frames: Dict[str, pd.DataFrame] = {}
    for city, coord in THREE_CITY_COORDS.items():
        payload = fetch_json(
            {
                "latitude": coord["latitude"],
                "longitude": coord["longitude"],
                "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,wind_direction_10m",
                "past_hours": 24,
                "forecast_hours": 0,
                "timezone": TIMEZONE,
            }
        )
        hourly = payload["hourly"]
        frames[city] = pd.DataFrame(
            {
                "time": pd.to_datetime(hourly["time"]),
                "temperature_2m": hourly["temperature_2m"],
                "precipitation_probability": hourly["precipitation_probability"],
                "wind_speed_10m": hourly["wind_speed_10m"],
                "wind_direction_10m": hourly["wind_direction_10m"],
            }
        )
    return frames


def get_capitals_future_24h() -> pd.DataFrame:
    rows: List[pd.DataFrame] = []
    for city, (lat, lon) in CAPITAL_COORDS.items():
        payload = fetch_json(
            {
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,weather_code",
                "forecast_hours": 24,
                "timezone": TIMEZONE,
            }
        )
        hourly = payload["hourly"]
        frame = pd.DataFrame(
            {
                "city": city,
                "latitude": lat,
                "longitude": lon,
                "time": pd.to_datetime(hourly["time"]),
                "temperature_2m": hourly["temperature_2m"],
                "weather_code": hourly["weather_code"],
            }
        )
        frame["weather_label"] = frame["weather_code"].apply(weather_code_to_label)
        frame["time_label"] = frame["time"].dt.strftime("%H:%M")
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def build_part1_line(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df,
        x="time",
        y="temperature_2m",
        markers=True,
        title="24小时温度变化（南昌）",
        labels={"time": "时间", "temperature_2m": "温度（℃）"},
    )
    fig.update_traces(
        line=dict(color="#ef553b", width=3),
        marker=dict(size=7, color="#ef553b"),
        hovertemplate="时间：%{x|%H:%M}<br>温度：%{y:.1f}℃<extra></extra>",
    )
    fig.update_layout(
        template="plotly_white",
        title_x=0.5,
        height=520,
        xaxis=dict(tickformat="%H:%M", showgrid=True, gridcolor="#dbe4f0"),
        yaxis=dict(showgrid=True, gridcolor="#dbe4f0"),
    )
    return fig


def build_part1_scatter(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df,
        x="temperature_2m",
        y="relative_humidity_2m",
        color="temperature_2m",
        color_continuous_scale="Turbo",
        trendline="ols",
        title="温湿度散点关系图（南昌）",
        labels={"temperature_2m": "温度（℃）", "relative_humidity_2m": "相对湿度（%）"},
    )
    fig.update_traces(
        marker=dict(size=10, line=dict(color="white", width=0.8)),
        hovertemplate="温度：%{x:.1f}℃<br>相对湿度：%{y:.0f}%<extra></extra>",
    )
    fig.update_layout(template="plotly_white", title_x=0.5, height=520)
    return fig


def build_compare_bar(city_frames: Dict[str, pd.DataFrame]) -> go.Figure:
    records = []
    for city, frame in city_frames.items():
        max_temp = float(frame["temperature_2m"].max())
        min_temp = float(frame["temperature_2m"].min())
        records.append(
            {
                "city": city,
                "max_temperature": max_temp,
                "day_night_range": max_temp - min_temp,
            }
        )
    compare_df = pd.DataFrame(records)
    fig = px.bar(
        compare_df,
        x="city",
        y="max_temperature",
        error_y="day_night_range",
        text="max_temperature",
        color="city",
        title="三城市最高温对比（误差线表示昼夜温差）",
        labels={"city": "城市", "max_temperature": "最高温（℃）"},
        color_discrete_sequence=["#2563eb", "#0ea5e9", "#f97316"],
    )
    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
        hovertemplate="城市：%{x}<br>最高温：%{y:.1f}℃<br>昼夜温差：%{error_y.array:.1f}℃<extra></extra>",
    )
    fig.update_layout(template="plotly_white", title_x=0.5, showlegend=False, height=560)
    return fig


def build_wind_rose(city: str, frame: pd.DataFrame) -> go.Figure:
    rose_df = frame.copy()
    rose_df["direction_label"] = rose_df["wind_direction_10m"].apply(direction_to_label)
    grouped = rose_df.groupby("direction_label", as_index=False)["wind_speed_10m"].mean()
    grouped = grouped.rename(columns={"wind_speed_10m": "avg_wind_speed"})
    grouped["direction_label"] = pd.Categorical(
        grouped["direction_label"],
        categories=DIRECTION_ORDER,
        ordered=True,
    )
    grouped = grouped.sort_values("direction_label").set_index("direction_label").reindex(DIRECTION_ORDER, fill_value=0).reset_index()

    fig = px.bar_polar(
        grouped,
        r="avg_wind_speed",
        theta="direction_label",
        color="avg_wind_speed",
        color_continuous_scale="Blues",
        title=f"{city}风速玫瑰图",
        labels={"direction_label": "风向", "avg_wind_speed": "平均风速（km/h）"},
    )
    fig.update_traces(hovertemplate="风向：%{theta}<br>平均风速：%{r:.1f} km/h<extra></extra>")
    fig.update_layout(template="plotly_white", title_x=0.5, height=620)
    return fig


def build_city_detail_figure(city: str, frame: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=(f"{city}最近24小时温度变化", f"{city}最近24小时降水概率变化"),
    )
    fig.add_trace(
        go.Scatter(
            x=frame["time"],
            y=frame["temperature_2m"],
            mode="lines+markers",
            name="温度（℃）",
            line=dict(color="#ef553b", width=3),
            marker=dict(size=7, color="#ef553b"),
            hovertemplate="时间：%{x|%H:%M}<br>温度：%{y:.1f}℃<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=frame["time"],
            y=frame["precipitation_probability"],
            name="降水概率（%）",
            marker_color="#2563eb",
            hovertemplate="时间：%{x|%H:%M}<br>降水概率：%{y:.0f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.update_xaxes(tickformat="%H:%M", title_text="时间", row=2, col=1)
    fig.update_yaxes(title_text="温度（℃）", row=1, col=1)
    fig.update_yaxes(title_text="降水概率（%）", row=2, col=1)
    fig.update_layout(template="plotly_white", height=680, title_x=0.5)
    return fig


def build_part2_dashboard_html(city_frames: Dict[str, pd.DataFrame]) -> None:
    compare_fig = build_compare_bar(city_frames)
    city_options = list(city_frames.keys())
    initial_city = city_options[0]
    wind_rose_by_city = {
        city: json.loads(pio.to_json(build_wind_rose(city, frame), pretty=False))
        for city, frame in city_frames.items()
    }
    detail_by_city = {
        city: json.loads(pio.to_json(build_city_detail_figure(city, frame), pretty=False))
        for city, frame in city_frames.items()
    }
    options_html = "".join(
        f'<option value="{city}" {"selected" if city == initial_city else ""}>{city}</option>'
        for city in city_options
    )

    html_text = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>实验七 Part 2 交互图表</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 24px;
            font-family: "Microsoft YaHei", sans-serif;
            background: linear-gradient(180deg, #f7f9fd 0%, #eef3fb 100%);
            color: #1f2937;
        }}
        .page {{
            max-width: 1480px;
            margin: 0 auto;
        }}
        .title {{
            font-size: 34px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: #64748b;
            margin-bottom: 24px;
            font-size: 16px;
        }}
        .toolbar {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 18px;
            padding: 16px 18px;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
        }}
        .toolbar label {{
            font-weight: 600;
        }}
        .toolbar select {{
            padding: 8px 12px;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            font-size: 15px;
            min-width: 180px;
            background: #fff;
        }}
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 16px;
        }}
        .tab-btn {{
            border: none;
            background: #dbeafe;
            color: #1d4ed8;
            padding: 10px 18px;
            border-radius: 999px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
        }}
        .tab-btn.active {{
            background: #2563eb;
            color: #ffffff;
        }}
        .panel {{
            display: none;
            background: #ffffff;
            border-radius: 18px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
            padding: 12px;
        }}
        .panel.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="page">
        <div class="title">实验七 Part 2 交互图表</div>
        <div class="subtitle">使用下拉框切换南昌、上海、广州，并通过选项卡查看不同气象图表。</div>

        <div class="toolbar">
            <label for="citySelect">选择城市：</label>
            <select id="citySelect">{options_html}</select>
        </div>

        <div class="tabs">
            <button class="tab-btn active" data-target="barPanel">城市对比柱状图</button>
            <button class="tab-btn" data-target="rosePanel">风速玫瑰图</button>
            <button class="tab-btn" data-target="detailPanel">城市气象详情图</button>
        </div>

        <section id="barPanel" class="panel active">
            <div id="compareBar" style="height: 640px;"></div>
        </section>

        <section id="rosePanel" class="panel">
            <div id="windRose" style="height: 680px;"></div>
        </section>

        <section id="detailPanel" class="panel">
            <div id="cityDetail" style="height: 760px;"></div>
        </section>
    </div>

    <script>
        const compareBarFigure = {pio.to_json(compare_fig, pretty=False)};
        const windRoseFigures = {json.dumps(wind_rose_by_city, ensure_ascii=False)};
        const detailFigures = {json.dumps(detail_by_city, ensure_ascii=False)};
        const initialCity = {json.dumps(initial_city, ensure_ascii=False)};

        Plotly.newPlot('compareBar', compareBarFigure.data, compareBarFigure.layout, {{ responsive: true, displaylogo: false }});
        Plotly.newPlot('windRose', windRoseFigures[initialCity].data, windRoseFigures[initialCity].layout, {{ responsive: true, displaylogo: false }});
        Plotly.newPlot('cityDetail', detailFigures[initialCity].data, detailFigures[initialCity].layout, {{ responsive: true, displaylogo: false }});

        document.getElementById('citySelect').addEventListener('change', function () {{
            const city = this.value;
            Plotly.react('windRose', windRoseFigures[city].data, windRoseFigures[city].layout, {{ responsive: true, displaylogo: false }});
            Plotly.react('cityDetail', detailFigures[city].data, detailFigures[city].layout, {{ responsive: true, displaylogo: false }});
        }});

        document.querySelectorAll('.tab-btn').forEach((button) => {{
            button.addEventListener('click', () => {{
                document.querySelectorAll('.tab-btn').forEach((btn) => btn.classList.remove('active'));
                document.querySelectorAll('.panel').forEach((panel) => panel.classList.remove('active'));
                button.classList.add('active');
                document.getElementById(button.dataset.target).classList.add('active');
            }});
        }});
    </script>
</body>
</html>
"""
    (OUTPUT_DIR / "part2_city_dashboard.html").write_text(html_text, encoding="utf-8")


def build_boundary_trace(geojson_data: Dict[str, object] | None) -> go.Scattergeo | None:
    if not geojson_data:
        return None

    lons: List[float | None] = []
    lats: List[float | None] = []
    for feature in geojson_data.get("features", []):
        geometry = feature.get("geometry", {})
        geo_type = geometry.get("type")
        coordinates = geometry.get("coordinates", [])
        polygons = coordinates if geo_type == "MultiPolygon" else [coordinates]
        for polygon in polygons:
            for ring in polygon:
                for lon, lat in ring:
                    lons.append(float(lon))
                    lats.append(float(lat))
                lons.append(None)
                lats.append(None)

    return go.Scattergeo(
        lon=lons,
        lat=lats,
        mode="lines",
        line=dict(color="#64748b", width=1.0),
        hoverinfo="skip",
        showlegend=False,
        name="省级边界",
    )


def calculate_bubble_sizes(values: pd.Series, global_min: float, global_max: float) -> List[float]:
    if global_max - global_min < 1e-6:
        return [22.0] * len(values)
    normalized = (values.astype(float) - global_min) / (global_max - global_min)
    return (normalized * 20 + 15).round(2).tolist()


def build_map_points_trace(
    frame: pd.DataFrame,
    global_min: float,
    global_max: float,
) -> go.Scattergeo:
    marker_colors = [WEATHER_COLORS.get(label, WEATHER_COLORS["其他"]) for label in frame["weather_label"]]
    custom_data = np.column_stack(
        [
            frame["city"].to_numpy(),
            frame["temperature_2m"].round(1).astype(str).to_numpy(),
            frame["weather_label"].to_numpy(),
            frame["time_label"].to_numpy(),
        ]
    )
    return go.Scattergeo(
        lon=frame["longitude"],
        lat=frame["latitude"],
        mode="markers",
        text=frame["city"],
        customdata=custom_data,
        hovertemplate=(
            "城市：%{customdata[0]}<br>"
            "时间：%{customdata[3]}<br>"
            "温度：%{customdata[1]}℃<br>"
            "天气：%{customdata[2]}<extra></extra>"
        ),
        marker=dict(
            size=calculate_bubble_sizes(frame["temperature_2m"], global_min, global_max),
            color=marker_colors,
            line=dict(color="#ffffff", width=1.2),
            opacity=0.9,
        ),
        showlegend=False,
        name="城市气象点",
    )


def build_geo_layout(title: str, subtitle: str, animated: bool = False) -> go.Layout:
    slider_block = []
    button_block = []
    if animated:
        button_block = [
            dict(
                type="buttons",
                direction="left",
                x=0.5,
                y=0.02,
                xanchor="center",
                yanchor="bottom",
                showactive=False,
                buttons=[
                    dict(
                        label="播放",
                        method="animate",
                        args=[
                            None,
                            {
                                "frame": {"duration": 700, "redraw": True},
                                "transition": {"duration": 250},
                                "fromcurrent": True,
                            },
                        ],
                    ),
                    dict(
                        label="暂停",
                        method="animate",
                        args=[
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "transition": {"duration": 0},
                                "mode": "immediate",
                            },
                        ],
                    ),
                ],
            )
        ]
        slider_block = [
            dict(
                active=0,
                x=0.08,
                y=0.06,
                len=0.84,
                currentvalue={"prefix": "当前时间：", "font": {"size": 15}},
                pad={"t": 30, "b": 0},
                steps=[],
            )
        ]

    return go.Layout(
        title=dict(text=f"{title}<br><span style='font-size:13px;color:#64748b'>{subtitle}</span>", x=0.03),
        height=780,
        margin=dict(l=12, r=12, t=72, b=90 if animated else 16),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        geo=dict(
            scope="asia",
            projection_type="mercator",
            center=dict(lat=35.5, lon=104.5),
            lonaxis=dict(range=[73, 136]),
            lataxis=dict(range=[17.5, 54.8]),
            showland=True,
            landcolor="#f8fafc",
            showocean=True,
            oceancolor="#eff6ff",
            showcountries=True,
            countrycolor="#94a3b8",
            countrywidth=1.0,
            showcoastlines=True,
            coastlinecolor="#94a3b8",
            coastlinewidth=0.8,
            bgcolor="#ffffff",
        ),
        updatemenus=button_block,
        sliders=slider_block,
    )


def build_map_snapshot_figure(capital_df: pd.DataFrame, boundary_trace: go.Scattergeo | None) -> go.Figure:
    first_time = capital_df["time"].min()
    first_hour_df = capital_df[capital_df["time"] == first_time].copy()
    global_min = float(capital_df["temperature_2m"].min())
    global_max = float(capital_df["temperature_2m"].max())

    traces: List[go.BaseTraceType] = []
    if boundary_trace is not None:
        traces.append(boundary_trace)
    traces.append(build_map_points_trace(first_hour_df, global_min, global_max))

    return go.Figure(
        data=traces,
        layout=build_geo_layout("全国主要省会城市气象分布图", "左侧地图可点击切换右侧城市温度曲线"),
    )


def build_animation_map_figure(capital_df: pd.DataFrame, boundary_trace: go.Scattergeo | None) -> go.Figure:
    global_min = float(capital_df["temperature_2m"].min())
    global_max = float(capital_df["temperature_2m"].max())
    time_labels = sorted(capital_df["time_label"].unique(), key=lambda value: pd.to_datetime(value, format="%H:%M"))
    first_hour_df = capital_df[capital_df["time_label"] == time_labels[0]].copy()

    traces: List[go.BaseTraceType] = []
    if boundary_trace is not None:
        traces.append(boundary_trace)
    traces.append(build_map_points_trace(first_hour_df, global_min, global_max))

    fig = go.Figure(
        data=traces,
        layout=build_geo_layout(
            "全国主要省会城市未来24小时温度场动画",
            "支持播放时间轴，并可点击左侧城市查看右侧完整温度曲线",
            animated=True,
        ),
    )

    frames: List[go.Frame] = []
    for label in time_labels:
        frame_df = capital_df[capital_df["time_label"] == label].copy()
        frames.append(
            go.Frame(
                name=label,
                data=[build_map_points_trace(frame_df, global_min, global_max)],
                traces=[1 if boundary_trace is not None else 0],
            )
        )
    fig.frames = frames
    fig.layout.sliders[0]["steps"] = [
        {
            "label": label,
            "method": "animate",
            "args": [
                [label],
                {
                    "mode": "immediate",
                    "frame": {"duration": 650, "redraw": True},
                    "transition": {"duration": 220},
                },
            ],
        }
        for label in time_labels
    ]
    return fig


def build_city_curve(capital_df: pd.DataFrame, city: str) -> go.Figure:
    city_df = capital_df[capital_df["city"] == city].copy().sort_values("time")
    mean_temp = float(city_df["temperature_2m"].mean())
    max_idx = city_df["temperature_2m"].idxmax()
    min_idx = city_df["temperature_2m"].idxmin()
    min_temp = float(city_df["temperature_2m"].min())
    max_temp = float(city_df["temperature_2m"].max())
    padding = max(1.2, (max_temp - min_temp) * 0.25)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=city_df["time"],
            y=city_df["temperature_2m"],
            mode="lines+markers",
            name="温度",
            line=dict(color="#0f766e", width=3.6),
            marker=dict(size=7, color="#0f766e"),
            hovertemplate="时间：%{x|%H:%M}<br>温度：%{y:.1f}℃<extra></extra>",
        )
    )
    fig.add_hline(
        y=mean_temp,
        line_dash="dash",
        line_color="#94a3b8",
        annotation_text="平均温度",
        annotation_position="top left",
    )
    fig.add_trace(
        go.Scatter(
            x=[city_df.loc[max_idx, "time"]],
            y=[city_df.loc[max_idx, "temperature_2m"]],
            mode="markers+text",
            name="最高温",
            text=[f"最高温 {city_df.loc[max_idx, 'temperature_2m']:.1f}℃"],
            textposition="top center",
            marker=dict(size=14, color="#ef4444", line=dict(color="white", width=1.5)),
            hovertemplate="最高温：%{y:.1f}℃<br>时间：%{x|%H:%M}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[city_df.loc[min_idx, "time"]],
            y=[city_df.loc[min_idx, "temperature_2m"]],
            mode="markers+text",
            name="最低温",
            text=[f"最低温 {city_df.loc[min_idx, 'temperature_2m']:.1f}℃"],
            textposition="bottom center",
            marker=dict(size=14, color="#2563eb", line=dict(color="white", width=1.5)),
            hovertemplate="最低温：%{y:.1f}℃<br>时间：%{x|%H:%M}<extra></extra>",
        )
    )
    fig.update_layout(
        template="plotly_white",
        title=dict(text=f"{city}未来24小时温度曲线", x=0.04),
        height=780,
        margin=dict(l=56, r=20, t=70, b=60),
        legend=dict(orientation="h", y=1.08, x=0),
        xaxis=dict(title="时间", tickformat="%H:%M", showgrid=True, gridcolor="#e2e8f0"),
        yaxis=dict(title="温度（℃）", showgrid=True, gridcolor="#e2e8f0", range=[min_temp - padding, max_temp + padding]),
    )
    return fig


def build_part3_linked_html(
    output_path: Path,
    page_title: str,
    page_subtitle: str,
    map_panel_title: str,
    map_figure: go.Figure,
    line_figures: Dict[str, go.Figure],
    default_city: str,
) -> None:
    map_json = json.loads(pio.to_json(map_figure, pretty=False))
    line_json = {city: json.loads(pio.to_json(fig, pretty=False)) for city, fig in line_figures.items()}
    legend_html = "".join(
        f'<span class="legend-item"><span class="swatch" style="background:{color}"></span>{label}</span>'
        for label, color in WEATHER_COLORS.items()
    )

    html_text = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 22px;
            font-family: "Microsoft YaHei", sans-serif;
            background: linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
            color: #0f172a;
        }}
        .page {{
            max-width: 1880px;
            margin: 0 auto;
        }}
        .page-title {{
            font-size: 34px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .page-subtitle {{
            color: #64748b;
            margin-bottom: 18px;
            font-size: 16px;
        }}
        .layout {{
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 18px;
            align-items: stretch;
        }}
        .panel {{
            background: #ffffff;
            border-radius: 22px;
            box-shadow: 0 16px 36px rgba(15, 23, 42, 0.10);
            padding: 16px 18px 14px;
            min-height: 840px;
        }}
        .panel-head {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 10px;
        }}
        .panel-title {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .panel-note {{
            font-size: 14px;
            color: #64748b;
        }}
        .legend-wrap {{
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 8px 10px;
            max-width: 420px;
        }}
        .legend-item {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            border-radius: 999px;
            background: #f8fafc;
            color: #334155;
            font-size: 13px;
        }}
        .swatch {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }}
        .city-chip {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 999px;
            background: #dbeafe;
            color: #1d4ed8;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .chart {{
            height: 790px;
        }}
        .hint {{
            color: #64748b;
            font-size: 14px;
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="page">
        <div class="page-title">{page_title}</div>
        <div class="page-subtitle">{page_subtitle}</div>

        <div class="layout">
            <section class="panel">
                <div class="panel-head">
                    <div>
                        <div class="panel-title">{map_panel_title}</div>
                        <div class="panel-note">地图已放大，并叠加中国省级分界线；点击城市气泡可切换右侧温度曲线。</div>
                    </div>
                    <div class="legend-wrap">{legend_html}</div>
                </div>
                <div id="mapChart" class="chart"></div>
            </section>

            <section class="panel">
                <div class="panel-title">城市温度联动曲线</div>
                <div class="hint">右侧曲线会根据左侧当前选中的城市同步更新。</div>
                <div class="city-chip">当前城市：<span id="currentCity">{default_city}</span></div>
                <div id="lineChart" class="chart"></div>
            </section>
        </div>
    </div>

    <script>
        const mapFigure = {json.dumps(map_json, ensure_ascii=False)};
        const lineFigures = {json.dumps(line_json, ensure_ascii=False)};
        const defaultCity = {json.dumps(default_city, ensure_ascii=False)};

        function renderLine(city) {{
            const safeCity = lineFigures[city] ? city : defaultCity;
            const figure = lineFigures[safeCity];
            document.getElementById('currentCity').textContent = safeCity;
            Plotly.react('lineChart', figure.data, figure.layout, {{ responsive: true, displaylogo: false }});
        }}

        function bindMapClick() {{
            const mapNode = document.getElementById('mapChart');
            mapNode.on('plotly_click', function(event) {{
                if (!event.points || !event.points.length) {{
                    return;
                }}
                const point = event.points[0];
                const city = point.customdata ? point.customdata[0] : point.text;
                if (city) {{
                    renderLine(city);
                }}
            }});
        }}

        Plotly.newPlot('mapChart', mapFigure.data, mapFigure.layout, {{ responsive: true, displaylogo: false }}).then(function() {{
            if (mapFigure.frames && mapFigure.frames.length) {{
                Plotly.addFrames('mapChart', mapFigure.frames);
            }}
            bindMapClick();
        }});
        renderLine(defaultCity);
    </script>
</body>
</html>
"""
    output_path.write_text(html_text, encoding="utf-8")


def save_static_outputs(
    nanchang_df: pd.DataFrame,
    city_frames: Dict[str, pd.DataFrame],
    capital_df: pd.DataFrame,
) -> None:
    build_part1_line(nanchang_df).write_html(OUTPUT_DIR / "part1_temperature_line.html", include_plotlyjs="cdn")
    build_part1_scatter(nanchang_df).write_html(OUTPUT_DIR / "part1_temp_humidity_scatter.html", include_plotlyjs="cdn")
    build_compare_bar(city_frames).write_html(OUTPUT_DIR / "part2_city_compare_bar.html", include_plotlyjs="cdn")
    build_wind_rose("南昌", city_frames["南昌"]).write_html(OUTPUT_DIR / "part2_wind_rose_nanchang.html", include_plotlyjs="cdn")
    build_part2_dashboard_html(city_frames)

    boundary_trace = build_boundary_trace(load_china_geojson())
    snapshot_map = build_map_snapshot_figure(capital_df, boundary_trace)
    animation_map = build_animation_map_figure(capital_df, boundary_trace)
    line_figures = {city: build_city_curve(capital_df, city) for city in CAPITAL_COORDS}

    build_part3_linked_html(
        OUTPUT_DIR / "part3_map_snapshot.html",
        "实验七 Part 3.1 全国主要省会城市气象地图",
        "左半屏显示放大后的地图与省界，右半屏同步显示选中城市的未来24小时温度曲线。",
        "未来首小时城市气象快照",
        snapshot_map,
        line_figures,
        default_city="南昌",
    )
    build_part3_linked_html(
        OUTPUT_DIR / "part3_temperature_animation.html",
        "实验七 Part 3.2 全国主要省会城市温度场动画",
        "左半屏支持播放未来24小时温度场动画，右半屏同步显示点击城市的完整温度曲线。",
        "全国温度场时间动画",
        animation_map,
        line_figures,
        default_city="南昌",
    )


def create_dash_app(
    nanchang_df: pd.DataFrame,
    city_frames: Dict[str, pd.DataFrame],
    capital_df: pd.DataFrame,
) -> dash.Dash:
    app = dash.Dash(__name__)
    compare_fig = build_compare_bar(city_frames)
    base_city = "南昌"
    boundary_trace = build_boundary_trace(load_china_geojson())
    part3_map = build_animation_map_figure(capital_df, boundary_trace)

    app.layout = html.Div(
        style={"padding": "20px 28px", "fontFamily": "Microsoft YaHei, sans-serif", "background": "#F7F9FC"},
        children=[
            html.H1("实验七 Plotly 数据可视化仪表盘", style={"textAlign": "center"}),
            dcc.Tabs(
                children=[
                    dcc.Tab(
                        label="基础图表",
                        children=[
                            dcc.Graph(figure=build_part1_line(nanchang_df)),
                            dcc.Graph(figure=build_part1_scatter(nanchang_df)),
                        ],
                    ),
                    dcc.Tab(
                        label="交互图表",
                        children=[
                            html.Div(
                                [
                                    html.Label("选择城市：", style={"fontWeight": "bold"}),
                                    dcc.Dropdown(
                                        id="city-dropdown",
                                        options=[{"label": city, "value": city} for city in city_frames.keys()],
                                        value=base_city,
                                        clearable=False,
                                        style={"width": "260px", "marginBottom": "16px"},
                                    ),
                                ],
                                style={"padding": "0 18px"},
                            ),
                            dcc.Tabs(
                                children=[
                                    dcc.Tab(label="城市对比柱状图", children=[dcc.Graph(id="compare-bar-graph", figure=compare_fig)]),
                                    dcc.Tab(label="风速玫瑰图", children=[dcc.Graph(id="wind-rose-graph", style={"height": "720px"})]),
                                    dcc.Tab(label="城市气象详情图", children=[dcc.Graph(id="city-detail-graph", style={"height": "760px"})]),
                                ]
                            ),
                        ],
                    ),
                    dcc.Tab(
                        label="时空数据可视化",
                        children=[
                            html.Div(
                                [
                                    dcc.Graph(
                                        id="part3-map-graph",
                                        figure=part3_map,
                                        style={"width": "55%", "height": "820px"},
                                    ),
                                    dcc.Graph(
                                        id="part3-line-graph",
                                        figure=build_city_curve(capital_df, base_city),
                                        style={"width": "45%", "height": "820px"},
                                    ),
                                ],
                                style={"display": "flex", "gap": "16px", "padding": "8px 12px 18px"},
                            )
                        ],
                    ),
                ]
            ),
        ],
    )

    @app.callback(
        Output("wind-rose-graph", "figure"),
        Output("city-detail-graph", "figure"),
        Input("city-dropdown", "value"),
    )
    def update_city_charts(city: str) -> tuple[go.Figure, go.Figure]:
        frame = city_frames[city]
        return build_wind_rose(city, frame), build_city_detail_figure(city, frame)

    @app.callback(
        Output("part3-line-graph", "figure"),
        Input("part3-map-graph", "clickData"),
    )
    def update_linked_curve(click_data: Dict[str, object] | None) -> go.Figure:
        city = base_city
        if click_data and click_data.get("points"):
            point = click_data["points"][0]
            if point.get("customdata"):
                city = point["customdata"][0]
            elif point.get("text"):
                city = point["text"]
        return build_city_curve(capital_df, city)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="实验七 Plotly 数据可视化")
    parser.add_argument("--serve", action="store_true", help="启动 Dash 交互页面")
    parser.add_argument("--host", default="127.0.0.1", help="Dash 服务地址")
    parser.add_argument("--port", type=int, default=8050, help="Dash 服务端口")
    args = parser.parse_args()

    ensure_dirs()

    nanchang_df = get_nanchang_future_24h()
    city_frames = get_three_city_recent_24h()
    capital_df = get_capitals_future_24h()

    save_static_outputs(nanchang_df, city_frames, capital_df)

    print("已生成静态图表：")
    for file_name in [
        "part1_temperature_line.html",
        "part1_temp_humidity_scatter.html",
        "part2_city_compare_bar.html",
        "part2_wind_rose_nanchang.html",
        "part2_city_dashboard.html",
        "part3_map_snapshot.html",
        "part3_temperature_animation.html",
    ]:
        print(f"- {OUTPUT_DIR / file_name}")

    if args.serve:
        app = create_dash_app(nanchang_df, city_frames, capital_df)
        print(f"Dash 页面地址：http://{args.host}:{args.port}")
        app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
