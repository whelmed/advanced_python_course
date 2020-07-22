import logging
import sys
from typing import Any, List, Tuple, Dict
from google.cloud import firestore

import falcon


def fetch_publications(db=None):
    for doc in db.collection('publications').stream():
        yield {'pub': doc.id, 'count': doc.get('count')}


def fetch_word_counts_for_pub(publication: str, top_n: int = 2000, db=None):
    q = db.collection('publications')
    q = q.document(publication).collection('ent')
    q = q.order_by('count', direction=firestore.Query.DESCENDING)
    q = q.limit(top_n)
    for doc in q.stream():
        yield {'pub': publication, 'word': doc.get('word'), 'count': doc.get('count')}


def fetch_word_counts_for_pubs(publications: List[str], top_n: int = 2000, db=None):
    for publication in publications:
        yield fetch_word_counts_for_pub(publication, top_n, db)


class PostAggregatesResource(object):

    def __init__(self, get_fn, get_kwargs: List[Any]):
        self.get_fn = get_fn
        self.get_kwargs = get_kwargs

    def on_get(self, req, resp):
        try:
            resp.media = self.get_fn(*get_kwargs)
        except Exception as ex:
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'database is unavailable', 30)


class WordCountsResource(object):

    def __init__(self, get_fn, get_kwargs: List[Any]):
        self.get_fn = get_fn
        self.get_kwargs = get_kwargs

    def on_get(self, req, resp):
        try:
            pubs = req.get_param_as_list('pubs')
            topn = req.get_param_as_int('topn', default=2000)

            resp.media = self.get_fn(pubs, topn, **get_kwargs)
        except Exception as ex:
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'database is unavailable', 30)


app = falcon.API()
post_aggrs = PostAggregatesResource(fetch_publications)
word_count = WordCountsResource(fetch_word_counts)

app.add_route('/post-aggrs', post_aggrs)
app.add_route('/word-counts', word_count)
