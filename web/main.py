'''
    The following configuration settings are exposed as environment variables
    ---------------------------------------------------------------------------
    data_storage:           if set to a value of: firestore
                            the data storage service will use:
                                DataStorage(client=get_client('db'))

                            if set to any other value:
                                NoOpDataStorage()

    blob_storage:           if set to a value of: cloudstorage
                            the blob storage service will use:
                                BlobStorage(client=get_client('blob'))

                            if set to any other value:
                                NoOpBlobStorage()

    blob_storage_bucket:    if set the value is used as the bucket where images reside
                            if not set the value is set to: fake


    allowed_origin:         if set the value is used as the Access-Control-Allow-Origin header value
                            if not set the value is set to: *

'''
from .data import BlobStorage, DataStorage, NoOpBlobStorage, NoOpDataStorage, generate_word_cloud, get_client
import falcon
from typing import Any, Dict, Generator, List, Tuple
from collections import Counter, defaultdict
import os
import logging

# From https://trstringer.com/logging-flask-gunicorn-the-manageable-way/
logger = logging.getLogger()
gunicorn_logger = logging.getLogger('gunicorn.error')
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)


if os.path.exists('/vagrant/Vagrantfile'):
    logger.info('(dev-only) dev environment identified.')
    os.environ['PYTHONBREAKPOINT'] = 'ipdb.set_trace'
    logger.info('(dev-only) ipdb set as default debugger.')


def can_generate_wordcloud(req, resp, resource, params, approved_token: str):
    '''can_generate_wordcloud is a Falcon hook that extracts an auth token
    from a request header named Authorization.
    If the extracted token value DOES NOT MATCH approved_token then a
    falcon.HTTPForbidden exception is raised. 
    '''
    if req.get_header('Authorization') != approved_token:
        raise falcon.HTTPForbidden('Forbidden', 'authorization token mismatch')


class CORSComponent(object):
    '''A middleware implementation for setting CORS origins.

    This class is a slightly modified version of the example
    found: https://falcon.readthedocs.io/en/stable/user/faq.html#how-do-i-implement-cors-with-falcon
    '''

    def __init__(self, origin: str = '*'):
        self._origin = origin

    def process_response(self, req, resp, resource, req_succeeded):
        resp.set_header('Access-Control-Allow-Origin', self._origin)

        if req_succeeded and req.method == 'OPTIONS' and req.get_header('Access-Control-Request-Method'):
            # NOTE(kgriffs): This is a CORS preflight request. Patch the response accordingly.
            allow = resp.get_header('Allow')
            resp.delete_header('Allow')

            allow_headers = req.get_header(
                'Access-Control-Request-Headers', default='*')

            resp.set_headers((
                ('Access-Control-Allow-Methods', allow),
                ('Access-Control-Allow-Headers', allow_headers),
                ('Access-Control-Max-Age', '86400'),  # 24 hours
            ))


class PublicationsResource(object):

    def __init__(self, data_storage: DataStorage, bucket_name: str):
        self._storage = data_storage
        self._bucket_name = bucket_name

    def on_get(self, req, resp):
        try:
            publications = self._storage.publications(self._bucket_name)
            resp.media = [p._asdict() for p in publications]
        except Exception as ex:
            logger.exception('unable to get publications')
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'database is unavailable', retry_after=30)


class FrequenciesResource(object):

    def __init__(self, data_storage: DataStorage):
        self._storage = data_storage

    def on_get(self, req, resp, pub):
        try:
            # Get the parameters and configure a checkpoint
            chkpt = (req.get_param('word'), req.get_param_as_int('count'))
            resp.media = [w._asdict() for w in self._storage.word_counts(pub, 10, chkpt)]  # noqa
        except Exception as ex:
            logger.exception('unable to get frequencies')
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'database is unavailable', retry_after=30)


class WordCloudResource(object):

    def __init__(self, blob_storage: BlobStorage, data_storage: DataStorage, bucket_name: str):
        self._blob_storage = blob_storage
        self._data_storage = data_storage
        self._bucket_name = bucket_name

    @falcon.before(can_generate_wordcloud, '8h45ty')
    def on_post(self, req, resp):
        '''An easy, albeit inefficient way to generate all of the images. 
        Effective enough for the intended use case.

        NOTE: from(@sowhelmed): Problems with this code: 
            1.) Gunicorn timeout will kill long running calls.
            2.) Single CPU used for CPU bound image generation.
            3.) Repeated calls likely result in a denial of service
        '''
        try:
            logger.info('generate word cloud images')
            for pub in self._data_storage.publications():
                # Get frequencies for the top 5000 words
                freqs = self._data_storage.frequencies(pub.name, 5000)
                # Get the bytes for the image
                ibytes = generate_word_cloud(freqs)
                # Save to the blob storage in the given bucket
                self._blob_storage.save(pub.name, self._bucket_name, ibytes)
        except:
            logger.exception('error generating wordclouds')
            raise falcon.HTTPServiceUnavailable(
                'Service Outage', 'word cloud image generation unavailable', retry_after=30)

        # Created!
        resp.status = falcon.HTTP_201


def _create_app(data_storage, blob_storage, blob_bucket_name, allowed_origin='*') -> falcon.API:
    app = falcon.API(
        middleware=[
            CORSComponent(origin=allowed_origin),
        ]
    )
    pubs = PublicationsResource(data_storage, blob_bucket_name)
    freq = FrequenciesResource(data_storage)
    wrdc = WordCloudResource(blob_storage, data_storage, blob_bucket_name)

    app.add_route('/publications', pubs)
    app.add_route('/frequencies/{pub}', freq)
    app.add_route('/images', wrdc)

    return app


def create_app():
    ''' Create an instance of falcon.API and configure the routes.

    By default, NoOp Blob &  Data storage options are used. 
    Use environment variables to use real storage options.
    '''
    if os.environ.get('data_storage') == 'firestore':
        data_storage = DataStorage(client=get_client('db'))
    else:
        data_storage = NoOpDataStorage()

    if os.environ.get('blob_storage') == 'cloudstorage':
        blob_storage = BlobStorage(client=get_client('blob'))
    else:
        blob_storage = NoOpBlobStorage()

    blob_bucket_name = os.environ.get('blob_storage_bucket', 'fake')
    allowed_origin = os.environ.get('allowed_origin', '*')

    return _create_app(data_storage, blob_storage, blob_bucket_name, allowed_origin)


def simple_app(environ, start_response):
    """Simplest possible application object"""
    breakpoint()
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [b'hey!']
