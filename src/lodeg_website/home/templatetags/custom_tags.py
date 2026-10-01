from django import template
register = template.Library()


@register.filter
def is_bool(value):
    return isinstance(value, bool)


@register.filter
def not_debug(key):
    return key != 'debug'


@register.simple_tag(takes_context=True)
def getLastUpdate(context):
    return context['system'].getLastUpdate()


@register.simple_tag(takes_context=True)
def getSystemSettings(context):
    return context['system'].getSystemSettings()


@register.simple_tag(takes_context=True)
def getNumberOfUsers(context, level):
    if level == 'course':
        return context['system'].getNumberOfUsers(context['course'])
    else:
        return context['system'].getNumberOfUsers()


@register.simple_tag(takes_context=True)
def getNumberOfSessions(context, level):
    if level == 'user':
        return context['system'].getNumberOfSessions(
            context['course'], context['user'])
    elif level == 'course':
        return context['system'].getNumberOfSessions(context['course'])
    else:
        return context['system'].getNumberOfSessions()


@register.simple_tag(takes_context=True)
def getNumberOfLessons(context, level):
    if level == 'course':
        return context['system'].getNumberOfLessons(context['course'])
    else:
        return context['system'].getNumberOfLessons()


@register.simple_tag(takes_context=True)
def getUsers(context, level):
    if level == 'course':
        return context['system'].getUsers(context['course'])
    else:
        return context['system'].getUsers()


@register.simple_tag(takes_context=True)
def getUserCoveragePercentage(context):
    return context['system'].getUserCoveragePercentage(
        context['course'], context['user'])


@register.simple_tag(takes_context=True)
def extractUserData(context):
    return context['system'].extractUserData(
        context['course'], context['user'])


@register.simple_tag(takes_context=True)
def executeCompleteExtraction(context):
    return context['system'].executeCompleteExtraction()


###########
# HEADERS #
###########

@register.simple_tag(takes_context=True)
def getUserSessionsHeaders(context):
    return context['system'].getUserSessionsHeaders(
        context['course'], context['user'])


@register.simple_tag(takes_context=True)
def getLessonsHeaders(context):
    return context['system'].getLessonsHeaders(context['course'])


@register.simple_tag(takes_context=True)
def getCourses(context):
    return context['system'].getCourses()

##########
# Charts #
##########


@register.simple_tag(takes_context=True)
def printLessonUserCorrelationGraph(context, time_format=None):
    return context['system'].printLessonUserCorrelationGraph(
        context['course'], time_format)


@register.simple_tag(takes_context=True)
def printSessionCoverage(context):
    return context['system'].printSessionCoverage(
        context['course'], context['user'], context['session'])


@register.simple_tag(takes_context=True)
def printLessonCoverage(context, level):
    if (level == 'user'):
        return context['system'].printLessonCoverage(
            context['lesson'], context['course'], context['user'])
    else:
        return context['system'].printLessonCoverage(
            context['lesson'], context['course'])


@register.simple_tag(takes_context=True)
def printLessonsHistogram(context, level):
    if (level == 'user'):
        return context['system'].printLessonsHistogram(
            context['course'], context['user'])
    else:
        return context['system'].printLessonsHistogram(context['course'])


@register.simple_tag(takes_context=True)
def printNotesBarChart(context, level):
    if (level == 'course'):
        return context['system'].printNotesBarChart(context['course'])
    elif (level == 'user'):
        return context['system'].printNotesBarChart(
            context['course'], context['user'])
    else:
        return context['system'].printNotesBarChart(
            context['course'], context['user'], context['session'])


@register.simple_tag(takes_context=True)
def printDaySessionDistribution(context, level):
    if (level == 'user'):
        return context['system'].printDaySessionDistribution(
            context['course'], context['user'])
    else:
        return context['system'].printDaySessionDistribution(context['course'])
