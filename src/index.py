import csv
import config
from WebScore import WebScore
from typing import List, Tuple
import analyzer

def init():
    (urls, keywords) = read_input(config.file_input)
    scores = analyzer.analyze(urls, keywords)
    write_csv(config.csv_output, keywords, scores)

def read_input(file: str) -> Tuple[List[str], List[str]]:
    urls = None
    with open(file) as file:
        urls = file.readlines()
        urls = [line.rstrip() for line in urls]

    keywords = list(set([word.lower() for word in urls.pop(0).split() if word]))
    return (urls, keywords)


def write_csv(file: str, keywords: List[str], scores: List[WebScore]):
    columns = ['url', 'total_top', 'total_sum'] + [term + '_top' for term in keywords] + [term + '_sum' for term in keywords] + [term + '_raw' for term in keywords]
    
    with open(file, 'w') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=columns)
        csv_writer.writeheader()

        for score in scores:
            csv_writer.writerow(get_row(score))

def get_row(score: WebScore):
    term_sum = {term+'_sum': sum(score.scores[term].values()) for term in score.scores.keys()}
    term_top = {term+'_top': next(iter(score.scores[term].values())) for term in score.scores.keys()}
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

init()