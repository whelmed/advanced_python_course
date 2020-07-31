
import logging

from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple, Generator
from .data import publications, word_counts, generate_word_cloud, get_client, upload_to_cloud_storage
import falcon


class PublicationsResource(object):

    def __init__(self):
        self.db = get_client()

    def on_get(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', '*')
        try:
            resp.media = [p._asdict() for p in publications(self.db)]
        except Exception as ex:
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'database is unavailable', 30)


class FrequenciesResource(object):

    def __init__(self):
        self.db = get_client()

    def on_get(self, req, resp, pub):
        resp.set_header('Access-Control-Allow-Origin', '*')
        try:
            word = req.get_param('word')
            count = req.get_param_as_int('count')
            chkpt = {'word': word, 'count': count} if word and count else None

            resp.media = [w._asdict()
                          for w in word_counts(pub, self.db, 10, chkpt)]
        except Exception as ex:
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'database is unavailable', 30)


class WordCloudResource(object):

    def __init__(self, bucket_name: str):
        self.db = get_client()
        self.blob = get_client('blob')
        self.bucket_name = bucket_name
        self.base_uri = 'https://storage.googleapis.com/'

    def on_get(self, req, resp, pub):
        resp.set_header('Access-Control-Allow-Origin', '*')

        if req.get_param_as_bool('regen'):
            imgbytes = generate_word_cloud(frequencies(pub, self.db, 5000))
            upload_to_cloud_storage(pub, imgbytes, self.blob, self.bucket_name)

            resp.content_type = falcon.MEDIA_PNG
            resp.data = imgbytes

        raise falcon.HTTPFound(f"{self.base_uri}{self.bucket_name}/{pub}.png")


app = falcon.API()
pubs = PublicationsResource()
freq = FrequenciesResource()
wrdc = WordCloudResource('advanced_python_cloud_academy')

app.add_route('/pubs', pubs)
app.add_route('/freq/{pub}', freq)
app.add_route('/images/{pub}.png', wrdc)

if __name__ == "__main__":
    pass
