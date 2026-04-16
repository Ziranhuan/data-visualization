from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import requests
import urllib3
from pyecharts import options as opts
from pyecharts.charts import Bar, Geo, HeatMap, Line, Radar, Timeline
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ChartType, ThemeType


TIMEZONE = "Asia/Shanghai"
FORECAST_API = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_API = "https://archive-api.open-meteo.com/v1/archive"
OUTPUT_DIR = Path("output")
ASSET_DIR = OUTPUT_DIR / "assets"

CITYS = {
    "南昌": {"latitude": 28.6829, "longitude": 115.8582},
    "长沙": {"latitude": 28.2278, "longitude": 112.9388},
    "武汉": {"latitude": 30.5928, "longitude": 114.3055},
    "南京": {"latitude": 32.0603, "longitude": 118.7969},
    "上海": {"latitude": 31.2304, "longitude": 121.4737},
}

SUMMARY_LABELS = {
    "avg_temp_max": "平均最高温",
    "total_precipitation": "总降水量",
    "avg_wind_speed": "平均风速",
    "hot_day_ratio": "高温日占比",
}

DAILY_METRIC_LABELS = {
    "temperature_2m_max": "日最高温",
    "precipitation_sum": "日降水量",
    "avg_wind_speed": "日均风速",
    "hot_day": "高温日",
}

RADAR_CITY_COLORS = {
    "南昌": "#5470C6",
    "长沙": "#91CC75",
    "武汉": "#FAC858",
    "南京": "#EE6666",
    "上海": "#73C0DE",
}


def fetch_json(url: str, params: Dict[str, object]) -> Dict[str, object]:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    ASSET_DIR.mkdir(exist_ok=True)


def try_copy_local_asset(filename: str, local_path: Path) -> bool:
    search_roots = [Path(__file__).resolve().parent, Path(requests.__file__).resolve().parent.parent]
    for root in search_roots:
        for candidate in root.rglob(filename):
            if candidate.is_file():
                shutil.copyfile(candidate, local_path)
                return True
    return False


def download_asset(filename: str, urls: List[str], local_path: Path) -> None:
    if local_path.exists():
        return
    if try_copy_local_asset(filename, local_path):
        return

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    last_error: Exception | None = None
    for url in urls:
        for verify in (True, False):
            try:
                response = requests.get(url, timeout=30, verify=verify)
                response.raise_for_status()
                local_path.write_bytes(response.content)
                return
            except Exception as exc:
                last_error = exc
    raise RuntimeError(f"下载资源失败: {filename}") from last_error


def localize_html_assets(html_path: Path) -> None:
    asset_map = {
        "https://assets.pyecharts.org/assets/v6/echarts.min.js": (
            "echarts.min.js",
            [
                "https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js",
                "https://unpkg.com/echarts@5/dist/echarts.min.js",
                "https://assets.pyecharts.org/assets/v6/echarts.min.js",
            ],
        ),
        "https://assets.pyecharts.org/assets/v6/maps/china.js": (
            "china.js",
            [
                "https://cdn.jsdelivr.net/npm/echarts@5/map/js/china.js",
                "https://unpkg.com/echarts@5/map/js/china.js",
                "https://assets.pyecharts.org/assets/v6/maps/china.js",
            ],
        ),
    }
    html_text = html_path.read_text(encoding="utf-8")
    for remote_url, (filename, candidate_urls) in asset_map.items():
        if remote_url not in html_text:
            continue
        local_path = ASSET_DIR / filename
        download_asset(filename, candidate_urls, local_path)
        html_text = html_text.replace(remote_url, f"./assets/{filename}")
    html_path.write_text(html_text, encoding="utf-8")


