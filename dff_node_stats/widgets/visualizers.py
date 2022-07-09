"""
Visualizers
***********
| This module implements visualizer functions and visualization utilities.
| :py:const:`~dff_node_stats.widgets.visualizers.VisualizerType` is a prototype for both ready and custom visualizers.
| Function :py:func:`~dff_node_stats.widgets.visualizers.colorize` is used to produce a color on each turn of an iterator.

"""
import random
from typing import Callable, Iterable
from base64 import b64encode
from io import BytesIO

import graphviz
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.colors import qualitative
from plotly.basedatatypes import BaseFigure

from dff_node_stats.utils import requires_transform, transform_once, requires_columns


VisualizerType = Callable[[pd.DataFrame], BaseFigure]
"""
| The prototype for visualizer functions: 
| They are required to take a pandas dataframe and return a plotly graph.
| It makes functions of this kind compatible with both Jupyter and Streamlit.

As long as you follow this signature, any visualizer you define on your own
should be successfully visualized.

"""


def generate_random_colors():
    """
    | Retrieves colours from the standard Plotly palette.
    | Generates random colors on exhaustion.

    """
    reserve = []
    for element in qualitative.Plotly:
        yield element
        reserve.append("#{:06x}".format(random.randint(0, 0xFFFFFF)).upper())
    while reserve:
        for element in reserve:
            yield element


def colorize(target: Iterable):
    """
    Produces a random color each iteration when paired with an iterator

    Example::

        for color, x in colorize(y)

    Parameters
    ----------

    target: Interable
        The object to iterate over.

    """
    return zip(generate_random_colors(), target)


def show_table(df: pd.DataFrame) -> BaseFigure:
    """
    Displays the dataframe.

    """
    fig = go.Figure(
        data=go.Table(
            header=dict(values=list(df.columns), align="left"),
            cells=dict(values=[df[col] for col in df.columns], align="left"),
        )
    )
    fig.update_layout(title="Data")
    return fig


@requires_columns(["duration_time"])
def show_duration_time(df: pd.DataFrame) -> BaseFigure:
    """
    Displays the node timings.

    """
    dt = df.describe().duration_time
    fig = go.Figure(
        data=go.Table(
            header=dict(values=list(dt.keys()), align="left"), cells=dict(values=list(dt.values), align="left")
        )
    )
    fig.update_layout(title="Timings")
    return fig


@requires_columns(["flow_label", "node_label"])
def show_node_counters(df: pd.DataFrame) -> BaseFigure:
    """
    Displays the node counters.

    """
    fig = go.Figure().update_layout(title="Node counters")
    for color, flow_label in colorize(df["flow_label"].unique()):
        subset = df.loc[df.flow_label == flow_label, "node_label"].value_counts()
        fig.add_trace(go.Bar(x=subset.keys(), y=subset.values, name=flow_label, marker_color=color))
    return fig


@requires_columns(["flow_label", "node_label"])
@transform_once
def get_nodes_and_edges(df: pd.DataFrame):
    """
    Transform function that adds info about nodes and edges to the dataframe

    """
    for context_id in df.context_id.unique():
        ctx_index = df.context_id == context_id
        df.loc[ctx_index, "node"] = df.loc[ctx_index, "flow_label"] + ":" + df.loc[ctx_index, "node_label"]
        df.loc[ctx_index, "edge"] = (
            df.loc[ctx_index, "node"].shift(periods=1).combine(df.loc[ctx_index, "node"], lambda *x: list(x))
        )
        flow_label = df.loc[ctx_index, "flow_label"]
        df.loc[ctx_index, "edge_type"] = flow_label.where(flow_label.shift(periods=1) == flow_label, "MIXED")
    return df


@requires_transform(get_nodes_and_edges)
def show_transition_trace(df: pd.DataFrame) -> BaseFigure:
    """
    Displays information about node traversal in the form of a heatmap.

    """
    df_trace = df[["history_id", "flow_label", "node"]]
    df_trace = df_trace.drop(columns=["flow_label"])
    fig = px.density_heatmap(df_trace, x="history_id", y="node", color_continuous_scale="YlGnBu")
    fig.update_layout(title="Transition Trace")
    return fig


@requires_transform(get_nodes_and_edges)
def show_transition_graph(df: pd.DataFrame) -> BaseFigure:
    """
    Displays the graph of node traversal.

    """
    node_counter = df.node.value_counts()
    edge_counter = df.edge.value_counts()
    node2code = {key: f"n{index}" for index, key in enumerate(df.node.unique())}

    graph = graphviz.Digraph()
    graph.attr(compound="true")

    for color, (i, flow_label) in colorize(enumerate(df["flow_label"].unique())):
        with graph.subgraph(name=f"cluster{i}") as sub_graph:
            sub_graph.attr(style="filled", color=color.lower())
            sub_graph.attr(label=flow_label)

            sub_graph.node_attr.update(style="filled", color="white")

            for _, (history_id, node, node_label) in df.loc[
                df.flow_label == flow_label, ("history_id", "node", "node_label")
            ].iterrows():
                counter = node_counter[node]
                label = f"{node_label} ({counter=})"
                if history_id == -1:
                    sub_graph.node(node2code[node], label=label, shape="Mdiamond")
                else:
                    sub_graph.node(node2code[node], label=label)

    for (in_node, out_node), counter in edge_counter.items():
        if isinstance(in_node, str):
            label = f"(probs={counter/node_counter[in_node]:.2f})"
            graph.edge(node2code[in_node], node2code[out_node], label=label)

    _bytes = graph.pipe(format="png")
    prefix = "data:image/png;base64,"
    with BytesIO(_bytes) as stream:
        base64 = prefix + b64encode(stream.getvalue()).decode("utf-8")
    fig = go.Figure(go.Image(source=base64))
    fig.update_layout(title="Graph of Transitions")
    fig.update_xaxes(showticklabels=False).update_yaxes(showticklabels=False)
    return fig


@requires_transform(get_nodes_and_edges)
def show_transition_counters(df: pd.DataFrame) -> BaseFigure:
    """
    Displays the counts of node transitions.

    """
    fig = go.Figure().update_layout(title="Transitions counters")

    for color, edge_type in colorize(df["edge_type"].unique()):

        subset = df.loc[df.edge_type == edge_type, "edge"].astype("str").value_counts()

        fig.add_trace(go.Bar(x=subset.keys(), y=subset.values, name=edge_type, marker_color=color))
    return fig


@requires_transform(get_nodes_and_edges)
def show_transition_duration(df: pd.DataFrame) -> BaseFigure:
    """
    Displays the duration of node transitions.

    """
    fig = go.Figure().update_layout(title="Transitions duration [sec]")
    edge_time = df[["edge", "edge_type", "duration_time"]]
    edge_time = edge_time.astype({"edge": "str"})
    edge_time = edge_time.groupby(["edge", "edge_type"], as_index=False).mean()
    edge_time.index = edge_time.edge

    for color, edge_type in colorize(df["edge_type"].unique()):

        subset = edge_time.loc[edge_time["edge_type"] == edge_type, "duration_time"]

        fig.add_trace(
            go.Bar(
                x=subset.keys(),
                y=subset.values,
                name=edge_type,
                marker_color=color,
            )
        )
    return fig
