from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^register$', views.register),
    url(r'^login$', views.login),
    url(r'^quotes$', views.quotes_index),
    url(r'^logout$', views.logout),
    url(r'^quotes/new_speaker$', views.quotes_new_speaker),
    url(r'^new_speaker$', views.add_speaker),
    url(r'^newquote$', views.add_quote),
    url(r'^add_to_favs/(?P<quote_id>\d+)$', views.add_quote_to_favs),
    url(r'^remove_from_favs/(?P<quote_id>\d+)$', views.remove_quote_from_favs),
    url(r'^quotes_by_user/(?P<user_id>\d+)$', views.quotes_uploaded_by),
    url(r'^quotes_by_speaker/(?P<speaker_id>\d+)$', views.quotes_spoken_by)
]
