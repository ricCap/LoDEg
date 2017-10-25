import numpy as np
from datetime import datetime
from collections import Counter
import dateutil.tz
from bson.objectid import ObjectId

import utility_queries as utils  # migrate

############################
# Session level extraction #
############################


def play_pause_extraction(sessionInfo: dict):
    """This function extracts information about of play and pauses.

    extracted_information : 
        - plays intervals
        - pauses intervals
        - play/pause ration

     Args:
        sessionInfo (dict): The dictionary that will be populated with the computed statistic.
    """

    play_pause_list = utils.purify_list(sessionInfo['data'], ['play', 'pause'])

    # List of pauses for this session
    pauses = []
    # List of play intervals for this session
    plays = []
    # List of fractions play_time/ pause_time;
    pauses_ratio = []

    play_time = play_pause_list[0]['value2']
    pause_time = 0

    for item in play_pause_list[1:]:
        if (item['type'] == 'play'):
            play_time = item['value2']
            pauses.append(play_time - pause_time)
            # Note that pause_time > play_time >= 0
            pauses_ratio.append(plays[-1] / pauses[-1])
        else:
            pause_time = item['value2']
            plays.append(pause_time - play_time)

    sessionInfo['pauses'] = pauses
    sessionInfo['plays'] = plays
    sessionInfo['pauses_ratio'] = pauses_ratio


def session_coverage_extraction(sessionInfo: dict):
    """This function extracts the video coverage of the session.

    Note: it adds the session_coverage and the total_time_watched to the sessionInfo

     Args:
        sessionInfo (dict): The dictionary that will be populated with the computed statistic.
    """
    intervals = []
    interval = []
    start_interval = 0.0
    end_interval = 0.0

    current_action = ''
    previous_action = ''
    current_value1 = 0.0

    play_pause_alive_jump_list = utils.purify_list(
        sessionInfo['data'], ['play', 'pause', 'alive', 'jump', 'speed'])

    for record in play_pause_alive_jump_list:
        previous_action = current_action
        current_action = record['type']
        current_value1 = record['value1']

        if (current_action == 'play'):
            if(previous_action != 'pause'):
                start_interval = current_value1

        elif (current_action == 'jump'):
            # Add an interval only if it has a duration of at least
            # 5 secs (to improve performances)
            end_interval = current_value1
            if (np.abs(end_interval - start_interval) > 5.0):
                intervals = utils.add_interval(
                    intervals, [start_interval, end_interval])
            start_interval = record['value2']

        elif (current_action == 'alive'):
            # Add a new interval only if we were playing
            if(previous_action == 'play' or previous_action == 'speed'):
                # Add an interval only if it has a duration of at least
                # 5 secs (to improve performances)
                end_interval = current_value1
                if (np.abs(end_interval - start_interval) > 5.0):
                    intervals = utils.add_interval(
                        intervals, [start_interval, end_interval])

        elif (current_action == 'speed'):
            # Add a new interval with the previous speed (without limitations)
            end_interval = current_value1
            intervals = utils.add_interval(
                intervals, [start_interval, end_interval])
            start_interval = end_interval

    # Add last interval if the session ends with a pause
    if(current_action == 'pause'):
        end_interval = current_value1
        if (np.abs(end_interval - start_interval) > 5.0):
            intervals = utils.add_interval(
                intervals, [start_interval, end_interval])

    # Computer total_time_watched
    total_time_watched = 0.
    for interval in intervals:
        total_time_watched += interval[1] - interval[0]

    # Add the video coverage
    sessionInfo['session_coverage'] = intervals
    # Add the total_time_watched
    sessionInfo['total_time_watched'] = total_time_watched


