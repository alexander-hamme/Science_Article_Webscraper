import newsscraper
import engadgetscraper
import techcrunchscraper
import popularmechanicsscraper
import find_trends
import pickle
import time


def main():
    t = time.time()
    list_of_articles = []
    news = newsscraper.NewsScraper()
    news.date_limit = news.get_date_limit()
    print "Time limit = {}".format(news.date_limit)

    eng_s = engadgetscraper.EngadgetScraper(date=news.date_limit)
    list_of_articles += eng_s.main(write_file=False)

    tech_s = techcrunchscraper.TechcrunchScraper(date=news.date_limit)
    list_of_articles += tech_s.main(write_file=False)

    pop_s = popularmechanicsscraper.PopularMechanicsScraper(date=news.date_limit)
    list_of_articles += pop_s.main(write_file=False)

    print "{} articles collected in total".format(len(list_of_articles))

    news.parse_articles(list_of_articles)

    print "Sorting articles"
    sort_t = time.time()

    
    list_of_articles.sort(key=lambda a: a.date_time, reverse=True)
    
    print "Elapsed sorting time: {} seconds".format(int(10000000*(time.time() - sort_t))/10000000.0)

    with open("articles.dat", "wb") as f:
        pickle.dump(list_of_articles, f)        # Serialize list of article objects for future use

    news.write_to_file(list_of_articles)

    print "Total elapsed time of this NewScraper Session: {}m {}s".format(
        (time.time() - t) // 60, int(1000*((time.time() - t) % 60))/1000.0
    )

if __name__ == "__main__":
    main()

