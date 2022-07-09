"""
Postgresql
---------------------------
Provides the Postgresql version of the :py:class:`~dff_node_stats.savers.saver.Saver`. 
You don't need to interact with this class manually, as it will be automatically 
imported and initialized when you construct :py:class:`~dff_node_stats.savers.saver.Saver` with specific parameters.

"""
from typing import List, Optional, Union, Dict
from numpy import sort

import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.schema import MetaData, Table


class PostgresSaver:
    """
    Saves and reads the stats dataframe from a csv file.
    You don't need to interact with this class manually, as it will be automatically
    initialized when you construct :py:class:`~dff_node_stats.savers.saver.Saver` with specific parameters.

    Parameters
    ----------

    path: str
        | The construction path.
        | It should match the sqlalchemy :py:class:`~sqlalchemy.engine.Engine` initialization string.

        >>> PostgresSaver("postgresql://user:password@localhost:5432/default")
    table: str
        Sets the name of the db table to use. Defaults to "dff_stats".
    """

    def __init__(self, path: str, table: str = "dff_stats") -> None:
        self.path: str = path
        self.schema: str = self.path[self.path.rfind("/") + 1 :]
        self.table = table
        self.engine = create_engine(self.path)
        self.engine.dialect._psycopg2_extensions().register_adapter(dict, self.engine.dialect._psycopg2_extras().Json)

    def save(
        self,
        dfs: List[pd.DataFrame],
        column_types: Optional[Dict[str, str]] = None,
        parse_dates: Union[List[str], bool] = False,
    ) -> None:

        df = pd.concat(dfs)

        if not inspect(self.engine).has_table(self.table):
            df.to_sql(name=self.table, index=False, con=self.engine, if_exists="append")

        metadata = MetaData()
        ExistingModel = Table(self.table, metadata, autoload_with=self.engine)
        existing_columns = set(ExistingModel.columns)

        if bool(column_types.keys() ^ existing_columns):  # recreate table if the schema was altered
            dates_to_parse = list(set(parse_dates) & existing_columns)  # make sure we do not parse non-existent cols
            existing_df = self.load(parse_dates=dates_to_parse)

            shallow_df, wider_df = sorted([df, existing_df], key=lambda x: len(x.columns))
            df = wider_df.append(shallow_df, ignore_index=True)

        df.to_sql(name=self.table, index=False, con=self.engine, if_exists="replace")

    def load(
        self,
        column_types: Optional[Dict[str, str]] = None,
        parse_dates: Union[List[str], bool] = False,
    ) -> pd.DataFrame:

        df = pd.read_sql_table(table_name=self.table, con=self.engine, parse_dates=parse_dates)

        return df