def jumps_info_extraction(sessionInfo: dict):
    """This function extracts information of jumps for the session.

    extracted_information : 
        - average jump length
        - number of jumps
        - number of jumps/type (click_or_drag,keyframe,note)
        - total jumps length

     Args:
        sessionInfo (dict): The dictionary that will be populated with the computed statistic.
    """
    total_jumps_length = 0.0
    jumps_per_type = {'click_or_drag': 0, 'keyframe': 0, 'note': 0}
    jump_list = utils.purify_list(sessionInfo['data'], ['jump'])

    for jump in jump_list:
        jump_length = np.abs(jump['value1'] - jump['value2'])
        total_jumps_length += jump_length
        jumps_per_type[jump['value3']] = jumps_per_type[jump['value3']] + 1

    number_of_jumps = len(jump_list)
    average_jumps_length = (total_jumps_length / number_of_jumps) if number_of_jumps > 0 else 0

    # Add values to sessionInfo
    sessionInfo['number_of_jumps'] = number_of_jumps
    sessionInfo['average_jumps_length'] = average_jumps_length
    sessionInfo['jumps_per_type'] = jumps_per_type
    sessionInfo['total_jumps_length'] = total_jumps_length


def add_lesson_id_to_session(sessionInfo: dict):
    """ This function adds the lesson_id to the sessionInfo dictionary

    Note:
        It requires a valid session.

    Args:
        sessionInfo (dict): The dictionary that will be populated with the computed statistic.
    """
    # We assume the first record of data to be a title record
    sessionInfo['lesson_id'] = sessionInfo['data'][0]['value1']


def add_session_date(sessionInfo: dict):
    """ This function adds the session_date to the sessionInfo dictionary

    Note:
        It requires a valid session.

    Args:
        sessionInfo (dict): The dictionary that will be populated with the computed statistic.
    """
    # We assume the session has at least one record
    sessionInfo['date'] = ObjectId(
        sessionInfo['data'][0]['_id']).generation_time


def compute_session_duration(sessionInfo: dict):
    """
    This function takes a session and calculates the session duration.

    Args:
        sessionInfo (dict): The dictionary that will be populated with the computed statistic.
    """
    first_timestamp = sessionInfo['data'][0]['_id'].generation_time
    last_timestamp = sessionInfo['data'][-1]['_id'].generation_time
    session_duration = (last_timestamp - first_timestamp).seconds
    if session_duration == 0:
        sessionInfo['session_duration'] = 1
    else:
        sessionInfo['session_duration'] = session_duration


def notes_info_extraction(sessionInfo: dict):
    """This function extracts information of notes for the session.

    extracted_information : 
        - number of notes
        - number of notes/type (click_or_drag,keyframe,note)
        - notes / session_duration

    Note:
        It requires the session_duration to be computed first.

    Args:
        sessionInfo (dict): The dictionary that will be populated with the computed statistic.
    """
    notes_list = utils.purify_list(sessionInfo['data'], ['note'])
    sessionInfo['number_of_notes'] = len(notes_list)
    sessionInfo['notes_per_type'] = {'handwritten': 0, 'text': 0}
    for note in notes_list:
        sessionInfo['notes_per_type'][note['value1']] += 1
    sessionInfo['notes_over_session_duration'] = sessionInfo[
        'number_of_notes'] / sessionInfo['session_duration']


#########################
# User level extraction #
#########################

def compute_lessons_coverage_for_single_user(userInfo: dict, lessons_durations: dict):
    """This function computes the lesson coverage for all lessons of a user.

    Note: It computes the coverage_histogram as well

    Args:
        userInfo (dict): The dictionary that will be populated with the computed statistic.
        lessons_durations (dict) : The systemInfo dictionary {'lesson_id':'lesson_duration'}.
    """
    interval_gap = 30  # seconds

    lessons_coverage = {}
    histogram = {}
    # Initialize lessons lists
    for lesson_id, duration in lessons_durations.items():
        number_of_buckets = int(duration) // interval_gap
        lessons_coverage[lesson_id] = [0] * number_of_buckets
        histogram[lesson_id] = 0

    # Compute lessons coverage
    for session, sessionInfo in userInfo['sessions'].items():
        lesson = sessionInfo['lesson_id']
        # Add this session to the histogram
        histogram[lesson] += 1
        for interval in sessionInfo['session_coverage']:
            left_bucket = int(interval[0]) // interval_gap
            right_bucket = int(interval[1]) // interval_gap
            if(right_bucket == left_bucket):
                lessons_coverage[lesson][right_bucket] += 1
            else:
                for bucket in range(left_bucket, right_bucket):
                    lessons_coverage[lesson][bucket] += 1

    userInfo['lessons_coverage'] = lessons_coverage
    userInfo['coverage_histogram'] = histogram


