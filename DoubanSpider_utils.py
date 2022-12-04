import os
import re
import json
import math
import execjs
import requests
from functools import *
from random import randint
from bs4 import BeautifulSoup

with open('./decrypt.js', 'r') as _fp:
    _js = _fp.read()
    _ctx = execjs.compile(_js)


########################################################


def _js_decrypt(s): return _ctx.call('decrypt', s)


_base_url = 'https://www.douban.com/'
_base_url_book = 'https://book.douban.com/'
_base_url_movie = 'https://movie.douban.com/'
_base_url_user = _base_url+'people/'
# _base_url_group = 'https://www.douban.com/group/'
# _base_url_search = 'https://search.douban.com/'

_recommend_url_base = "https://m.douban.com/rexxar/api/v2/type/recommend/"
_filter_url_base = _recommend_url_base+'filter_tags/'

_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15"
}
########################################################


def _gen_proxies() -> list:
    # total ip in pool: 15
    if 'ip_proxy_pool.json' not in os.listdir():
        os.system('python get_ip_proxies.py')
    with open('./ip_proxy_pool.json', 'r') as fp:
        raw_ip_pool = json.load(fp)
    return [{'http': 'http://'+list(raw_ip_pool['IP'].values())[i]+':'+list(raw_ip_pool['PORT'].values())[i]} for i in range(15)]


def _get_user_info(id: str, proxy: list = None) -> dict:
    r = requests.get(url=_base_url_user+str(id),
                     proxies=proxy[randint(0, 14)], headers=_headers)
    assert r.status_code == 200
    soup = BeautifulSoup(r.text)
    user_basic_info = soup.find('div', class_='basic-info')
    user_info = {
        'id': user_basic_info.find(class_='pl').contents[0].strip(),
        'nick_name': soup.find('div', class_='info').next.next.next.strip(),
        'avatar': user_basic_info.find('img', class_='userface').attrs['src'],
        'join_time': user_basic_info.find(class_='pl').contents[2].strip()[:-2],
        'intro': soup.find('span', id='intro_display').text,
        'mainpage': {
            'review': _base_url_user+str(id)+'/reviews/',
            'book': _base_url_book+'people/'+str(id)+'/',
            'movie': _base_url_movie+'people/'+str(id)+'/'
        }
    }
    return user_info


def _get_new_books_list(subcat: str = '全部', page: int = 1, proxy: list = None) -> tuple:
    """
    tuple:(list,int or None)
    """
    params = {
        "subcat": subcat,
        "p": str(page),
    }
    r = requests.get(url=_base_url_book+'latest',
                     headers=_headers, params=params, proxies=proxy[randint(0, 14)])
    assert r.status_code == 200
    soup = BeautifulSoup(r.text)
    if page == 1:
        if soup.find(class_='paginator'):
            page_count = int(
                soup.find(class_='paginator').findAll('a')[-2].text)
        else:
            page_count = 1
    else:
        page_count = None
    book_tags = soup.findAll('li', class_='media clearfix')
    books_info = [{
        'cover': t.find(class_='media__img').img.attrs['src'],
        'name':t.find(class_='clearfix').text.strip(),
        'id':t.find(class_='clearfix').find('a').attrs['href'].split('/')[-2],
        'info':t.find(class_='subject-abstract').text.strip(),
        'score':t.find(class_='clearfix w250').text.strip()
    } for t in book_tags]
    return books_info, page_count


def _get_top_books(proxy: list = None) -> list:
    books = []
    for p in range(10):
        params = {
            "start": str(p*25),
        }
        r = requests.get(url=_base_url_book+'top250',
                         headers=_headers, params=params, proxies=proxy[randint(0, 14)])
        assert r.status_code == 200
        soup = BeautifulSoup(r.text)
        book_tags = soup.findAll('table')
        books += [{
            'cover': t.find('img').attrs['src'],
            'name':t.find(class_='pl2').text.strip(),
            'id':t.find('td').find('a').attrs['href'].split('/')[-2],
            'info':t.find(class_='pl').text.strip(),
            'score':t.find(class_='star clearfix').text.strip()
        } for t in book_tags]
    return books


