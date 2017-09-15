# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 15:42:34 2017

@author: Alexander Hamme
"""

from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException, ElementNotVisibleException
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString
from datetime import datetime
from lxml import html
import requests
import article
import time
import newsscraper


class EngadgetScraper(newsscraper.NewsScraper):

    URL = u"https://www.engadget.com/topics/science"
    WEBSITE_NAME = u"Engadget"
    WEBSITE_LINK_BASE = u"https://www.engadget.com"
    ELEMENT_CLASS_NAME = ("article", "o-hit")    
    ELEMENT_ID = ('', '')
    ARTICLE_TITLE_CLASS_NAME = ("div", "th-title")  
    ARTICLE_TIME_CLASS_NAME = ("span", " hide@tp")   
    ARTICLE_DESCRIPTION_CLASS_NAME = ("p", "c-gray-3")   
    ARTICLE_IMG_CLASS_NAME = ("img", "stretch-img", "stretch-img lazy")
    ARTICLE_FEATURE_IMG_CLASS_NAME = ("img", "stretch-img")
    ARTICLE_LINK_CLASS_NAME = ("a", "o-hit__link")   
    ARTICLE_LABEL_CLASS_NAME = ("a", "th-topic")   
    DEFAULT_ARTICLE_LABEL = u"Science"

    ARTICLE_POPULARITY_CLASS_NAME = ('meta', 'swifttype', 'popularity')
    ARTICLE_POPULARITY_XPATH = r'/html/head//meta[@name="popularity"]'

    DRIVER_IMPLICIT_WAIT_TIME = 5
    LOADING_WAIT_TIME = 5
    CHROME_DRIVER_PATH = r"C:\Chromedriver\chromedriver.exe"

    def __init__(self, date=None):
        """
        :param date: datetime object
        collect only articles published on or after given date
        """
        newsscraper.NewsScraper.__init__(self)
        self.list_of_articles = None
        self.page_number = 1  # Will be increased to 2 before the first call of visit_next_page()
        self.print_feedback = False

        self.driver = None

        if date is not None:
            if isinstance(date, datetime):
                self.date_limit = date
            elif isinstance(date, tuple):
                self.date_limit = datetime(*date)

    def open_new_session(self):
        chop = webdriver.ChromeOptions()
        chop.add_extension('adblockpluschrome-1.13.2.1767.crx')
        self.driver = webdriver.Chrome(executable_path=self.CHROME_DRIVER_PATH, chrome_options=chop)

    def get_postings(self, url):
        """
        Indirectly recursive method to retrieve new article postings from website
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

        soup = BeautifulSoup(str(page.content), "lxml")  # html.parser
        postings = None

        if not(self.ELEMENT_ID is None and self.ELEMENT_CLASS_NAME is None):

            if self.ELEMENT_CLASS_NAME is not None:
                postings = soup.find_all(self.ELEMENT_CLASS_NAME[0], class_=self.ELEMENT_CLASS_NAME[1])

            elif self.ELEMENT_ID is not None:
                postings = soup.find_all(self.ELEMENT_ID[0], id=self.ELEMENT_ID[1])

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

                a.time_published = unicode(post.find(self.ARTICLE_TIME_CLASS_NAME[0],
                                                     class_=self.ARTICLE_TIME_CLASS_NAME[1]).text).strip()
                if "." in a.time_published:
                    a.date_time = self.parse_article_date(a.time_published)
                else:
                    a.date_time = self.get_date_limit(lim=a.time_published)

                if not self.check_date(a.date_time):
                    break

                a.title = unicode(post.find(self.ARTICLE_TITLE_CLASS_NAME[0],
                                                    class_=self.ARTICLE_TITLE_CLASS_NAME[1]).text).strip()
                a.description = unicode(post.find(self.ARTICLE_DESCRIPTION_CLASS_NAME[0],
                                                    class_=self.ARTICLE_DESCRIPTION_CLASS_NAME[1]).text).strip()

                a.link = self.WEBSITE_LINK_BASE + unicode(post.find(self.ARTICLE_LINK_CLASS_NAME[0],
                                                    class_=self.ARTICLE_LINK_CLASS_NAME[1]).get('href')).strip()

                a.label = post.find(self.ARTICLE_LABEL_CLASS_NAME[0],
                                                    class_=self.ARTICLE_LABEL_CLASS_NAME[1])
                # Some articles do not have a label
                if a.label is not None:
                    a.label = unicode(a.label.text).strip()
                else:
                    a.label = self.DEFAULT_ARTICLE_LABEL

                a.img_link = unicode(post.find(self.ARTICLE_IMG_CLASS_NAME[0],
                                                    class_=self.ARTICLE_IMG_CLASS_NAME[1]).get('data-original'))

                if not a.img_link or a.img_link == "None":
                    a.img_link = unicode(post.find(self.ARTICLE_IMG_CLASS_NAME[0],
                                                    class_=self.ARTICLE_IMG_CLASS_NAME[1]).get('src'))
                if a.img_link is None:
                    a.img_link = a.IMAGE_NOT_FOUND_LINK

                articles.append(a)

            except AttributeError:  # 'NoneType' object has no attribute 'text', etc.
                pass

        print "Collected {} articles from {}".format(len(articles), self.WEBSITE_NAME)

        if self.check_date(a.date_time):
            if self.print_feedback:
                print "Article publication of {} less than time limit: <{}>. Continuing to next page...".format(
                    a.date_time, self.date_limit
                )
            self.page_number += 1
            articles += self.visit_next_page()

        print "List of {} articles length: {}".format(self.WEBSITE_NAME, len(articles))

        return articles

    def parse_article_date(self, dt):
        """
        :param dt: string
        :return: datetime object
        """
        if self.print_feedback:
            print "Parsing date: {}".format(dt)
        # Example: "03.04.17"
        mnth, day, yr = map(int, dt.split('.'))
        yr += 2000
        return datetime(yr, mnth, day)

    def check_date(self, dt):
        assert isinstance(dt, datetime)
        return dt > self.date_limit

    def visit_next_page(self):
        """
        This is the agent of the indirect recursion of get_articles().
        Return get_postings() of the next page, which calls get_articles().
        """
        if self.print_feedback:
            print "We must go deeper!"
        return self.get_postings(self.URL + "/page/" + str(self.page_number))

    def collect_popularity(self, art):
        '''
        Collect popularity element using Requests and LXML tree
        '''
        t = time.time()
        assert isinstance(art, article.Article)
        try:
            page = requests.get(art.link, timeout=self.REQUESTS_TIMEOUT_VALUE, stream=True)
        except requests.ConnectionError, requests.ConnectTimeout:
            print "Site could not be reached: <{}>".format(art.link)
            return None

        tree = html.fromstring(page.content)
        popularity = tree.xpath(self.ARTICLE_POPULARITY_XPATH, namespaces={'name': 'popularity'})[0].get('content')

        if ',' in popularity:
            indx = popularity.index(',')
            popularity = popularity[:indx] + popularity[indx+1:]

        try:
            popularity = float(popularity)
        except ValueError:
            return None

        print "Article popularity :{}".format(popularity)
        return popularity

    def collect_popularity_backup(self, art):
        '''
        Backup method using Selenium WebDriver. Far more time costly.
        '''
        assert isinstance(art, article.Article)
        try:
            self.driver.get(art.link)
        except WebDriverException:
            print "Site could not be reached: <{}>".format(art.link)
        else:
            try:
                # wait until page is loaded using specific class name of text boxes on indeed
                WebDriverWait(self.driver, self.DRIVER_IMPLICIT_WAIT_TIME).until(
                    ec.presence_of_element_located((By.CLASS_NAME, self.ARTICLE_POPULARITY_CLASS_NAME[1]))
                )
            except TimeoutException:
                print "Could not find '{}' as element class name".format(self.ARTICLE_POPULARITY_CLASS_NAME)

            soup = BeautifulSoup(unicode(self.driver.page_source), "lxml")

        pop = unicode(soup.find(self.ARTICLE_POPULARITY_CLASS_NAME[0],
                                class_=self.ARTICLE_POPULARITY_CLASS_NAME[1]).text).strip()

        if not pop:
            return None

        if 'k' in pop:
            pop = float(pop[:-1])*1000

        return int(pop)


    def parse_articles(self, lst_of_articles):

        print("Parsing articles and collecting popularity scores")

        for art in lst_of_articles:

            assert isinstance(art, article.Article)
            assert isinstance(art.date_time, datetime)

            if "Read More" in art.description[-len("Read More"):]:
                art.description = art.description[:-len("Read More")]

            art.popularity = self.collect_popularity(art)

            if not art.popularity:
                continue

            today = datetime.today()

            time_delta = today - art.date_time

            seconds_in_a_day = 86400.0
            
            # Scale popularity values as number of shares per day since publication date
            days = float(time_delta.days) + time_delta.seconds / seconds_in_a_day

            art.popularity /= days


    def main(self, write_file=False, save_data=True):

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

        if save_data:
            self.save_data(list_of_articles, "engadget_articles.dat")

        return list_of_articles

def main():
    ts = EngadgetScraper()
    return ts.main()

#if __name__ == "__main__":
#    main()
