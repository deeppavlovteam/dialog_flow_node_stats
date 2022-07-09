"""
API
*********
| :py:const:`RouteType <dff_node_stats.api.RouteType>` defines the prototype
| of a routing function. Any functions that add custom endpoints to the API
| should have this signature.

"""
from typing import Callable, Dict, Optional

from fastapi import FastAPI
import pandas as pd
import uvicorn

from dff_node_stats.utils import requires_transform, requires_columns, transform_once

RouteType = Callable[[FastAPI, Optional[pd.DataFrame]], FastAPI]
"""
| The prototype for any user-defined routing function.
| It should get a FastAPI object by reference, add the routes and then pass it back.

"""


def add_default_routes(app: FastAPI, df: pd.DataFrame) -> FastAPI:
    """
    | Add a standard set of routes to the FastAPI object, using the provided dataframe

    Parameters
    ----------

    api: :py:class:`~fastapi.FastAPI`
        The FastAPI object to which the endpoints should be atached.
    df: :py:class:`~pandas.DataFrame`
        The dataframe to retrieve data from.
    """

    @requires_columns(["flow_label", "node_label"])
    def transitions(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["node"] = df.apply(lambda row: f"{row.flow_label}:{row.node_label}", axis=1)
        df = df.drop(["flow_label", "node_label"], axis=1)
        df = df.sort_values(["context_id"], kind="stable")
        df["next_node"] = df.node.shift()
        df = df[df.history_id != 0]
        transitions = df.apply(lambda row: f"{row.node}->{row.next_node}", axis=1)
        return transitions.value_counts()

    @requires_transform(transitions)
    def transition_counts(df) -> Dict[str, int]:
        return {k: int(v) for k, v in dict(df).items()}

    @app.get("/api/v1/stats/transition-counts", response_model=Dict[str, int])
    async def get_transition_counts():
        return transition_counts(df)

    @requires_transform(transitions)
    def transition_probs(df) -> Dict[str, float]:
        tc = {k: int(v) for k, v in dict(df).items()}
        return {k: v / sum(tc.values(), 0) for k, v in tc.items()}

    @app.get("/api/v1/stats/transition-probs", response_model=Dict[str, float])
    async def get_transition_probs():
        return transition_probs(df)

    return app


def api_run(df: pd.DataFrame, routes: Optional[RouteType] = None, port: int = 8000) -> None:
    """
    | Run a FastAPI server with a user-provided dataframe

    Parameters
    ----------

    df: :py:class:`~pandas.DataFrame`
        The dataframe to retrieve data from.
    routes: :py:const:`RouteType <dff_node_stats.api.RouteType>`
        Optional function that attaches the user-defined endpoints to the API,
        overriding the default ones.
    port: int
        The port the API will listen to.
    """
    app = FastAPI()
    app = add_default_routes(app, df) if not routes else routes(app, df)
    uvicorn.run(app, host="0.0.0.0", port=port)