def _get_popular_book_tags(proxy: list = None) -> list:
    r = requests.get(url=_base_url_book+'tag', headers=_headers,
                     proxies=proxy[randint(0, 14)])
    assert r.status_code == 200
    soup = BeautifulSoup(r.text)
    tags = soup.find('div', class_='article').findAll('td')
    return [(lambda l:[i.text for i in l])(t.contents) for t in tags]


def _search_book_by_tag(tag: str, sortby: str = 'T', proxy: list = None) -> list:
    """
    sortby: 'T' - Total/comprehensive
            'R' - Release date
            'S' - Score
    """
    r = requests.get(url=_base_url_book+'tag/'+tag,
                     headers=_headers, proxies=proxy[randint(0, 14)], params={'type': sortby})
    if r.status_code == 404:
        return []
    assert r.status_code == 200
    soup = BeautifulSoup(r.text)
    if soup.find('div', class_='paginator'):
        page_count = soup.find('div', class_='paginator').findAll('a')[-2].text
    else:
        page_count = 1
    book_list = []
    for page in range(int(page_count)):
        params = {
            'type': sortby,
            'start': str(page*20)
        }
        r = requests.get(url=_base_url_book+'tag/'+tag,
                         headers=_headers, params=params, proxies=proxy[randint(0, 14)])
        assert r.status_code == 200
        soup = BeautifulSoup(r.text)
        book_tags = soup.findAll('li', class_='subject-item')
        book_list += [{
            'cover': t.find('img').attrs['src'],
            'name':t.find('h2').text.strip(),
            'id':t.find('h2').a.attrs['href'].split('/')[-2],
            'info':t.find(class_='pub').text.strip(),
            'score':t.find('div', class_='star').text.strip()
        } for t in book_tags]
    return book_list


def _get_top_movies(proxy: list = None) -> list:
    movies = []
    for i in range(10):
        params = {
            "start": str(25*i),
            "filter": "null",
        }
        r = requests.get(url=_base_url_movie+'top250',
                         params=params, headers=_headers, proxies=proxy[randint(0, 14)])
        assert r.status_code == 200
        soup = BeautifulSoup(r.text)
        movie_tags = soup.findAll('div', class_='item')
        movies += [{
            'cover': t.find(class_='pic').img.attrs['src'],
            'name':t.find(class_='hd').a.text.strip(),
            'id':t.find(class_='pic').a.attrs['href'].split('/')[-2],
            'info':t.find(class_='bd').p.text.strip(),
            'score':t.find('div', class_='star').text.strip()
        } for t in movie_tags]
    return movies


def _get_top_new_movies(proxy: list = None) -> list:
    r = requests.get(url=_base_url_movie+'chart',
                     headers=_headers, proxies=proxy[randint(0, 14)])
    assert r.status_code == 200
    soup = BeautifulSoup(r.text)
    return [{
        'cover': t.find('a', class_='nbg').img.attrs['src'],
        'name':t.find(class_='pl2').a.text.strip(),
        'id':t.find(class_='pl2').a.attrs['href'].split('/')[-2],
        'info':t.find(class_='pl').text.strip(),
        'score':t.find('div', class_='star').text.strip()
    } for t in soup.findAll('table')]


def _get_movie_tags(TYPE: str = 'movie', proxy: list = None) -> dict:
    """
    type: movie/tv
    """
    assert TYPE == 'movie' or TYPE == 'tv'
    _headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Referer": "https://movie.douban.com/explore"
    }
    r = requests.get(
        url=_filter_url_base.replace('type', TYPE), headers=_headers, proxies=proxy[randint(0, 14)])
    assert r.status_code == 200
    d_age = {'age': json.loads(r.text)['tags'][0]['tags']}
    if TYPE == 'tv':
        d_platform = {'platform': json.loads(r.text)['tags'][1]['tags']}
    r = requests.get(
        url=_recommend_url_base.replace('type', TYPE), headers=_headers, proxies=proxy[randint(0, 14)])
    assert r.status_code == 200
    d_area = {'area': [t['text'] for t in json.loads(
        r.text)['recommend_categories'][1]['data']]}
    d_sort = {
        'sort': [t['text'] for t in json.loads(r.text)['sorts']],
        'short': [t['name'] for t in json.loads(r.text)['sorts']]
    }
    if TYPE == 'movie':
        d_type = {'type': [t['text'] for t in json.loads(
            r.text)['recommend_categories'][0]['data']]}
        return {**d_age, **d_type, **d_area, **d_sort}
    else:
        d_type = {'type': reduce(
            lambda x, y: x+y, [t['tags'] for t in json.loads(r.text)['recommend_categories'][0]['data']])}
        return {**d_age, **d_platform, **d_type, **d_area, **d_sort}


