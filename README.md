# science_article_webscraper
A **web crawler** that collects data about thousands of science articles, using Requests, Urllib2, and Selenium modules. Program visualizes article statistics using Plotly library, then outputs an HTML document.


Note: the *newscraper.py* file is the **parent class** for all the specific site scrapers. In order to add a new website scraper, make it inherit all the functions from this class. This currently collects data from three websites: engadget, popularmechanics, and techcrunch. Scrapers for additional websites can easily be added.


###### See the examples folder to view the sample HTML output document source. Also in that folder are more images, however the current graphs created by the program are fairly messy and need to be made more aesthetically pleasing in the future.

<a href="https://cdn.rawgit.com/alexander-hamme/science_article_webscraper/6d277774/examples/html_output_articles_list.html">
  <img src="https://github.com/alexander-hamme/science_article_webscraper/blob/master/examples/screenshot.png?raw=true" alt="Image could not be loaded, please look in the examples folder of this respository."></a>

