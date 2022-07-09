from multiprocessing import Process
from typing import Dict, List
import sys

import pytest
import requests

from dff_node_stats.api import api_run


@pytest.fixture(scope="module")
def host():
    yield "localhost"


@pytest.fixture(scope="module")
def port():
    yield 8000


def customize(app, *args):
    @app.get("/customendpoint", response_model=List[Dict[str, str]])
    async def custom_route():
        return [{"foo": "bar"}, {"baz": "qux"}]

    return app


@pytest.fixture(scope="function")
def custom_API(host, port, testing_dataframe):
    df = testing_dataframe
    proc = Process(target=api_run, args=(df, customize, port), daemon=True)
    proc.start()
    yield
    proc.kill()


@pytest.fixture(scope="function")
def default_API(host, port, testing_dataframe):
    df = testing_dataframe
    proc = Process(target=api_run, args=(df, None, port), daemon=True)
    proc.start()
    yield
    proc.kill()


def test_custom(custom_API, host, port):
    response = requests.get(f"http://{host}:{port}/customendpoint")
    code = response.status_code
    data = response.json()
    assert code == 200
    assert len(data) > 0
    first = data[0]
    assert len(first) > 0
    assert isinstance(first, dict)
    assert first["foo"] == "bar"


def test_default_transition_counts(default_API, host, port):
    response = requests.get(f"http://{host}:{port}/api/v1/stats/transition-counts")
    code = response.status_code
    data = response.json()
    assert code == 200
    assert len(data) > 0
    sys.stderr.write(str(type(data)))
    for key, value in data.items():
        assert isinstance(key, str)
        assert isinstance(value, int)


def test_default_transition_probs(default_API, host, port):
    response = requests.get(f"http://{host}:{port}/api/v1/stats/transition-probs")
    code = response.status_code
    data = response.json()
    assert code == 200
    sys.stderr.write(str(type(data)))
    for key, value in data.items():
        assert isinstance(key, str)
        assert isinstance(value, float)