def get_nanchang_past_7_days() -> pd.DataFrame:
    city = CITYS["南昌"]
    payload = fetch_json(
        FORECAST_API,
        {
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "hourly": "temperature_2m,precipitation",
            "past_hours": 168,
            "forecast_hours": 0,
            "timezone": TIMEZONE,
        },
    )

    hourly = payload["hourly"]
    df = pd.DataFrame(
        {
            "time": pd.to_datetime(hourly["time"]),
            "temperature_2m": hourly["temperature_2m"],
            "precipitation": hourly["precipitation"],
        }
    )
    return df


def get_city_august_2025_data() -> tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    summary_rows: List[Dict[str, float]] = []
    daily_data_by_city: Dict[str, pd.DataFrame] = {}

    for city_name, coord in CITYS.items():
        payload = fetch_json(
            ARCHIVE_API,
            {
                "latitude": coord["latitude"],
                "longitude": coord["longitude"],
                "start_date": "2025-08-01",
                "end_date": "2025-08-31",
                "daily": "temperature_2m_max,precipitation_sum",
                "hourly": "wind_speed_10m",
                "timezone": TIMEZONE,
            },
        )

        daily_df = pd.DataFrame(
            {
                "date": pd.to_datetime(payload["daily"]["time"]),
                "temperature_2m_max": payload["daily"]["temperature_2m_max"],
                "precipitation_sum": payload["daily"]["precipitation_sum"],
            }
        )

        hourly_df = pd.DataFrame(
            {
                "time": pd.to_datetime(payload["hourly"]["time"]),
                "wind_speed_10m": payload["hourly"]["wind_speed_10m"],
            }
        )
        hourly_df["date"] = hourly_df["time"].dt.normalize()
        wind_daily_mean = (
            hourly_df.groupby("date", as_index=False)["wind_speed_10m"]
            .mean()
            .rename(columns={"wind_speed_10m": "avg_wind_speed"})
        )

        merged_df = daily_df.merge(wind_daily_mean, on="date", how="left")
        merged_df["hot_day"] = (merged_df["temperature_2m_max"] > 30).astype(int)
        merged_df["city"] = city_name
        daily_data_by_city[city_name] = merged_df

        summary_rows.append(
            {
                "city": city_name,
                "avg_temp_max": round(float(merged_df["temperature_2m_max"].mean()), 2),
                "total_precipitation": round(float(merged_df["precipitation_sum"].sum()), 2),
                "avg_wind_speed": round(float(merged_df["avg_wind_speed"].mean()), 2),
                "hot_day_ratio": round(float(merged_df["hot_day"].mean()), 4),
            }
        )

    summary_df = pd.DataFrame(summary_rows).set_index("city")
    return summary_df, daily_data_by_city


def get_realtime_and_forecast_data() -> tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    realtime_rows: List[Dict[str, float]] = []
    forecast_by_city: Dict[str, pd.DataFrame] = {}

    for city_name, coord in CITYS.items():
        payload = fetch_json(
            FORECAST_API,
            {
                "latitude": coord["latitude"],
                "longitude": coord["longitude"],
                "current": "temperature_2m,wind_speed_10m",
                "hourly": "temperature_2m",
                "forecast_hours": 24,
                "timezone": TIMEZONE,
            },
        )

        current = payload["current"]
        realtime_rows.append(
            {
                "city": city_name,
                "latitude": coord["latitude"],
                "longitude": coord["longitude"],
                "temperature_2m": float(current["temperature_2m"]),
                "wind_speed_10m": float(current["wind_speed_10m"]),
                "current_time": current["time"],
            }
        )

        forecast_by_city[city_name] = pd.DataFrame(
            {
                "time": pd.to_datetime(payload["hourly"]["time"]),
                "temperature_2m": payload["hourly"]["temperature_2m"],
            }
        )

    realtime_df = pd.DataFrame(realtime_rows)
    return realtime_df, forecast_by_city


def z_score(series: pd.Series) -> pd.Series:
    std = float(series.std(ddof=0))
    if std == 0:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - float(series.mean())) / std


