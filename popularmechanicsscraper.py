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
from bs4 import Tag, NavigableString
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
import article
import time
import pickle
import newsscraper


class PopularMechanicsScraper(newsscraper.NewsScraper):

    URL = u"http://www.popularmechanics.com/science/"
    WEBSITE_NAME = u"PopularMechanics"
    WEBSITE_LINK_BASE = u"https://www.popularmechanics.com"
    ELEMENT_CLASS_NAME = ("div", "landing-feed--story-inner")    
    ELEMENT_ID = ('', '')
    ARTICLE_TITLE_CLASS_NAME = ("a", "landing-feed--story-title") 
    ARTICLE_TIME_CLASS_NAME = ("time", '')   
    ARTICLE_DESCRIPTION_CLASS_NAME = ("span", "abstract-text")    
    ARTICLE_IMG_AND_LINK_CLASS_NAME = ("div", "landing-feed--story-image") 
    ARTICLE_IMG_CLASS_NAME = ("img", "swap-image", )   
    ARTICLE_LINK_CLASS_NAME = ("a", "link story-image--link")   
    ARTICLE_LABEL_CLASS_NAME = ("a", "landing-feed--story-section-name")   
    ARTICLE_POPULARITY_CLASS_NAME = ("span", "share-count")
    DEFAULT_ARTICLE_LABEL = u"Science"
    LOAD_MORE_BUTTON_ID = "load-more"
    LOADING_WAIT_TIME = 5
    OVERLAY_AD_ID = ("bouncex_el_3", "bouncex_el_17")  
    DRIVER_IMPLICIT_WAIT_TIME = 5
    CHROME_DRIVER_PATH = "C:\Chromedriver\chromedriver.exe"
    LOAD_MORE_NUMBER = 30

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

    def open_new_session(self, url):
        self.timeSinceBeginning = time.time()
        chop = webdriver.ChromeOptions()
        chop.add_extension('adblockpluschrome-1.13.2.1767.crx')
        self.driver = webdriver.Chrome(executable_path=self.CHROME_DRIVER_PATH, chrome_options=chop)
        self.driver.get(url)
        if self.print_feedback:
            print "Time elapsed in opening session:", time.time() - self.timeSinceBeginning

    def get_postings(self, url):
        """
        Indirectly recursive method to retrieve new article postings from website
        Calls visit_next_page() to collect more articles until it reaches an article published before date_limit
        :return: list of Article objects
        """

        self.open_new_session(self.URL)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        # Popular Mechanics site usually dynamically loads new results ONCE. Then, the 'LOAD MORE' button must be clicked.

        for i in range(self.LOAD_MORE_NUMBER):

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

            try:
                load_more_button = self.driver.find_element_by_id(self.LOAD_MORE_BUTTON_ID)
                self.driver.execute_script("return arguments[0].scrollIntoView(true);", load_more_button)
                load_more_button.click()

            except NoSuchElementException:
                break

            except ElementNotVisibleException:
                try:
                    overlay_ad = self.driver.find_element_by_id(self.OVERLAY_AD_ID[0])
                    overlay_ad.click()
                except WebDriverException:
                    try:
                        overlay_ad = self.driver.find_element_by_id(self.OVERLAY_AD_ID[1])
                        overlay_ad.click()
                    except WebDriverException:
                        pass
                else:
                    print("Closed Ad overlay")

            except WebDriverException:
                # There might be an Ad overlay, or we reached the bottom, or it's still loading
                print("breaking")
                break

            else:
                try:
                    WebDriverWait(self.driver, self.LOADING_WAIT_TIME).until(
                        ec.presence_of_element_located((By.ID, self.LOAD_MORE_BUTTON_ID))
                    )
                except TimeoutException:
                    print "Load More button could not be found!\nBreaking from while loop..."
                    break

            time.sleep(1.5)  # Allow loading

        soup = BeautifulSoup(unicode(self.driver.page_source), "lxml")  

        postings = None

        if not(self.ELEMENT_ID is None and self.ELEMENT_CLASS_NAME is None):

            if self.ELEMENT_CLASS_NAME is not None:
                postings = soup.find_all(self.ELEMENT_CLASS_NAME[0], class_=self.ELEMENT_CLASS_NAME[1])

            elif self.ELEMENT_ID is not None:
                postings = soup.find_all(self.ELEMENT_ID[0], id=self.ELEMENT_ID[1])

        print(len(postings))

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

                time_info = post.find(self.ARTICLE_TIME_CLASS_NAME[0])

                print(time_info)

                if time_info is None:
                    continue

                if time_info is not None:
                    # For example: '2017-04-13T08:00:00-0400'  --> '2017-04-13T08:00'
                    date_time = unicode(time_info.get('datetime')).strip()[:-8]
                    # datetime.datetime.strptime(date_time, '%Y-%m-%dT%H:%M')
                    dat, tim = date_time.split('T')
                    yr, mon, dy = map(int, dat.split('-'))
                    hr, mn = map(int, tim.split(':'))
                    a.date_time = datetime(yr, mon, dy, hr, mn)

                    a.time_published = unicode(time_info.text).strip()

                    print (a.date_time, type(a.date_time))

                    if isinstance(a.date_time, datetime) and not self.check_date(a.date_time):
                        break

                a.title = unicode(post.find(self.ARTICLE_TITLE_CLASS_NAME[0],
                                                    class_=self.ARTICLE_TITLE_CLASS_NAME[1]).text).strip()

                a.description = unicode(post.find(self.ARTICLE_DESCRIPTION_CLASS_NAME[0],
                                                    class_=self.ARTICLE_DESCRIPTION_CLASS_NAME[1]).text).strip()

                img_and_link = post.find(self.ARTICLE_IMG_AND_LINK_CLASS_NAME[0], self.ARTICLE_IMG_AND_LINK_CLASS_NAME[1])

                assert isinstance(img_and_link, Tag)

                a.link = self.WEBSITE_LINK_BASE + unicode(img_and_link.find(self.ARTICLE_LINK_CLASS_NAME[0],
                                                    class_=self.ARTICLE_LINK_CLASS_NAME[1]).get('href')).strip()

                a.img_link = unicode(img_and_link.find(self.ARTICLE_IMG_CLASS_NAME[0],
                                                    class_=self.ARTICLE_IMG_CLASS_NAME[1]).get('src'))

                if not a.img_link or a.img_link == "None":
                    a.img_link = unicode(img_and_link.find(self.ARTICLE_IMG_CLASS_NAME[0],
                                                    class_=self.ARTICLE_IMG_CLASS_NAME[1]).get('data-src'))
                if not a.img_link:
                    a.img_link = a.IMAGE_NOT_FOUND_LINK

                a.label = post.find(self.ARTICLE_LABEL_CLASS_NAME[0],
                                                    class_=self.ARTICLE_LABEL_CLASS_NAME[1])
                # Some articles do not have a label
                if a.label is not None:
                    a.label = unicode(a.label.text).strip()
                else:
                    a.label = self.DEFAULT_ARTICLE_LABEL

                articles.append(a)

            except AttributeError:  # 'NoneType' object has no attribute 'text', etc.
                pass

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

    def wait_for_results_loaded(self):
        try:
            # wait until page is loaded using specific class name of text boxes on indeed
            WebDriverWait(self.driver, self.DRIVER_IMPLICIT_WAIT_TIME).until(
                ec.presence_of_element_located((By.CLASS_NAME, self.VISIBLE_ELEMENT_CLASS_CHECK))
            )
        except TimeoutException as e:
            print "Could not find '{}' as element class name".format(self.VISIBLE_ELEMENT_CLASS_CHECK)
            raise e

    def closeSession(self):
        try:
            self.driver.close()
            self.driver.quit()
        except WebDriverException:
            pass
        else:
            if self.print_feedback:
                print("\nChromedriver closed successfully.\n")
        finally:
            self.driver.quit()

    def collect_popularity(self, art):
        assert isinstance(art, article.Article)
        try:
            # Requests cannot get the element, it seems to be dynamically loaded by front-end JavaScript
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

        if 'k' in pop:      # E.g. 27.8k
            pop = float(pop[:-1])*1000

        return int(pop)

    def parse_articles(self, lst_of_articles):
        time_avg = []
        for i, art in enumerate(lst_of_articles):
            assert isinstance(art, article.Article)
            if "Read More" in art.description[-len("Read More"):]:
                art.description = art.description[:-len("Read More")]

            t = time.time()
            art.popularity = self.collect_popularity(art)
            print("{} of {} articles collected".format(i+1, len(lst_of_articles)))
            t2 = time.time()-t
            time_avg.append(t2)

            if not(i % 10):     # Every ten seconds, print estimated time remaining
                avg = reduce(lambda x, y: x+y, time_avg)/len(time_avg)
                print("Average popularity collection time: {:.5f}s".format(avg))
                print("Estimated time remaining: {:.3f}s".format(
                       avg * (len(lst_of_articles)-i-1))
                )

        # Scale popularity values as number of shares per day since publication date
        today = datetime.today()

        for art in lst_of_articles:

            if not art.popularity:
                continue

            assert isinstance(art.date_time, datetime)

            time_delta = today - art.date_time

            seconds_in_a_day = 86400.0

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
            self.save_data(list_of_articles, "pop_mech_articles.dat")

        return list_of_articles


def main():
    ts = PopularMechanicsScraper()
    artcls = ts.main(write_file=True)


