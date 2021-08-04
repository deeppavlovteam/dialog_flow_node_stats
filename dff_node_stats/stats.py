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

    def streamlit_run(self):
        import streamlit as st

        st.title("Node Analytics")
        st.dataframe(self.dataframe[["flow_label", "node_label"]])
        # st.subheader('Node labels')
        st.bar_chart(self.dataframe["node_label"].value_counts())
        st.bar_chart(self.dataframe["node_label"])
        # st.dataframe(self.dataframe)
