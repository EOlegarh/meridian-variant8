from django.urls import path
from . import views
app_name='travel'
urlpatterns=[path('',views.home,name='home'),path('help/',views.faq,name='faq'),path('contacts/',views.contacts,name='contacts')]+[path(p+'/',views.page,name=p) for p in ['tours','directions','login','dashboard']]+[path('tours/<slug:slug>/',views.page,name='tour')]
