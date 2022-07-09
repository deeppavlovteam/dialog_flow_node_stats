# Statistics collection extension for Dialog Flow Framework
dff_node_stats is package, that extends basic [dialog_flow_engine](https://github.com/deepmipt/dialog_flow_engine) by adding statistic collection **and** dashboard for visualization.

# Installation
Installation:
```bash
# install dialog flow framework
pip install dff
# Install dff_node_stats
pip install dff-node-stats #basic
# the default version is only capable of saving stats to a csv file.
# However, you can use any combination of the listed extras that give you much more
# freedom in saving and analyzing your data.
# pip install dff-node-stats[api] # extra for rest-api interface
# pip install dff-node-stats[streamlit] # extra for streamlit-based dashboard
# pip install dff-node-stats[jupyter] # extra for jupyter-based dashboard
# pip install dff-node-stats[pg] # extra for postgresql backend
# pip install dff-node-stats[clickhouse] # extra for clickhouse backend
# pip install dff-node-stats[all] # extra for all options
```
# Code snippets

Insert stats in your dff code:
```python
# import dependencies
from df_engine.core.plot import Plot
from df_engine.core.actor import Actor
from dff_node_stats import Stats, Saver
# ....
# Define a plot and an actor
plot = Plot(foo)
actor = Actor(bar, baz)

# Define file for stats saving
stats = Stats(
    saver=Saver("csv://examples/stats.csv")
)
# As an alternative, you can use a database. Currently, Clickhouse and Postgreql are supported
stats = Stats(
    saver=Saver("postgresql://user:password@localhost:5432/default")
)

# You can optionally add predefined Collectors to gather additional data
from dff_node_stats import collectors as DSC
from dff_node_stats import Stats, Saver

stats = Stats(
    saver=Saver("csv://examples/stats.csv"),
    collectors=[
        DSC.NodeLabelCollector()
    ]
)
# Or define your own Collector. 
# It should implement methods and properties, defined in the Collector protocol,
# which will make it compatible with multiple databackends.
# For more information see dff_node_stats.collectors


# Add handlers to actor
stats.update_actor_handlers(actor, auto_save=False)

# ....
# Handle user requests
# ....

```
Dashboard on stored data (\[streamlit\] extra required!):
```python
from dff_node_stats import Stats, Saver
from dff_node_stats.widgets.streamlit import StreamlitDashboard

stats = Stats(
    saver=Saver("csv://examples/stats.csv")
)

streamlit_dashboard = StreamlitDashboard(df)
streamlit_dashboard()
```

http-api on stored data (\[api\] extra required!om dff_node_stats import Stats, Saver
```python
from dff_node_stats.api import api_run
from dff_node_stats import Stats, Saver

stats = Stats(
    saver=Saver("csv://examples/stats.csv"),
    collectors=[
        DSC.NodeLabelCollector()
    ]
)

api_run(stats.dataframe)
```


# Run Examples:
```bash
# run dff dialog bot and collect stats
python examples/1.collect_stats.py
# or this one, they have differences only in a dialog scripts
python examples/1.collect_stats_vscode_demo.py

# run dashboard (make sure you installed the lib with [streamlit] extra)
streamlit run examples/2.run_dashboard_for_stats.py
# run api and follow to swagger by http://localhost:8000/docs
# note that [api] install option is required.
python examples/2.get_stats_by_api.py
# jupyter version of the dashboard can be launched by:
jupyter notebook examples/run_dashboard.ipynb
# you need to have [jupyter] option installed.
```