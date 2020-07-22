from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from .debugging import app_logger as log
from .messageq import QueueWrapper, create_queue_manager, register_manager
from .models import Post

# Use an access token to secure the post/enqueue uri
API_KEY_HEADER = APIKeyHeader(name='access_token', auto_error=False)
app = FastAPI()


class Connector:
    '''Connector is used to manage the connection to the input Queue.
    The queue manager requires a call to .connect() to establish a connection.
    By reusing connections we can better manage our networking resources.
    '''

    def __init__(self):
        register_manager('iqueue')
        self.manager = create_queue_manager(50000)
        self.iqueue = None

    def __call__(self):
        '''returns a connected input queue manager or raises an error. '''
        if self.iqueue:
            return self.iqueue

        try:
            self.iqueue = self.manager.iqueue()
            return self.iqueue
        except AssertionError as ae:
            if ae.args == ('server not yet started',):
                try:
                    self.manager.connect()
                except ConnectionRefusedError:
                    raise

                return self()
        except:
            raise


iqueue = Connector()


def check_auth_header(api_key_header: str = Security(API_KEY_HEADER)):
    # https://github.com/tiangolo/fastapi/issues/142
    if api_key_header == 'ijdf8h74nj':
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="invalid API key provided in the header",
    )


@app.post("/post/enqueue", status_code=status.HTTP_201_CREATED)
def create_post(post: Post, queue: QueueWrapper = Depends(iqueue), authenticated: bool = Depends(check_auth_header)):
    try:
        queue.put(post.dict())
    except Exception as ex:
        raise HTTPException(status_code=500)
