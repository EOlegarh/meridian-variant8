from datetime import date,timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError,PermissionDenied
from django.db import IntegrityError,transaction
from django.test import TestCase,override_settings
from .models import *
from .services import *

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class BookingLogicTests(TestCase):
    def setUp(self):
        self.u=get_user_model().objects.create_user('owner',email='o@example.test')
        self.other=get_user_model().objects.create_user('other')
        direction=Direction.objects.create(name='Алтай',country='Россия')
        hotel=Hotel.objects.create(direction=direction,name='Тест',stars=4,address='Адрес')
        self.tour=Tour.objects.create(hotel=hotel,name='Алтай',slug='altai',description='Тест',nights=6,published=True)
        self.d=Departure.objects.create(tour=self.tour,start_date=date(2027,7,10),capacity=3,adult_price=10000,child_price=7000,infant_price=2000)
        self.s=ExtraService.objects.create(name='Трансфер',basis='booking')
        self.ps=ExtraService.objects.create(name='Экскурсия',basis='person')
        TourService.objects.create(tour=self.tour,service=self.s,price=1500)
        TourService.objects.create(tour=self.tour,service=self.ps,price=500)
        self.people=[{'full_name':'Взрослый Турист','birth_date':date(1990,1,1)},{'full_name':'Ребёнок Турист','birth_date':date(2018,7,10)}]
    def test_child_and_extra_calculation(self):
        b=reserve(self.u,self.d.pk,self.people,[self.s.pk,self.ps.pk])
        self.assertEqual(b.total,Decimal('19500'))
        self.assertEqual(list(b.tourists.values_list('tariff',flat=True)),['adult','child'])
        self.d.refresh_from_db();self.assertEqual(self.d.reserved,2)
    def test_age_boundaries_on_departure(self):
        self.d.start_date=date(2027,7,10)
        births=[date(2025,7,11),date(2025,7,10),date(2015,7,11),date(2015,7,10)]
        result=quote(self.d,[dict(full_name='Турист',birth_date=d) for d in births],[])
        self.assertEqual([r['tariff'] for r in result['tourists']],['infant','child','child','adult'])
    def test_no_overbooking_and_no_partial_records(self):
        reserve(self.u,self.d.pk,self.people)
        with self.assertRaises(ValidationError):reserve(self.other,self.d.pk,self.people)
        self.assertEqual(Booking.objects.count(),1);self.assertEqual(BookingTourist.objects.count(),2)
        self.d.refresh_from_db();self.assertEqual(self.d.reserved,2)
    def test_cancel_releases_once(self):
        b=reserve(self.u,self.d.pk,self.people)
        cancel(self.u,b.pk);cancel(self.u,b.pk)
        self.d.refresh_from_db();self.assertEqual(self.d.reserved,0)
    def test_installments_idempotency_and_overpayment(self):
        b=reserve(self.u,self.d.pk,self.people)
        p=record_payment(self.u,b.pk,5000,'ONE')
        self.assertEqual(record_payment(self.u,b.pk,5000,'ONE').pk,p.pk)
        record_payment(self.u,b.pk,12000,'TWO')
        with self.assertRaises(ValidationError):record_payment(self.u,b.pk,1,'THREE')
        b.refresh_from_db();self.assertEqual(b.balance,0);self.assertEqual(b.payments.count(),2)
    def test_foreign_owner_forbidden(self):
        b=reserve(self.u,self.d.pk,self.people)
        with self.assertRaises(PermissionDenied):record_payment(self.other,b.pk,100,'FOREIGN')
        with self.assertRaises(PermissionDenied):cancel(self.other,b.pk)
    def test_unavailable_service_and_future_birth(self):
        s=ExtraService.objects.create(name='Чужая',basis='booking')
        with self.assertRaises(ValidationError):reserve(self.u,self.d.pk,self.people,[s.pk])
        with self.assertRaises(ValidationError):quote(self.d,[dict(full_name='Тест',birth_date=date.today()+timedelta(days=1))],[])
        self.d.refresh_from_db();self.assertEqual(self.d.reserved,0)
    def test_database_capacity_constraint(self):
        with self.assertRaises(IntegrityError),transaction.atomic():Departure.objects.filter(pk=self.d.pk).update(reserved=4)
    def test_paid_booking_requires_refund(self):
        b=reserve(self.u,self.d.pk,self.people);record_payment(self.u,b.pk,100,'PAID')
        with self.assertRaises(ValidationError):cancel(self.u,b.pk)
    def test_snapshot_survives_tariff_change(self):
        b=reserve(self.u,self.d.pk,self.people,[self.s.pk]);total=b.total
        Departure.objects.filter(pk=self.d.pk).update(adult_price=99999)
        TourService.objects.filter(tour=self.tour).update(price=99999)
        b.refresh_from_db();self.assertEqual(b.total,total)
        self.assertEqual(b.tourists.first().price,Decimal('10000'))
