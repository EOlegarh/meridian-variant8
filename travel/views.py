from datetime import date
from django.shortcuts import render
from .models import Tour

def home(request):
    tours=Tour.objects.filter(published=True).select_related('hotel__direction')
    featured=tours.filter(hotel__direction__name='Алтай').first()
    return render(request,'travel/home.html',{'featured':featured,'departure':featured.departures.filter(start_date__gt=date.today()).first(),'istanbul':tours.filter(hotel__direction__name='Стамбул').first(),'karelia':tours.filter(hotel__direction__name='Карелия').first()})

def page(request):return render(request,'travel/page.html',{'title':'Места и маршруты'})
