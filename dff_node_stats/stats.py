# %%

import pathlib

import pandas as pd
from pydantic import validate_arguments, BaseModel
from dff import Context


class Stats(BaseModel):
    csv_file: pathlib.Path

    @validate_arguments
    def save(self, ctx: Context, *args, **kwargs):
        if not self.csv_file.exists():
            pd.DataFrame({"history_id": [], "context_id": [], "flow_label": [], "node_label": []}).to_csv(
                self.csv_file,
                index=False,
            )
        df = pd.read_csv(self.csv_file)
        df.history_id = df.history_id.astype(int)
        indexes, flow_labels, node_labels = list(
            zip(
                *[
                    (
                        index,
                        flow_label,
                        node_label,
                    )
                    for index, (flow_label, node_label) in ctx.node_label_history.items()
                ]
            )
        )
        ctx_df = pd.DataFrame(
            {
                "history_id": indexes,
                "context_id": [str(ctx.id)] * len(indexes),
                "flow_label": flow_labels,
                "node_label": node_labels,
            },
        )
        history_ids = df.history_id[df.context_id == str(ctx.id)]
        ctx_df = ctx_df[~ctx_df.history_id.isin(history_ids)]
        pd.concat([df, ctx_df]).to_csv(self.csv_file, index=False)

    @property
    def dataframe(self):
        return pd.read_csv(self.csv_file)

    @property
    def transition_counts(self):
        df = self.dataframe.copy()
        df["node"] = df.apply(lambda row: f"{row.flow_label}:{row.node_label}", axis=1)
        df = df.drop(["flow_label", "node_label"], axis=1)
        # %%
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

        st.title("Node Analytics")
        st.dataframe(self.dataframe[["flow_label", "node_label"]])
        # st.subheader('Node labels')
        st.bar_chart(self.dataframe["node_label"].value_counts())
        st.bar_chart(self.dataframe["node_label"])
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
