from falcon import testing
import pytest

from .main import create_app
from .data import NoOpBlobStorage, NoOpDataStorage


@pytest.fixture()
def client():
    return testing.TestClient(create_app())


def test_get_publications(client):
    result = client.simulate_get('/publications')
    assert result.status_code == 200
    assert result.headers.get('Access-Control-Allow-Origin') == '*'
    assert isinstance(result.json, list)
    assert len(result.json)
    for prop in ['name', 'count', 'img_uri']:
        assert prop in result.json[0]


def test_get_frequencies(client):
    result = client.simulate_get('/frequencies/pub0')
    assert result.status_code == 200
    assert result.headers.get('Access-Control-Allow-Origin') == '*'
    assert isinstance(result.json, list)
    assert len(result.json)
    for prop in ['word', 'count']:
        assert prop in result.json[0]


def test_post_images_unauthorized(client):
    result = client.simulate_post(f'/images')
    assert result.headers.get('Access-Control-Allow-Origin') == '*'
    assert result.status_code == 403


def test_post_images(client):
    result = client.simulate_post(
        f'/images', headers={'Authorization': '8h45ty'})
    assert result.headers.get('Access-Control-Allow-Origin') == '*'
    assert result.status_code == 201
