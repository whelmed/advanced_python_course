import zipfile
import os
from urllib.request import urlretrieve
# The data for this app comes from
# https://components.one/datasets/all-the-news-2-news-articles-dataset/

data_uri = "https://www.dropbox.com/s/cn2utnr5ipathhh/all-the-news-2-1.zip?dl=1"
zippath = "/tmp/all-the-news-2-1.zip"
extractdir = "/tmp/all_the_news/"


def download_and_extract():
    print('downloading file. this will take a while.')
    urlretrieve(data_uri, zippath)
    print('extracting file.')
    if not os.path.exists(extractdir):
        os.mkdir(extractdir)

    with zipfile.ZipFile(zippath, 'r') as zf:
        zf.extractall(extractdir)
