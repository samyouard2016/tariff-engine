from django.conf.urls import url

from . import views
from .views import (index, AdvancedSearch, ratestructure, Savings)
from django.views.decorators.cache import cache_page

urlpatterns =[
    url(r'^$', index , name='index'),
    url(r'^advancedsearch$', AdvancedSearch , name='AdvancedSearch'),
    url(r'^ratestructure$', ratestructure , name='ratestructure'),
    url(r'^savings$', Savings , name='Savings'),
]