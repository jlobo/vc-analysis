from typing import Dict

class WebScore:
    def __init__(self, url: str, scores: Dict[str, Dict[str, float]]):
        self.url = url
        self.scores = scores