def _get_movies_by_tag(TYPE='movie', start=1, count=20, sort='null', proxy: list = None, **tag) -> list:
    """
    sort: 'null'  comprehensive
          'T' hoT
          'R' Release date
          'S' Sort
    tag: area,age,platform,type
         from get_movie_tags
    """
    url = _recommend_url_base.replace('type', TYPE)
    params = {
        'start': start,
        'count': count,
        'sort': sort,
        'tags': ','.join(tag.values())
    }
    r = requests.get(url, params, proxies=proxy[randint(0, 14)], headers={
                     **_headers, **{"Referer": "https://movie.douban.com/explore"}})
    assert r.status_code == 200
    items = json.loads(r.text)['items']
    return items


def _search_douban(keywords='', start=0, TYPE='book', proxy: list = None) -> dict:
    url = "https://search.douban.com/"+TYPE+"/subject_search"
    params = {
        "search_text": keywords,
        'start': start
    }
    r = requests.get(url, params, headers=_headers,
                     proxies=proxy[randint(0, 14)])
    assert r.status_code == 200
    soup = BeautifulSoup(r.text)
    tag = soup.findAll('script', type='text/javascript')[0]
    pat = re.compile(r'window.__DATA__..*?"(.*?)"')
    encrypt_data = pat.findall(tag.text)[0]
    data = _js_decrypt(encrypt_data)
    return {'total': data['payload']['total'], 'items': data['payload']['items']}


def _parse_book(id: int, proxy: list = None) -> dict:
    url = _base_url_book+'subject/'+str(id)+'/'
    r = requests.get(url, headers=_headers, proxies=proxy[randint(0, 14)])
    assert r.status_code == 200
    soup = BeautifulSoup(r.text)

    book_title = soup.find('span', property='v:itemreviewed').text
    tag_main = soup.find('div', class_='article')
    book_cover = tag_main.find('div', id='mainpic').a.img.attrs['src']

    tag_info = soup.find('div', class_='article').find('div', id='info')
    info_list_tmp = [i.strip()
                     for i in tag_info.text.split('\n') if not i.strip() == '']
    pat_info = re.compile(r'.*?:\Z')
    book_info = {}
    i = 0
    while i < len(info_list_tmp):
        if pat_info.fullmatch(info_list_tmp[i]):
            book_info.update(
                {info_list_tmp[i].replace(':', ''): info_list_tmp[i+1]})
            i += 2
        else:
            p_colon = info_list_tmp[i].find(':')
            book_info.update(
                {info_list_tmp[i][:p_colon]: info_list_tmp[i][p_colon+1:].strip()})
            i += 1

    book_score_tag = tag_main.find('div', class_='rating_wrap clearbox')
    if book_score_tag.find('div', class_='rating_sum').span.a.text == '评价人数不足':
        book_score = {}
    else:
        book_score = {
            'score': book_score_tag.find('strong', property='v:average').text.strip(),
            'num': book_score_tag.find('div', class_='rating_sum').text.strip(),
            'dist': [i.text for i in book_score_tag.findAll('span', class_='rating_per')]
        }

    tag_related_info = tag_main.find('div', class_='related_info')
    if tag_related_info.find('div', id='link-report'):
        tag_book_intro = tag_related_info.find('div', id='link-report')
        if tag_book_intro.find('span', class_='all hidden'):
            book_intro = tag_book_intro.find('span', class_='all hidden').find(
                'div', class_='intro').text.strip()
        else:
            book_intro = tag_book_intro.find(
                'div', class_='intro').text.strip()
    else:
        book_intro = ''

    if tag_related_info.find('div', class_='indent', id=None):
        tag_author_intro = tag_related_info.find(
            'div', class_='indent', id=None)
        if tag_author_intro.find('span', class_='all hidden'):
            author_intro = tag_author_intro.find('span', class_='all hidden').find(
                'div', class_='intro').text.strip()
        else:
            author_intro = tag_author_intro.find(
                'div', class_='intro').text.strip()
    else:
        author_intro = ''

    if tag_main.find('div', id='dir_'+str(id)+'_full'):
        book_menu = tag_main.find(
            'div', id='dir_'+str(id)+'_full').text.replace('· · · · · ·     (收起)', '')
    else:
        book_menu = ''

    if tag_related_info.find('div', id='db-rec-section', class_='knnlike'):
        tag_recommend = tag_related_info.find('div', id='db-rec-section', class_='knnlike').find(
            'div', class_='content clearfix').findAll('dl', class_='')
        book_recommend = [i.dd.text.strip() for i in tag_recommend]
    else:
        book_recommend = ''

    return {
        'title': book_title,
        'cover': book_cover,
        'info': book_info,
        'score': book_score,
        'intro': book_intro,
        'author': author_intro,
        'menu': book_menu,
        'recommend': book_recommend
    }


