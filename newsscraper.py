# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 15:42:34 2017

@author: Alexander Hamme
"""

from datetime import datetime
import calendar
import os
import codecs
import article
import re
import time
import pickle


class NewsScraper:

    ARBITRARY_YEARS_LIMIT = 50
    ARBITRARY_MONTH_LIMIT = 60  # 5 years
    ARBITRARY_WEEKS_LIMIT = 20  # ~<5 months
    ARBITRARY_DAYS_LIMIT = 35  # 5 weeks
    ARBITRARY_HOURS_LIMIT = 120  # 5 days
    ARBITRARY_MINUTES_LIMIT = 300  # 5 hours
    ARBITRARY_MINIMUM_TIME_VALUE = 1
    WEBSITE_BACKGROUND_IMAGE_PATH = "textures/blackmamba.png"
    REQUESTS_TIMEOUT_VALUE = 10  # 10 seconds

    def __init__(self, date=None):
        self.timeSinceBeginning = 0
        self.print_feedback = False
        if date is None:
            self.date_limit = None
        else:
            if isinstance(date, datetime):
                self.date_limit = date
            elif isinstance(date, tuple):
                self.date_limit = datetime(*date)

    def get_date_limit(self, lim=None):
        """
        Optional param: limit - string, pass a phrase such as "17h ago" to be parsed
        :return: datetime object from parse_date_limit()
        """

        if not lim:
            lim = str(raw_input("Enter article publication limit >>>\n(e.g. '1 year ago' or 'Within 3 weeks')")).lower()

        num = [int(s) for s in re.findall(r'\d+', lim)]

        if len(num) != 1:
            
            if "last" in lim or "yesterday" in lim:  # Last-ditch effort
                num = 1
            else:
                raise ValueError("Time limit should contain exactly one number."
                                 "\nPlease enter something like: '1 day ago'.")

        else:
            num = num[0]

        return self.parse_date_limit(num, lim)

    def parse_date_limit(self, numb, limit):
        """
        :param numb: int, number of units
        :param limit: string with time unit value in it, e.g. 'hours', 'days', 'weeks', etc.
        :return: datetime object with given time limit subtracted from current datetime
        """
        if self.print_feedback:
            print "Parsing {}".format(limit)

        now = datetime.now()
        if any(wrd in limit for wrd in {'years', 'year', 'yrs', 'yr', '  y'}):
            if numb <= 0 or numb > self.ARBITRARY_YEARS_LIMIT:
                raise ValueError("Number out of bounds for year limit: '{}'\nRange is from {} to {}".format(
                    numb, self.ARBITRARY_MINIMUM_TIME_VALUE, self.ARBITRARY_YEARS_LIMIT)
                )
            else:
                return datetime(now.year-numb, now.month, 1)

        elif any(wrd in limit for wrd in {'months', 'month', 'mon', 'mnths', 'mnth'}):
            '''
            doesn't retain day number in returned datetime because different months have different numbers of days
            '''
            if numb <= 0 or numb // 12 > self.ARBITRARY_YEARS_LIMIT:
                raise ValueError("Number out of bounds for month limit: '{}'\nRange is from {} to {}".format(
                    numb, self.ARBITRARY_MINIMUM_TIME_VALUE, self.ARBITRARY_MONTH_LIMIT)
                )
            if 0 < numb <= 12:
                # numb is between 0 and 12
                if numb < now.month:
                    return datetime(now.year, now.month - numb, 1)
                else:
                    return datetime(now.year - 1, 12 - (numb - now.month), 1)
            else:  # numb is greater than 12 but not larger than the limit
                yr = now.year - (numb // 12)
                if numb % 12 < now.month:
                    return datetime(yr, now.month - (numb % 12), 1)
                else:
                    return datetime(yr-1, 12 - (numb % 12 - now.month), 1)

        elif any(wrd in limit for wrd in {'weeks', 'week', 'wks', 'wk', 'w'}):
            if numb <= 0 or numb > self.ARBITRARY_WEEKS_LIMIT:
                raise ValueError("Number out of bounds for week limit: '{}'\nRange is from {} to {}".format(
                    numb, self.ARBITRARY_MINIMUM_TIME_VALUE, self.ARBITRARY_WEEKS_LIMIT)
                )
            # avoid using now.isocalendar() for week number because there can be discrepancies with Gregorian calendar
            days = 7 * numb
            days_in_month = calendar.monthrange(now.year, now.month)[1]
            if now.month != 1:
                days_in_prev_month = calendar.monthrange(now.year, now.month - 1)[1]
            else:
                days_in_prev_month = calendar.monthrange(now.year, 12)[1]

            if days <= days_in_month:
                if days < now.day:
                    return datetime(now.year, now.month, now.day-days)
                else:
                    if now.month != 1:
                        return datetime(now.year, now.month - 1, days_in_prev_month - (days - now.day))
                    else:
                        return datetime(now.year-1, 11, days_in_prev_month - (days - now.day))
            else:
                # number of weeks is > 4, as days > number of days in current month, which must be >= ((28) = 4 weeks).
                days -= now.day
                month = int(now.month)-1  # Keep track of months to go back by
                year = int(now.year)
                if month == 0:
                    month = 12
                    year -= 1

                days_in_month = days_in_prev_month
                # subtract months until (days) is less than number of days in the month
                while days > days_in_month:
                    days -= days_in_month
                    month -= 1
                    if month == 0:
                        month = 12
                        year -= 1
                    days_in_month = calendar.monthrange(year, month)[1]

                return datetime(year, month, days_in_month - days)

        elif any(wrd in limit for wrd in {'days', 'day', 'dys', 'dy', ' d', 'd '}):
            if numb <= 0 or numb > self.ARBITRARY_DAYS_LIMIT:
                raise ValueError("Number out of bounds for day limit: '{}'\nRange is from {} to {}".format(
                    numb, self.ARBITRARY_MINIMUM_TIME_VALUE, self.ARBITRARY_DAYS_LIMIT)
                )
            days = calendar.monthrange(now.year, now.month)[1]
            if 0 < numb <= days:
                # numb is between 1 and number of days in current month
                if numb < now.day:
                    return datetime(now.year, now.month, now.day - numb)
                else:
                    if now.month == 1:
                        # If in January, go back to December and subtract remaining number of days
                        return datetime(now.year - 1, 11, 31 - (numb - now.day))
                    else:
                        days_in_prev_month = calendar.monthrange(now.year, now.month - 1)[1]
                        return datetime(now.year, now.month - 1, days_in_prev_month - (numb - now.day))
            else:
                    count = 0
                    days = now.day
                    while numb > days:
                        # subtract months until numb is within the range of a month
                        numb -= days
                        count += 1
                        days = calendar.monthrange(now.year, now.month - count)[1]
                    if count > now.month:
                        # go to previous year
                        return datetime(now.year-1, 12 - (count - now.month), days-numb)  # remaining days to subtract
                    else:
                        return datetime(now.year, now.month-count, days-numb)

        elif any(wrd in limit for wrd in {'hours', 'hour', 'hrs', 'hr', 'h '}):
            if not (0 < numb <= 24):
                if numb < 0 or numb > self.ARBITRARY_HOURS_LIMIT:  # Convert minutes to years
                    raise ValueError("Number out of bounds for hour limit: '{}'\nRange is from {} to {}".format(
                        numb, self.ARBITRARY_MINIMUM_TIME_VALUE, self.ARBITRARY_HOURS_LIMIT)
                    )
                else:
                    days = 0
                    numb -= now.hour
                    while numb >= 24:
                        numb -= 24
                        days += 1

                    if days < now.day:  # simple case
                        return datetime(now.year, now.month, now.day-days, 24-numb)

                    else:  # If near beginning of month and number of hours falls back into the previous month
                        if now.month == 1:
                            return datetime(now.year - 1, 11, 31 - (days - now.day), 24 - numb)
                        else:
                            days_in_prev_month = calendar.monthrange(now.year, now.month - 1)[1]
                            return datetime(now.year, now.month - 1, days_in_prev_month - (days - now.day), 24 - numb)

            else:
                if numb > now.hour:
                    if now.day == 1:
                        days_in_prev_month = calendar.monthrange(now.year, now.month - 1)[1]
                        return datetime(now.year, now.month-1, days_in_prev_month, 24-(numb-now.hour))
                    else:
                        return datetime(now.year, now.month, now.day - 1, 24-(numb-now.hour))
                else:
                    return datetime(now.year, now.month, now.day, now.hour-numb)

        elif any(wrd in limit for wrd in {'minutes', 'minute', 'mins', 'min', 'mns', 'mn', 'm '}):
            if not (0 < numb <= 60):
                if numb < 0 or numb > self.ARBITRARY_MINUTES_LIMIT:
                    raise ValueError("Number out of bounds for minute limit: '{}'\nRange is from {} to {}".format(
                        numb, self.ARBITRARY_MINIMUM_TIME_VALUE, self.ARBITRARY_MINUTES_LIMIT)
                    )
                else:
                    hours = 0
                    while numb > 60:
                        numb -= 60
                        hours += 1

                    if hours < now.hour:
                        return datetime(now.year, now.month, now.day, now.hour - hours)
                    else:
                        if now.day != 1:
                            return datetime(now.year, now.month, now.day - 1, 24 - (hours - now.hour))
                        else:
                            if now.month != 1:
                                days_in_prev_month = calendar.monthrange(now.year, now.month - 1)[1]
                                return datetime(now.year, now.month-1, days_in_prev_month-1, 24-(hours-now.hour))
                            else:
                                return datetime(now.year-1, 11, 30, 24-(hours-now.hour))
            else:
                if numb > now.minute:
                    if now.hour == 0:
                        return datetime(now.year, now.month, now.day-1, 23, 60-(numb-now.minute))
                    else:
                        return datetime(now.year, now.month, now.day, now.hour-1, 60-(numb-now.minute))
                else:
                    return datetime(now.year, now.month, now.day, now.hour, now.minute - numb)

    def parse_articles(self, lst_of_articles):
        for art in lst_of_articles:
            assert isinstance(art, article.Article)
            if 'ago' in art.time_published:
                art.time_published = datetime.strftime(art.date_time, "%M %d, %HH:%MM")

    def save_data(self, lst_of_articles, file_name):
        try:
            name, extension = file_name.split('.')
        except ValueError:   # need more than 1 value to unpack
            raise ValueError("Filename must include extension")
        else:
            path_numb = 0
            while os.path.exists(name + str(path_numb) + '.' + extension):
                path_numb += 1

            with open(name + str(path_numb) + '.' + extension, "wb") as f:
                pickle.dump(lst_of_articles, f)

    def write_to_file(self, lst_of_articles):

        path_numb = 0
        while os.path.exists('articles_list_' + str(path_numb) + '.html'):
            path_numb += 1
        with codecs.open('articles_list_' + str(path_numb) + '.html', 'w', encoding='utf8') as f:
            f.write(u"""<!DOCTYPE html>
        <html lang="en-us">
            <head>
                <title>jobSearcher_JobResults</title>
                <meta charset="UTF-8" content="width=device-width, initial-scale=1.0">
            </head>
            <style>

                body {
                    padding: 6em;
                    font-family: "Lucida Sans Unicode", "Lucida Grande", sans-serif;
                    background-image: url('""" + self.WEBSITE_BACKGROUND_IMAGE_PATH + """');
                    background-color: gray;
                    background-repeat: repeat;
                }

                .techcrunch {

                }

                div.container {
                    width: 100%;
                    border: 1px solid Lavender;
                    border-width:10px;
                    border-style:ridge;
                    text-align: center;
                    padding: 8px;
                    background-image: none;
                    background-color: white;
                }

                div.container:hover {
                    border-color: Slategray;
                }

                header{
                    padding: 1em;
                    color: aliceblue;
                    background-color: darkgray;
                    clear: left;
                    text-align: center;
                    <!--font-family: 'Verdana';-->
                }

                footer {
                }

                nav {
                    float: left;
                    max-width: 160px;
                    margin: 0;
                    padding: 1em;
                    background-color: #f8f8f8
                    color:dimgray;
                }

                nav ul {
                    list-style-type: none;
                    padding: 0;
                }

                nav ul a {
                    text-decoration: none;
                }

                article {
                    margin-left: 170px;
                    border-left: 1px solid gray;
                    padding: 1em;
                    overflow: hidden;
                    min-height: 150px;
                }

                p.description, h3.title {
                    text-align:left;
                    font-family: "Lucida Sans Unicode", "Lucida Grande", sans-serif;
                }

                section {float:right; background: ghostwhite;color:dimgray;}
                aside {float:right; background:ghostwhite; color:dimgray; padding:2px;}
                hr {
                    width:85%;
                    margin-left=3;
                    margin-right:1
                    align="center"
                }

            </style>
        <body>""")

            for a in lst_of_articles:
                assert isinstance(a, article.Article)
                f.write(u"""
                        <div class="container">
                            <header>
                                <h3>{}</h3>
                            </header>
                        <nav class="nav">
                            <a href="{}">
                                <img src="{}" alt="Image not found" width="128" height="128"></img>
                            </a>
                        </nav>
                        <aside>
                            <p>{}</p>
                        </aside>
                        <article class="article">
                            <h3 class="title">{}</h3>
                            <p class="description">{}</p>
                        </article>
                    <footer><a href="{}">Read More...</a></footer>
                    </div>""".format(
                    a.website_name, a.link, a.img_link, a.time_published, a.title,
                    a.description, a.link,
                    )
                )
                f.write(u"<br></br><hr><br></br>")
            f.write(
                    u'''
            <p style="color:white;text-align:center"><small>Website designed by Alexander Hamme</small></p>
            </body>
        </html>'''
)