def user_notes_info_extraction(userInfo: dict):
    """This function extracts information of notes for the user.

    extracted_information : 
        - number of notes
        - number of notes/type (click_or_drag,keyframe,note)
        - notes / total_duration

    Note:
        It requires the notes_info_extraction to be executed first.

    Args:
        userInfo (dict): The dictionary that will be populated with the computed statistic.
    """
    number_of_notes = 0
    notes_per_type = {'handwritten': 0, 'text': 0}
    total_duration = 1

    for sessionInfo in userInfo['sessions'].values():
        number_of_notes += sessionInfo['number_of_notes']
        notes_per_type[
            'handwritten'] += sessionInfo['notes_per_type']['handwritten']
        notes_per_type['text'] += sessionInfo['notes_per_type']['text']
        total_duration += sessionInfo['session_duration']

    userInfo['number_of_notes'] = number_of_notes
    userInfo['notes_per_type'] = notes_per_type
    userInfo['notes_over_session_duration'] = number_of_notes / \
        total_duration


def user_jump_info_extraction(userInfo: dict):
    """This function extracts information of jumps for the user.

    extracted_information : 
        - number of jumps
        - number of jumps/type (click_or_drag,keyframe,note)
        - total jumps length
        - average jumps length

     Args:
        userSession (dict): The dictionary that will be populated with the computed statistic.
    """

    number_of_jumps = 0
    jumps_per_type = {'click_or_drag': 0, 'keyframe': 0, 'note': 0}
    total_duration = 0
    total_jumps_length = 0
    average_jumps_length = 0

    for sessionInfo in userInfo['sessions'].values():
        number_of_jumps += sessionInfo['number_of_jumps']
        jumps_per_type[
            'click_or_drag'] += sessionInfo['jumps_per_type']['click_or_drag']
        jumps_per_type['keyframe'] += sessionInfo['jumps_per_type']['keyframe']
        jumps_per_type['note'] += sessionInfo['jumps_per_type']['note']
        total_jumps_length += sessionInfo['total_jumps_length']
        total_duration += sessionInfo['session_duration']
        
    userInfo['number_of_jumps'] = number_of_jumps
    userInfo['jumps_per_type'] = jumps_per_type
    userInfo['total_jumps_length'] = total_jumps_length
    userInfo['average_jumps_length'] = (total_jumps_length / number_of_jumps ) if number_of_jumps > 0 else 0
    userInfo['jumps_over_total_duration'] = number_of_jumps / total_duration


def user_lessons_visualization_extraction(userInfo: dict):
    """Extract for each lesson when the user watched the lesson.

    This function adds to the userInfo a Counter of datetimes; the Counter is called called 'lessons_visualization'.

    Args:
        userInfo (dict): The dictionaty that will be populated with the computed statistic.
    """
    try:
        lessons_visualization = {}
        for sessionInfo in userInfo['sessions'].values():
            lesson = sessionInfo['lesson_id']
            date = sessionInfo['date']
            if lesson not in lessons_visualization:
                lessons_visualization[lesson] = Counter({date: 1})
            else:
                lessons_visualization[lesson] += Counter({date: 1})
        userInfo['lessons_visualization'] = lessons_visualization
    except KeyError:
        # Some statistics are missing (dates or sessionInfo)
        userInfo['lessons_visualization'] = {}


