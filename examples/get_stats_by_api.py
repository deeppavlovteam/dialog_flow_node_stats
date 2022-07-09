import dff_node_stats
from dff_node_stats import collectors as DSC
from dff_node_stats.api import api_run

stats = dff_node_stats.Stats(
    saver=dff_node_stats.Saver("csv://examples/stats.csv"), collectors=[DSC.NodeLabelCollector()]
)

df = stats.dataframe

api_run(df, port=8000)
