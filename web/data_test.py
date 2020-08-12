import os
import pytest
from unittest.mock import Mock, patch
from PIL import Image
from google.cloud import firestore
from google.cloud.storage import Blob
from google.cloud import storage
from wordcloud.wordcloud import WordCloud
from .data import (get_client, image_to_byte_array, DataStorage,
                   NoOpDataStorage, generate_word_cloud, image_url_path)

black_square = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x80\x00\x00\x00\x80\x08\x02\x00\x00\x00L\\\xf6\x9c\x00\x00\x00DIDATx\x9c\xed\xc1\x01\x01\x00\x00\x00\x80\x90\xfe\xaf\xee\x08\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x18\xc0\x80\x00\x01c\x16u\x00\x00\x00\x00\x00IEND\xaeB`\x82'


class Client:
    collections = {
        'publications': [
            Mock(**{'id': 'pub0', 'get.return_value': 0}),
            Mock(**{'id': 'pub1', 'get.return_value': 1}),
            Mock(**{'id': 'pub2', 'get.return_value': 2}),
            Mock(**{'id': 'pub3', 'get.return_value': 3}),
        ],
        'ent': [
            {'word': 'ent0', 'count': 0},
            {'word': 'ent1', 'count': 1},
            {'word': 'ent2', 'count': 2},
            {'word': 'ent3', 'count': 3},
        ],
    }

    def __init__(self):
        self._collection = 'publications'
        self._checkpoint = None

    def collection(self, name):
        self._collection = name
        return self

    def document(self, *_, **__):
        return self

    def order_by(self, *_, **__):
        return self

    def limit(self, *_, **__):
        return self

    def start_after(self, checkpoint):
        self._checkpoint = checkpoint
        return self

    def stream(self, *_, **__):
        if self._checkpoint:

            for index, ent in enumerate(Client.collections[self._collection]):
                if ent == self._checkpoint:
                    return Client.collections[self._collection][index+1:]
        else:
            return Client.collections[self._collection]


@pytest.fixture(scope="function", params=[DataStorage, NoOpDataStorage])
def data_storage(request):
    ''' Creates DataStorage & NoOpDataStorage for fixture callers.
        Enables testing of both classes with a mock client.
    '''
    return request.param(client=Client())


@pytest.mark.skipif(os.path.exists('/vagrant/Vagrantfile'), reason='run in prod-like environments only')
@pytest.mark.parametrize(
    '_in,_out', [
        (None, firestore.Client),
        ('db', firestore.Client),
        ('blob', storage.Client)
    ])
def test_get_client_return_type(_in, _out):
    c = get_client(_in) if _in else get_client()
    assert type(c) == _out


def test_image_to_byte_array():
    img = Image.new("RGB", (128, 128), "black")
    assert image_to_byte_array(img) == black_square


def test_publications(data_storage):
    for index, publication in enumerate(data_storage.publications()):
        assert publication.count == index
        assert publication.name == f'pub{index}'
        assert publication.img_uri == image_url_path(publication.name)


def test_publications_diff_img_dir(data_storage):
    for index, publication in enumerate(data_storage.publications('reimagined')):
        assert publication.count == index
        assert publication.name == f'pub{index}'
        assert publication.img_uri == image_url_path(publication.name, path='reimagined')  # noqa


def test_word_counts(data_storage):
    for index, (word, count) in enumerate(data_storage.word_counts('pub0')):
        assert word == f'ent{index}'
        assert count == index


def test_word_counts_checkpoint(data_storage):
    entity_index = 1
    ent = Client.collections['ent'][entity_index]
    chk = (ent['word'], ent['count'])
    for index, (word, count) in enumerate(data_storage.word_counts('pub0', checkpoint=chk)):
        # Set the index to the entity_index + 1 to get the next record
        index += (entity_index+1)
        assert word == f'ent{index}'
        assert count == index


def test_generate_word_cloud_return_types():
    freqs = {wc['word']: wc['count'] for wc in Client.collections['ent']}
    assert isinstance(generate_word_cloud(freqs, fmt='bytes'), bytes)
    assert isinstance(generate_word_cloud(freqs, fmt='image'), Image.Image)
    assert isinstance(generate_word_cloud(freqs, fmt='raw'), WordCloud)


def test_generate_word_cloud_invalid_fmt():
    freqs = {wc['word']: wc['count'] for wc in Client.collections['ent']}
    with pytest.raises(ValueError):
        generate_word_cloud(freqs, fmt='unexpected')
