import hashlib
import io
from typing import Any, Dict, Generator, Tuple

from google.cloud import firestore, storage
from google.cloud.storage import Blob

from PIL import Image
from wordcloud import WordCloud

from .models import Publication, WordCount


def get_client(_type='db'):
    '''get_client returns a client used for accessessing data or blob storage. 
    '''
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


def pub_to_url(publ: str):
    '''convert the name of a publication to a URL friendly hash'''
    return hashlib.md5(publ.encode()).hexdigest()


class DataStorage():
    name = 'data-firestore'

    def __init__(self, client: firestore.Client = None):
        self.db = client

    def publications(self, bucket_name: str = '/') -> Generator[Publication, None, None]:
        '''Yields a `Publication` for each publication in the dataset.'''
        for doc in self.db.collection('publications').stream():
            yield Publication(doc.id, doc.get('count'), f'{bucket_name}{pub_to_url(doc.id)}.png')

    def word_counts(self, publ: str, top_n: int = 10, checkpoint: Tuple[str, int] = None) -> Generator[WordCount, None, None]:
        '''Yields up to top_n WordCounts for the given publication.
        If a checkpoint tuple is provided, it's used as starting place for the results.
        This allows for pagination. Example:
            word_counts('vox', 10, firestore.Client(), ('apple', 30))
        The results would start from the record with the word: apple with the count of 30.
        '''
        # If it's None at the start, make it Tuple
        checkpoint = checkpoint or (None, None)
        (word, count) = checkpoint  # Unpack
        # Check the truthiness of word, check to see if count is None
        # Since count is expected to be an int, checking truthiness will fail for 0.
        # Not sure that's likely, but, it could happen...right?
        if word and count is not None:
            # If all the values in the tuple are truthy setup a checkpoint dictionary
            checkpoint = {'word': word, 'count': count}
        else:
            checkpoint = {}

        q = self.db.collection('publications').document(publ).collection('ent')
        q = q.order_by('count', direction=firestore.Query.DESCENDING)
        q = q.order_by('word')
        q = q.limit(top_n)

        if checkpoint:
            q = q.start_after(checkpoint)

        for doc in q.stream():
            yield WordCount(doc.get('word'), doc.get('count'))

    def frequencies(self, publ: str, top_n: int = 10, checkpoint: Tuple[str, int] = None) -> Dict[str, int]:
        '''Returns a dictionary containing the frequency of each key '''
        return {wc.word: wc.count for wc in self.word_counts(publ, top_n, checkpoint)}


class NoOpDataStorage():
    name = 'data-noop'

    def __init__(self, *args, **kwargs):
        pass

    def publications(self, bucket_name='/', *_, **__) -> Generator[Publication, None, None]:
        for i in range(10):
            pub = f'pub{i}'
            yield Publication(pub, i, f'{bucket_name}{pub_to_url(pub)}.png')

    def word_counts(self, *_, checkpoint: Tuple[str, int] = None, **__) -> Generator[WordCount, None, None]:
        # If a checkpoint is passed, use the count to determine
        # where the range generator starts
        # Allows us to simulate setting a checkpoint
        checkpoint = checkpoint or (None, -1)
        # Offset by one. If a value wasn't passed in, this will end up as 0
        # If a value was passed in, then it's a checkpoint, and we need to increment by 1
        # in order to get the value after the checkpoint
        checkpoint = checkpoint[1] + 1
        # Hardcoding 10 records. Could make class level setting if needed
        for i in range(checkpoint, 10):
            yield WordCount(f'ent{i}', i)

    def frequencies(self, *_, **__) -> Dict[str, int]:
        return {wc.word: wc.count for wc in self.word_counts()}


class BlobStorage():
    name = 'blob-gc-storage'

    def __init__(self, client: storage.Client):
        self.blob = client

    def save(self, publ: str, bucket: str, ibytes: bytes):
        publ = pub_to_url(publ)
        b = self.blob.get_bucket(bucket)
        Blob(f'{publ}.png', b).upload_from_string(ibytes, content_type='image/png')  # noqa


class NoOpBlobStorage():
    name = 'blob-noop'

    def __init__(self, *args, **kwargs):
        pass

    def save(self, *_, **__):
        pass
