# %%
from typing import Optional
import pathlib
import datetime


import pandas as pd
from pydantic import validate_arguments, BaseModel
from dff import Context, Actor


class Stats(BaseModel):
    csv_file: pathlib.Path
    start_time: Optional[datetime.datetime] = None
    dfs: list = []

    @validate_arguments
    def update_actor(self, actor: Actor, auto_save: bool = True, *args, **kwargs):

        actor.pre_handlers += [self.get_start_time]
        actor.post_handlers += [self.collect_stats]
        if auto_save:
            actor.post_handlers += [self.save]

    @validate_arguments
    def get_start_time(self, ctx: Context, actor: Actor, *args, **kwargs):
        self.start_time = datetime.datetime.now()

    @validate_arguments
    def collect_stats(self, ctx: Context, actor: Actor, *args, **kwargs):
        history = [(-1, actor.fallback_node_label[:2])] + list(ctx.node_label_history.items())
        indexes, flow_labels, node_labels = list(zip(*[(index, flow, node) for index, (flow, node) in history]))
        self.dfs += [
            pd.DataFrame(
                {
                    "history_id": indexes,
                    "context_id": str(ctx.id),
                    "flow_label": flow_labels,
                    "node_label": node_labels,
                    "start_time": self.start_time,
                    "duration_time": datetime.datetime.now() - self.start_time,
                },
            )
        ]

    def save(self, *args, **kwargs):
        saved_df = (
            pd.read_csv(self.csv_file)
            if self.csv_file.exists()
            else pd.DataFrame(
                {
                    "history_id": [],
                    "context_id": [],
                }
            )
        )
        saved_df.history_id = saved_df.history_id.astype(int)
        dfs_history_ids = [saved_df.history_id[saved_df.context_id.isin(df.context_id)] for df in self.dfs]
        dfs = [df[~df.history_id.isin(history_ids)] for history_ids, df in zip(dfs_history_ids, self.dfs)]
        pd.concat([saved_df] + dfs).to_csv(self.csv_file, index=False)
        self.dfs.clear()

    @property
    def dataframe(self):
        return pd.read_csv(self.csv_file)

    @property
    def transition_counts(self):
        df = self.dataframe.copy()
        df["node"] = df.apply(lambda row: f"{row.flow_label}:{row.node_label}", axis=1)
        df = df.drop(["flow_label", "node_label"], axis=1)
        df = df.sort_values(["context_id"], kind="stable")
        df["next_node"] = df.node.shift()
        df = df[df.history_id != 0]
        transitions = df.apply(lambda row: f"{row.node}->{row.next_node}", axis=1)
        return {k: int(v) for k, v in dict(transitions.value_counts()).items()}

    @property
    def transition_probs(self):
        tc = self.transition_counts
        total = sum(tc.values(), 0)
        return {k: v / total for k, v in tc.items()}

    def streamlit_run(self):
        import streamlit as st
        import graphviz

        st.title("Node Analytics")
        graph = graphviz.Digraph()

        with graph.subgraph(name="cluster_0") as sub_graph:
            sub_graph.attr(style="filled", color="lightgrey")
            sub_graph.node_attr.update(style="filled", color="white")
            sub_graph.edges([("a0", "a1"), ("a1", "a2"), ("a2", "a3")])
            sub_graph.node("start1")
            sub_graph.edge("run", "intr")
            sub_graph.attr(label="process #1")

        graph.edge("start", "a0")
        graph.edge("start", "b0")

        graph.node("start", shape="Mdiamond")
        graph.node("end", shape="Msquare")

        st.graphviz_chart(graph)

        st.dataframe(self.dataframe[["flow_label", "node_label"]])
        # st.subheader('Node labels')
        st.bar_chart(self.dataframe["node_label"].value_counts())
        st.bar_chart(self.dataframe[["node_label"]])
        df = self.dataframe
        df["node_label1"] = df["node_label"]
        st.vega_lite_chart(
            df[["node_label", "node_label1"]],
            {
                "mark": {"type": "circle", "tooltip": True},
                "encoding": {
                    "x": {"field": "a", "type": "quantitative"},
                    "y": {"field": "b", "type": "quantitative"},
                    "size": {"field": "c", "type": "quantitative"},
                    "color": {"field": "c", "type": "quantitative"},
                },
            },
        )
        # st.dataframe(self.dataframe)

    def api_run(self, port=8000):
        import uvicorn
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/api/v1/stats/transition-counts", response_model=dict[str, int])
        async def get_transition_counts():
            return self.transition_counts

        @app.get("/api/v1/stats/transition-probs", response_model=dict[str, float])
        async def get_transition_probs():
            return self.transition_probs

        uvicorn.run(app, host="0.0.0.0", port=port)

        # st.title("Node Analytics")
        # st.dataframe(self.dataframe[["flow_label", "node_label"]])
        # # st.subheader('Node labels')
        # st.bar_chart(self.dataframe["node_label"].value_counts())
        # st.bar_chart(self.dataframe["node_label"])
        # # st.dataframe(self.dataframe)
