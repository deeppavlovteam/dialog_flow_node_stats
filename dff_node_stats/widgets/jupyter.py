"""
Jupyter
---------------------------
Provides the Jupyter version of the :py:class:`~dff_node_stats.widgets.widget.AbstractDashboard` . 

"""
from typing import List, Optional
from functools import partial

import plotly.graph_objects as go
import pandas as pd
from ipywidgets import widgets

from . import visualizers as vs
from .widget import AbstractDashboard, FilterType


class WidgetDashboard(AbstractDashboard, widgets.VBox):
    """
    | Jupyter-specific implementation of the :py:class:`~dff_node_stats.widgets.widget.AbstractDashboard` class.
    | Inherits the construction parameters.

    """

    def __init__(
        self,
        df: pd.DataFrame,
        plots: Optional[List[vs.VisualizerType]] = None,
        filters: Optional[List[FilterType]] = None,
    ) -> None:
        widgets.VBox.__init__(self)
        AbstractDashboard.__init__(self, df, plots, filters)
        self._controls = self._construct_controls()

    @property
    def controls(self):
        return self._controls

    def _slice(self):
        masks = []
        for _filter, dropdown in zip(self._filters, self.controls.children):
            val = dropdown.value
            if val == _filter.default:
                masks += [pd.Series(([True] * self._df_cache.shape[0]), copy=False)]
            else:
                func_to_apply = partial(_filter.comparison_func, y=val)
                masks += [self._df_cache[_filter.colname].apply(func_to_apply)]
        mask = masks[0]
        for m in masks[1:]:
            mask = mask & m
        if mask.sum() == 0:
            return
        self._df = self._df_cache.loc[mask]

    def _construct_controls(self):
        def handleChange(change):
            self._slice()
            self.children = [self.controls, self.plots()]

        box = widgets.VBox()
        filters = []
        for _filter in self._filters:
            if _filter.colname not in self._df_cache.columns:
                raise KeyError(
                    """
                    Column {} for filter {}
                    not found in the dataframe
                    """.format(
                        _filter.colname, _filter.label
                    )
                )
            options = [(_filter.default, _filter.default)] + [(i, i) for i in self._df_cache[_filter.colname].unique()]
            dropdown = widgets.Dropdown(value=_filter.default, options=options, description=_filter.colname)
            dropdown.observe(handleChange, "value")
            filters += [dropdown]
        box.children = filters
        return box

    def plots(self):
        box = widgets.VBox()
        plot_list = []
        df = self._df.copy()
        for plot_func in self._plots:
            plot = plot_func(df)
            plot_list += [go.FigureWidget(data=plot)]
        box.children = plot_list
        return box

    def __call__(self):
        self.children = [self.controls, self.plots()]
        return self
