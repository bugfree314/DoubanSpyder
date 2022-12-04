import DoubanSpider_utils as dbutil


class DoubanScrapy:
    global _proxy
    _proxy = dbutil._gen_proxies()

    def __init__(self) -> None:
        self.book = self._Book()
        self.movie = self._Movie()
        self.tv = self._Tv()
        self.user = self._User()

    class _Book:
        @property
        def tags(self) -> list:
            return dbutil._get_popular_book_tags(_proxy)

        @property
        def top(self) -> list:
            return dbutil._get_top_books(_proxy)

        @property
        def newest(self) -> list:
            book_list, pages = dbutil._get_new_books_list(proxy=_proxy)
            for n in range(2, pages+1):
                book_list += dbutil._get_new_books_list(
                    page=n, proxy=_proxy)[0]
            return book_list

        def search(self, words: str = '', count: int = 15) -> dict:
            d = {}
            for p in range(dbutil.math.ceil(count/15)):
                d.update(dbutil._search_douban(keywords=words,
                         start=p*15, TYPE='book', proxy=_proxy))
            return d

        def search_by_tag(self, tag: str, sortby: str = 'T') -> list:
            """
            sortby: 'T' - Total/comprehensive
                    'R' - Release date
                    'S' - Score
            """
            return dbutil._search_book_by_tag(tag=tag, sortby=sortby, proxy=_proxy)

        def parse(self, id: str) -> dict:
            return dbutil._parse_book(id, _proxy)

        def comments(self, bookid: str) -> dict:
            return dbutil._get_comments(bookid, 'book', _proxy)

        def reviews_id(self, bookid: str) -> list:
            return dbutil._get_review_id_list(bookid, 'book', _proxy)

        def review(self, reviewid: str) -> dict:
            return dbutil._get_review(reviewid, 'book', _proxy)

    class _Movie:
        @property
        def newest(self) -> list:
            return dbutil._get_top_new_movies(_proxy)

        @property
        def top(self) -> list:
            return dbutil._get_top_movies(_proxy)

        @property
        def tags(self) -> dict:
            return dbutil._get_movie_tags(TYPE='movie', proxy=_proxy)

        def search(self, words: str = '', count: int = 15) -> dict:
            d = {}
            for p in range(dbutil.math.ceil(count/15)):
                d.update(dbutil._search_douban(keywords=words,
                         start=p*15, TYPE='movie', proxy=_proxy))
            return d

        def search_by_tag(self, count: int = 20, sortby='null', **tag) -> list:
            """
            sortby: 'null'  comprehensive
            'T' hoT
            'R' Release date
            'S' Sort
            tag: area,age,type from property: tags
            """
            return dbutil._get_movies_by_tag(TYPE='movie', start=1, count=count, sort=sortby, proxy=_proxy, **tag)

        def parse(self, id: str) -> dict:
            return dbutil._parse_movie(id, _proxy)

        def comments(self, movieid: str) -> dict:
            return dbutil._get_comments(movieid, 'movie', _proxy)

        def reviews_id(self, movieid: str) -> list:
            return dbutil._get_review_id_list(movieid, 'movie', _proxy)

        def review(self, reviewid: str) -> dict:
            return dbutil._get_review(reviewid, 'movie', _proxy)

    class _Tv(_Movie):
        @property
        def tags(self) -> dict:
            return dbutil._get_movie_tags(TYPE='tv', proxy=_proxy)

        def search_by_tag(self, count: int = 20, sortby='null', **tag) -> list:
            """
            sortby: 'null'  comprehensive
            'T' hoT
            'R' Release date
            'S' Sort
            tag: area,age,type,platform from property: tags
            """
            return dbutil._get_movies_by_tag(TYPE='tv', start=1, count=count, sort=sortby, proxy=_proxy, **tag)

    class _User:
        def parse_by_id(self, id: str) -> dict:
            return dbutil._get_user_info(id, proxy=_proxy)


# if __name__ == '__main__':
#     d = DoubanScrapy()
#     with open('./test57345794.txt', 'w+') as fp:
#         fp.write(str(d.movie.search('金玉良缘')))