def day_session_distribution_extraction(userInfo: dict):
    """Extract the number of sessions for each hour of the day.

    Args:
        userInfo (dict): The dictionaty that will be populated with the computed statistic. 
    """
    day_distribution = [0] * 24
    for sessionInfo in userInfo['sessions'].values():
        hour = sessionInfo['date'].hour
        day_distribution[hour] += 1
    userInfo['day_distribution'] = day_distribution


###########################
# Course level extraction #
###########################


def compute_course_global_coverage(courseInfo: dict):
    """This function computes the global coverage and the users histogram for a single course.

     Args:
        courseInfo (dict): The dictionary that will be populated with the computed statistic.
    """
    interval_gap = 30  # seconds
    global_coverage = {}
    histogram = {}
    lessons_durations = courseInfo['lessons_durations']

    # Initialize lessons lists
    for lesson_id, duration in lessons_durations.items():
        number_of_buckets = int(duration) // interval_gap
        global_coverage[lesson_id] = [0] * number_of_buckets
        histogram[lesson_id] = 0

    # Compute global coverage
    for user, userInfo in courseInfo['users'].items():
        if 'lessons_coverage' in userInfo.keys():
            # If we have already computed the lessons_coverage
            for lesson_title in userInfo['lessons_coverage'].keys():
                # Add this user to the histogram
                histogram[lesson_title] += 1
                # if lesson_title in userInfo['lessons_coverage']:
                # If the user has watched the lesson
                for i in range(len(userInfo['lessons_coverage'][lesson_title])):
                    global_coverage[lesson_title][
                        i] += (userInfo['lessons_coverage'][lesson_title][i] > 0)

    courseInfo['global_coverage'] = global_coverage
    courseInfo['coverage_histogram'] = histogram


def course_notes_info_extraction(courseInfo: dict):
    """This function extracts information of notes for the system.

    extracted_information : 
        - number of notes
        - number of notes/type (click_or_drag,keyframe,note)

    Note:
        It requires the user notes_info_extraction to be executed first.

    Args:
        courseInfo (dict): The dictionary that will be populated with the computed statistic.
    """
    number_of_notes = 0
    notes_per_type = {'handwritten': 0, 'text': 0}

    for userInfo in courseInfo['users'].values():
        number_of_notes += userInfo['number_of_notes']
        notes_per_type[
            'handwritten'] += userInfo['notes_per_type']['handwritten']
        notes_per_type['text'] += userInfo['notes_per_type']['text']

    courseInfo['number_of_notes'] = number_of_notes
    courseInfo['notes_per_type'] = notes_per_type


def course_lessons_visualization_extraction(courseInfo: dict):
    """Extract for each course when the users watched the lessons.

    This function adds to the courseInfo a Counter of datetimes; the Counter is called called 'lessons_visualization'.

    Args:
        courseInfo (dict): The dictionaty that will be populated with the computed statistic.
    """
    try:
        lessons_visualization = {}
        for userInfo in courseInfo['users'].values():
            for lesson, dates_counter in userInfo['lessons_visualization'].items():
                if lesson not in lessons_visualization:
                    lessons_visualization[lesson] = dates_counter.copy()
                else:
                    lessons_visualization[lesson] += dates_counter
        courseInfo['lessons_visualization'] = lessons_visualization
    except KeyError:
        # Some statistics are missing
        courseInfo['lessons_visualization'] = {}


def course_day_distribution_extraction(courseInfo: dict):
    """Extract the number of sessions for each hour of the day.

    Args:
        courseInfo (dict): The dictionaty that will be populated with the computed statistic. 
    """
    day_distribution = [0] * 24
    for userInfo in courseInfo['users'].values():
        user_distribution = userInfo['day_distribution']
        day_distribution = np.add(day_distribution, user_distribution)
    courseInfo['day_distribution'] = day_distribution


###########################
# System level extraction #
###########################


#######
# API #
#######


