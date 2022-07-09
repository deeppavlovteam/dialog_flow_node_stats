import sys
import pathlib

try:
    import sqlalchemy
    from infi import clickhouse_orm
except ImportError:
    pass
import pytest
from dff_node_stats import Saver, Stats


def test_uri():
    with pytest.raises(ValueError) as error:
        saver = Saver("erroneous")
    assert "Saver should be initialized" in str(error.value)
    with pytest.raises(ValueError) as error:
        saver = Saver("mysql://auth")
    assert "Cannot recognize option" in str(error.value)


def test_uri_priority():
    saver1 = Saver("csv://file.csv")
    saver2 = Saver("csv://file2.csv")
    assert saver2.path == pathlib.Path("file2.csv")


def test_saver_registry():
    class MongoSaver(Saver, storage_type="mongo"):
        pass

    assert Saver._saver_mapping.get("mongo") == "MongoSaver"


if "sqlalchemy" in sys.modules:

    @pytest.fixture(scope="session")
    def PG_connection(PG_uri_string):
        engine = sqlalchemy.create_engine(PG_uri_string)
        connection = engine.connect()
        yield connection
        connection.close()

    @pytest.fixture(scope="session")
    def CH_connection(CH_uri_string):
        engine = sqlalchemy.create_engine(CH_uri_string)
        connection = engine.connect()
        yield connection
        connection.close()


@pytest.mark.xfail
@pytest.mark.skipif("sqlalchemy" not in sys.modules, reason="Postgres extra not installed")
def test_PG_saving(PG_connection, PG_uri_string, data_generator):
    if sqlalchemy.inspect(PG_connection.engine).has_table("dff_stats"):
        PG_connection.execute("TRUNCATE dff_stats")
    stats = Stats(saver=Saver(PG_uri_string))
    stats_object = data_generator(stats, 3)
    initial_cols = set(stats_object.dfs[0].columns)
    stats_object.save()
    result = PG_connection.execute("SELECT COUNT(*) FROM dff_stats")
    first = result.first()
    assert int(first[0]) > 0
    df = stats_object.dataframe
    assert set(df.columns) == initial_cols


@pytest.mark.xfail
@pytest.mark.skipif(
    ("infi" not in sys.modules or "sqlalchemy" not in sys.modules), reason="Clickhouse extra not installed"
)
def test_CH_saving(CH_connection, CH_uri_string, data_generator):
    stats = Stats(saver=Saver(CH_uri_string))
    stats_object = data_generator(stats, 3)
    initial_cols = set(stats_object.dfs[0].columns)
    stats_object.save()
    result = CH_connection.execute("SELECT COUNT (*) FROM dff_stats")
    first = result.first()
    assert int(first[0]) > 0
    df = stats_object.dataframe
    assert set(df.columns) == initial_cols
