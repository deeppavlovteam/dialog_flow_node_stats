# Statistics collection extension for Dialog Flow Framework
dff_node_stats is package, that extends basic [dff](https://github.com/deepmipt/dialog_flow_framework) by adding statistic collection **and** dashboard for visualization.

# Installation
Installation:
```bash
# install dialog flow framework
pip install dff
# Install dff_node_stats
pip install dff-node-stats #basic
# pip install dff-node-stats[api] # version with rest-api, that provides access to stats by http requests
# pip install dff-node-stats[dashboard] # version with dashboard, that provides access to stats by web-UI
# pip install dff-node-stats[all] # version with both
```
# Code snippets

Insert stats in your dff code:
```python
# import
import dff_node_stats
# ....
# Define a plot
# Define an actor
# ....

# Define file for stats saving
stats = dff_node_stats.Stats(csv_file=STATS_FILE_PATH)
# Add handlers to actor
stats.update_actor_handlers(actor, auto_save=False)

# ....
# Handle user requests
# ....

```
Dashboard on stored data:
```python
import dff_node_stats

stats = dff_node_stats.Stats(csv_file=STATS_FILE_PATH)

stats.streamlit_run()
```

http-api on stored data:
```python
import dff_node_stats

stats = dff_node_stats.Stats(csv_file=STATS_FILE_PATH)

stats.api_run()
```


# Run Examples:
```bash
# install addition reqs
pip install tqdm
# run dff dialog bot and collect stats
python examples/1.collect_stats.py
# or this one, they have differences only in a dialog scripts
python examples/1.collect_stats_vscode_demo.py
# run dashboard and go to http://localhost:8501 to get it
streamlit run examples/2.run_dashboard_for_stats.py
# and run api and follow to swagger by http://localhost:8000/docs
python examples/2.get_stats_by_api.py
```