def execute_sessionInfo_extraction(sessionInfo: dict, logs_collection=None, session=None, data_provided=False, keep_session_data=False):
    """Execute a complete extraction for a single session.

    Note:
        If data_provided = True, than the only required parameter is sessionInfo.

    Args:
        sessionInfo (dict): The dictionary that will be populated with the computed statistics.
        logs_collection : The MongoDb collection that containes the logs.
        session (str): The id of the session we are interested in.
        data_provided (bool): Set to True if the sessionInfo has already been populated with the raw data. Defaults to False.
        keep_session_data (bool): Keep the raw session data in the system. Defaults to False.
    """
    if (not data_provided):
        # Get the raw data from the database
        utils.get_all_records_for_session(
            logs_collection, session, sessionInfo)
    # Set session_id
    add_lesson_id_to_session(sessionInfo)
    # Add session date
    add_session_date(sessionInfo)
    # Execute play_pause_extraction
    play_pause_extraction(sessionInfo)
    # Get session coverage
    session_coverage_extraction(sessionInfo)
    # Compute session duration
    compute_session_duration(sessionInfo)
    # Execute jumps_info_extraction
    jumps_info_extraction(sessionInfo)
    # Notes_info_extraction
    notes_info_extraction(sessionInfo)
    if(not keep_session_data):
        # Delete raw data for all users
        del sessionInfo['data']


def execute_userInfo_extraction(logs_collection, lessons_durations: dict, course: str,
                                user: str, userInfo: dict, keep_session_data=False, sessionInfo_provided=False):
    """Execute a complete extraction for a single user.

    Args:
        logs_collection : The MongoDb collection that containes the logs.
        lessons_durations (dict) : The systemInfo dictionary {'lesson_id':'lesson_duration'}.
        course (str): Used if sessionInfo_provided = False (as default)
        user (str): The id of the user whose userInfo we are extracting.
        userInfo (dict): The dictionary that will be populated with the computed statistics.
        keep_session_data (bool): Keep the raw session data in the system. Defaults to False.
        sessionInfo_provided (bool): Set to true if the sessionInfo has already been computed. Defaults to False.
    """
    if(not sessionInfo_provided):
        # Get the raw data from the database
        utils.get_all_records_for_user_and_course(
            logs_collection, course, user, userInfo)
        for sessionInfo in userInfo['sessions'].values():
            # Extract sessionInfo information
            execute_sessionInfo_extraction(
                sessionInfo, data_provided=True, keep_session_data=keep_session_data)
            # Add coverage percentage
            try:
                duration = lessons_durations[sessionInfo['lesson_id']]
                sessionInfo['coverage_percentage'] = sessionInfo[
                    'total_time_watched'] / duration
            except KeyError:
                sessionInfo['coverage_percentage'] = 'unknown'

    # Extract userInfo level statistics
    # user_lessons_coverage
    compute_lessons_coverage_for_single_user(userInfo, lessons_durations)
    # notes info extraction
    user_notes_info_extraction(userInfo)
    # jumps info extraction
    user_jump_info_extraction(userInfo)
    # Lessons_visualization extraction
    user_lessons_visualization_extraction(userInfo)
    # Get sessions day distribution
    day_session_distribution_extraction(userInfo)


