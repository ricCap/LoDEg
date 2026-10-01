import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.collections import PolyCollection
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import matplotlib.cm as cm
import mpld3
import datetime
import pytz

# Workaround for polar charts
import sys
import base64
import io

# For correlation_graph test only
# import test_utils  # migrate
from ..lodegML.exceptions import AutoPlotException  # migrate


class AutoPlot:
    """A helper class that holds all the library plotting capabilities"""

    def __init__(self, target: str = 'console', title_font_size: int = 14):
        """
        Params:
            target (str): ['console','web'] the target of the plot function; if 'console' than the function plt.show() is used, otherwise it will be plotted as either html or png depending on the type of chart. Defaults to 'web'.
            title_font_size (int): figures title font size. Defaults to 14.
        """
        self._target = target
        self._title_font_size = title_font_size
        self._save_next_figure = False

    def _save(func):
        def func_wrapper(self, *args, **kwargs):
            if self._save_next_figure:
                self._save_next_figure = False
                try:
                    figure = args[0]
                    figure.savefig(self._save_path)
                except Exception as exc:
                    raise AutoPlotException(
                        'Error while saving figure') from exc
            return func(self, *args, **kwargs)
        return func_wrapper

    @_save
    def _plot(self, figure, output_type='png'):
        if self._target == 'console':
            plt.show()
        elif self._target == 'web' or self._target == 'default':
            if output_type == 'html':
                html = mpld3.fig_to_html(figure)
                return html
            elif output_type == 'png':
                f = io.BytesIO()
                figure.savefig(f, format="png")
                plt.clf()  # Might break everything when parallelizing
                return "data:image/png;base64," + \
                    base64.b64encode(f.getvalue()).decode()

    def saveNextFigure(self, filename, folder='./'):
        self._save_next_figure = True
        self._save_path = folder + filename
        return self

    def printSessionCoverage(self, sessionInfo: dict, lesson_duration: float):
        """ Print the session coverage, i.e. which parts of the video have been watched.

        Params:
            sessionInfo (dict): the session that contains the session_coverage to be plotted.
            lesson_duration (float): the duration of the lesson to be plotted in seconds.
        """
        session_coverage = sessionInfo['session_coverage']
        fig, ax = plt.subplots()

        lesson_duration_in_minutes = lesson_duration / 60.

        ax.plot([0, lesson_duration_in_minutes],
                [-2, -2], color='b', linewidth=20)
        y = 0
        for interval in session_coverage:
            y = y + 1
            interval_in_minutes = (interval[0] / 60., interval[1] / 60)
            ax.plot(interval_in_minutes, [-2, -2], color='r', linewidth=20)
            ax.plot(interval_in_minutes, [y, y], color='r', linewidth=6)
            ax.plot([interval_in_minutes[0], interval_in_minutes[0]],
                    [-2, y], "g--", linewidth=0.5)
            ax.plot([interval_in_minutes[1], interval_in_minutes[1]],
                    [-2, y], "g--", linewidth=0.5)

        ax.grid(True)
        ax.set_title(
            'SESSION COVERAGE: which parts of the video have been watched',
            fontsize=self._title_font_size)
        ax.set_xlabel('minutes')
        ax.set_ylabel('Inteval number')
        return self._plot(fig, 'html')

    def printLessonCoverage(self, coverage: list):
        """Plot a bar chart of the number of users per time bucket for the lesson.

        Params:
            notes_types (dict): the dictionary of type {'note_name': #notes}

        Todo:
            * add a bucket_length parameter and scale the ticks accordingly
        """
        fig, ax = plt.subplots()
        ax.grid(True)
        ax.set_xlabel('Slots (30s)')
        ax.set_ylabel('Number of users')
        bars = ax.bar(np.arange(len(coverage)), coverage)
        return self._plot(fig, 'html')

    def printNotesPolarChart(self, notes_types: dict):
        """
        Todo:
            * this method is never used and might be removed
        """
        # Compute pie slices
        N = len(notes_types)
        theta = np.linspace(0.0, 2 * np.pi, N, endpoint=False)
        radii = notes_types.values()
        width = 2 * np.pi / 3
        labels = list(notes_types.keys())

        fig, ax = plt.subplot(111, projection='polar')
        bars = ax.bar(theta, radii, width=width, bottom=0.0)

        ax.legend((bars[i] for i in range(len(bars))), (labels[i]
                                                        for i in range(len(bars))))

        # Use custom colors and opacity
        for r, bar in zip(radii, bars):
            bar.set_facecolor(plt.cm.plasma(r / 5.))
            bar.set_alpha(0.5)

        return self._plot(fig, 'png')

    def printNotesBarChart(self, notes_types: dict):
        """Plot a bar chart of the number of the notes per type.

        Params:
            notes_types (dict): the dictionary of type {'note_name': #notes}
        """
        number_of_types = np.arange(len(notes_types))
        types = list(notes_types.keys())

        fig, ax = plt.subplots()
        colors = ['r', 'b']
        bars = ax.bar(number_of_types, notes_types.values(),
                      color=colors, align="center")

        ax.set_title('Number of notes per type',
                     fontsize=self._title_font_size)
        ax.legend((bars[0], bars[1]), types)
        plt.xticks(range(2), types)
        ax.grid(True)

        return self._plot(fig, 'html')

    def printLessonsHistogram(self, histogram: dict, user_level: bool):
        """Plot a bar chart of the number of users/sessions per lesson.

        Params:
            histogram (dict): a dictionary of type {'lesson':'number_of_users'}
            user_level (bool): if True we are plotting the number of sessions
            per lesson for a given user; otherwise, the number of users per lesson for a given course.
        """
        fig, ax = plt.subplots()
        colors = ['r', 'b']
        x = np.arange(len(histogram))
        bars = ax.bar(x, histogram.values(), color=colors)

        # Set title according to the chart we aare plotting
        if user_level:
            # We are plotting the number of sessions per lesson
            ax.set_title('Number of sessions per lesson',
                         fontsize=self._title_font_size)
        else:
            # We are plotting the number of users per lesson
            ax.set_title('Number of users that have watched each lesson',
                         fontsize=self._title_font_size)

        plt.xticks(x, histogram.keys())
        ax.grid(True)

        return self._plot(fig, 'html')

    def printDaySessionDistribution(self, distribution: list):
        """A polar chart with the distribution of sessions throughout the day

        Args:
            distribution (list): a list of 24 values, i.e. the number of sessions for each time slice
        """
        # Check if the distribution has exactly 24 hours
        if len(distribution) == 24:

            grid = gridspec.GridSpec(2, 2)
            plt.figure()

            # Compute pie slices
            theta = np.linspace(0.0, 2 * np.pi, 12, endpoint=False)
            radii = distribution
            max_radio = max(distribution)
            width = 2 * np.pi / 12.0

            radii1 = list(reversed(np.append(radii[1:12], radii[0:1])))
            radii2 = list(reversed(np.append(radii[13:24], radii[12:13])))

            ax1 = plt.subplot(grid[0, 0], projection='polar')
            bars = ax1.bar(theta, radii1, width=width, bottom=0.0)

            # Use custom colors and opacity
            for r, bar in zip(radii1, bars):
                bar.set_facecolor(plt.cm.viridis(r / max_radio))

            ax1.set_theta_zero_location("N")  # Rotate bars
            ax1.set_xticklabels(['0', '', '9', '', '6', '', '3'])

            ax2 = plt.subplot(grid[1, 0], projection='polar')
            bars = ax2.bar(theta, radii2, width=width, bottom=0.0)

            # Use custom colors and opacity
            for r, bar in zip(radii2, bars):
                bar.set_facecolor(plt.cm.viridis(r / max_radio))

            ax2.set_theta_zero_location("N")  # Rotate bars
            ax2.set_xticklabels(['12', '', '21', '', '18', '', '15'])

            ax3 = plt.subplot(grid[:, 1])
            bars = ax3.bar(range(0, 24), distribution)
            # Add text
            for bar in bars:
                height = bar.get_height()
                bar.set_facecolor(plt.cm.viridis(height / max_radio))
            ax3.set_xticks(range(0, 24, 2))

            fig = plt.gcf()
            fig.suptitle("Sessions day distribution",
                         fontsize=self._title_font_size)

        return self._plot(fig, 'png')

    def printLessonUserCorrelationGraph(
            self, lessons_visualization: dict, registration_dates: dict,
            time_format: str='abs'):
        """Print a 3d graph of users lesson visualization.

        The graph plots a function of the number of users against time and lessons: for every lesson,
        a curve is plotted to show when and how many users have watched the lessons.

        Time has two formats: abs and rel. It expresses wheter each lesson curve is plotted agains its registration date (rel)
        or against the registration date of the first lesson (abs).

        Params:
            lessons_visualization (dict): the dictionary of type {'lesson_id':Counter(datetime)}.
            registration_dates (dict): the dates of registration of every lesson.
            time_format (str): the time format (abs or rel). Defaults to abs.
        """
        # Create the figure
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(projection='3d')

        # Set z as lessons
        y_ticks = lessons_visualization.keys()
        zs = iter(np.arange(0, len(lessons_visualization)))

        # Dates formatters
        months = mdates.MonthLocator()  # every month
        days = mdates.DayLocator()  # every day
        # Setup the DateFormatter for the x axis
        date_format = mdates.DateFormatter('%D')

        # Min/max for x ticks
        datemin = min(registration_dates.values())
        datemax = max(registration_dates.values())

        # Maxvalue for z axis
        max_value = 0

        for lesson, dates_counter in lessons_visualization.items():
            # Get the dates that are present in the counter
            dates = sorted(dates_counter.keys())

            # Compute datemin and datemax
            max_date = max(dates)
            # Select a relative mindate if time_format = rel
            if (time_format == 'rel'):
                min_date = min(dates)
                if min_date < datemin:
                    datemin = min_date
            else:
                min_date = datemin

            if max_date > datemax:
                datemax = max_date

            # Create verts adding a 0 before the first and after the last days
            xs = np.asarray(
                [mdates.date2num(min_date + datetime.timedelta(days=-1))] +
                list(mdates.date2num(dates)) +
                [mdates.date2num(max_date + datetime.timedelta(days=1))])
            ys = [0]
            for date in dates:
                ys.append(dates_counter[date])
            ys.append(0)

            # Update max_value
            tmp = max(dates_counter.values())
            if (tmp > max_value):
                max_value = tmp

            current_z = next(zs)
            ax.bar(xs, ys, zs=current_z, zdir='y', alpha=0.8)

        # Set ticks
        ax.set_yticklabels(y_ticks)

        # format the ticks
        ax.xaxis.set_major_locator(months)
        ax.xaxis.set_minor_locator(days)
        ax.xaxis.set_major_formatter(date_format)

        # Set axis labels and limits
        ax.set_zlabel('Users')

        # Convert the image to a base64 binary stream
        return self._plot(fig, 'png')
