import asyncio
import csv
import config
import crawler
from WebScore import WebScore
from typing import List, Tuple

async def main():
    (urls, keywords) = read_input(config.file_input)
    await crawler.crawl(urls)

def read_input(file: str) -> Tuple[List[str], List[str]]:
    urls = None
    with open(file) as file:
        urls = file.readlines()
        urls = [line.rstrip() for line in urls]

    keywords = list(set([word.lower() for word in urls.pop(0).split() if word]))
    return (urls, keywords)

if __name__ == '__main__':
    asyncio.run(main())
