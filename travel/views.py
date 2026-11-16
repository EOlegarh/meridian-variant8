from datetime import date
from django.shortcuts import render
from .models import Tour

def home(request):
    tours=Tour.objects.filter(published=True).select_related('hotel__direction')
    featured=tours.filter(hotel__direction__name='Алтай').first()
    return render(request,'travel/home.html',{'featured':featured,'departure':featured.departures.filter(start_date__gt=date.today()).first() if featured else None,'istanbul':tours.filter(hotel__direction__name='Стамбул').first(),'karelia':tours.filter(hotel__direction__name='Карелия').first()})

def faq(request):
    return render(request,'travel/faq.html',{'title':'Как устроено путешествие'})

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
    if request.resolver_match.url_name=='catalog_api':
        from django.template.loader import render_to_string
        return JsonResponse({'html':render_to_string('includes/catalog_results.html',context,request=request),'count':page.paginator.count})
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

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm,PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse,JsonResponse
from django.conf import settings
import json
from django.views.decorators.http import require_POST
from .forms import RegisterForm,ProfileForm,ContactForm,TouristFormSet,BookingForm,PaymentForm,ReviewForm,TourForm,DepartureForm
from .services import reserve,update_booking,cancel,record_payment,quote
import csv,uuid

def register(request):
    form=RegisterForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save();login(request,user);messages.success(request,'Аккаунт создан. Можно выбирать путешествие.');return redirect('travel:dashboard')
    return render(request,'travel/form.html',{'title':'Начнём путешествие','form':form,'submit':'Создать аккаунт','auth':True})

@login_required
def profile(request):
    form=ProfileForm(request.POST or None,instance=request.user)
    if request.method=='POST' and form.is_valid():form.save();messages.success(request,'Профиль сохранён.');return redirect('travel:profile')
    return render(request,'travel/account_form.html',{'title':'Ваш профиль','form':form,'submit':'Сохранить профиль'})

