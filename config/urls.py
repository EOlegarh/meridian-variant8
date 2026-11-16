from django.contrib import admin
from django.urls import path,include
urlpatterns=[path('admin/',admin.site.urls),path('',include('travel.urls'))]

handler404='travel.views.not_found'
handler403='travel.views.forbidden'

from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
