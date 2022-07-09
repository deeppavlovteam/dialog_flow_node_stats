"""
Widget
**********
| This module provides utilities for visualizing dff statistics.
| :py:class:`~dff_node_stats.widgets.widget.AbstractDasboard` is the protocol class that is implemented by concrete dashboards.
| :py:class:`~dff_node_stats.widgets.widget.FilterType` standardizes custom filters.
| :py:const:`~dff_node_stats.widgets.widget.default_plots` are the default plots for the dashboard.
| :py:const:`~dff_node_stats.widgets.widget.default_filters` is a list of default filters.

"""
from typing import Any, Callable, List, Optional, NamedTuple

import pandas as pd

from . import visualizers as vs

default_plots: List[vs.VisualizerType] = [
    vs.show_table,
    vs.show_duration_time,
    vs.show_transition_graph,
    vs.show_node_counters,
    vs.show_transition_counters,
    vs.show_transition_duration,
]


class FilterType(NamedTuple):
    """
    Instances of :py:class:`~dff_node_stats.widgets.widget.FilterType` can be passed to
    a dashboard on construction to add custom filters.

    Attributes:
        label: The label that will be displayed near the filter.

        colname: The name of the column to apply the rule to.

        comparison_func:  A boolean function that will be used to compare the entered values to column values. In most cases lambda x, y: x == y is sufficient.

        default: The default value that will be displayed in the filter.

    """

    label: str
    colname: str
    comparison_func: Callable[[Any, Any], bool]
    default: str = "None"


default_filters: List[FilterType] = [
    FilterType("Choose context_id", "context_id", lambda x, y: x == y, "None"),
]


class AbstractDashboard:
    """
    An abstract class that other dashboards inherit from.

    Parameters
    ----------

    df: pd.DataFrame
        The dataframe containing stats data to display.
    plots: Optional[List[Callable]]
        An optional list of user-defined visualizers. It will be used to add new plots.
    filters: Optional[List[FilterType]]
        An optional list of :py:class:`~dff_node_stats.widgets.widget.FilterType` instances that will be used
        to construct additional fiters.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        plots: Optional[List[vs.VisualizerType]] = None,
        filters: Optional[List[FilterType]] = None,
    ) -> None:
        self._filters: List[FilterType] = default_filters if filters is None else default_filters + filters
        self._plots: List[vs.VisualizerType] = default_plots if plots is None else default_plots + plots
        self._df_cache = df  # original df used to construct the widget
        self._df = df  # current state

    def plots(self):
        raise NotImplementedError

    @property
    def controls(self):
        raise NotImplementedError

    def __call__(self):
        raise NotImplementedError
