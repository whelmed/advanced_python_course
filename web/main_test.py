from unittest.mock import patch
import os
import pytest
from falcon import testing
from collections import OrderedDict
from .data import NoOpBlobStorage, NoOpDataStorage, DataStorage, BlobStorage
from .main import create_app


@pytest.fixture()
def client():
    return testing.TestClient(create_app())


# Environment variables to use for NoOP settings
noop_environvars = OrderedDict({
    # Key: (EnvVar Value, Expected Type)
    'data_storage': ('', NoOpDataStorage),
    'blob_storage': ('', NoOpBlobStorage),
    'blob_storage_bucket': ('', str),
    'allowed_origin': ('', str)
})


def _create_app(*args, **kwargs):
    '''A version of the private _create_app from main.py used in testing.'''
    keys = list(noop_environvars.keys())  # Get the keys in the order defined
    for idx, arg in enumerate(args):
        envvar = keys[idx]
        value, expected = noop_environvars[envvar]
        assert os.getenv(envvar) == value
        assert isinstance(arg, expected)


@patch(f'{__package__}.main._create_app', _create_app)
def test_create_app_noop_return_types(monkeypatch):
    for key, (value, _) in noop_environvars.items():
        monkeypatch.setenv(key, value)
    create_app()


def test_get_publications(client):
    result = client.simulate_get('/publications')
    assert result.status_code == 200
    assert result.headers.get('Access-Control-Allow-Origin') == '*'
    assert isinstance(result.json, list)
    assert len(result.json) == 10
    for prop in ['name', 'count', 'img_uri']:
        assert prop in result.json[0]


def test_get_frequencies(client):
    result = client.simulate_get('/frequencies/pub0')
    assert result.status_code == 200
    assert result.headers.get('Access-Control-Allow-Origin') == '*'
    assert isinstance(result.json, list)
    assert len(result.json) == 10
    for prop in ['word', 'count']:
        assert prop in result.json[0]


def test_get_frequencies_with_params(client):
    result = client.simulate_get('/frequencies/pub0?word=ent1&count=1')
    assert result.status_code == 200
    assert result.headers.get('Access-Control-Allow-Origin') == '*'
    assert isinstance(result.json, list)
    assert len(result.json) == 8
    for prop in ['word', 'count']:
        assert prop in result.json[0]


def test_post_images_unauthorized(client):
    result = client.simulate_post(f'/images')
    assert result.headers.get('Access-Control-Allow-Origin') == '*'
    assert result.status_code == 403


def test_post_images(client):
    result = client.simulate_post(f'/images', headers={'Authorization': '8h45ty'})  # noqa
    assert result.headers.get('Access-Control-Allow-Origin') == '*'
    assert result.status_code == 201