def build_part1_chart(df: pd.DataFrame) -> Bar:
    x_axis = df["time"].dt.strftime("%m-%d %H:%M").tolist()
    bar = (
        Bar(init_opts=opts.InitOpts(width="1400px", height="620px", theme=ThemeType.LIGHT))
        .add_xaxis(x_axis)
        .add_yaxis(
            "降水量(mm)",
            df["precipitation"].round(2).tolist(),
            yaxis_index=0,
            color="#4C78A8",
            category_gap="40%",
        )
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="温度(°C)",
                type_="value",
                position="right",
                axislabel_opts=opts.LabelOpts(formatter="{value} °C"),
            )
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="南昌过去7天逐小时温度与降水变化"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            legend_opts=opts.LegendOpts(pos_top="5%"),
            xaxis_opts=opts.AxisOpts(
                name="时间",
                name_gap=42,
                axislabel_opts=opts.LabelOpts(rotate=45, interval=11),
            ),
            yaxis_opts=opts.AxisOpts(
                name="降水量(mm)",
                axislabel_opts=opts.LabelOpts(formatter="{value} mm"),
            ),
            datazoom_opts=[
                opts.DataZoomOpts(type_="inside"),
                opts.DataZoomOpts(type_="slider", pos_bottom="7%", height=28),
            ],
        )
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    )
    bar.options["grid"] = {
        "left": "8%",
        "right": "8%",
        "top": "16%",
        "bottom": "24%",
    }

    line = (
        Line()
        .add_xaxis(x_axis)
        .add_yaxis(
            "温度(°C)",
            df["temperature_2m"].round(2).tolist(),
            yaxis_index=1,
            is_smooth=True,
            color="#E45756",
            symbol="circle",
            symbol_size=5,
            linestyle_opts=opts.LineStyleOpts(width=2.5),
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(is_show=False),
            markpoint_opts=opts.MarkPointOpts(
                data=[
                    opts.MarkPointItem(type_="max", name="最高温"),
                    opts.MarkPointItem(type_="min", name="最低温"),
                ]
            ),
        )
    )

    bar.overlap(line)
    return bar


def build_radar_chart(zscore_df: pd.DataFrame) -> Radar:
    max_abs_value = float(np.abs(zscore_df.values).max())
    radar_limit = round(max(max_abs_value + 0.4, 1.2), 1)
    indicators = [
        opts.RadarIndicatorItem(name=SUMMARY_LABELS[column], min_=-radar_limit, max_=radar_limit)
        for column in zscore_df.columns
    ]

    initial_city = zscore_df.index[0]
    chart = Radar(init_opts=opts.InitOpts(width="860px", height="540px", theme=ThemeType.LIGHT))
    chart.add_schema(
        schema=indicators,
        shape="circle",
        radius="72%",
        center=["45%", "54%"],
        splitline_opt=opts.SplitLineOpts(is_show=True),
        splitarea_opt=opts.SplitAreaOpts(
            is_show=True,
            areastyle_opts=opts.AreaStyleOpts(opacity=0.08),
        ),
        textstyle_opts=opts.TextStyleOpts(font_size=15),
    )
    chart.add(
        "五城市综合气象特征",
        build_radar_series_payload(zscore_df, initial_city),
        linestyle_opts=opts.LineStyleOpts(width=2),
        areastyle_opts=opts.AreaStyleOpts(opacity=0.08),
        tooltip_opts=opts.TooltipOpts(is_show=True),
    )
    chart.options["series"][0]["colorBy"] = "data"
    chart.options["color"] = [RADAR_CITY_COLORS[city] for city in zscore_df.index]
    chart.set_global_opts(
        title_opts=opts.TitleOpts(
            title="五城市标准化气象特征雷达图",
            subtitle="点击任一城市折线，可切换右侧热力图焦点",
        ),
        legend_opts=opts.LegendOpts(is_show=False),
    )
    return chart