def _get_comments(id: int, TYPE='book', proxy: list = None) -> dict:
    """
    get only 100 comments because of login required for getting more
    """
    r = requests.get({'book': _base_url_book, 'movie': _base_url_movie}[
                     TYPE]+'subject/'+str(id), headers=_headers, proxies=proxy[randint(0, 14)])
    assert r.status_code == 200
    soup = BeautifulSoup(r.text)
    if soup.find('div', class_='mod-hd').find('span', class_='pl'):
        total = int(soup.find('div', class_='mod-hd').find('span',
                    class_='pl').a.text[3:-1].strip())
    else:
        return {
            'total': 0,
            'comments': []
        }
    comments = []
    url = {'book': _base_url_book, 'movie': _base_url_movie}[
        TYPE]+'subject/'+str(id)+'/comments/'

    def test_stars(t):
        if t.find('span', class_='comment-info').find('span', class_='rating'):
            return t.find('span', class_='comment-info').find('span', class_='rating').attrs['title']
        else:
            return ''

    for page in range(5):
        params = {
            "start": str(20*page),
            "limit": "20",
            "status": "P",
            "sort": "score",
        }
        if TYPE == 'movie':
            params['sort'] = 'new_score'
        r = requests.get(url=url, headers=_headers,
                         params=params, proxies=proxy[randint(0, 14)])
        assert r.status_code == 200
        soup = BeautifulSoup(r.text)

        if soup.find(class_='comment-item'):
            pat = re.compile(r'.*/(.*?)/\Z')
            comments += [
                {
                    'avatar': i.find('div', class_='avatar').a.img.attrs['src'],
                    'nickname':i.find('div', class_='avatar').a.attrs['title'],
                    'id':pat.findall(i.find('div', class_='avatar').a.attrs['href'])[0],
                    'stars':test_stars(i),
                    'time':i.find(class_='comment-time').text.strip(),
                    'vote':i.find('span', class_='comment-vote').span.text.strip(),
                    'content':i.find('p', class_='comment-content').text.strip()
                }
                for i in soup.findAll(class_='comment-item')]
        else:
            break
    return {
        'total': total,
        'comments': comments
    }


