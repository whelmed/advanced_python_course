from falcon import testing
import pytest

from .main import create_app
from .data import NoOpBlobStorage, NoOpDataStorage, pub_to_url


@pytest.fixture()
def client():
    ds = NoOpDataStorage()
    bs = NoOpBlobStorage()
    return testing.TestClient(create_app(ds, bs, 'fake'))


@pytest.fixture()
def publication_image_name():
    return f"{pub_to_url('pub0')}.png"


def test_get_publications(client):
    result = client.simulate_get('/pubs')
    assert result.status_code == 200
    assert isinstance(result.json, list)
    assert len(result.json)
    assert 'name' in result.json[0]
    assert 'count' in result.json[0]
    assert 'img_uri' in result.json[0]


def test_get_frequencies(client):
    result = client.simulate_get('/freq/pub0')
    assert result.status_code == 200
    assert isinstance(result.json, list)
    assert len(result.json)
    assert 'word' in result.json[0]
    assert 'count' in result.json[0]


def test_get_images(client, publication_image_name):
    result = client.simulate_get(f'/images/{publication_image_name}')
    assert result.status_code == 302
    assert result.headers.get('location').endswith(f'{publication_image_name}')


def test_post_images_unauthorized(client, publication_image_name):
    result = client.simulate_post(f'/images/{publication_image_name}')
    assert result.status_code == 403


def test_post_images(client, publication_image_name):
    result = client.simulate_post(
        f'/images/{publication_image_name}', headers={'Authorization': '8h45ty'})
    assert result.status_code == 302
    assert result.headers.get('location').endswith(publication_image_name)