def build_radar_series_payload(
    zscore_df: pd.DataFrame,
    selected_city: str,
) -> List[Dict[str, object]]:
    payload: List[Dict[str, object]] = []
    for city in zscore_df.index:
        is_selected = city == selected_city
        payload.append(
            {
                "name": city,
                "value": zscore_df.loc[city].round(2).tolist(),
                "lineStyle": {"width": 4.8 if is_selected else 2.0, "opacity": 1 if is_selected else 0.5},
                "areaStyle": {"opacity": 0.2 if is_selected else 0.05},
                "label": {
                    "show": is_selected,
                    "fontSize": 16,
                    "fontWeight": "bold",
                    "color": RADAR_CITY_COLORS[city],
                    "distance": 10,
                    "backgroundColor": "rgba(255,255,255,0.85)",
                    "padding": [2, 5],
                    "borderRadius": 4,
                },
                "symbolSize": 9 if is_selected else 6,
                "itemStyle": {"opacity": 1 if is_selected else 0.55},
                "emphasis": {
                    "lineStyle": {"width": 5.2},
                    "label": {
                        "show": True,
                        "fontSize": 16,
                        "fontWeight": "bold",
                        "distance": 10,
                        "backgroundColor": "rgba(255,255,255,0.9)",
                        "padding": [2, 5],
                        "borderRadius": 4,
                    },
                },
            }
        )
    return payload


def correlation_to_heatmap_data(corr_df: pd.DataFrame) -> List[List[float]]:
    data: List[List[float]] = []
    for y_index, row_name in enumerate(corr_df.index):
        for x_index, column_name in enumerate(corr_df.columns):
            data.append([x_index, y_index, round(float(corr_df.loc[row_name, column_name]), 2)])
    return data


def build_heatmap_chart(city_name: str, corr_df: pd.DataFrame) -> HeatMap:
    labels = [DAILY_METRIC_LABELS[column] for column in corr_df.columns]
    chart = (
        HeatMap(init_opts=opts.InitOpts(width="520px", height="380px", theme=ThemeType.LIGHT))
        .add_xaxis(labels)
        .add_yaxis(
            series_name="相关系数",
            yaxis_data=labels,
            value=correlation_to_heatmap_data(corr_df),
            label_opts=opts.LabelOpts(
                is_show=True,
                formatter=JsCode("function(params){return Number(params.value[2]).toFixed(2);}"),
            ),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="城市气象指标相关性热力图",
                subtitle=f"当前城市：{city_name}",
            ),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=0, font_size=11)),
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(font_size=11)),
            visualmap_opts=opts.VisualMapOpts(min_=-1, max_=1, pos_right="4%", item_height=210),
            tooltip_opts=opts.TooltipOpts(
                formatter=JsCode(
                    "function(params){return params.marker + params.name + '<br/>相关系数: ' + Number(params.value[2]).toFixed(2);}"
                )
            ),
        )
    )
    return chart


def extract_body_fragment(embed_html: str) -> str:
    match = re.search(r"<body[^>]*>(.*)</body>", embed_html, flags=re.S)
    if not match:
        raise ValueError("无法提取图表 HTML 片段。")
    return match.group(1).strip()


