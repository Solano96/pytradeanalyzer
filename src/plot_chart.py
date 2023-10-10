
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from screeninfo import get_monitors
from pandas import DataFrame
import pandas as pd

from src.backtesting_engine.type_dict_classes import DateValue

DARK_THEME = {
    'plot_bgcolor': '#333333',
    'paper_bgcolor': '#333333',
    'font_colot': '#f0f0f0',
    'gridcolor': '#636363',
    'line_color': '#c2c2c2',
    'hoverlabel_font_color': 'white',
    'increasing_fillcolor': '#6ECC62',
    'increasing_line_color': '#6ECC62',
    'decreasing_fillcolor': '#FF4848',
    'decreasing_line_color': '#FF4848',
    'bar_marker_color': '#52c8ff',
    'bar_marker_line_color': '#333333',
    'bar_marker_color_up': '#75ff93',
    'bar_marker_color_down': '#ff7575' 
}

LIGHT_THEME = {
    'plot_bgcolor': '#FFFFFF',
    'paper_bgcolor': '#FFFFFF',
    'font_colot': '#222222',
    'gridcolor': '#636363',
    'line_color': '#000000',
    'hoverlabel_font_color': 'white',
    'increasing_fillcolor': '#02ad44',
    'increasing_line_color': '#02ad44',
    'decreasing_fillcolor': '#f72a2c',
    'decreasing_line_color': '#f72a2c',
    'bar_marker_color': '#3176eb',
    'bar_marker_line_color': '#FFFFFF',
    'bar_marker_color_up': '#26d167',
    'bar_marker_color_down': '#ff4042'
}

