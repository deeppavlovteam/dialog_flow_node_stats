# Getting started

Installation:
```bash
# install dialog flow framework
pip install -e ../dialog_flow_framework
# basics
pip install -e .
# run for dashboard mode:
pip install -r requirements_dashboard.txt
# run for api mode:
pip install -r requirements_api.txt
# and etc.:
pip install tqdm
```

Examples:
```bash
# run dff dialog bot and collect stats
python examples/1.collect_stats.py
# or this one, they have differences only in a dialog scripts
python examples/1.collect_stats_vscode_demo.py
# run dashboard and go to http://localhost:8501 to get it
streamlit run examples/2.run_dashboard_for_stats.py
# and run api and follow to swagger by http://localhost:8000/docs
python examples/2.get_stats_by_api.py
```