def build_part2_page(summary_df: pd.DataFrame, daily_data_by_city: Dict[str, pd.DataFrame]) -> None:
    zscore_df = summary_df.apply(z_score, axis=0).round(3)

    correlation_by_city: Dict[str, List[List[float]]] = {}
    radar_series_by_city: Dict[str, List[Dict[str, object]]] = {}
    initial_city = next(iter(daily_data_by_city))
    initial_corr_df: pd.DataFrame | None = None
    all_daily_rows: List[pd.DataFrame] = []

    for city_name, daily_df in daily_data_by_city.items():
        metric_df = daily_df[list(DAILY_METRIC_LABELS.keys())].copy()
        corr_df = metric_df.corr().fillna(0)
        correlation_by_city[city_name] = correlation_to_heatmap_data(corr_df)
        radar_series_by_city[city_name] = build_radar_series_payload(zscore_df, city_name)
        all_daily_rows.append(daily_df)
        if city_name == initial_city:
            initial_corr_df = corr_df

    if initial_corr_df is None:
        raise ValueError("未能生成初始热力图数据。")

    summary_output = summary_df.rename(columns=SUMMARY_LABELS)
    summary_output.to_csv(OUTPUT_DIR / "city_summary_metrics.csv", encoding="utf-8-sig")
    pd.concat(all_daily_rows, ignore_index=True).rename(columns=DAILY_METRIC_LABELS).to_csv(
        OUTPUT_DIR / "city_daily_metrics.csv",
        index=False,
        encoding="utf-8-sig",
    )

    radar = build_radar_chart(zscore_df)
    heatmap = build_heatmap_chart(initial_city, initial_corr_df)
    html_path = OUTPUT_DIR / "part2_radar_heatmap.html"
    radar_fragment = extract_body_fragment(radar.render_embed())
    heatmap_fragment = extract_body_fragment(heatmap.render_embed())
    radar_legend_html = "".join(
        [
            f'<div class="legend-item" data-city="{city}"><span class="legend-color" style="background:{RADAR_CITY_COLORS[city]};"></span><span>{city}</span></div>'
            for city in zscore_df.index
        ]
    )

    linkage_script = f"""
<script>
const heatmapDataByCity = {json.dumps(correlation_by_city, ensure_ascii=False)};
const radarSeriesByCity = {json.dumps(radar_series_by_city, ensure_ascii=False)};
const heatmapMetricNames = {json.dumps(list(DAILY_METRIC_LABELS.values()), ensure_ascii=False)};
const radarChart = chart_{radar.chart_id};
const heatmapChart = chart_{heatmap.chart_id};

function updateRadar(cityName) {{
    if (!radarSeriesByCity[cityName]) {{
        return;
    }}
    radarChart.setOption({{
        series: [{{
            data: radarSeriesByCity[cityName]
        }}]
    }});
    document.querySelectorAll('.legend-item').forEach(function (item) {{
        item.classList.toggle('active', item.getAttribute('data-city') === cityName);
    }});
}}

function updateHeatmap(cityName) {{
    if (!heatmapDataByCity[cityName]) {{
        return;
    }}
    heatmapChart.setOption({{
        title: {{
            text: "城市气象指标相关性热力图",
            subtext: "当前城市：" + cityName
        }},
        xAxis: {{
            data: heatmapMetricNames
        }},
        yAxis: {{
            data: heatmapMetricNames
        }},
        series: [{{
            name: cityName + " 指标相关性",
            data: heatmapDataByCity[cityName]
        }}]
    }});
}}

radarChart.on("click", function (params) {{
    const cityName = params.name || (params.data && params.data.name);
    updateRadar(cityName);
    updateHeatmap(cityName);
}});

updateRadar({json.dumps(initial_city, ensure_ascii=False)});
updateHeatmap({json.dumps(initial_city, ensure_ascii=False)});
</script>
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>实验六-气象特征对比与关联分析</title>
    <script type="text/javascript" src="https://assets.pyecharts.org/assets/v6/echarts.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 18px;
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            background: #f6f8fb;
        }}
        .dashboard {{
            max-width: 1380px;
            margin: 0 auto;
            display: flex;
            gap: 18px;
            align-items: flex-start;
        }}
        .panel {{
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(31, 45, 61, 0.08);
            padding: 10px 10px 6px;
        }}
        .panel-radar {{
            flex: 0 0 62%;
        }}
        .panel-heatmap {{
            flex: 0 0 38%;
        }}
        .radar-chart-wrap {{
            flex: 1 1 auto;
            min-width: 0;
        }}
        .chart-container {{
            margin: 0 auto;
        }}
        .radar-layout {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }}
        .radar-legend {{
            width: 120px;
            padding-right: 10px;
        }}
        .legend-title {{
            font-size: 14px;
            font-weight: 600;
            color: #334155;
            margin-bottom: 12px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 10px;
            border-radius: 10px;
            color: #475569;
            margin-bottom: 8px;
            background: #f8fafc;
            transition: all 0.2s ease;
        }}
        .legend-item.active {{
            background: #e8f0ff;
            color: #1f2937;
            font-weight: 600;
            transform: translateX(-2px);
        }}
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 999px;
            flex: 0 0 12px;
        }}
        @media (max-width: 1180px) {{
            .dashboard {{
                flex-direction: column;
            }}
            .panel-radar,
            .panel-heatmap {{
                flex: 1 1 auto;
                width: 100%;
            }}
            .radar-layout {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .radar-chart-wrap {{
                width: 100%;
            }}
            .radar-legend {{
                width: 100%;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
                gap: 8px;
            }}
            .legend-title {{
                grid-column: 1 / -1;
                margin-bottom: 0;
            }}
            .legend-item {{
                margin-bottom: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <section class="panel panel-radar">
            <div class="radar-layout">
                <div class="radar-chart-wrap">
                    {radar_fragment}
                </div>
                <aside class="radar-legend">
                    <div class="legend-title">城市颜色对应</div>
                    {radar_legend_html}
                </aside>
            </div>
        </section>
        <section class="panel panel-heatmap">
            {heatmap_fragment}
        </section>
    </div>
    {linkage_script}
</body>
</html>
"""
    html_path.write_text(html_content, encoding="utf-8")


