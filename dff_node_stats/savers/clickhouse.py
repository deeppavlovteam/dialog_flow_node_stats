"""
Clickhouse
---------------------------
Provides the Clickhouse version of the :py:class:`~dff_node_stats.savers.saver.Saver`. 
You don't need to interact with this class manually, as it will be automatically 
imported and initialized when you construct :py:class:`~dff_node_stats.savers.saver.Saver` with specific parameters.

"""
from typing import List, Optional, Union, Dict

from infi.clickhouse_orm.database import Database
from infi.clickhouse_orm.models import Model
from infi.clickhouse_orm import fields
from infi.clickhouse_orm.engines import Memory
import pandas as pd


class ClickHouseSaver:
    """
    Saves and reads the stats dataframe from a csv file.
    You don't need to interact with this class manually, as it will be automatically
    initialized when you construct :py:class:`~dff_node_stats.savers.saver.Saver` with specific parameters.

    Parameters
    ----------

    path: str
        | The construction path.
        | It should match the sqlalchemy :py:class:`~sqlalchemy.engine.Engine` initialization string.

        >>> ClickHouseSaver("clickhouse://user:password@localhost:8000/default")
    table: str
        Sets the name of the db table to use. Defaults to "dff_stats".
    """

    def __init__(self, path: str, table: str = "dff_stats") -> None:
        self.path = path
        self.table = table
        auth, _, address = path.partition("@")
        address, _, db_name = address.partition("/")
        address = "http://" + address
        username, _, password = auth.partition("://")[2].partition(":")
        if not all([db_name, address, username, password]):
            raise ValueError("Invalid database URI or credentials")
        self.db = Database(db_name, db_url=address, username=username, password=password)
        return

    def save(
        self,
        dfs: List[pd.DataFrame],
        column_types: Optional[Dict[str, str]] = None,
        parse_dates: Union[List[str], bool] = False,
    ) -> None:
        df = pd.concat(dfs)

        Model = self.create_clickhouse_table(column_types, self.table)

        def lazyupload(df):
            for _, row in df.iterrows():
                row = row.to_dict()
                for column in parse_dates:
                    row[column] = row[column].to_pydatetime()
                yield Model(**row)

        # in case new columns have been added,
        # but the table already exists
        # we recreate the table and insert old entries
        if self.db.does_table_exist(Model):
            ExistingModel = self.db.get_model_for_table(self.table, system_table=False)
            existing_fields = set(ExistingModel.fields())
            if set(Model.fields()) ^ existing_fields:

                dates_to_parse = [col for col in parse_dates if col in existing_fields]
                existing_df = self.load(parse_dates=dates_to_parse)
                shallow_df, wider_df = sorted([df, existing_df], key=lambda x: len(x.columns))
                df = wider_df.append(shallow_df, ignore_index=True)

                self.db.drop_table(ExistingModel)
                self.db.create_table(Model)
        else:
            self.db.create_table(Model)

        self.db.insert(lazyupload(df), batch_size=1000)

    def load(
        self,
        column_types: Optional[Dict[str, str]] = None,
        parse_dates: Union[List[str], bool] = False,
    ) -> pd.DataFrame:

        Model = self.db.get_model_for_table(self.table, system_table=False)
        response = self.db.select(query=f"SELECT * FROM {self.table}", model_class=Model)
        results = [item.to_dict() for item in response]
        df = pd.DataFrame.from_records(results)
        return df

    @staticmethod
    def create_clickhouse_table(column_types: Dict[str, str], tablename: str):
        model_namespace = {"engine": Memory()}
        ch_mapping = {
            "object": fields.StringField,
            "str": fields.StringField,
            "uint64": fields.UInt64Field,
            "uint32": fields.UInt32Field,
            "uint16": fields.UInt16Field,
            "uint8": fields.UInt8Field,
            "bool": fields.UInt8Field,
            "float64": fields.Float64Field,
            "float32": fields.Float32Field,
            "int64": fields.Int64Field,
            "int32": fields.Int32Field,
            "int16": fields.Int16Field,
            "int8": fields.Int8Field,
            "datetime64[D]": fields.DateField,
            "datetime64[ns]": fields.DateTimeField,
        }
        for column, _type in column_types.items():
            model_namespace.update(
                {column: fields.NullableField(ch_mapping[_type](), extra_null_values=[float("nan")])}
            )
        dff_stats = type(tablename, (Model,), model_namespace)
        return dff_stats
