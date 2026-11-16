from datetime import date
from decimal import Decimal,InvalidOperation
from django.core.exceptions import ValidationError,PermissionDenied
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from .models import Departure,Booking,BookingTourist,TourService,BookingExtra,Payment

def age_on(birth,on):
    return on.year-birth.year-((on.month,on.day)<(birth.month,birth.day))

def quote(departure,tourists,service_ids):
    if not 1<=len(tourists)<=10:raise ValidationError('Укажите от 1 до 10 туристов.')
    rows=[]
    for data in tourists:
        birth=data['birth_date']
        if not isinstance(birth,date) or birth>date.today():raise ValidationError('Проверьте дату рождения.')
        if not str(data['full_name']).strip() or len(data['full_name'])>180:raise ValidationError('Укажите ФИО туриста.')
        age=age_on(birth,departure.start_date)
        if not 0<=age<=120:raise ValidationError('Возраст туриста вне допустимого диапазона.')
        kind='infant' if age<2 else 'child' if age<12 else 'adult'
        rows.append(dict(full_name=data['full_name'].strip(),birth_date=birth,tariff=kind,price=getattr(departure,kind+'_price')))
    ids=set(map(int,service_ids))
    extras=list(TourService.objects.filter(tour=departure.tour,service_id__in=ids).select_related('service'))
    if len(extras)!=len(ids):raise ValidationError('Услуга недоступна для этого тура.')
    items=[dict(service=e.service,unit_price=e.price,quantity=len(rows) if e.service.basis=='person' else 1) for e in extras]
    total=sum((r['price'] for r in rows),Decimal('0'))+sum((r['unit_price']*r['quantity'] for r in items),Decimal('0'))
    return {'tourists':rows,'extras':items,'total':total.quantize(Decimal('.01'))}

@transaction.atomic
def reserve(user,departure_id,tourists,service_ids=()):
    if not user.is_authenticated:raise PermissionDenied
    d=Departure.objects.select_for_update().select_related('tour').get(pk=departure_id)
    if d.start_date<=date.today() or not d.tour.published:raise ValidationError('Бронирование закрыто.')
    result=quote(d,tourists,service_ids)
    n=len(tourists)
    changed=Departure.objects.filter(pk=d.pk,reserved__lte=F('capacity')-n).update(reserved=F('reserved')+n)
    if changed!=1:raise ValidationError('На выбранный заезд недостаточно мест. Выберите другую дату.')
    b=Booking.objects.create(user=user,departure=d,seats=n,total=result['total'])
    BookingTourist.objects.bulk_create([BookingTourist(booking=b,**r) for r in result['tourists']])
    BookingExtra.objects.bulk_create([BookingExtra(booking=b,**r) for r in result['extras']])
    transaction.on_commit(lambda:send_mail('Бронирование подтверждено',f'Бронь №{b.pk}. К оплате {b.total} ₽.','demo@localhost',[user.email],fail_silently=False))
    return b

@transaction.atomic
def record_payment(user,booking_id,amount,reference):
    b=Booking.objects.select_for_update().get(pk=booking_id)
    if b.user_id!=user.pk and not user.is_staff:raise PermissionDenied
    if b.status!='confirmed':raise ValidationError('Оплата недоступна для этого статуса.')
    try:amount=Decimal(str(amount))
    except (InvalidOperation,ValueError):raise ValidationError('Неверная сумма.')
    if not amount.is_finite() or amount<=0 or amount!=amount.quantize(Decimal('.01')):raise ValidationError('Сумма должна быть положительной, с точностью до копейки.')
    if not reference or len(reference)>100:raise ValidationError('Укажите идентификатор платежа.')
    old=Payment.objects.filter(reference=reference).first()
    if old:
        if old.booking_id==b.pk and old.amount==amount:return old
        raise ValidationError('Идентификатор платежа уже использован.')
    if Booking.objects.filter(pk=b.pk,status='confirmed',paid__lte=F('total')-amount).update(paid=F('paid')+amount)!=1:raise ValidationError('Сумма превышает остаток к оплате.')
    return Payment.objects.create(booking=b,amount=amount,reference=reference)

@transaction.atomic
def cancel(user,booking_id):
    b=Booking.objects.select_for_update().get(pk=booking_id)
    if b.user_id!=user.pk and not user.is_staff:raise PermissionDenied
    if b.status=='cancelled':return b
    if b.status!='confirmed' or b.paid:raise ValidationError('Отмена оплаченной брони выполняется менеджером после возврата; автоматический возврат в учебном проекте не реализуется.')
    if Booking.objects.filter(pk=b.pk,status='confirmed',paid=0).update(status='cancelled')!=1:raise ValidationError('Бронь уже изменена.')
    if Departure.objects.filter(pk=b.departure_id,reserved__gte=b.seats).update(reserved=F('reserved')-b.seats)!=1:raise ValidationError('Нарушен учёт мест.')
    b.status='cancelled';return b