def build_part3_geo_chart(realtime_df: pd.DataFrame) -> Geo:
    temperatures = realtime_df["temperature_2m"].tolist()
    geo_chart = Geo(init_opts=opts.InitOpts(width="1400px", height="720px", theme=ThemeType.LIGHT))
    geo_chart.add_schema(
        maptype="china",
        itemstyle_opts=opts.ItemStyleOpts(color="#F7F5EF", border_color="#A0A0A0"),
        emphasis_itemstyle_opts=opts.ItemStyleOpts(color="#E4D8B4"),
    )

    for row in realtime_df.itertuples(index=False):
        geo_chart.add_coordinate(row.city, row.longitude, row.latitude)

    geo_chart.add(
        "实时天气",
        [(row.city, row.temperature_2m) for row in realtime_df.itertuples(index=False)],
        type_=ChartType.SCATTER,
        symbol_size=JsCode("function (val) { return Math.max(22 + val[3] * 2.4, 28); }"),
        label_opts=opts.LabelOpts(
            is_show=True,
            font_size=13,
            formatter=JsCode(
                "function(params){return params.name + '\\n' + Number(params.value[2]).toFixed(1) + '°C' + '\\n风速 ' + Number(params.value[3]).toFixed(1) + ' km/h';}"
            ),
        ),
    )

    geo_chart.options["series"][0]["data"] = [
        {
            "name": row.city,
            "value": [row.longitude, row.latitude, row.temperature_2m, row.wind_speed_10m],
        }
        for row in realtime_df.itertuples(index=False)
    ]

    geo_chart.set_global_opts(
        title_opts=opts.TitleOpts(
            title="五城市实时天气地理分布图",
            subtitle="颜色表示温度，点大小表示风速",
        ),
        legend_opts=opts.LegendOpts(is_show=False),
        tooltip_opts=opts.TooltipOpts(
            formatter=JsCode(
                "function(params){return params.name + '<br/>温度：' + Number(params.value[2]).toFixed(1) + '°C' + '<br/>风速：' + Number(params.value[3]).toFixed(1) + ' km/h';}"
            )
        ),
        visualmap_opts=opts.VisualMapOpts(
            min_=float(min(temperatures)) - 1,
            max_=float(max(temperatures)) + 1,
            dimension=2,
            pos_left="3%",
            range_color=["#4C78A8", "#F2CF5B", "#E45756"],
        ),
    )
    return geo_chart


