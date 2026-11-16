from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator,MaxValueValidator,FileExtensionValidator
from django.db import models
from django.db.models import Q,F

def image_size(value):
    if value.size>5*1024*1024: raise ValidationError('Размер изображения не больше 5 МиБ.')

class Direction(models.Model):
    name=models.CharField('направление',max_length=100,unique=True)
    country=models.CharField('страна',max_length=80)
    description=models.TextField('описание',blank=True)
    class Meta:
        verbose_name='направление';verbose_name_plural='направления';ordering=['country','name']
    def __str__(self):return self.name

class Hotel(models.Model):
    direction=models.ForeignKey(Direction,on_delete=models.PROTECT,related_name='hotels',verbose_name='направление')
    name=models.CharField('название',max_length=160)
    stars=models.PositiveSmallIntegerField('звёзды',validators=[MinValueValidator(1),MaxValueValidator(5)])
    address=models.CharField('адрес',max_length=255)
    class Meta:
        verbose_name='отель';verbose_name_plural='отели';ordering=['name']
        constraints=[models.UniqueConstraint(fields=['direction','name'],name='hotel_direction_name'),models.CheckConstraint(condition=Q(stars__gte=1,stars__lte=5),name='hotel_stars_1_5')]
    def __str__(self):return self.name

class ExtraService(models.Model):
    name=models.CharField('услуга',max_length=100,unique=True)
    PER_PERSON='person';PER_BOOKING='booking'
    basis=models.CharField('единица тарифа',max_length=8,choices=[(PER_PERSON,'за туриста'),(PER_BOOKING,'за бронь')])
    class Meta:
        verbose_name='дополнительная услуга';verbose_name_plural='дополнительные услуги';ordering=['name']
        constraints=[models.CheckConstraint(condition=Q(basis__in=['person','booking']),name='service_basis_valid')]
    def __str__(self):return self.name

class Tour(models.Model):
    hotel=models.ForeignKey(Hotel,on_delete=models.PROTECT,related_name='tours',verbose_name='отель')
    name=models.CharField('название',max_length=160)
    slug=models.SlugField('адрес',unique=True,max_length=160)
    description=models.TextField('программа')
    nights=models.PositiveSmallIntegerField('ночей',validators=[MinValueValidator(1),MaxValueValidator(30)])
    published=models.BooleanField('опубликован',default=False)
    image=models.ImageField('фотография',upload_to='tours/%Y/%m/',blank=True,validators=[image_size,FileExtensionValidator(['jpg','jpeg','png','webp'])])
    services=models.ManyToManyField(ExtraService,through='TourService',related_name='tours',verbose_name='дополнительные услуги')
    class Meta:
        verbose_name='тур';verbose_name_plural='туры';ordering=['name']
        constraints=[models.CheckConstraint(condition=Q(nights__gte=1,nights__lte=30),name='tour_nights_1_30')]
    def __str__(self):return self.name

class TourService(models.Model):
    tour=models.ForeignKey(Tour,on_delete=models.CASCADE,related_name='service_prices',verbose_name='тур')
    service=models.ForeignKey(ExtraService,on_delete=models.PROTECT,related_name='tour_prices',verbose_name='услуга')
    price=models.DecimalField('цена',max_digits=12,decimal_places=2,validators=[MinValueValidator(Decimal('0'))])
    class Meta:
        verbose_name='услуга тура';verbose_name_plural='услуги туров';ordering=['tour','service']
        constraints=[models.UniqueConstraint(fields=['tour','service'],name='unique_tour_service'),models.CheckConstraint(condition=Q(price__gte=0),name='tour_service_price_positive')]
    def __str__(self):return f'{self.tour}: {self.service}'

class Departure(models.Model):
    tour=models.ForeignKey(Tour,on_delete=models.PROTECT,related_name='departures',verbose_name='тур')
    start_date=models.DateField('дата заезда')
    capacity=models.PositiveIntegerField('всего мест',validators=[MinValueValidator(1)])
    reserved=models.PositiveIntegerField('занято мест',default=0)
    adult_price=models.DecimalField('взрослый (12+)',max_digits=12,decimal_places=2,validators=[MinValueValidator(Decimal('0'))])
    child_price=models.DecimalField('ребёнок (2–11)',max_digits=12,decimal_places=2,validators=[MinValueValidator(Decimal('0'))])
    infant_price=models.DecimalField('малыш (0–1)',max_digits=12,decimal_places=2,validators=[MinValueValidator(Decimal('0'))])
    class Meta:
        verbose_name='дата заезда';verbose_name_plural='даты заезда';ordering=['start_date','pk']
        constraints=[models.UniqueConstraint(fields=['tour','start_date'],name='unique_tour_date'),models.CheckConstraint(condition=Q(capacity__gte=1,reserved__gte=0,reserved__lte=F('capacity')),name='departure_capacity_valid'),models.CheckConstraint(condition=Q(adult_price__gte=0,child_price__gte=0,infant_price__gte=0),name='departure_prices_positive')]
    def __str__(self):return f'{self.tour} — {self.start_date}'
    @property
    def available(self):return self.capacity-self.reserved

