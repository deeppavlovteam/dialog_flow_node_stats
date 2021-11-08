# %%
from typing import Optional
import pathlib
import datetime


import pandas as pd
from pydantic import validate_arguments, BaseModel
from dff.core import Context, Actor
from dff.core.types import ActorStage


class Stats(BaseModel):
    csv_file: pathlib.Path
    start_time: Optional[datetime.datetime] = None
    dfs: list = []
    column_dtypes: dict = {
        "context_id": "str",
        "flow_label": "str",
        "node_label": "str",
        "history_id": "int64",
        "duration_time": "float64",
    }

    @validate_arguments
    def _update_handlers(self, actor: Actor, stage: ActorStage, handler) -> Actor:
        actor.handlers[stage] = actor.handlers.get(stage, []) + [handler]
        return actor

    def update_actor_handlers(self, actor: Actor, auto_save: bool = True, *args, **kwargs):
        self._update_handlers(actor, ActorStage.CONTEXT_INIT, self.get_start_time)
        self._update_handlers(actor, ActorStage.FINISH_TURN, self.collect_stats)
        if auto_save:
            self._update_handlers(actor, ActorStage.FINISH_TURN, self.save)

    @validate_arguments
    def get_start_time(self, ctx: Context, actor: Actor, *args, **kwargs):
        self.start_time = datetime.datetime.now()
        if ctx.last_label is None:
            self.add_df(ctx.id, -1, *actor.start_label[:2])

    def add_df(self, context_id, history_id, flow_label, node_label):
        self.dfs += [
            pd.DataFrame(
                {
                    "context_id": [str(context_id)],
                    "history_id": [history_id],
                    "start_time": [self.start_time],
                    "duration_time": [(datetime.datetime.now() - self.start_time).total_seconds()],
                    "flow_label": [flow_label],
                    "node_label": [node_label],
                },
            )
        ]

    @validate_arguments
    def collect_stats(self, ctx: Context, actor: Actor, *args, **kwargs):
        indexes = list(ctx.labels)
        current_index = indexes[-1] if indexes else -1
        self.add_df(
            ctx.id,
            current_index,
            *ctx.last_label[:2],
        )

    def save(self, *args, **kwargs):
        saved_df = (
            pd.read_csv(self.csv_file, dtype=self.column_dtypes, parse_dates=["start_time"])
            if self.csv_file.exists()
            else pd.DataFrame()
        )
        pd.concat([saved_df] + self.dfs).to_csv(self.csv_file, index=False)

        self.dfs.clear()

    @property
    def dataframe(self):
        return pd.read_csv(self.csv_file, dtype=self.column_dtypes, parse_dates=["start_time"])

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

    def preproc_df(self, df):
        for context_id in self.dataframe.context_id.unique():
            ctx_index = df.context_id == context_id
            df.loc[ctx_index, "node"] = df.loc[ctx_index, "flow_label"] + ":" + df.loc[ctx_index, "node_label"]
            df.loc[ctx_index, "edge"] = (
                df.loc[ctx_index, "node"].shift(periods=1).combine(df.loc[ctx_index, "node"], lambda *x: list(x))
            )
            flow_label = df.loc[ctx_index, "flow_label"]
            df.loc[ctx_index, "edge_type"] = flow_label.where(flow_label.shift(periods=1) == flow_label, "MIXED")
        return df

    def streamlit_run(self):
        import streamlit as st
        import graphviz
        import datetime

        @st.cache(allow_output_mutation=True)
        def read_data():
            df = pd.read_csv(self.csv_file, dtype=self.column_dtypes, parse_dates=["start_time"])
            df = self.preproc_df(df)
            return df

        df_origin = read_data()

        @st.cache()
        def get_datatimes():
            start_time = pd.to_datetime(df_origin.start_time.min()) - datetime.timedelta(days=1)
            end_time = pd.to_datetime(df_origin.start_time.max()) + datetime.timedelta(days=1)
            return start_time, end_time

        start_time_border, end_time_border = get_datatimes()

        def get_sidebar_chnges():
            start_date = pd.to_datetime(st.sidebar.date_input("Start date", start_time_border))
            end_date = pd.to_datetime(st.sidebar.date_input("End date", end_time_border))
            if start_date < end_date:
                st.sidebar.success("Start date: `%s`\n\nEnd date:`%s`" % (start_date, end_date))
            else:
                st.sidebar.error("Error: End date must fall after start date.")

            context_id = st.sidebar.selectbox(
                "Choose context_id",
                options=["all"] + df_origin.context_id.unique().tolist(),
            )
            return start_date, end_date, context_id

        start_date, end_date, context_id = get_sidebar_chnges()

        @st.cache()
        def slice_df_origin(start_date, end_date, context_id):
            return df_origin[
                (df_origin.start_time >= start_date)
                & (df_origin.start_time <= end_date)
                & ((df_origin.context_id == context_id) | (context_id == "all"))
            ]

        df = slice_df_origin(start_date, end_date, context_id)
        node_counter = df.node.value_counts()
        edge_counter = df.edge.value_counts()
        node2code = {key: f"n{index}" for index, key in enumerate(df.node.unique())}

        st.title("DialogFlow Framework Statistic Dashboard")
        col1, col2 = st.columns(2)
        col1.subheader("Data")
        col1.dataframe(df)
        col2.subheader("Timings")
        col2.dataframe(df.describe().duration_time)
        col2.write(f"Data shape {df.shape}")

        st.subheader("Graph of Transitions")
        graph = graphviz.Digraph()
        graph.attr(compound="true")
        flow_labels = df.flow_label.unique()
        for i, flow_label in enumerate(flow_labels):
            with graph.subgraph(name=f"cluster{i}") as sub_graph:
                sub_graph.attr(style="filled", color="lightgrey")
                sub_graph.attr(label=flow_label)

                sub_graph.node_attr.update(style="filled", color="white")

                for _, (history_id, node, node_label) in df.loc[
                    df.flow_label == flow_label, ("history_id", "node", "node_label")
                ].iterrows():
                    counter = node_counter[node]
                    label = f"{node_label} ({counter=})"
                    if history_id == -1:
                        sub_graph.node(node2code[node], label=label, shape="Mdiamond")
                    else:
                        sub_graph.node(node2code[node], label=label)

        for (in_node, out_node), counter in edge_counter.items():
            if isinstance(in_node, str):
                label = f"(probs={counter/node_counter[in_node]:.2f})"
                graph.edge(node2code[in_node], node2code[out_node], label=label)

        st.graphviz_chart(graph)

        st.subheader("Transition Trace")
        df_trace = df[["history_id", "flow_label", "node"]]
        df_trace.index = df_trace.history_id
        df_trace = df_trace.drop(columns=["history_id"])
        df_trace
        node_trace = {}
        for flow_label in df_trace.flow_label.unique():
            node_trace[flow_label] = df_trace.loc[df_trace.flow_label == flow_label, "node"]
        st.bar_chart(df_trace.loc[:, "node"])

        st.subheader("Node counters")
        node_counters = {}
        for flow_label in flow_labels:
            node_counters[flow_label] = df.loc[df.flow_label == flow_label, "node_label"].value_counts()
        st.bar_chart(node_counters)

        st.subheader("Transitions counters")
        edge_counters = {}
        for edge_type in df.edge_type.unique():
            edge_counters[edge_type] = df.loc[df.edge_type == edge_type, "edge"].astype("str").value_counts()
        st.bar_chart(edge_counters)

        st.subheader("Transitions duration [sec]")
        edge_time = df[["edge", "edge_type", "duration_time"]]
        edge_time = edge_time.astype({"edge": "str"})
        edge_time = edge_time.groupby(["edge", "edge_type"], as_index=False).mean()
        edge_time.index = edge_time.edge

        edge_duration = {}
        for edge_type in df.edge_type.unique():
            edge_duration[edge_type] = edge_time.loc[edge_time.edge_type == edge_type, "duration_time"]
        st.bar_chart(edge_duration)

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
