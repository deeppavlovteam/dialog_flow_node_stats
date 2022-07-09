"""
Utils
**********
Utilities for processing statistics inside the module.

#. :py:const:`TransformType <dff_node_stats.utils.TransformType>` defines the signature that the user-created transform functions should comply with.
#. py:const:`DffStatsException <dff_node_stats.utils.DffStatsException>` should be raised in module-specific error conditions.

"""
from functools import partial, wraps
from typing import List, Callable

import pandas as pd


TransformType = Callable[[pd.DataFrame], pd.DataFrame]
"""
| The prototype for transform functions: 
| They are required to take and return a pandas dataframe.

"""


class DffStatsException(Exception):
    """Exception to raise for module-specific errors."""

    pass


def transform_once(func: TransformType):
    """
    Caches the transformations results by columns

    Parameters
    ----------

    func: :py:const:`~dff_node_stats.utils.TransformType`
        A function that transforms the target pandas dataframe.
    """

    @wraps(func)
    def wrapper(dataframe: pd.DataFrame):
        cols_as_string = ".".join(dataframe.columns)
        if cols_as_string != wrapper.columns:
            new_df = func(dataframe)
            wrapper.columns = ".".join(new_df.columns)
            return new_df
        return dataframe

    wrapper.columns = ""
    return wrapper


def check_transform(transform: TransformType, exctype: type):
    """
    Applies a specified transform operation to the dataset before the decorated function is executed.

    Parameters
    ----------

    func: :py:const:`~dff_node_stats.utils.TransformType`
        A transformation function to apply in advance.
    exctype: type
        An exception to raise in case an error occurs.
    """

    def check_func(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) == 0 and len(kwargs) == 0:
                raise exctype(f"No dataframe found.")
            df = kwargs.get("df") or args[0]
            if not isinstance(df, pd.DataFrame):
                raise exctype(f"No dataframe found.")
            df = transform(df)
            return func(df)

        return wrapper

    return check_func


def check_columns(cols: List[str], exctype: type):
    """
    Raises an error, if the columns needed for a transformation
    or for making a plot are missing.

    Parameters
    ----------

    cols: list
        A list of columns, that are used in the decorated function.
    exctype: type
        An exception class to raise in case an error occurs.
    """

    def check_func(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) == 0 and len(kwargs) == 0:
                raise exctype(f"No dataframe found.")
            df = kwargs.get("df") or args[0]
            if not isinstance(df, pd.DataFrame):
                raise exctype(f"No dataframe found.")
            missing = [col for col in cols if col not in df.columns]
            if len(missing) > 0:
                raise exctype(
                    """
                    Required columns missing: {}. 
                    Did you collect them?
                    """.format(
                        ", ".join(missing)
                    )
                )
            return func(*args, **kwargs)

        return wrapper

    return check_func


requires_transform = partial(check_transform, exctype=DffStatsException)

requires_columns = partial(check_columns, exctype=DffStatsException)