class Booking(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='bookings',verbose_name='заказчик')
    departure=models.ForeignKey(Departure,on_delete=models.PROTECT,related_name='bookings',verbose_name='заезд')
    status=models.CharField('статус',max_length=12,choices=[('confirmed','подтверждено'),('cancelled','отменено'),('completed','завершено')],default='confirmed')
    seats=models.PositiveSmallIntegerField('мест',validators=[MinValueValidator(1),MaxValueValidator(10)])
    total=models.DecimalField('стоимость',max_digits=12,decimal_places=2)
    paid=models.DecimalField('оплачено',max_digits=12,decimal_places=2,default=0)
    created_at=models.DateTimeField('создано',auto_now_add=True)
    class Meta:
        verbose_name='бронирование';verbose_name_plural='бронирования';ordering=['-created_at','-pk']
        constraints=[models.CheckConstraint(condition=Q(seats__gte=1,seats__lte=10),name='booking_seats_1_10'),models.CheckConstraint(condition=Q(total__gte=0,paid__gte=0,paid__lte=F('total')),name='booking_amounts_valid'),models.CheckConstraint(condition=Q(status__in=['confirmed','cancelled','completed']),name='booking_status_valid')]
    def __str__(self):return f'Бронь №{self.pk}'
    @property
    def balance(self):return self.total-self.paid

class BookingTourist(models.Model):
    booking=models.ForeignKey(Booking,on_delete=models.CASCADE,related_name='tourists',verbose_name='бронь')
    full_name=models.CharField('ФИО',max_length=180)
    birth_date=models.DateField('дата рождения')
    tariff=models.CharField('тариф',max_length=6,choices=[('adult','взрослый'),('child','детский'),('infant','малыш')])
    price=models.DecimalField('цена на дату брони',max_digits=12,decimal_places=2)
    class Meta:
        verbose_name='турист в бронировании';verbose_name_plural='туристы в бронировании';ordering=['booking','pk']
        constraints=[models.CheckConstraint(condition=Q(price__gte=0),name='tourist_price_positive'),models.CheckConstraint(condition=Q(tariff__in=['adult','child','infant']),name='tourist_tariff_valid')]
    def __str__(self):return self.full_name

class BookingExtra(models.Model):
    booking=models.ForeignKey(Booking,on_delete=models.CASCADE,related_name='extras',verbose_name='бронь')
    service=models.ForeignKey(ExtraService,on_delete=models.PROTECT,related_name='booking_extras',verbose_name='услуга')
    unit_price=models.DecimalField('цена на дату брони',max_digits=12,decimal_places=2)
    quantity=models.PositiveSmallIntegerField('количество',validators=[MinValueValidator(1)])
    class Meta:
        verbose_name='услуга бронирования';verbose_name_plural='услуги бронирования';ordering=['booking','pk']
        constraints=[models.UniqueConstraint(fields=['booking','service'],name='unique_booking_service'),models.CheckConstraint(condition=Q(unit_price__gte=0,quantity__gte=1),name='booking_extra_positive')]
    def __str__(self):return f'{self.booking}: {self.service}'

class Payment(models.Model):
    booking=models.ForeignKey(Booking,on_delete=models.PROTECT,related_name='payments',verbose_name='бронь')
    amount=models.DecimalField('сумма',max_digits=12,decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))])
    reference=models.CharField('внешний идентификатор',max_length=100,unique=True)
    created_at=models.DateTimeField('дата платежа',auto_now_add=True)
    class Meta:
        verbose_name='платёж';verbose_name_plural='платежи';ordering=['-created_at','-pk']
        constraints=[models.CheckConstraint(condition=Q(amount__gt=0),name='payment_positive')]
    def __str__(self):return f'Платёж {self.reference}: {self.amount}'

class Review(models.Model):
    booking=models.OneToOneField(Booking,on_delete=models.PROTECT,related_name='review',verbose_name='бронирование')
    rating=models.PositiveSmallIntegerField('оценка',validators=[MinValueValidator(1),MaxValueValidator(5)])
    text=models.TextField('текст',max_length=3000)
    image=models.ImageField('фото',upload_to='reviews/%Y/%m/',blank=True,validators=[image_size,FileExtensionValidator(['jpg','jpeg','png','webp'])])
    created_at=models.DateTimeField('дата',auto_now_add=True)
    class Meta:
        verbose_name='отзыв';verbose_name_plural='отзывы';ordering=['-created_at','-pk']
        constraints=[models.CheckConstraint(condition=Q(rating__gte=1,rating__lte=5),name='review_rating_1_5')]
    def clean(self):
        if self.booking_id and self.booking.status!='completed':raise ValidationError('Отзыв доступен после завершённой поездки.')
    def __str__(self):return f'Отзыв: {self.booking}'