def build_part3_timeline(forecast_by_city: Dict[str, pd.DataFrame]) -> Timeline:
    timeline = Timeline(
        init_opts=opts.InitOpts(width="1400px", height="680px", theme=ThemeType.LIGHT)
    )
    timeline.add_schema(
        is_auto_play=False,
        is_loop_play=False,
        play_interval=1800,
        pos_left="8%",
        pos_right="8%",
        pos_bottom="4%",
        width="84%",
        height="55",
        label_opts=opts.LabelOpts(color="#333333"),
    )

    for city_name, forecast_df in forecast_by_city.items():
        temp_values = forecast_df["temperature_2m"].round(2).tolist()
        y_min = float(np.floor(min(temp_values) - 1))
        y_max = float(np.ceil(max(temp_values) + 1))
        line_chart = (
            Line()
            .add_xaxis(forecast_df["time"].dt.strftime("%m-%d %H:%M").tolist())
            .add_yaxis(
                "温度(°C)",
                temp_values,
                is_smooth=True,
                symbol="circle",
                symbol_size=7,
                color="#2E86AB",
                linestyle_opts=opts.LineStyleOpts(width=3),
            )
            .set_series_opts(
                label_opts=opts.LabelOpts(is_show=False),
                markpoint_opts=opts.MarkPointOpts(
                    data=[
                        opts.MarkPointItem(type_="max", name="最高温"),
                        opts.MarkPointItem(type_="min", name="最低温"),
                    ]
                ),
                markline_opts=opts.MarkLineOpts(
                    data=[opts.MarkLineItem(type_="average", name="平均温度")]
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=f"{city_name}未来24小时温度预测",
                    subtitle="图中虚线表示平均温度",
                ),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(
                    name="时间",
                    name_gap=34,
                    axislabel_opts=opts.LabelOpts(rotate=25, interval=2),
                ),
                yaxis_opts=opts.AxisOpts(
                    name="温度(°C)",
                    min_=y_min,
                    max_=y_max,
                    axislabel_opts=opts.LabelOpts(formatter="{value} °C"),
                ),
            )
        )
        line_chart.options["grid"] = {
            "left": "8%",
            "right": "8%",
            "top": "18%",
            "bottom": "28%",
        }
        timeline.add(line_chart, time_point=city_name)

    return timeline


def main() -> None:
    ensure_output_dir()

    nanchang_df = get_nanchang_past_7_days()
    summary_df, daily_data_by_city = get_city_august_2025_data()
    realtime_df, forecast_by_city = get_realtime_and_forecast_data()

    part1_chart = build_part1_chart(nanchang_df)
    part1_path = OUTPUT_DIR / "part1_nanchang_past7days.html"
    part1_chart.render(str(part1_path))
    localize_html_assets(part1_path)

    build_part2_page(summary_df, daily_data_by_city)
    localize_html_assets(OUTPUT_DIR / "part2_radar_heatmap.html")

    geo_chart = build_part3_geo_chart(realtime_df)
    geo_path = OUTPUT_DIR / "part3_geo_scatter.html"
    geo_chart.render(str(geo_path))
    localize_html_assets(geo_path)
    geo_chart.render(str(OUTPUT_DIR / "part3_geo_scatter_updated.html"))
    localize_html_assets(OUTPUT_DIR / "part3_geo_scatter_updated.html")

    timeline_chart = build_part3_timeline(forecast_by_city)
    timeline_path = OUTPUT_DIR / "part3_forecast_timeline.html"
    timeline_chart.render(str(timeline_path))
    localize_html_assets(timeline_path)

    generated_files = [
        "part1_nanchang_past7days.html",
        "part2_radar_heatmap.html",
        "part3_geo_scatter.html",
        "part3_geo_scatter_updated.html",
        "part3_forecast_timeline.html",
        "city_summary_metrics.csv",
        "city_daily_metrics.csv",
    ]
    print("已生成以下文件：")
    for file_name in generated_files:
        print(f"- {OUTPUT_DIR / file_name}")


if __name__ == "__main__":
    main()
