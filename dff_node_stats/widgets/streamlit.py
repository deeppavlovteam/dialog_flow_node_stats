"""
Streamlit
---------------------------
Provides the Streamlit version of the :py:class:`~dff_node_stats.widgets.widget.AbstractDashboard` . 

"""
from typing import List, Optional
from functools import partial

import pandas as pd
import streamlit as st

from . import visualizers as vs
from .widget import AbstractDashboard, FilterType


class StreamlitDashboard(AbstractDashboard):
    """
    | Streamlit-specific implementation of the :py:class:`~dff_node_stats.widgets.widget.AbstractDashboard` class.
    | Inherits the construction parameters.

    """

    def __init__(
        self,
        df: pd.DataFrame,
        plots: Optional[List[vs.VisualizerType]] = None,
        filters: Optional[List[FilterType]] = None,
    ) -> None:
        super().__init__(df, plots, filters)
        self._df: pd.DataFrame = self._slice(self._df_cache, *self.controls)

    @st.cache(allow_output_mutation=True)
    def _slice(self, df_origin: pd.DataFrame, *args):
        masks = []
        for _filter, dropdown in zip(self._filters, args):
            val = dropdown
            if val == _filter.default:
                masks += [pd.Series(([True] * df_origin.shape[0]), copy=False)]
            else:
                func_to_apply = partial(_filter.comparison_func, y=val)
                masks += [df_origin[_filter.colname].apply(func_to_apply)]
        mask = masks[0]
        for m in masks[1:]:
            mask = mask & m
        if mask.sum() == 0:
            return df_origin
        return df_origin.loc[mask]

    @property
    def controls(self):
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
            filters.append(
                st.sidebar.selectbox(
                    _filter.label,
                    options=([_filter.default] + self._df_cache[_filter.colname].unique().tolist()),
                )
            )
        return tuple(filters)

    def plots(self):
        df = self._df.copy()
        for plot_func in self._plots:
            plot = plot_func(df)
            st.plotly_chart(plot, use_container_width=True)

    def __call__(self):
        st.title("DialogFlow Framework Statistic Dashboard")
        self.plots()
