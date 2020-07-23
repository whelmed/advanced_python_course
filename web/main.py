import io
import logging
import os
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

from google.cloud import firestore
from google.cloud.storage import Blob
from google.cloud import storage

import falcon
from PIL import Image
from wordcloud import WordCloud
from urllib.parse import quote

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/vagrant/service_account.json'

BASE_IMG_URI = 'https://storage.cloud.google.com/advanced_python_cloud_academy/'


def publications(db=None):
    for doc in db.collection('publications').stream():
        yield {'pub': doc.id, 'count': doc.get('count'), 'img': f'{BASE_IMG_URI}{quote(doc.id)}.png'}


def word_counts_for_pub(publication: str, top_n: int = 2000, db=None, checkpoint=None):
    checkpoint = checkpoint or {}
    q = db.collection('publications')
    q = q.document(publication).collection('ent')
    q = q.order_by('count', direction=firestore.Query.DESCENDING)
    q = q.order_by('word')
    q = q.limit(top_n)

    if checkpoint:
        q = q.start_after(checkpoint)

    for doc in q.stream():
        yield {'pub': publication, 'word': doc.get('word'), 'count': doc.get('count')}


def word_counts_for_pubs(pubs: List[str], top_n: int = 2000, db=None):
    pubs = pubs or [p.get('pub') for p in publications(db)]

    for pub in pubs:
        for wc in word_counts_for_pub(pub, top_n, db):
            yield wc


def generate_word_cloud(frequencies):
    wc = WordCloud(height=500, width=500)
    return wc.fit_words(frequencies).to_image()


def image_to_byte_array(image: Image):
    ioba = io.BytesIO()
    image.save(ioba, format='png')
    return ioba.getvalue()


def counters(pubs: List[str], top_n: int = 2000, db=None, checkpoint=None):
    results = defaultdict(Counter)
    for doc in word_counts_for_pub(pubs[0], top_n=top_n, db=db, checkpoint=checkpoint):
        results[doc.get('pub')][doc.get('word')] = doc.get('count')
    return results


def generate_word_clouds(pubs: List[str], top_n: int = 2000, db=None):
    for pub, wc in counters(pubs, top_n, db).items():
        yield pub, image_to_byte_array(generate_word_cloud(wc))


class PublicationsResource(object):

    def __init__(self):
        self.db = firestore.Client()

    def on_get(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', '*')
        try:
            resp.media = list(publications(self.db))
        except Exception as ex:
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'database is unavailable', 30)


class WordCountsResource(object):

    def __init__(self):
        self.db = firestore.Client()

    def on_get(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', '*')
        try:
            pubs = req.get_param_as_list('pubs')
            word = req.get_param('word')
            count = req.get_param_as_int('count')
            checkpoint = None

            if word and count:
                checkpoint = {
                    'word': word,
                    'count': count
                }

            resp.media = counters(pubs, 10, db=self.db, checkpoint=checkpoint)
        except Exception as ex:
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'database is unavailable', 30)


app = falcon.API()
pubs = PublicationsResource()
words = WordCountsResource()

app.add_route('/pubs', pubs)
app.add_route('/words', words)

if __name__ == "__main__":
    db = firestore.Client()
    pubs = [p.get('pub') for p in publications(db)]

    client = storage.Client()
    bucket = client.get_bucket('advanced_python_cloud_academy')

    for p, i in generate_word_clouds(pubs, db=db):
        Blob(f'{p}.png', bucket).upload_from_string(
            i, content_type='image/png')
