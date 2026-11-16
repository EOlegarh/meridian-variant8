from django.urls import path
from . import views
app_name='travel'
urlpatterns=[path('',views.home,name='home')]+[path(p+'/',views.page,name=p) for p in ['tours','directions','faq','contacts','login','dashboard']]+[path('tours/<slug:slug>/',views.page,name='tour')]
