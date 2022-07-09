"""
Saver
******
Provides the base class :py:class:`~dff_node_stats.savers.saver.Saver`. 
It is an interface class that defines methods for saving and loading dataframes.
On the other hand, it is also used to automatically construct the child classes 
depending on the input parameters. See the class documentation for more info.

"""
from typing import Dict, List, Union, Optional
import pathlib
import importlib

import pandas as pd


class Saver:
    """
    :py:class:`~dff_node_stats.savers.saver.Saver` interface requires two methods to be impemented:

    #. :py:meth:`~dff_node_stats.savers.saver.Saver.save`
    #. :py:meth:`~dff_node_stats.savers.saver.Saver.load`

    | A call to Saver is needed to instantiate one of the predefined child classes.
    | The subclass is chosen depending on the `path` parameter value (see Parameters).

    | Your own Saver can be implemented by following the current structure:
    | You can add this class to a separate module in this directory and then register it at runtime
    | by subclassing the Saver class, passing the module name as the `storage_type` parameter::

        MongoSaver(Saver, storage_type="mongo")

    | As a result, the Saver class will look for `MongoSaver` implementation in `mongo.py`

    Parameters
    ----------

    path: str
        A string that contains a prefix and a url of the target data storage, separated by ://.
        The prefix is used to automatically import a child class from one of the submodules
        and instantiate it.
        For instance, a call to `Saver("csv://...")` will eventually produce a :py:class:`~dff_node_stats.savers.csv.CsvSaver`,
        while a call to `Saver("clickhouse://...")` produces a :py:class:`~dff_node_stats.savers.clickhouse.ClickHouseSaver`

    table: str
        Sets the name of the db table to use, if necessary. Defaults to "dff_stats".
    """

    _saver_mapping = {}

    def __init_subclass__(cls, storage_type: str, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        cls._saver_mapping[storage_type] = cls.__name__

    def __new__(cls, path: Optional[str] = None, table: str = "dff_stats"):
        if not path:
            raise ValueError(
                """
            Saver should be initialized with a string
            """
            )

        storage_and_path = path.partition("://")
        if not all(storage_and_path):
            raise ValueError(
                """Saver should be initialized with either:
                csv://path_to_file or dbname://engine_params
                Available options: {}
                """.format(
                    ", ".join(list(cls._saver_mapping.keys()))
                )
            )
        storage_type = storage_and_path[0]
        subclass_name = cls._saver_mapping.get(storage_type)
        if not subclass_name:
            raise ValueError(
                """
                Cannot recognize option: {}
                Available options: {}            
                """.format(
                    storage_type, ", ".join(list(cls._saver_mapping.keys()))
                )
            )
        subclass = getattr(
            importlib.import_module(f".{storage_type}", package="dff_node_stats.savers"),
            subclass_name,
        )
        obj = object.__new__(subclass)
        obj.__init__(str(path), table)
        return obj

    def save(
        self,
        dfs: List[pd.DataFrame],
        column_types: Optional[Dict[str, str]] = None,
        parse_dates: Union[List[str], bool] = False,
    ) -> None:
        """
        Save the data to a database or a file.
        Append if the table already exists.

        Parameters
        ----------

        dfs: List[pd.DataFrame]
        column_types: Optional[Dict[str, str]] = None
        parse_dates: Union[List[str], bool] = False
        """
        raise NotImplementedError

    def load(
        self,
        column_types: Optional[Dict[str, str]] = None,
        parse_dates: Union[List[str], bool] = False,
    ) -> pd.DataFrame:
        """
        Load the data from a database or a file.

        Parameters
        ----------

        column_types: Optional[Dict[str, str]] = None
        parse_dates: Union[List[str], bool] = False
        """
        raise NotImplementedError


class ClickHouseSaver(Saver, storage_type="clickhouse"):
    """ClickHouseSaver Class prototype"""

    pass


class CsvSaver(Saver, storage_type="csv"):
    """CsvSaver Class prototype"""

    pass


class PostgresSaver(Saver, storage_type="postgresql"):
    """PostgresSaver Class prototype"""

    pass
