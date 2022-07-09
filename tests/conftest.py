import sys
from typing import Callable

import pytest
from dff_node_stats import Saver, Stats
from dff_node_stats import collectors as DSC

from . import config


@pytest.fixture(scope="session")
def data_generator():
    sys.path.insert(0, "../")
    main: Callable
    from examples.collect_stats import main

    yield main


@pytest.fixture(scope="session")
def testing_file(tmpdir_factory):
    fn = tmpdir_factory.mktemp("data").join("stats.csv")
    return str(fn)


@pytest.fixture(scope="session")
def testing_saver(testing_file):
    yield Saver("csv://{}".format(testing_file))


@pytest.fixture(scope="session")
def testing_dataframe(data_generator, testing_saver):
    stats = Stats(saver=testing_saver, collectors=[DSC.NodeLabelCollector()])
    stats_object: Stats = data_generator(stats, 3)
    stats_object.save()
    yield stats_object.dataframe


@pytest.fixture(scope="session")
def PG_uri_string():
    return "postgresql://{}:{}@{}:{}/{}".format(
        config.PG_USERNAME, config.PG_PASSWORD, config.HOST, config.PG_PORT, config.DATABASE
    )


@pytest.fixture(scope="session")
def CH_uri_string():
    return "clickhouse://{}:{}@{}:{}/{}".format(
        config.CH_USERNAME, config.CH_PASSWORD, config.HOST, config.CH_PORT, config.DATABASE
    )
