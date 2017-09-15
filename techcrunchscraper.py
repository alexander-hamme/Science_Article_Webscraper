# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 15:42:34 2017

@author: Alexander Hamme
"""

from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString
from datetime import datetime
import requests
import article
import time
import newsscraper


class TechcrunchScraper(newsscraper.NewsScraper):

    URL = u"https://techcrunch.com/gadgets/"
    WEBSITE_NAME = u"Techcrunch Gadgets"
    ELEMENT_CLASS_NAME = "block-content"
    ELEMENT_ID = ''
    ARTICLE_TITLE_CLASS_NAME = ("h2", "post-title")
    ARTICLE_TIME_CLASS_NAME = ("time", "timestamp", "datetime")
    ARTICLE_DESCRIPTION_CLASS_NAME = ("p", "excerpt")
    ARTICLE_IMG_CLASS_NAME = ("a", "thumb")
    ARTICLE_FEATURE_IMG_CLASS_NAME = ("a", "feature-hero")
    ARTICLE_LINK_CLASS_NAME = ("a", "read-more")
    ARTICLE_LABEL_CLASS_NAME = ("a", "tag")

    def __init__(self, date=None):
        """
        :param date: str
        collect only articles published on or after given date
        """
        newsscraper.NewsScraper.__init__(self)
        self.list_of_articles = None
        self.page_number = 1  # Will increase to 2 before first call of visit_next_page()
        self.print_feedback = False
        if date is not None:
            if isinstance(date, datetime):
                self.date_limit = date
            elif isinstance(date, tuple):
                self.date_limit = datetime(*date)


    def get_postings(self, url):
        """
        Indirectly recursive method to retrieve new article postings from TechCrunch.com
        Calls visit_next_page() to collect more articles until it reaches an article published before date_limit
        :return: list of Article objects
        """
        try:
            page = requests.get(url, timeout=self.REQUESTS_TIMEOUT_VALUE, stream=True)
        except requests.ConnectionError, requests.ConnectTimeout:
            print "Site could not be reached: <{}>".format(url)
            return []
        if self.print_feedback:
            try:
                print "Request sent to {} at {}".format(self.WEBSITE_NAME, page.raw._fp.fp._sock.getpeername()[0])
            except AttributeError:  # '_io.BufferedReader' object has no attribute '_sock'
                print "Request sent to {}".format(self.WEBSITE_NAME)
            finally:
                print "Status code: {}".format(page.status_code)

        soup = BeautifulSoup(str(page.content), "lxml")  
        postings = None

        if not(self.ELEMENT_ID is None and self.ELEMENT_CLASS_NAME is None):

            if self.ELEMENT_CLASS_NAME is not None:
                postings = soup.find_all("div", class_=self.ELEMENT_CLASS_NAME)

            elif self.ELEMENT_ID is not None:
                postings = soup.find_all("div", id=self.ELEMENT_ID)

        if postings is None or len(postings) == 0:
            return []
        else:
            return self.get_articles(postings)

    def get_articles(self, list_of_postings):

        articles = []

        for post in list_of_postings:
            assert isinstance(post, Tag)
            try:
                a = article.Article()
                a.website_name = self.WEBSITE_NAME

                time_info = post.find(self.ARTICLE_TIME_CLASS_NAME[0], class_=self.ARTICLE_TIME_CLASS_NAME[1])
                a.date_time = self.parse_article_date(time_info.get(self.ARTICLE_TIME_CLASS_NAME[2]))

                if not self.check_date(a.date_time):
                    break

                a.time_published = unicode(time_info.text).strip()


                a.title = unicode(post.find(self.ARTICLE_TITLE_CLASS_NAME[0],
                                                            class_=self.ARTICLE_TITLE_CLASS_NAME[1]).text).strip()

                a.description = unicode(post.find(self.ARTICLE_DESCRIPTION_CLASS_NAME[0],
                                                            class_=self.ARTICLE_DESCRIPTION_CLASS_NAME[1]).text).strip()

                a.link = unicode(post.find(self.ARTICLE_LINK_CLASS_NAME[0],
                                                            class_=self.ARTICLE_LINK_CLASS_NAME[1]).get('href')).strip()

                a.label = unicode(post.parent.find(self.ARTICLE_LABEL_CLASS_NAME[0],
                                                            class_=self.ARTICLE_LABEL_CLASS_NAME[1]).text.strip())
                try:
                    a.img_link = unicode(post.span.a.img['data-src']).strip()
                except AttributeError:  # "NoneType object has no attribute 'img'"
                    try:
                        feature_img = post.find(self.ARTICLE_FEATURE_IMG_CLASS_NAME[0],
                                                       class_=self.ARTICLE_FEATURE_IMG_CLASS_NAME[1])
                        a.img_link = unicode(feature_img.img.get('src').strip())
                    except AttributeError:
                        a.img_link = a.IMAGE_NOT_FOUND_LINK

                articles.append(a)

            except AttributeError:
                continue

        print "Collected {} articles from {}".format(len(articles), self.WEBSITE_NAME)

        if self.check_date(a.date_time):
            if self.print_feedback:
                print "Article publication of <{}> less than time limit: <{}>. Continuing to next page...".format(
                    a.date_time, self.date_limit
                )
            self.page_number += 1
            articles += self.visit_next_page()

        print "List of {} articles length: {}".format(self.WEBSITE_NAME, len(articles))
        return articles

    def parse_article_date(self, dt):
        """
        Method to create datetime object from article's string representation of date and time
        :param dt: string
        :return: datetime object
        """
        # Example: "2017-01-25 05:34:58"
        date, tm = str(dt).split(' ')
        yr, mnth, day = map(int, date.split('-'))
        hr, mn, sec = map(int, tm.split(':'))
        return datetime(yr, mnth, day, hr, mn, sec)

    def check_date(self, dt):
        """
        Check if article was published within the date/time limit
        :param dt: datetime object
        :return: boolean
        """
        assert isinstance(dt, datetime)
        return dt > self.date_limit

    def visit_next_page(self):
        """
        This method creates indirect recursion in get_articles().
        :return: get_postings() of the next page, which calls get_articles().
        """
        if self.print_feedback:
            print "We must go deeper!"
        return self.get_postings(self.URL + "/page/" + str(self.page_number))

    def parse_articles(self, lst_of_articles):
        for art in lst_of_articles:
            assert isinstance(art, article.Article)
            if "Read More" in art.description[-len("Read More"):]:
                art.description = art.description[:-len("Read More")]

    def main(self, write_file=True):

        t = time.time()
        list_of_articles = []

        if not self.date_limit:
            self.date_limit = self.get_date_limit()

        if self.print_feedback:
            print "Time limit = {}".format(self.date_limit)

        list_of_articles += self.get_postings(self.URL)

        print "Elapsed time of {} article collection: {}m {}s".format(
            self.WEBSITE_NAME, (time.time() - t) // 60, int(1000*((time.time() - t) % 60))/1000.0
        )

        self.parse_articles(list_of_articles)

        if write_file:
            self.write_to_file(list_of_articles)

        return list_of_articles

def main():
    ts = TechcrunchScraper()
    return ts.main()


