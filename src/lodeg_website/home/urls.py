from django.urls import include, re_path

from . import views

urlpatterns = [
    re_path(r'^contact/', views.contact, name='contact'),
    re_path(r'^user/', views.user, name='user'),
    re_path(r'^courseInfo/', views.courseInfo, name='courseInfo'),
    re_path(r'^userInfo/', views.userInfo, name='userInfo'),
    re_path(r'^sessionInfo/', views.sessionInfo, name='sessionInfo'),
    re_path(r'^collectDataFromDb/', views.collectDataFromDb, name='collectDataFromDb'),
    re_path(r'^saveDataToDb/', views.saveDataToDb, name='saveDataToDb'),
    re_path(r'^exportToCsv/', views.exportToCsv, name='exportToCsv'),
    re_path(r'^setUser/', views.setUser, name='setUser'),
    re_path(r'^setSession/', views.setSession, name='setSession'),
    re_path(r'^setLesson/', views.setLesson, name='setLesson'),
    re_path(r'^setCourse/', views.setCourse, name='setCourse'),
    re_path(r'^sendEmail/', views.sendEmail, name='sendEmail'),
    re_path(r'^executeCompleteExtraction/', views.executeCompleteExtraction,
        name='executeCompleteExtraction'),
    re_path(r'^$', views.index, name='index'),

    re_path(r'^settings/', views.settings, name='settings'),
    re_path(r'^modifySystemSettings/', views.modifySystemSettings,
        name='modifySystemSettings'),
    re_path(r'^debuggingConsole/', views.debuggingConsole, name='debuggingConsole')
]
