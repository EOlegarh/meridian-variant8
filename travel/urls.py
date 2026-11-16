from django.urls import path
from . import views
app_name='travel'
urlpatterns=[path('',views.home,name='home'),path('help/',views.faq,name='faq'),path('contacts/',views.contacts,name='contacts'),path('tours/',views.catalogue,name='tours'),path('search/',views.catalogue,name='search'),path('tours/<slug:slug>/',views.tour,name='tour'),path('directions/',views.directions,name='directions'),path('directions/<int:pk>/',views.direction,name='direction'),path('accounts/login/',views.page,name='login'),path('account/',views.page,name='dashboard'),path('bookings/new/<int:pk>/',views.page,name='booking_new')]
