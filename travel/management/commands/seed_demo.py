from datetime import date,timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test.utils import override_settings
from travel.models import *
from travel.services import reserve,record_payment

class Command(BaseCommand):
    help='Создать согласованные демонстрационные данные в пустой базе.'
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @transaction.atomic
    def handle(self,*args,**kwargs):
        if Tour.objects.exists():raise CommandError('База уже заполнена; повторный запуск не изменяет существующие данные.')
        U=get_user_model()
        for role in ['admin','manager']:
            U.objects.create_user(role,email=role+'@example.test',password='DemoTravel8!2026',is_staff=True,is_superuser=(role=='admin'))
        users=[U.objects.create_user(f'tourist{i:02}',email=f'tourist{i:02}@example.test',password='DemoTravel8!2026',first_name='Турист',last_name=str(i)) for i in range(1,13)]
        names=[('Алтай','Россия'),('Карелия','Россия'),('Байкал','Россия'),('Казань','Россия'),('Стамбул','Турция'),('Анталья','Турция'),('Тбилиси','Грузия'),('Ереван','Армения'),('Самарканд','Узбекистан'),('Минск','Беларусь'),('Дагестан','Россия'),('Калининград','Россия')]
        services=[ExtraService.objects.create(name=n,basis=b) for n,b in [('Трансфер','booking'),('Экскурсия в старый город','person'),('Страхование багажа','person'),('Ужин с местной кухней','person'),('Музейный абонемент','person'),('Индивидуальный гид','booking'),('Ранний заезд','booking'),('Поздний выезд','booking'),('Прогулка на катере','person'),('Фотосессия','booking')]]
        deps=[]
        for i,(name,country) in enumerate(names):
            d=Direction.objects.create(name=name,country=country,description='Демонстрационное направление. Учебные цены не являются предложением реального тура.')
            h=Hotel.objects.create(direction=d,name='Меридиан '+name,stars=3+i%3,address=f'{name}, Туристическая улица, {i+1}')
            t=Tour.objects.create(hotel=h,name=name+' — неделя открытий',slug=f'tour-{i+1}',description='День 1: прибытие и размещение. Дни 2–6: прогулки и экскурсии. День 7: возвращение.',nights=6,published=True)
            for k,s in enumerate(services[:4]):TourService.objects.create(tour=t,service=s,price=Decimal(1500+k*500))
            for k in range(3):
                p=Decimal(32000+i*2500+k*1000)
                deps.append(Departure.objects.create(tour=t,start_date=date.today()+timedelta(days=30+i*3+k*14),capacity=40,adult_price=p,child_price=p*Decimal('.70'),infant_price=p*Decimal('.20')))
        # Все брони создаются тем же серверным сервисом, что и будущая форма сайта.
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            for i in range(36):
                u=users[i%12];d=deps[i]
                people=[dict(full_name=f'Алексей Демонстрационный {i+1}',birth_date=date(1990,3,12)),dict(full_name=f'Анна Демонстрационная {i+1}',birth_date=date(1992,7,1))]
                if i%2==0:people.append(dict(full_name=f'Михаил Демонстрационный {i+1}',birth_date=date.today().replace(year=date.today().year-8)))
                b=reserve(u,d.pk,people,[services[i%4].pk])
                if i%3!=0:
                    record_payment(u,b.pk,b.total*Decimal('.30'),f'DEMO-{i+1}-1')
                if i%6==1:
                    b.refresh_from_db();record_payment(u,b.pk,b.balance,f'DEMO-{i+1}-2')
        # Отдельные завершённые поездки — источник реалистичных отзывов.
        for i in range(12):
            b=Booking.objects.all()[i];b.status='completed';b.paid=b.total;b.save(update_fields=['status','paid'])
            Departure.objects.filter(pk=b.departure_id).update(start_date=date.today()-timedelta(days=80-i*3))
            current=sum(b.payments.values_list('amount',flat=True),Decimal('0'))
            if current<b.total:Payment.objects.create(booking=b,amount=b.total-current,reference=f'DEMO-FINAL-{b.pk}')
            Review.objects.create(booking=b,rating=4+i%2,text='Учебный отзыв: понравились программа и понятный расчёт стоимости. Все данные вымышлены.')
        self.stdout.write(self.style.SUCCESS('Данные созданы: 12 туров, 36 заездов, 36 бронирований, 90 туристов.'))
