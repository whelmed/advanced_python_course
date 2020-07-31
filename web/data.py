import os

import io
import logging

from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple, Generator

from google.cloud import firestore
from google.cloud.storage import Blob
from google.cloud import storage

from PIL import Image
from wordcloud import WordCloud
from urllib.parse import quote
from .models import Publication, WordCount

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/vagrant/service_account.json'
BASE_IMG_URI = 'http://0.0.0.0:8000/images/'


def get_client(_type='db'):
    if _type == 'db':
        return firestore.Client()
    elif _type == 'blob':
        return storage.Client()
    else:
        raise ValueError('unknown client type')


def image_to_byte_array(image: Image):
    '''Converts a PIL.Image to a byte array, encoded as a PNG'''
    ioba = io.BytesIO()
    image.save(ioba, format='png')
    return ioba.getvalue()


def generate_word_cloud(freqs, fmt: str = 'bytes') -> Any:
    '''Generates a word cloud PIL.Image of 500px X 500px 
    Uses fmt to determine how to return the word cloud. 
        Options: raw, image, bytes
    '''
    wc = WordCloud(height=500, width=500)
    wc.fit_words(freqs)
    fmt = fmt.lower()

    if fmt == 'raw':
        return wc
    elif fmt == 'image':
        return wc.to_image()
    elif fmt == 'bytes':
        return image_to_byte_array(wc.to_image())
    else:
        raise ValueError('unsupported fmt value.')


def publications(db) -> Generator[Publication, None, None]:
    '''Yields a `Publication` for each publication in the dataset.'''
    for doc in db.collection('publications').stream():
        yield Publication(doc.id, doc.get('count'), f'{BASE_IMG_URI}{quote(doc.id)}.png')


def word_counts(publ: str, db: firestore.Client, top_n: int = 10, checkpoint: Dict[str, Any] = None) -> Generator[WordCount, None, None]:
    '''Yields up to top_n WordCounts for the given publication.
    If a checkpoint dictionary is provided, it's used as starting place for the results. 
    This allows for pagination. Example:
        word_counts('vox', 10, firestore.Client(), {'word': 'apple', 'count': 30})
    The results would start from the record with the word: apple with the count of 30.
    '''
    checkpoint = checkpoint or {}
    q = db.collection('publications').document(publ).collection('ent')
    q = q.order_by('count', direction=firestore.Query.DESCENDING)
    q = q.order_by('word')
    q = q.limit(top_n)

    if checkpoint:
        q = q.start_after(checkpoint)

    for doc in q.stream():
        yield WordCount(doc.get('word'), doc.get('count'))


def frequencies(publ: str, db: firestore.Client, top_n: int = 10, checkpoint: Dict[str, Any] = None) -> Dict[str, int]:
    '''Returns a dictionary containing the frequency of each key '''
    return {wc.word: wc.count for wc in word_counts(publ, db, top_n, checkpoint)}


def upload_to_cloud_storage(publ: str, ibytes, client, bucket: str):
    b = client.get_bucket(bucket)
    Blob(f'{p}.png', b).upload_from_string(ibytes, content_type='image/png')
