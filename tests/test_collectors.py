import pytest

from dff_node_stats import collectors as DSC
from dff_node_stats import Stats


def test_inheritance():
    class NewCollector(DSC.Collector):
        @property
        def column_dtypes(self):
            return None

        @property
        def parse_dates(self):
            return None

        def collect_stats(self, ctx, actor, *args, **kwargs):
            return None

    new_collector = NewCollector()

    assert isinstance(new_collector, DSC.Collector)


def test_default_collection(data_generator, testing_saver):
    stats = Stats(saver=testing_saver, collectors=None)
    stats_object: Stats = data_generator(stats, 3)
    assert len(stats_object.dfs) > 0
    first = stats_object.dfs[0]
    assert "context_id" in first.columns
    assert "history_id" in first.columns
    assert "start_time" in first.columns
    assert "duration_time" in first.columns


def test_node_label_collection(data_generator, testing_saver):
    stats = Stats(saver=testing_saver, collectors=[DSC.NodeLabelCollector()])
    stats_object: Stats = data_generator(stats, 3)
    assert len(stats_object.dfs) > 0
    first = stats_object.dfs[0]
    assert "flow_label" in first.columns
    assert "node_label" in first.columns


def test_request_collection(data_generator, testing_saver):
    stats = Stats(saver=testing_saver, collectors=[DSC.RequestCollector()])
    stats_object: Stats = data_generator(stats, 3)
    assert len(stats_object.dfs) > 0
    first = stats_object.dfs[0]
    assert "user_request" in first.columns


def test_response_collection(data_generator, testing_saver):
    stats = Stats(saver=testing_saver, collectors=[DSC.ResponseCollector()])
    stats_object: Stats = data_generator(stats, 3)
    assert len(stats_object.dfs) > 0
    first = stats_object.dfs[0]
    assert "bot_response" in first.columns


def test_context_collection(data_generator, testing_saver):
    stats = Stats(saver=testing_saver, collectors=[DSC.ContextCollector(column_dtypes={"foo": "str"}, parse_dates=[])])
    stats_object: Stats = data_generator(stats, 3)
    assert len(stats_object.dfs) > 0
    first = stats_object.dfs[0]
    assert "foo" in first.columns
    assert "bar" in first["foo"].values
