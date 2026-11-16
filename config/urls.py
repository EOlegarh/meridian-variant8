from django.contrib import admin
from django.urls import path,include
urlpatterns=[path('admin/',admin.site.urls),path('',include('travel.urls'))]

handler404='travel.views.not_found'
handler403='travel.views.forbidden'
