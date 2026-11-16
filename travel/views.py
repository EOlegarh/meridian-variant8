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

from django.shortcuts import get_object_or_404
from django.db.models import Q,Min,Prefetch,OuterRef,Exists
from django.core.paginator import Paginator
from .models import Direction,Departure,Review
from .forms import SearchForm

def tour_query():
    return Tour.objects.filter(published=True).select_related('hotel__direction').prefetch_related(Prefetch('departures',queryset=Departure.objects.filter(start_date__gt=date.today()).order_by('start_date'),to_attr='upcoming'))

def catalogue(request):
    form=SearchForm(request.GET);qs=tour_query()
    if form.is_valid():
        data=form.cleaned_data
        if data['q']:qs=qs.filter(Q(name__icontains=data['q'])|Q(hotel__direction__name__icontains=data['q'])|Q(description__icontains=data['q']))
        if data['direction']:qs=qs.filter(hotel__direction=data['direction'])
        if data['nights']:qs=qs.filter(nights__lte=data['nights'])
        dates=Departure.objects.filter(tour_id=OuterRef('pk'),start_date__gt=date.today())
        if data['date']:dates=dates.filter(start_date__gte=data['date'])
        if data['budget'] is not None:dates=dates.filter(adult_price__lte=data['budget'])
        qs=qs.filter(Exists(dates))
    else:qs=qs.none()
    page=Paginator(qs,20).get_page(request.GET.get('page'));query=request.GET.copy();query.pop('page',None)
    context={'title':'Результаты поиска' if request.resolver_match.url_name=='search' else 'Маршруты','form':form,'page_obj':page,'query':query.urlencode()}
    return render(request,'travel/catalogue.html',context)

def tour(request,slug):
    obj=get_object_or_404(tour_query(),slug=slug)
    reviews=Review.objects.filter(booking__departure__tour=obj).select_related('booking__user')
    return render(request,'travel/tour.html',{'title':obj.name,'tour':obj,'reviews':reviews})

def directions(request):
    return render(request,'travel/directions.html',{'title':'Атлас направлений','directions':Direction.objects.all()})

def direction(request,pk):
    obj=get_object_or_404(Direction,pk=pk)
    return render(request,'travel/direction.html',{'title':obj.name,'direction':obj,'tours':tour_query().filter(hotel__direction=obj)})
