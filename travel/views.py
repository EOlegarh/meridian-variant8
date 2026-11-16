from datetime import date
from django.shortcuts import render
from .models import Tour

def home(request):
    tours=Tour.objects.filter(published=True).select_related('hotel__direction')
    featured=tours.filter(hotel__direction__name='Алтай').first()
    return render(request,'travel/home.html',{'featured':featured,'departure':featured.departures.filter(start_date__gt=date.today()).first(),'istanbul':tours.filter(hotel__direction__name='Стамбул').first(),'karelia':tours.filter(hotel__direction__name='Карелия').first()})

def page(request, **kwargs):return render(request,'travel/page.html',{'title':'Места и маршруты'})


def faq(request):
    return render(request,'travel/faq.html',{'title':'Как устроено путешествие'})

def contacts(request):
    return render(request,'travel/page.html',{'title':'На связи перед дорогой','text':'Меридиан. Учебное турагентство. Вопросы о заезде, составе группы и дополнительных услугах можно отправить через форму обратной связи. Контактный адрес: demo@localhost.'})
