"""Reusable Plotly chart builders and rendering helpers."""

from textwrap import fill

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

COLORS = ["#174A7E", "#6E9FC5", "#4E7C59", "#D69A3A", "#8B9AA8", "#A74F4F"]


def _style(figure: go.Figure, title: str, x_title: str, y_title: str) -> go.Figure:
    wrapped_title = fill(title, width=36).replace("\n", "<br>")
    has_legend = any(trace.showlegend for trace in figure.data)
    figure.update_layout(
        title={
            "text": wrapped_title,
            "x": 0,
            "xanchor": "left",
            "y": 0.98,
            "yanchor": "top",
            "font": {"size": 16},
        },
        font={"family": "sans-serif", "color": "#233344", "size": 13},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        autosize=True,
        height=430,
        margin={"l": 56, "r": 24, "t": 92, "b": 100 if has_legend else 64},
        legend={
            "orientation": "h",
            "y": -0.3,
            "x": 0,
            "xanchor": "left",
            "yanchor": "top",
            "font": {"size": 11},
        },
        hoverlabel={"bgcolor": "#FFFFFF", "font_color": "#233344"},
    )
    figure.update_xaxes(
        title={"text": x_title, "standoff": 12},
        showgrid=False,
        linecolor="#DCE4EB",
        automargin=True,
        tickfont={"size": 11},
    )
    figure.update_yaxes(
        title={"text": y_title, "standoff": 12},
        gridcolor="#E8EDF2",
        zeroline=False,
        automargin=True,
        tickfont={"size": 11},
    )
    return figure


def line_chart(
    dataframe: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    x_title: str,
    y_title: str,
    color: str = COLORS[0],
    markers: bool = True,
) -> go.Figure:
    figure = px.line(dataframe, x=x, y=y, markers=markers, color_discrete_sequence=[color])
    return _style(figure, title, x_title, y_title)


def bar_chart(
    dataframe: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    x_title: str,
    y_title: str,
    color: str = COLORS[0],
    horizontal: bool = False,
) -> go.Figure:
    if horizontal:
        figure = px.bar(
            dataframe,
            x=y,
            y=x,
            orientation="h",
            color_discrete_sequence=[color],
        )
        figure.update_layout(yaxis={"categoryorder": "total ascending"})
    else:
        figure = px.bar(dataframe, x=x, y=y, color_discrete_sequence=[color])
    return _style(figure, title, x_title, y_title)


def stacked_bar_chart(
    dataframe: pd.DataFrame,
    *,
    x: str,
    y: list[str],
    title: str,
    x_title: str,
    y_title: str,
) -> go.Figure:
    long_frame = dataframe.melt(
        id_vars=[x], value_vars=y, var_name="Admission Status", value_name="Patients"
    )
    figure = px.bar(
        long_frame,
        x=x,
        y="Patients",
        color="Admission Status",
        barmode="stack",
        color_discrete_sequence=COLORS[:2],
    )
    return _style(figure, title, x_title, y_title)


def donut_chart(
    dataframe: pd.DataFrame,
    *,
    names: str,
    values: str,
    title: str,
) -> go.Figure:
    figure = px.pie(
        dataframe,
        names=names,
        values=values,
        hole=0.62,
        color_discrete_sequence=COLORS,
    )
    figure.update_traces(textposition="inside", textinfo="percent")
    return _style(figure, title, "", "")


def render_chart(figure: go.Figure, key: str) -> None:
    st.plotly_chart(
        figure,
        key=key,
        width="stretch",
        config={"displayModeBar": False, "responsive": True},
    )