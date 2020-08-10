import io
import logging
import os
from base64 import urlsafe_b64encode
from collections import Counter, defaultdict
from typing import Any, Dict, Generator, List, Tuple
from urllib.parse import quote
import hashlib
from google.cloud import firestore, storage
from google.cloud.storage import Blob

from PIL import Image
from wordcloud import WordCloud

from .models import Publication, WordCount

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/vagrant/service_account.json'


def get_client(_type='db'):
    if _type == 'db':
        return firestore.Client()
    elif _type == 'blob':
        return storage.Client()
    else:
        raise ValueError('unknown client type')


def image_to_byte_array(image: Image.Image, fmt: str = 'png'):
    '''Converts a PIL.Image.Image to a byte array, encoded as a PNG'''
    ioba = io.BytesIO()
    image.save(ioba, format=fmt)
    return ioba.getvalue()


def generate_word_cloud(freqs, fmt: str = 'bytes', height: int = 500, width: int = 500) -> Any:
    '''Generates a word cloud PIL.Image.Image of 500px X 500px
    Uses fmt to determine how to return the word cloud.
        Options: raw, image, bytes
    '''
    wc = WordCloud(height=height, width=width)
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


class DataStorage():

    def __init__(self, client: firestore.Client = None):
        self.db = client

    def publications(self, base_img_uri: str = '/images/') -> Generator[Publication, None, None]:
        '''Yields a `Publication` for each publication in the dataset.'''
        for doc in self.db.collection('publications').stream():
            yield Publication(doc.id, doc.get('count'), f'{base_img_uri}{quote(doc.id)}.png')

    def word_counts(self, publ: str, top_n: int = 10, checkpoint: Dict[str, Any] = None) -> Generator[WordCount, None, None]:
        '''Yields up to top_n WordCounts for the given publication.
        If a checkpoint dictionary is provided, it's used as starting place for the results.
        This allows for pagination. Example:
            word_counts('vox', 10, firestore.Client(),
                        {'word': 'apple', 'count': 30})
        The results would start from the record with the word: apple with the count of 30.
        '''
        checkpoint = checkpoint or {}
        q = self.db.collection('publications').document(publ).collection('ent')
        q = q.order_by('count', direction=firestore.Query.DESCENDING)
        q = q.order_by('word')
        q = q.limit(top_n)

        if checkpoint:
            q = q.start_after(checkpoint)

        for doc in q.stream():
            yield WordCount(doc.get('word'), doc.get('count'))

    def frequencies(self, publ: str, top_n: int = 10, checkpoint: Dict[str, Any] = None) -> Dict[str, int]:
        '''Returns a dictionary containing the frequency of each key '''
        return {wc.word: wc.count for wc in self.word_counts(publ, top_n, checkpoint)}


class NoOpDataStorage():

    def __init__(self, *args, **kwargs):
        pass

    def publications(self, base_img_uri='/images/', *_, **__) -> Generator[Publication, None, None]:
        for i in range(10):
            yield Publication(f'pub{i}', i, f'{base_img_uri}pub{i}.png')

    def word_counts(self, *_, **__) -> Generator[WordCount, None, None]:
        for i in range(10):
            yield WordCount(f'ent{i}', i)

    def frequencies(self, *_, **__) -> Dict[str, int]:
        return {wc.word: wc.count for wc in self.word_counts()}


def pub_to_url(publ: str):
    return hashlib.md5(publ.encode()).hexdigest()


class BlobStorage():

    def __init__(self, client: storage.Client):
        self.blob = client

    def save(self, publ: str, bucket: str, ibytes: bytes):
        publ = pub_to_url(publ)
        b = self.blob.get_bucket(bucket)
        Blob(f'{publ}.png', b).upload_from_string(ibytes, content_type='image/png')  # noqa


class NoOpBlobStorage():

    def __init__(self, *args, **kwargs):
        pass

    def save(self, *_, **__):
        pass