def plot_candlestick(
    df: DataFrame,
    plot_type='candle',
    indicators: List[Dict[str, Any]] = [],
    operations: Dict[str, List] = {},
    capital_series: List[DateValue] = [],
    theme_name: str = 'DARK_THEME',
    data_name: str = '',
    width: Optional[int] = None,
    height: Optional[int] = None,
    show_fig: bool = True,
    save_fig: bool = False,
    path_fig: str = ''
) -> None:

    if not show_fig and not save_fig:
        return 

    row_candle_chart = 1
    row_volume = 2
    row_indicator = 3
    rows = 2
    row_width = [0.2, 0.7]
    has_hour = df.index[0].date() == df.index[1].date()

    theme = LIGHT_THEME if theme_name == 'LIGHT_THEME' else DARK_THEME

    for indicator in indicators:
        if not indicator['in_candle_chart']:
            rows+=1
            row_width = [0.2] + row_width

    if capital_series:
        row_capital_series = 1
        row_candle_chart += 1
        row_volume += 1
        row_indicator += 1
        rows += 1
        row_width = row_width + [0.2]
            
    fig = make_subplots(rows=rows, cols=1, vertical_spacing=0, shared_xaxes = True, row_width=row_width)

    if width is None or height is None:
        width = int(get_monitors()[0].width*0.98)
        height = int(get_monitors()[0].height*0.78)

    fig.update_layout(
        autosize=True,
        width=width,
        height=height,
        margin=dict(l=20, r=20, b=20, t=30, pad=4),
        title=f'\n<b>{data_name}</b>',
        font=dict(size=18)
    )
    fig.update_xaxes(ticks="outside", mirror=True, showline=True, linecolor=theme['line_color'])
    fig.update_yaxes(ticks="outside", mirror=True, showline=True, linecolor=theme['line_color'])

    if plot_type == 'candle':
        fig.append_trace(
            go.Candlestick(
                x=df.index, 
                open=df["Open"], 
                high=df["High"],
                low=df["Low"], 
                close=df["Close"], 
                name="OHLC", 
                showlegend=False,
                hoverlabel={'font_color': theme['hoverlabel_font_color']}
            ), 
            row=row_candle_chart, col=1
        )
        fig.data[0].increasing.fillcolor = theme['increasing_fillcolor']
        fig.data[0].increasing.line.color = theme['increasing_line_color']
        fig.data[0].decreasing.fillcolor = theme['decreasing_fillcolor']
        fig.data[0].decreasing.line.color = theme['decreasing_line_color']
    elif plot_type == 'line':
        fig.append_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"],
                marker_color=theme['line_color'],
                name='Close', 
                showlegend=False,
                hoverlabel={'font_color': theme['hoverlabel_font_color']}
            ), 
            row=row_candle_chart, col=1
        )
    else:
        raise Exception(f'ERROR: plot_type {plot_type} not valid.')

    df_color = pd.DataFrame()
    df_color['bar_color'] = df.apply(lambda row: theme['bar_marker_color_up'] if row['Close'] >= row['Open'] else theme['bar_marker_color_down'], axis=1)
    df_color['bar_edge_color'] = df.apply(lambda row: theme['increasing_line_color'] if row['Close'] >= row['Open'] else theme['decreasing_line_color'], axis=1)
    
    marker_distance = 0.03 if has_hour else 0.1

    if len(operations) > 0:
        fig.add_trace(
            go.Scatter(
                x=[operation['date'] for operation in operations['buy']],
                y=[operation['price']*(1-marker_distance) for operation in operations['buy']],
                customdata=[round(operation['price'], 4) for operation in operations['buy']],
                mode="markers",
                marker=dict(symbol='triangle-up', size = 12),
                marker_color=theme['bar_marker_color_up'],
                hovertemplate='[BUY] Date: %{x}<br>Price: %{customdata}<extra></extra>',
                hoverlabel={'font_color': theme['hoverlabel_font_color']}, 
                showlegend=False
            ), 
            row=row_candle_chart, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=[operation['date'] for operation in operations['sell']],
                y=[operation['price']*(1+marker_distance) for operation in operations['sell']],
                customdata=[round(operation['price'], 4) for operation in operations['sell']],
                mode="markers",
                marker=dict(symbol='triangle-down', size = 10),
                marker_color=theme['bar_marker_color_down'],
                hovertemplate='[SELL] Date: %{x}<br>Price: %{customdata}<extra></extra>',
                hoverlabel={'font_color': theme['hoverlabel_font_color']}, 
                showlegend=False
            ), 
            row=row_candle_chart, col=1
        )

    if len(indicators) > 0:
        i = row_indicator
        for indicator in indicators:
            row = row_candle_chart
            if not indicator['in_candle_chart']:
                row = i
                i+=1
            fig.append_trace(
                go.Scatter(
                    x=df.index,
                    y=df[indicator['name']],
                    name=indicator['name'], 
                    showlegend=False
                ), 
                row=row, col=1
            )

    fig.append_trace(
        go.Bar(
            x=df.index,
            y=df['Volume'],
            showlegend=False,
            marker_color=df_color['bar_color'],
            marker_line_color=df_color['bar_edge_color']
        ),
        row=row_volume,
        col=1
    )

    if capital_series:
        fig.append_trace(
            go.Scatter(
                x=[period['date'] for period in capital_series],
                y=[period['value'] for period in capital_series],
                marker_color=theme['bar_marker_color'],
                name='Capital', 
                showlegend=False
            ), 
            row=row_capital_series, col=1
        )

    '''
    rangebreaks = [dict(bounds=["sat", "mon"])]
    if has_hour:
        rangebreaks.append(dict(bounds=[17.5, 9], pattern="hour"))

    # Hide weekend gaps
    fig.update_xaxes(
        rangeslider_visible=False,
        rangebreaks=rangebreaks
    )
    '''
    
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_layout(plot_bgcolor=theme['plot_bgcolor'], paper_bgcolor=theme['paper_bgcolor'], font=dict(color=theme['font_colot'], size=10))

    for i in range(1, rows+1):
        fig['layout'][f'xaxis{i}'].update(showgrid=True, gridwidth=0.9, gridcolor=theme['gridcolor'])
        fig['layout'][f'yaxis{i}'].update(showgrid=True, gridwidth=0.9, gridcolor=theme['gridcolor'])

    if save_fig:
        fig.write_image(path_fig)
    
    if show_fig:
        fig.show()

    
