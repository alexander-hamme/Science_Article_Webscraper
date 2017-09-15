# science_article_webscraper
A **web crawler** that collects data about thousands of science articles, using Requests, Urllib2, and Selenium modules. Program visualizes article statistics using Plotly library, then outputs HTML document.

Currently collects data from three websites: engadget, popularmechanics, and techcrunch. Scrapers for additional websites can easily be added.


Note: the *newscraper.py* file is the **parent class** for all the specific site scrapers. In order to add a new website scraper, make it inherit all the functions from this class. 


######See the examples folder for sample HTML output document. Also in that folder are more images, however the current graphs created by the program are fairly messy and need to be made more aesthetically pleasing in the future.

