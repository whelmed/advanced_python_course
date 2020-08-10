
import logging

from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple, Generator
from .data import (BlobStorage, NoOpBlobStorage, DataStorage,
                   NoOpDataStorage, generate_word_cloud, get_client, pub_to_url)
import falcon


def can_generate_wordcloud(req, resp, resource, params, approved_token: str):
    if req.get_header('Authorization') != approved_token:
        raise falcon.HTTPForbidden(
            'Forbidden', 'authorization token mismatch'
        )


class PublicationsResource(object):

    def __init__(self, data_storage: DataStorage):
        self._data_storage = data_storage

    def on_get(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', '*')
        try:
            resp.media = [p._asdict()
                          for p in self._data_storage.publications()]
        except Exception as ex:
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'database is unavailable', 30)


class FrequenciesResource(object):

    def __init__(self, data_storage: DataStorage):
        self._data_storage = data_storage

    def on_get(self, req, resp, pub):
        resp.set_header('Access-Control-Allow-Origin', '*')
        try:
            word = req.get_param('word')
            count = req.get_param_as_int('count')
            chkpt = {'word': word, 'count': count} if word and count else None

            resp.media = [w._asdict()
                          for w in self._data_storage.word_counts(pub, 10, chkpt)]
        except Exception as ex:
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'database is unavailable', 30)


class WordCloudResource(object):

    def __init__(self, blob_storage: BlobStorage, data_storage: DataStorage, bucket_name: str):
        self._blob_storage = blob_storage
        self._data_storage = data_storage
        self._bucket_name = bucket_name
        self._base_uri = 'https://storage.googleapis.com/'

    def on_get(self, req, resp, pub):
        resp.set_header('Access-Control-Allow-Origin', '*')
        raise falcon.HTTPFound(
            f"{self._base_uri}{self._bucket_name}/{pub}.png")

    @falcon.before(can_generate_wordcloud, '8h45ty')
    def on_post(self, req, resp, pub):
        resp.set_header('Access-Control-Allow-Origin', '*')
        try:
            frequencies = self._data_storage.frequencies(pub, 5000)
        except:
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'data storage is unavailable', 30)

        imagebytes = generate_word_cloud(frequencies)

        try:
            self._blob_storage.save(pub, self._bucket_name, imagebytes)
        except:
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'blob storage is unavailable', 30)

        raise falcon.HTTPFound(
            f'{self._base_uri}{self._bucket_name}/{pub}.png')


def create_app(data_storage, blob_storage, blob_bucket_name):
    app = falcon.API()
    pubs = PublicationsResource(data_storage)
    freq = FrequenciesResource(data_storage)
    wrdc = WordCloudResource(blob_storage, data_storage, blob_bucket_name)

    app.add_route('/pubs', pubs)
    app.add_route('/freq/{pub}', freq)
    app.add_route('/images/{pub}.png', wrdc)

    return app


if __name__ == "__main__":
    pass
