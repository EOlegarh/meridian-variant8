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

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum,Count,Avg,F
from .models import Booking,Payment

def require_staff(request,admin=False):
    if not request.user.is_authenticated or not (request.user.is_superuser if admin else request.user.is_staff):raise PermissionDenied

def own_booking(request,pk,staff=False):
    obj=get_object_or_404(Booking.objects.select_related('user','departure__tour__hotel__direction').prefetch_related('tourists','extras__service','payments'),pk=pk)
    if staff:require_staff(request)
    elif obj.user_id!=request.user.pk:raise PermissionDenied
    return obj

@login_required
def dashboard(request):
    if request.user.is_staff:return manage(request)
    qs=request.user.bookings.select_related('departure__tour__hotel__direction')
    return render(request,'travel/dashboard.html',{'title':'Ваши путешествия','bookings':qs[:3],'totals':qs.aggregate(count=Count('id'),total=Sum('total'),paid=Sum('paid'))})

@login_required
def bookings(request):
    qs=request.user.bookings.select_related('departure__tour')
    page=Paginator(qs,20).get_page(request.GET.get('page'))
    return render(request,'travel/bookings.html',{'title':'Мои бронирования','page_obj':page})

@login_required
def booking(request,pk):
    b=own_booking(request,pk)
    return render(request,'travel/booking.html',{'title':str(b),'booking':b})

@login_required
def manage(request):
    require_staff(request)
    totals=Booking.objects.aggregate(count=Count('id'),revenue=Sum('total'),paid=Sum('paid'),seats=Sum('seats'))
    return render(request,'travel/manage.html',{'title':'Рабочий стол менеджера','totals':totals,'bookings':Booking.objects.select_related('user','departure__tour')[:5]})

@login_required
def manage_bookings(request):
    require_staff(request);qs=Booking.objects.select_related('user','departure__tour')
    status=request.GET.get('status','');q=request.GET.get('q','').strip()[:160]
    if status in dict(Booking._meta.get_field('status').choices):qs=qs.filter(status=status)
    if q:qs=qs.filter(Q(user__username__icontains=q)|Q(departure__tour__name__icontains=q))
    return render(request,'travel/manage_bookings.html',{'title':'Все бронирования','page_obj':Paginator(qs,20).get_page(request.GET.get('page')),'q':q,'status':status})

@login_required
def manage_booking(request,pk):
    b=own_booking(request,pk,staff=True)
    return render(request,'travel/booking.html',{'title':str(b),'booking':b,'staff':True})

@login_required
def departures(request):
    require_staff(request)
    qs=Departure.objects.select_related('tour')
    return render(request,'travel/departures.html',{'title':'Заезды и свободные места','page_obj':Paginator(qs,20).get_page(request.GET.get('page'))})

@login_required
def analytics(request):
    require_staff(request)
    return render(request,'travel/analytics.html',{'title':'Итоги путешествий','totals':Booking.objects.exclude(status='cancelled').aggregate(count=Count('id'),total=Sum('total'),paid=Sum('paid'),seats=Sum('seats')),'rating':Review.objects.aggregate(avg=Avg('rating'))['avg'],'groups':Booking.objects.values('departure__tour__hotel__direction__name').annotate(count=Count('id'),seats=Sum('seats'),paid=Sum('paid')).order_by('-count')})

@login_required
def staff_tours(request):
    require_staff(request,admin=True)
    return render(request,'travel/staff_tours.html',{'title':'Управление маршрутами','page_obj':Paginator(Tour.objects.select_related('hotel__direction'),20).get_page(request.GET.get('page'))})

def not_found(request,exception=None):return render(request,'travel/page.html',{'title':'Страница не найдена','text':'Проверьте адрес или откройте раздел «Все маршруты».'},status=404)
def forbidden(request,exception=None):return render(request,'travel/page.html',{'title':'Доступ ограничен','text':'Эта страница доступна владельцу бронирования или сотруднику с соответствующей ролью.'},status=403)
