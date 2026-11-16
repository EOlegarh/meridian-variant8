from django.urls import path
from . import views
app_name='travel'
urlpatterns=[path('',views.home,name='home'),path('help/',views.faq,name='faq'),path('contacts/',views.contacts,name='contacts'),path('tours/',views.catalogue,name='tours'),path('search/',views.catalogue,name='search'),path('tours/<slug:slug>/',views.tour,name='tour'),path('directions/',views.directions,name='directions'),path('directions/<int:pk>/',views.direction,name='direction'),path('accounts/login/',views.page,name='login'),path('account/',views.dashboard,name='dashboard'),path('bookings/new/<int:pk>/',views.page,name='booking_new')]

urlpatterns += [path('account/profile/',views.page,name='profile'),path('accounts/password_change/',views.page,name='password'),path('accounts/logout/',views.page,name='logout'),path('bookings/',views.bookings,name='bookings'),path('bookings/<int:pk>/',views.booking,name='booking'),path('manage/',views.manage,name='manage'),path('manage/bookings/',views.manage_bookings,name='manage_bookings'),path('manage/bookings/<int:pk>/',views.manage_booking,name='manage_booking'),path('manage/departures/',views.departures,name='departures'),path('manage/analytics/',views.analytics,name='analytics'),path('staff/tours/',views.staff_tours,name='admin')]
urlpatterns += [path('bookings/<int:pk>/'+name+'/',views.page,name='booking_'+name) for name in ['edit','cancel','print']]
urlpatterns += [path('bookings/<int:pk>/'+name+'/',views.page,name=name) for name in ['payment','review']]
urlpatterns += [path('staff/'+kind+'s/new/',views.page,name=kind+'_new') for kind in ['tour','departure']]
urlpatterns += [path('staff/'+kind+'s/<int:pk>/'+action+'/',views.page,name=kind+'_'+action) for kind in ['tour','departure'] for action in ['edit','delete']]
urlpatterns += [path('manage/export/',views.page,name='export')]
