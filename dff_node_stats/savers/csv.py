"""
CSV
---------------------------
Provides the CSV version of the :py:class:`~dff_node_stats.savers.saver.Saver`. 
You don't need to interact with this class manually, as it will be automatically 
initialized when you construct a :py:class:`~dff_node_stats.savers.saver.Saver` with specific parameters.

"""
from typing import List, Optional, Union, Dict
import pathlib
import os

import pandas as pd


class CsvSaver:
    """
    Saves and reads the stats dataframe from a csv file.
    You don't need to interact with this class manually, as it will be automatically
    initialized when you construct :py:class:`~dff_node_stats.savers.saver.Saver` with specific parameters.

    Parameters
    ----------

    path: str
        | The construction path.
        | The part after :// should contain a path to the file that pandas will be able to recognize.

        >>> CsvSaver("csv://foo/bar.csv")
    table: str
        Does not affect the class. Added for constructor uniformity.
    """

    def __init__(self, path: str, table: str = "dff_stats") -> None:
        path = path.partition("://")[2]
        self.path = pathlib.Path(path)

    def save(
        self,
        dfs: List[pd.DataFrame],
        column_types: Optional[Dict[str, str]] = None,
        parse_dates: Union[List[str], bool] = False,
    ) -> None:

        if self.path.exists() and os.path.getsize(self.path) > 0:
            saved_df = self.load(column_types=column_types, parse_dates=parse_dates)
        else:
            saved_df = pd.DataFrame()
        pd.concat([saved_df] + dfs).to_csv(self.path, index=False)

    def load(
        self,
        column_types: Optional[Dict[str, str]] = None,
        parse_dates: Union[List[str], bool] = False,
    ) -> pd.DataFrame:
        if parse_dates and column_types:
            true_types = {k: v for k, v in column_types.items() if k in (column_types.keys() - set(parse_dates))}
        return pd.read_csv(
            self.path,
            usecols=column_types.keys(),
            dtype=true_types,
            parse_dates=parse_dates,
        )
