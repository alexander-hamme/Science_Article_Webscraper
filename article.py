class Article:

    IMAGE_NOT_FOUND_LINK = u'file://images/placeholder.jpg'

    def __init__(self):
        self.link = u''
        self.title = u''
        self.time_published = u''
        self.date_time = u''        # datetime object
        self.description = u''
        self.label = u''
        self.img_link = u''
        self.website_name = u''
        self.popularity = 0         # views per unit of time


    @property
    def info(self):
        return self.title, self.description, self.label, self.time_published, self.link, self.img_link, self.date_time

    def __str__(self):
        return u"\nTitle: {}\nTag: {}\nTime published: {}\nDescription: {}\nPopularity: {}".format(
            self.title, self.label, self.time_published, self.description, self.popularity
        )