def execute_courseInfo_extraction(logs_collection, lessons_collection, course: str, courseInfo: dict,
                                  keep_session_data=False, keep_user_info=True, query_mem_opt=True):
    """Execute a complete extraction for a single course.

    Note: query_mem_opt will keep a lot of data in memory due to mongoDb query caching mechanism.
        We have left the possibility of setting query_mem_opt to False though in practice we see 
        that there is no relevant speed improvement with big datasets (might have with small ones).

    Args:
        logs_collection : The MongoDb collection that containes the logs.
        lessons_collection : The MongoDb collection that containes the uploaded lessons logs.
        course: The id of the course whose information we are extracting.
        courseInfo (dict): The dictionary that will be populated with the computed statistics.
        keep_session_data (bool): Keep the raw session data in the system. Defaults to False.
        keep_user_info (bool): Keep the statistics computed at the userInfo level. Defaults to True.
        query_mem_opt (bool): Do only partial queries to keep memory usage low. Defaults to True.
    """

    # Check if the lessons_durations has already been extracted
    if ('lessons_durations' not in courseInfo.keys()):
        utils.get_lessons_durations_and_registration_dates(
            lessons_collection, course, courseInfo)
    # Create a counter for the total number of sessions
    total_number_of_sessions = 0

    if (not query_mem_opt):
        # Collect all raw data at once
        utils.get_all_users_records(logs_collection, course, courseInfo)
        # Extract features
        for user, userInfo in courseInfo['users'].items():
            for session, sessionInfo in userInfo['sessions'].items():
                # Execute sessionInfo extraction
                execute_sessionInfo_extraction(
                    sessionInfo, data_provided=True, keep_session_data=keep_session_data)
            execute_userInfo_extraction(logs_collection, courseInfo[
                                        'lessons_durations'], course, user, userInfo, keep_session_data=keep_session_data, sessionInfo_provided=True)
            # Add this user sessions to the total counter
            total_number_of_sessions += len(userInfo['sessions'])
    else:
        courseInfo['users'] = {}
        # Collect user ids
        users = utils.get_all_users_for_course(logs_collection, course)
        # Extract features
        for user in users:
            userInfo = {}
            execute_userInfo_extraction(logs_collection, courseInfo[
                                        'lessons_durations'], course, user, userInfo, keep_session_data=keep_session_data, sessionInfo_provided=False)
            # Add this user sessions to the total counter
            total_number_of_sessions += len(userInfo['sessions'])
            # Add this user to the systemInfo
            courseInfo['users'][user] = userInfo

    # Save the total number of sessions
    courseInfo['number_of_sessions'] = total_number_of_sessions
    # Compute system level statistics
    # Compute global coverage and histogram
    compute_course_global_coverage(courseInfo)
    # Execute notes info extraction
    course_notes_info_extraction(courseInfo)
    # Lessons_visualization extraction
    course_lessons_visualization_extraction(courseInfo)
    # Get sessions day distribution
    course_day_distribution_extraction(courseInfo)
    # Add update time
    courseInfo['last_update'] = datetime.utcnow()

    if (not keep_user_info):
        # Discard userInfo
        pass


def execute_complete_extraction(logs_collection, lessons_collection, systemInfo, keep_session_data=False, keep_user_info=True, query_mem_opt=True):
    """Execute a complete extraction of the whole system.

    This function extracts all the data from the collection, extracts the
    features we want, deletes the raw data and returns a dict of courseInfo, with
    one key(course_id) for each course in the database.

    Note: query_mem_opt will keep a lot of data in memory due to mongoDb query caching mechanism.
        We have left the possibility of setting query_mem_opt to False though in practice we see 
        that there is no relevant speed improvement with big datasets (might have with small ones).

    Args:
        logs_collection : The MongoDb collection that containes the logs.
        lessons_collection : The MongoDb collection that containes the uploaded lessons logs.
        systemInfo (dict): The dictionary that will be populated with the computed statistics.
        keep_session_data (bool): Keep the raw session data in the system. Defaults to False.
        keep_user_info (bool): Keep the statistics computed at the userInfo level. Defaults to True.
        query_mem_opt (bool): Do only partial queries to keep memory usage low. Defaults to True.
    """

    # Get courses headers
    courses = utils.get_all_courses(lessons_collection)

    for course in courses:
        courseInfo = {}
        # Extract features
        execute_courseInfo_extraction(logs_collection, lessons_collection, course, courseInfo,
                                      keep_session_data=keep_session_data, keep_user_info=keep_user_info, query_mem_opt=query_mem_opt)
        # Add this course to the systemInfo
        systemInfo['courses'][course] = courseInfo

    # Add update time
    systemInfo['last_update'] = datetime.utcnow()


#################
# Miscellaneous #
#################

def check_session_validity():
    """ Check if the session meets the basic requirements in order not to raise exceptions.
    """
    pass
    # Check if user has at least one session
    # Check if every session is well formed
