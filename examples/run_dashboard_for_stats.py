import dff_node_stats
from dff_node_stats import collectors as DSC
from dff_node_stats.widgets.streamlit import StreamlitDashboard

stats = dff_node_stats.Stats(
    saver=dff_node_stats.Saver("csv://examples/stats.csv"), collectors=[DSC.NodeLabelCollector()]
)

df = stats.dataframe
from dff_node_stats.widgets import FilterType

filt = FilterType("Choose flow", "flow_label", lambda x, y: x == y, default=None)
filt2 = FilterType("Choose turn", "history_id", lambda x, y: x == y, default=None)

StreamlitDashboard(df, filters=[filt, filt2])()
