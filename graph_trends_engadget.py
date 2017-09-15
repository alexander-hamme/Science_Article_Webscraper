from __future__ import print_function
from datetime import datetime
import plotly.plotly as py
import plotly.graph_objs as go
import pickle
import article


class EngadgetTrendGrapher:

    def __init__(self):
        self.list_of_articles = []

    def load_data(self, filename):

        lst_of_articles = []

        try:
            with open(filename, "rb") as f:
                lst_of_articles = pickle.load(f)
        except IOError as ioe:
            raise ioe
        except Exception as e:
            raise e

        return lst_of_articles

    def make_points(self, lst_of_articles):

        points = []

        for art in lst_of_articles:
            assert isinstance(art, article.Article)
            if art.popularity:
                points.append((art.date_time, art.popularity, art.label, art.date_time.weekday()))

        return points

    def strain_articles(self, lst_of_articles):
        '''
        Keep only articles with valid popularity value
        '''
        arts = []
        for art in lst_of_articles:
            assert isinstance(art, article.Article)

            if art.popularity:
                arts.append(art)

        return arts

    def graph_days(self, lst_of_articles, points):
        '''
        Graph which days of the week have highest popularity rates
        '''
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        points = []

        for art in lst_of_articles:
            assert isinstance(art, article.Article)
            if art.popularity:
                points.append((art.popularity, art.date_time.weekday()))

        trace1 = go.Scatter(x=map(lambda p: days[p[1]], points), y=map(float, [point[0] for point in points]),
                            marker={'color': 'blue', 'symbol': 'dot', 'size': "5"}, mode="markers+lines",
                            text='', name='1st trace')

        data = go.Data([trace1])
        layout = go.Layout(title="Popularity - days of the week'", xaxis={'title': 'x1'}, yaxis={'title': 'x2'})
        figure = go.Figure(data=data, layout=layout)

        return figure

    def graph_label_popularities(self, lst_of_articles):
        '''
        Graph which topics (labels) are the most popular overall
        '''
        labels = {
            "Politics": [], "Space": [], "Cameras": [], "Gadgetry": [], "DIY": [], "Internet":  [], "Medicine":  [],
            "Transportation":  [], "Business":  [], "Food and Drink":  [], "Robots":  [], "Services":  [], "Mobile":  [],
            "Science":  [], "Green":  [], "AV":  [], "Opinion":  [], "Security":  [], "Personal Computing":  [], "Art":  [],
            "Wearables":  [], "Sex":  [], "Design":  [], "Home": []
        }

        points = []

        for art in lst_of_articles:
            assert isinstance(art, article.Article)
            if art.popularity:
                points.append((art.popularity, art.label))

        for pt in points:
            labels[pt[1]].append(pt[0])

        averages = []
        for label, lst in labels.iteritems():
            averages.append((label, reduce(lambda x, y: x + y, lst) / float(len(lst))))

        # Average the popularity of each label
        trace1 = go.Scatter(x=([pair[0] for pair in averages]), y=([pair[1] for pair in averages]),
                            marker={'color': 'teal', 'symbol': 'dot', 'size': "4"}, mode="markers+lines",
                            text='', name='Popularity - days of the week')

        data = go.Data([trace1])

        layout = go.Layout(autosize=True, title="Article Topic Popularities", xaxis={"autorange": True, 'title': '', },
                           yaxis={"autorange": True, 'title': 'Article Popularity (number of shares per day)'})

        figure = go.Figure(data=data, layout=layout)

        return figure

    def graph_label_date_trends(self, lst_of_articles, graph_avgs=True):
        '''
        Graph popularity of each topic (label) over time
        '''
        date_coords = {}

        labels = {
            "Politics": [], "Space": [], "Cameras": [], "Gadgetry": [], "DIY": [], "Internet":  [], "Medicine":  [],
            "Transportation":  [], "Business":  [], "Food and Drink":  [], "Robots":  [], "Services":  [], "Mobile":  [],
            "Science":  [], "Green":  [], "AV":  [], "Opinion":  [], "Security":  [], "Personal Computing":  [], "Art":  [],
            "Wearables":  [], "Sex":  [], "Design":  [], "Home": []
        }

        months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

        # Add each article to corresponding label list in labels dictionary
        for art in lst_of_articles:
            if art.label in labels.iterkeys():
                labels[art.label].append(art)
            print("Did it")

        traces = []
        colors = ('blue', 'orange', 'green', 'purple', 'pink', 'brown', 'yellow', 'rgb(188,189,34)')

        colors = ('rgb(128, 198, 255', 'rgb(200, 150, 255)', 'rgb(220, 150, 150)', 'rgb(180, 150, 80)',
                  'rgb(250, 150, 120)', 'rgb(120, 120, 180)', 'rgb(80, 160, 80)', 'rgb(180,180,180)',
                  'teal', 'maroon', 'brown', 'green', 'yellow', 'red', 'blue', 'purple', 'black',
                  '#E377C2', '#1F77B4', '#BCBD22', '#6E5981', '#6F8159', '#648CA1', '#A19264')

        # Sort articles within each Label by date
        for ky in labels.iterkeys():
            labels[ky].sort(key=lambda a: a.date_time, reverse=False)

        for i, key in enumerate(labels.iterkeys()):

            xpoints = [art.date_time for art in labels.get(key)]
            ypoints = [art.popularity for art in labels.get(key)]
            # Turn datetime object into Mon + Year, e.g. "Apr 2017"
            for j in range(len(xpoints)):
                dt = xpoints[j]
                assert isinstance(xpoints[j], datetime)
                # Plotly will automatically group stuff together if same exact name
                # Datetime months are 1 to 12
                xpoints[j] = unicode("{} {}".format(months[dt.month - 1], dt.year))

            # Maintain month order  (calling set() on list reorders the list because it sorts it)
            unique_date_points = sorted(set(xpoints), key=xpoints.index)

            counts = [xpoints.count(dt) for dt in unique_date_points]
            y_averages = []
            prev = 0            

            # Average the popularity scores for each month (for each specific label)
            for indx in counts:
                pts = ypoints[prev: prev + indx]
                if len(pts) > 1:
                    if graph_avgs:
                        y_averages.append(reduce(lambda y1, y2: y1+y2, pts) / float(len(pts)))
                    else:
                        y_averages.append(reduce(lambda y1, y2: y1 + y2, pts))
                elif len(pts) == 1:
                    y_averages.append(float(pts[0]))

                prev += indx

            # Graph all points as dots, graph average points as lines

            traceDots = go.Scatter(x=(xpoints), y=(ypoints),
                                marker={'color': colors[i], 'symbol': 'dot', 'size': "4"}, mode="markers",
                                text='', name=key)

            traceLine = go.Scatter(x=(unique_date_points), y=(y_averages), showlegend=False,
                                marker={'color': colors[i], 'symbol': 'dot', 'size': "7"}, mode="lines",
                                text='', name=None)

            traces.append(traceDots)
            traces.append(traceLine)

        data = go.Data(traces)

        layout = go.Layout(autosize=True, title="Article Subject Popularity Trends", xaxis={"autorange": True, 'title': '', },
                           yaxis={"autorange": True, 'title': 'Engadget Popularity Trends'})

        figure = go.Figure(data=data, layout=layout)

        return figure

    def plot(self, fig, name):
        return py.plot(fig, filename=name)

    def main(self, filename, graph_choice):

        self.list_of_articles = self.strain_articles(self.load_data(filename))

        self.list_of_articles.sort(key=lambda a: a.date_time, reverse=True)

        choices = [
                    self.plot(self.graph_label_popularities(self.list_of_articles), 'py_graph_4'),
                    self.plot(self.graph_label_date_trends(self.list_of_articles, graph_avgs=False), 'py_graph_3')
                  ]

        return choices[graph_choice]

def main():
    grapher = EngadgetTrendGrapher()
    grapher.main("engadget_articles3.dat", 2)