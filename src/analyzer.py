import config
from WebScore import WebScore
import requests
import numpy as np
from typing import Dict, List
from bs4 import BeautifulSoup
from gensim.models.keyedvectors import KeyedVectors
from gensim.parsing.preprocessing import preprocess_string
from urllib.parse import urlparse, urljoin
#from gensim.scripts.glove2word2vec import glove2word2vec
#glove2word2vec(config.model_path, config.model_path+'.gensim')

model = KeyedVectors.load_word2vec_format(config.model_path)

def vector(word: str):
    try:
        return model[word]
    except KeyError:
        return None
    
class Score:
    def __init__(self, term: str, max: int = 10):
        self.term = term
        self.vector = vector(term)
        self.words: list[tuple[str, float]] =  []
        self.max = max
    
    def score(self, word: str) -> bool:
        vec = vector(word)
        if vec is None or self.vector is None: return False

        product: float = np.dot(self.vector, vec) / (np.linalg.norm(self.vector) * np.linalg.norm(vec))
        for i in range(len(self.words)):
            if product > self.words[i][1]:
                self.words.insert(i, (word, product))
                if len(self.words) > self.max: self.words.pop()
                return True
        
        if len(self.words) < self.max:
            self.words.append((word, product))
            return True
        
        return False
    
    def map_dic(self) -> Dict[str, float]:
        return {word[0]: word[1] for word in self.words}

def analyze(urls: List[str], terms: List[str]) -> List[WebScore]:
    pages: list[WebScore] = []
    
    for parent_url in urls:
        index = 0
        child_url = None
        child_urls: list = None
        error = False
        results: dict[str, Score] = {score.term : score for score in [ Score(term) for term in terms ] if score.vector is not None}#the model shoul be loaded
        while child_urls is None or index <= len(child_urls):
            base_url = child_url if child_url else parent_url
            body = None

            try:
                r = requests.get(base_url, headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0',
                })

                if (r.status_code < 200 or r.status_code >=300):
                    if child_urls is None:
                        error = True
                        break
                    elif index < len(child_urls):
                        child_url = child_urls[index]
                    
                    index += 1
                    continue

                soup = BeautifulSoup(r.text, 'html.parser')
                body = soup.find('body').text
            except:
                if child_urls is None:
                    error = True
                    break
                if index < len(child_urls):
                    child_url = child_urls[index]

                index += 1
                continue

            for word in set(preprocess_string(body)):
                for term in terms:
                    results[term].score(word)

            if child_urls is None:
                child_urls = filter_urls(base_url, [link.get('href') for link in soup.findAll('a')])

            if index < len(child_urls):
                child_url = child_urls[index]

            index += 1

        if (not error):
            pages.append(WebScore(parent_url, { term : results[term].map_dic() for term in terms }))
    return pages      

def filter_urls(base_url: str, urls: List[str]):
    master_url = urlparse(base_url)

    urls_v1 = [urlparse(urljoin(base_url, url)) for url in urls]
    urls_v2 = [url for url in urls_v1 if url.netloc == master_url.netloc and url.path != master_url.path]
    urls_v2 = [url.geturl().replace('#'+url.fragment, '')  if url.fragment else url.geturl() for url in urls_v2]
    urls_v4 = list(set([url for url in urls_v2]))

    return urls_v4