@login_required
def password(request):
    form=PasswordChangeForm(request.user,request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save();update_session_auth_hash(request,user);messages.success(request,'Пароль изменён.');return redirect('travel:dashboard')
    return render(request,'travel/account_form.html',{'title':'Смена пароля','form':form,'submit':'Сохранить пароль'})

def contacts(request):
    form=ContactForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        d=form.cleaned_data
        send_mail('Вопрос о путешествии',f"{d['name']} / {d['email']} / {d['phone']}\n{d['text']}",'demo@localhost',['manager@example.test'])
        messages.success(request,'Сообщение передано менеджеру через почтовый модуль. В учебном режиме письмо выводится в консоль сервера.');return redirect('travel:contacts')
    return render(request,'travel/form.html',{'title':'На связи перед дорогой','intro':'Меридиан · Учебное турагентство. Расскажите, куда хотите поехать, или задайте вопрос о бронировании.','form':form,'submit':'Отправить вопрос','credits':json.loads((settings.BASE_DIR/'static/images/sources.json').read_text())})

def tourists_from(formset):return [dict(full_name=f.cleaned_data['full_name'],birth_date=f.cleaned_data['birth_date']) for f in formset if f.cleaned_data and not f.cleaned_data.get('DELETE')]

@login_required
def booking_form(request,pk,edit=False):
    b=own_booking(request,pk) if edit else None
    d=b.departure if b else get_object_or_404(Departure.objects.select_related('tour'),pk=pk,tour__published=True)
    if edit and (b.paid or b.status!='confirmed'):raise PermissionDenied
    if d.start_date<=date.today():raise PermissionDenied
    initial=list(b.tourists.values('full_name','birth_date')) if b else []
    formset=TouristFormSet(request.POST or None,initial=initial,prefix='tourists')
    form=BookingForm(request.POST or None,departure=d,initial={'services':list(b.extras.values_list('service_id',flat=True)) if b else []})
    if request.method=='POST':
        valid=form.is_valid();valid_set=formset.is_valid()
        if valid and valid_set:
            try:
                people=tourists_from(formset);ids=list(form.cleaned_data['services'].values_list('pk',flat=True))
                result=update_booking(request.user,b.pk,people,ids) if edit else reserve(request.user,d.pk,people,ids)
            except ValidationError as e:form.add_error(None,e)
            else:
                messages.success(request,'Бронирование обновлено.' if edit else 'Места забронированы. Подтверждение отправлено на почту.');return redirect('travel:booking',pk=result.pk)
    return render(request,'travel/booking_form.html',{'title':'Изменить туристов' if edit else 'Кто отправится в путешествие?','form':form,'formset':formset,'departure':d,'booking':b})

@login_required
def booking_new(request,pk):return booking_form(request,pk)
@login_required
def booking_edit(request,pk):return booking_form(request,pk,edit=True)

@login_required
def booking_cancel(request,pk):
    b=own_booking(request,pk);error=''
    if request.method=='POST':
        try:cancel(request.user,b.pk)
        except ValidationError as e:error=' '.join(e.messages)
        else:messages.success(request,'Бронирование отменено. Места возвращены в продажу.');return redirect('travel:booking',pk=b.pk)
    return render(request,'travel/confirm.html',{'title':'Отменить бронирование?','text':f'{b.departure.tour.name}. Неоплаченную бронь можно отменить. Для оплаченной поездки обратитесь к менеджеру.','error':error,'booking':b,'submit':'Подтвердить отмену'})

@login_required
def payment(request,pk):
    b=own_booking(request,pk,staff=request.user.is_staff)
    form=PaymentForm(request.POST or None,initial={'amount':b.balance,'reference':'DEMO-'+uuid.uuid4().hex[:16]})
    if request.method=='POST' and form.is_valid():
        try:record_payment(request.user,b.pk,**form.cleaned_data)
        except ValidationError as e:form.add_error(None,e)
        else:messages.success(request,'Учебный платёж записан. Банковское списание не выполнялось.');return redirect('travel:manage_booking' if request.user.is_staff else 'travel:booking',pk=b.pk)
    return render(request,'travel/account_form.html',{'title':f'Оплата брони №{b.pk}','intro':f'Остаток {b.balance} ₽. Учебный режим: банковский эквайринг не подключён. Можно внести часть суммы.','form':form,'submit':'Записать учебный платёж'})

@login_required
def review(request,pk):
    b=own_booking(request,pk)
    if b.status!='completed':raise PermissionDenied
    instance=Review.objects.filter(booking=b).first() or Review(booking=b)
    form=ReviewForm(request.POST or None,request.FILES or None,instance=instance)
    if request.method=='POST' and form.is_valid():form.save();messages.success(request,'Спасибо! Отзыв сохранён.');return redirect('travel:booking',pk=b.pk)
    return render(request,'travel/account_form.html',{'title':'Что запомнилось в поездке?','intro':b.departure.tour.name,'form':form,'submit':'Сохранить отзыв'})

@login_required
def staff_form(request,kind,pk=None):
    require_staff(request,admin=True);model,form_class=(Tour,TourForm) if kind=='tour' else (Departure,DepartureForm)
    instance=get_object_or_404(model,pk=pk) if pk else model()
    form=form_class(request.POST or None,request.FILES or None,instance=instance)
    if request.method=='POST' and form.is_valid():
        # Protect capacity even if another reservation arrived after the form was opened.
        from django.db import transaction
        with transaction.atomic():
            current=model.objects.select_for_update().filter(pk=pk).first() if pk else None
            if kind=='departure' and current and form.cleaned_data['capacity']<current.reserved:form.add_error('capacity','Количество занятых мест изменилось. Увеличьте вместимость.')
            else:
                if current and kind=='departure':form.instance.reserved=current.reserved
                form.save();messages.success(request,'Изменения сохранены.');return redirect('travel:admin' if kind=='tour' else 'travel:departures')
    return render(request,'travel/account_form.html',{'title':('Изменить ' if pk else 'Добавить ')+('маршрут' if kind=='tour' else 'заезд'),'form':form,'submit':'Сохранить'})

@login_required
def staff_delete(request,kind,pk):
    require_staff(request,admin=True);model=Tour if kind=='tour' else Departure;obj=get_object_or_404(model,pk=pk);error=''
    if request.method=='POST':
        try:obj.delete()
        except ProtectedError:error='Удаление невозможно: запись используется в заездах или бронированиях. У тура можно снять публикацию.'
        else:messages.success(request,'Запись удалена.');return redirect('travel:admin' if kind=='tour' else 'travel:departures')
    return render(request,'travel/confirm.html',{'title':'Удалить запись?','text':str(obj),'error':error,'submit':'Удалить'})

@login_required
def booking_print(request,pk):
    b=own_booking(request,pk,staff=request.user.is_staff)
    return render(request,'travel/print.html',{'title':f'Памятка по брони №{b.pk}','booking':b})

@login_required
def export(request):
    require_staff(request);response=HttpResponse(content_type='text/csv; charset=utf-8-sig');response['Content-Disposition']='attachment; filename="bookings.csv"';response.write('\ufeff')
    writer=csv.writer(response,delimiter=';');writer.writerow(['Бронь','Заказчик','Маршрут','Дата','Статус','Мест','Стоимость','Оплачено'])
    for b in Booking.objects.select_related('user','departure__tour'):
        safe=lambda x:"'"+x if isinstance(x,str) and x.startswith(('=','+','-','@')) else x
        writer.writerow([b.pk,safe(b.user.username),safe(b.departure.tour.name),b.departure.start_date,b.get_status_display(),b.seats,b.total,b.paid])
    return response

@login_required
@require_POST
def quote_api(request,pk):
    departure=get_object_or_404(Departure.objects.select_related('tour'),pk=pk,tour__published=True)
    form=BookingForm(request.POST,departure=departure);formset=TouristFormSet(request.POST,prefix='tourists')
    ok=form.is_valid();people_ok=formset.is_valid()
    if not ok or not people_ok:return JsonResponse({'error':'Заполните ФИО и корректные даты рождения всех туристов.','fields':form.errors.get_json_data(),'tourists':[f.errors.get_json_data() for f in formset]},status=400)
    try:
        result=quote(departure,tourists_from(formset),form.cleaned_data['services'].values_list('pk',flat=True))
    except (ValidationError,ValueError) as e:return JsonResponse({'error':' '.join(e.messages) if isinstance(e,ValidationError) else 'Проверьте услуги.'},status=400)
    return JsonResponse({'total':str(result['total']),'seats':len(result['tourists']),'available':departure.available,'rows':[{'name':r['full_name'],'tariff':{'adult':'взрослый','child':'ребёнок','infant':'малыш'}[r['tariff']],'price':str(r['price'])} for r in result['tourists']],'extras':[{'name':e['service'].name,'quantity':e['quantity'],'price':str(e['unit_price'])} for e in result['extras']]})
