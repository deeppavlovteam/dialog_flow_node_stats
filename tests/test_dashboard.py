import pytest
import sys

try:
    import streamlit
    import ipywidgets
except ImportError:
    pass

from dff_node_stats.widgets.jupyter import WidgetDashboard
from dff_node_stats.widgets.streamlit import StreamlitDashboard
from dff_node_stats.widgets.widget import AbstractDashboard


if "ipywidgets" in sys.modules:

    @pytest.fixture(scope="session")
    def testing_jwidget(testing_dataframe):
        yield WidgetDashboard(testing_dataframe)

    def test_plots_jupyter(testing_jwidget):
        assert len(testing_jwidget.children) == 0
        testing_jwidget.__call__()
        assert len(testing_jwidget.children) == 2
        plots = testing_jwidget.children[1]
        assert isinstance(plots, ipywidgets.VBox)
        assert len(plots.children) == 6

    def test_controls_jupyter(testing_jwidget):
        testing_jwidget: WidgetDashboard
        assert isinstance(testing_jwidget.controls, ipywidgets.VBox)
        assert len(testing_jwidget.controls.children) == 1
        default_filter = testing_jwidget.controls.children[0]
        assert isinstance(default_filter, ipywidgets.Dropdown)