def _get_review_id_list(id: int, TYPE: str = 'book', proxy: list = None) -> list:
    url = {'book': _base_url_book, 'movie': _base_url_movie}[
        TYPE] + 'subject/'+str(id)+'/reviews/'
    r = requests.get(url, headers=_headers, proxies=proxy[randint(0, 14)])
    assert r.status_code == 200
    pat = re.compile(r'.*\((\d+)\)')
    total = int(pat.findall(BeautifulSoup(
        r.text).find('div', id='content').h1.text)[0])
    if total == 0:
        return []
    id_list = []
    for page in range(math.ceil(total/20)):
        param = {'start': str(page*20)}
        r = requests.get(url, params=param, headers=_headers,
                         proxies=proxy[randint(0, 14)])
        assert r.status_code == 200
        soup = BeautifulSoup(r.text)
        tag_reviews = soup.find(
            'div', class_='review-list').findAll('div', attrs={'data-cid': True})
        id_list += [t.attrs['data-cid'] for t in tag_reviews]
    return id_list


def _get_review(id: int, TYPE: str = 'book', proxy: list = None) -> dict:
    url = {'book': _base_url_book, 'movie': _base_url_movie}[
        TYPE]+'review/'+str(id)+'/'
    r = requests.get(url, headers=_headers, proxies=proxy[randint(0, 14)])
    assert r.status_code == 200
    soup = BeautifulSoup(r.text)
    tag_main = soup.find('div', class_='article')
    title = tag_main.find('h1').text.strip()
    tag_header = tag_main.find('script')
    header = json.loads(tag_header.text.strip())

    if TYPE == 'book':
        content = tag_main.find(
            'div', class_='review-content clearfix').text.strip()
    else:
        tag_content = tag_main.find(
            'div', class_='review-content clearfix')
        content = ''.join([t.text.strip() for t in tag_content.findAll('p')])

    reply = {
        'agree': int(tag_main.find('div', class_='main-panel-useful').find(class_='useful_count').text.strip()[3:]),
        'disagree': int(tag_main.find('div', class_='main-panel-useful').find(class_='useless_count').text.strip()[3])
    }
    return {
        'info': header,
        'title': title,
        'content': content,
        'reply': reply
    }


def _parse_movie(id: int, proxy: list = None) -> dict:
    url = _base_url_movie+'/subject/'+str(id)
    r = requests.get(url, headers=_headers, proxies=proxy[randint(0, 14)])
    assert r.status_code == 200
    soup = BeautifulSoup(r.text)
    tag_main = soup.find('div', id='content')
    title = tag_main.find('span', property='v:itemreviewed').text.strip()
    cover = tag_main.find('div', id='mainpic').a.img.attrs['src']
    info = json.loads(soup.find(
        'script', type='application/ld+json').text.strip().replace('\n', ' '))

    if info['aggregateRating']['ratingCount'] == '0':
        score = {}
    else:
        book_score_tag = tag_main.find('div', class_='rating_wrap clearbox')
        score = {
            'score': book_score_tag.find('strong', property='v:average').text.strip(),
            'num': book_score_tag.find('div', class_='rating_sum').text.strip(),
            'dist': [i.text.strip() for i in book_score_tag.findAll('span', class_='rating_per')]
        }

    tag_intro = tag_main.find('div', class_='related-info')
    if tag_intro.find('span', class_='all hidden'):
        intro = tag_intro.find('span', class_='all hidden').text.strip()
    elif tag_intro.find('span', property='v:summary'):
        intro = tag_intro.find('span', property='v:summary').text.strip()
    else:
        intro = ''

    url_awards = _base_url_movie+'subject/'+str(id)+'/awards/'
    r_awards = requests.get(url_awards, headers=_headers,
                            proxies=proxy[randint(0, 14)])
    assert r_awards.status_code == 200
    tag_awards = BeautifulSoup(r_awards.text).find(
        'div', class_='article').findAll('div', class_='awards')
    awards = [{
        'title': t.div.text.strip(),
        'awards': [i.text.strip() for i in t.findAll('ul', class_='award')]
    }for t in tag_awards]

    if tag_main.find('div', class_='recommendations-bd'):
        tag_rec = tag_main.find(
            'div', class_='recommendations-bd').findAll('dl')
        recommend = [t.dd.text.strip() for t in tag_rec]
    else:
        recommend = []

    return {
        'title': title,
        'cover': cover,
        'info': info,
        'score': score,
        'intro': intro,
        'awards': awards,
        'recommend': recommend
    }
