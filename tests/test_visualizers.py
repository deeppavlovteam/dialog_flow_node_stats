import pytest
import sys

try:
    from plotly.basedatatypes import BaseFigure
except ImportError:
    pass
from dff_node_stats.widgets import visualizers as vs
from dff_node_stats.utils import DffStatsException
import pandas as pd


def test_colors():
    for color, num in vs.colorize(range(100)):
        assert color


def test_error_raising():
    with pytest.raises(DffStatsException) as error:
        df = pd.DataFrame(columns=["foo", "bar"])
        fig = vs.show_duration_time(df)
    assert "Required columns missing" in str(error.value)


@pytest.mark.skipif("plotly" not in sys.modules, reason="plotly not installed")
@pytest.mark.parametrize(
    "plottype",
    [
        (vs.show_table),
        (vs.show_duration_time),
        (vs.show_transition_graph),
        (vs.show_transition_trace),
        (vs.show_transition_duration),
        (vs.show_transition_counters),
    ],
)
def test_plots(testing_dataframe, plottype):
    fig = plottype(testing_dataframe)
    assert isinstance(fig, BaseFigure)
