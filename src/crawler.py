from os.path import exists
import config
import base64
from hashlib import sha256
from urllib.parse import urlparse, urljoin
import aiohttp
import asyncio
import aiofiles
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple

__buffer = 400
__headers = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0' }
__timeout = aiohttp.ClientTimeout(total=4)

async def crawl(urls: str):
    while len(urls) > 0:
        tasks = [asyncio.ensure_future(crawl_web(url)) for url in urls[0:__buffer]]
        del urls[0:__buffer]
        await asyncio.gather(*tasks)
        print(f'<-------- pending:{len(urls)}')

async def crawl_web(url: str) -> Tuple[bool, str, list]:
    async with aiohttp.ClientSession(timeout=__timeout) as clint:
        (err, _, urls) = await request_web(clint, url)
        if err: return

        for child in urls:
            await request_web(clint, child)

async def request_web(client: aiohttp.ClientSession, url: str) -> Tuple[bool, str, list]:
    name = base64.urlsafe_b64encode(sha256(url.encode('utf-8')).digest()).decode('utf-8')
    path = f'{config.web_path}/{name}.html'
    
    err, html = False, ''
    if exists(path):
        async with aiofiles.open(path, mode='r') as f:
            html = await f.read()
            if not html: err = True
    else:
        try:
            url_base = 'http://' + url if not urlparse(url).scheme else url
            async with client.get(url_base, headers=__headers, allow_redirects=True) as res:
                if (res.status < 200 or res.status >= 300):
                    err = True
                    msg = (await res.read()).decode('utf-8')
                    #print(f'--> ERR: {msg}')
                else:
                    html = (await res.read()).decode('utf-8')
        except Exception as e:
            err = True

        async with aiofiles.open(path, mode='w') as f:
            await f.write(html)
    
    if err: return (err, '', [])

    soup = BeautifulSoup(html, 'html.parser')
    child_urls = [link.get('href') for link in soup.findAll('a')]
    return (err, html, filter_urls(url, child_urls))

def filter_urls(base_url: str, urls: List[str]):
    master_url = urlparse(base_url)

    urls_v1 = [urlparse(urljoin(base_url, url)) for url in urls]
    urls_v2 = [url for url in urls_v1 if url.netloc == master_url.netloc and url.path != master_url.path]
    urls_v2 = [url.geturl().replace('#'+url.fragment, '')  if url.fragment else url.geturl() for url in urls_v2]
    urls_v4 = list(set([url for url in urls_v2]))

    return urls_v4
