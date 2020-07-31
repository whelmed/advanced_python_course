###############################################################################
'''
    This module enables us to process text using natural language processing
    to extract known entities - i.e. nouns (person, place, thing,)

    It uses Spacy to extract entites based on a pre-built model.
    The model must be downloaded before using spacy. 

'''
###############################################################################
from collections import Counter
from typing import Dict

import spacy

from .debugging import app_logger as log
from .models import Post, ProcessedPost


class DataProcessor():

    def __init__(self):
        log.info('spacy model loading')
        self.nlp = spacy.load("en_core_web_sm")
        log.info('spacy model loaded')
        self.skip = ['CARDINAL', 'MONEY', 'ORDINAL', 'DATE', 'TIME']

    def entities(self, doc) -> Counter:
        t = [e.text.lower() for e in doc.ents if e.label_ not in self.skip]
        return Counter(t)

    def process(self, text: str) -> Dict:
        return {'entities': self.entities(self.nlp(text))}

    def process_message(self, post) -> ProcessedPost:
        return ProcessedPost(
            **{
                **post,
                **self.process(post['content'])
            }
        )
