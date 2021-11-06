from io import FileIO
import config
from WebScore import WebScore
import numpy as np
from typing import Dict, List, Tuple
from gensim.models.keyedvectors import KeyedVectors, Word2VecKeyedVectors
from gensim.parsing.preprocessing import preprocess_string
import crawler
import aiohttp
import csv

#from gensim.scripts.glove2word2vec import glove2word2vec
#glove2word2vec(config.model_path, config.model_path+'.gensim')
#raise Exception('I know Python!')


def vector(model: Word2VecKeyedVectors, word: str):
    try:
        if "+" not in word:
            return model[word]
        
        return np.sum([model[wrd] for wrd in word.split('+')] , axis=0)
    except KeyError:
        return None
    
class Score:
    def __init__(self, model: Word2VecKeyedVectors, term: str, max: int = 10):
        self.__model = model
        self.term = term
        self.vector = vector(model, term)
        self.words: list[tuple[str, float]] =  []
        self.max = max
    
    def score(self, word: str) -> bool:
        vec = vector(self.__model, word)
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

async def analyze(urls: List[str], terms: List[str]) -> List[WebScore]:
    urls = filter_urls(urls)
    model: Word2VecKeyedVectors = KeyedVectors.load_word2vec_format(config.model_path, binary=True)
    pages: list[WebScore] = []

    async with aiohttp.ClientSession() as clint:
        (file, writer) = get_writer(config.csv_output, terms)
        with file:
            for parent_url in urls:
                index = 0
                child_url = None
                child_urls: list = None
                error = False
                results: dict[str, Score] = {score.term : score for score in [ Score(model, term) for term in terms ] if score.vector is not None}#the model shoul be loaded
                while child_urls is None or index <= len(child_urls):
                    base_url = child_url if child_url else parent_url
                    
                    (err, body, urls) = await crawler.request_web(clint, base_url)
                    if err:
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
                        child_urls = urls

                    if index < len(child_urls):
                        child_url = child_urls[index]

                    index += 1

                if (not error):
                    score = WebScore(parent_url, { term : results[term].map_dic() for term in terms })
                    writer.writerow(get_row(score))
                    pages.append(score)

        return pages

def get_writer(file: str, keywords: List[str]) -> Tuple[FileIO, csv.DictWriter]:
    columns = ['url', 'total_top', 'total_sum'] + [term + '_top' for term in keywords] + [term + '_sum' for term in keywords] + [term + '_raw' for term in keywords]
    
    csv_file = open(file, 'a')
    csv_writer = csv.DictWriter(csv_file, fieldnames=columns)
    csv_writer.writeheader()
    
    return (csv_file, csv_writer)

def get_row(score: WebScore):
    term_sum = {term+'_sum': sum(score.scores[term].values()) for term in score.scores.keys()}
    term_top = {term+'_top': next(iter(score.scores[term].values())) if score.scores[term] else 0 for term in score.scores.keys()}
    term_raw = {term+'_raw': '|'.join([f'{word}:{score}' for word, score in score.scores[term].items() ])  for term in score.scores.keys()}

    final_dic = {
        "url": score.url,
        "total_top": max(term_sum.values()),
        "total_sum": sum(term_sum.values())
    }

    final_dic.update(term_top)
    final_dic.update(term_sum)
    final_dic.update(term_raw)
    
    return final_dic

def filter_urls(urls: List[str]) -> List[str]:
    with open(config.csv_output) as file:
        reader = csv.reader(file)
        sroted_urls = [row[0] for i, row in enumerate(reader) if i != 0]
        return [ url for url in urls if url not in sroted_urls]
