from django.urls import path
from django.contrib.auth.views import LoginView,LogoutView
from . import views
app_name='travel'
urlpatterns=[
    path('',views.home,name='home'),path('help/',views.faq,name='faq'),path('contacts/',views.contacts,name='contacts'),
    path('tours/',views.catalogue,name='tours'),path('search/',views.catalogue,name='search'),path('tours/<slug:slug>/',views.tour,name='tour'),path('directions/',views.directions,name='directions'),path('directions/<int:pk>/',views.direction,name='direction'),
    path('accounts/login/',LoginView.as_view(template_name='travel/login.html'),name='login'),path('accounts/logout/',LogoutView.as_view(),name='logout'),path('accounts/register/',views.register,name='register'),path('accounts/password_change/',views.password,name='password'),
    path('account/',views.dashboard,name='dashboard'),path('account/profile/',views.profile,name='profile'),
    path('bookings/',views.bookings,name='bookings'),path('bookings/new/<int:pk>/',views.booking_new,name='booking_new'),path('bookings/<int:pk>/',views.booking,name='booking'),path('bookings/<int:pk>/edit/',views.booking_edit,name='booking_edit'),path('bookings/<int:pk>/cancel/',views.booking_cancel,name='booking_cancel'),path('bookings/<int:pk>/payment/',views.payment,name='payment'),path('bookings/<int:pk>/review/',views.review,name='review'),path('bookings/<int:pk>/print/',views.booking_print,name='booking_print'),
    path('manage/',views.manage,name='manage'),path('manage/bookings/',views.manage_bookings,name='manage_bookings'),path('manage/bookings/<int:pk>/',views.manage_booking,name='manage_booking'),path('manage/departures/',views.departures,name='departures'),path('manage/analytics/',views.analytics,name='analytics'),path('manage/export/',views.export,name='export'),path('staff/tours/',views.staff_tours,name='admin'),
]
urlpatterns += [path('staff/'+kind+'s/new/',views.staff_form,{'kind':kind},name=kind+'_new') for kind in ['tour','departure']]
urlpatterns += [path('staff/'+kind+'s/<int:pk>/edit/',views.staff_form,{'kind':kind},name=kind+'_edit') for kind in ['tour','departure']]
urlpatterns += [path('staff/'+kind+'s/<int:pk>/delete/',views.staff_delete,{'kind':kind},name=kind+'_delete') for kind in ['tour','departure']]

urlpatterns += [path('api/quote/<int:pk>/',views.quote_api,name='quote'),path('api/tours/',views.catalogue,name='catalog_api')]
