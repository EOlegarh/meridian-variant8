from datetime import date,timedelta
from decimal import Decimal
from django.test import TestCase,Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Direction,Hotel,Tour,Departure,Booking,Payment,Review
from .services import reserve

class InterfaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user=User.objects.create_user('traveler',email='user@example.test',password='StrongDemo8!')
        cls.other=User.objects.create_user('other',password='StrongDemo8!')
        cls.manager=User.objects.create_user('manager',password='StrongDemo8!',is_staff=True)
        cls.admin=User.objects.create_superuser('admin','admin@example.test','StrongDemo8!')
        d=Direction.objects.create(name='Алтай',country='Россия');h=Hotel.objects.create(direction=d,name='Горы',stars=4,address='Горно-Алтайск')
        cls.tour=Tour.objects.create(name='Дорога к горам',slug='mountains',hotel=h,nights=6,description='Программа из базы',published=True)
        cls.departure=Departure.objects.create(tour=cls.tour,start_date=date.today()+timedelta(days=60),capacity=10,adult_price=30000,child_price=21000,infant_price=6000)
    def setUp(self):self.client.force_login(self.user)
    def url(self,name,*args):return reverse('travel:'+name,args=args)
    def data(self,n=1):
        data={'tourists-TOTAL_FORMS':str(n),'tourists-INITIAL_FORMS':'0','tourists-MIN_NUM_FORMS':'1','tourists-MAX_NUM_FORMS':'10'}
        for i in range(n):data.update({f'tourists-{i}-full_name':f'Турист {i+1}',f'tourists-{i}-birth_date':'1990-01-01'})
        return data
    def make(self,user=None):return reserve(user or self.user,self.departure.pk,[{'full_name':'Иван Петров','birth_date':date(1990,1,1)}])
    def test_empty_home(self):
        Tour.objects.update(published=False);self.assertEqual(self.client.get(self.url('home')).status_code,200)
    def test_catalogue_filters_and_json(self):
        self.assertContains(self.client.get(self.url('tours'),{'q':'Дорога','budget':40000}),self.tour.name)
        self.assertNotContains(self.client.get(self.url('tours'),{'budget':100}),self.tour.name)
        self.assertEqual(self.client.get(self.url('catalog_api'),{'q':'Дорога'}).json()['count'],1)
        self.assertEqual(self.client.get(self.url('catalog_api'),{'budget':'ошибка'}).json()['count'],0)
    def test_pagination(self):
        for i in range(22):
            t=Tour.objects.create(name=f'Маршрут {i:02}',slug=f'tour-{i}',hotel=self.tour.hotel,nights=4,description='Данные',published=True)
            Departure.objects.create(tour=t,start_date=self.departure.start_date,capacity=10,adult_price=1000,child_price=700,infant_price=200)
        self.assertEqual(len(self.client.get(self.url('tours')).context['page_obj']),20)
        self.assertEqual(len(self.client.get(self.url('tours'),{'page':2}).context['page_obj']),3)
    def test_authentication_and_quote_validation(self):
        url=self.url('quote',self.departure.pk);self.assertEqual(self.client.get(url).status_code,405)
        self.assertEqual(self.client.post(url,self.data(2)).json()['total'],'60000.00')
        data=self.data();data['tourists-0-birth_date']='2099-01-01';self.assertEqual(self.client.post(url,data).status_code,400)
        self.client.logout();self.assertEqual(self.client.get(self.url('booking_new',self.departure.pk)).status_code,302)
    def test_csrf(self):
        c=Client(enforce_csrf_checks=True);c.force_login(self.user)
        self.assertEqual(c.post(self.url('quote',self.departure.pk),self.data()).status_code,403)
    def test_booking_errors_values_and_prg(self):
        url=self.url('booking_new',self.departure.pk);data=self.data();data['tourists-0-birth_date']='wrong'
        self.assertContains(self.client.post(url,data),'Турист 1');self.assertEqual(Booking.objects.count(),0)
        r=self.client.post(url,self.data(2));self.assertEqual(r.status_code,302);b=Booking.objects.get();self.assertEqual(b.seats,2)
        self.assertContains(self.client.get(r.url),'Места забронированы')
    def test_edit_updates_capacity(self):
        b=self.make();data=self.data(2);data['tourists-INITIAL_FORMS']='1'
        self.assertEqual(self.client.post(self.url('booking_edit',b.pk),data).status_code,302)
        b.refresh_from_db();self.departure.refresh_from_db();self.assertEqual((b.seats,b.total,self.departure.reserved),(2,Decimal(60000),2))
    def test_foreign_booking_and_role_access(self):
        b=self.make(self.other)
        for name in ['booking','booking_edit','booking_cancel','payment','review','booking_print']:self.assertEqual(self.client.get(self.url(name,b.pk)).status_code,403,name)
        for name in ['manage','manage_bookings','departures','analytics','admin','export']:self.assertEqual(self.client.get(self.url(name)).status_code,403,name)
        self.client.force_login(self.manager);self.assertEqual(self.client.get(self.url('manage')).status_code,200);self.assertEqual(self.client.get(self.url('tour_edit',self.tour.pk)).status_code,403)
    def test_cancel_get_is_safe(self):
        b=self.make();self.client.get(self.url('booking_cancel',b.pk));b.refresh_from_db();self.assertEqual(b.status,'confirmed')
        self.assertEqual(self.client.post(self.url('booking_cancel',b.pk)).status_code,302);self.departure.refresh_from_db();self.assertEqual(self.departure.reserved,0)
    def test_partial_idempotent_payment(self):
        b=self.make();url=self.url('payment',b.pk);data={'amount':'5000','reference':'TEST-ONCE'}
        self.client.post(url,data);self.client.post(url,data);b.refresh_from_db();self.assertEqual(b.paid,Decimal(5000));self.assertEqual(Payment.objects.count(),1)
        self.assertEqual(self.client.get(self.url('booking_edit',b.pk)).status_code,403)
        self.assertEqual(self.client.post(url,{'amount':'999999','reference':'TOO-MUCH'}).status_code,200)
    def test_review_completion_required(self):
        b=self.make();url=self.url('review',b.pk);self.assertEqual(self.client.get(url).status_code,403)
        b.status='completed';b.save();self.assertEqual(self.client.post(url,{'rating':5,'text':'Спасибо за поездку'}).status_code,302)
        self.client.post(url,{'rating':4,'text':'Обновлённый отзыв'});self.assertEqual(Review.objects.count(),1);self.assertEqual(Review.objects.get().rating,4)
    def test_contact_server_validation(self):
        data={'name':'Олег','email':'bad','phone':'123','text':'Вопрос о датах'};r=self.client.post(self.url('contacts'),data)
        self.assertContains(r,'Вопрос о датах');self.assertTrue(r.context['form'].errors)
        data.update(email='oleg@example.test',phone='+7 (999) 123-45-67');self.assertEqual(self.client.post(self.url('contacts'),data).status_code,302)
    def test_registration_profile(self):
        self.client.logout();r=self.client.post(self.url('register'),{'username':'newuser','first_name':'Олег','email':'oleg@example.test','password1':'StrongDemo8!','password2':'StrongDemo8!'})
        self.assertEqual(r.status_code,302);self.assertTrue(User.objects.filter(username='newuser').exists())
        self.client.post(self.url('profile'),{'first_name':'Олег','last_name':'Елеков','email':'oleg@example.test'});self.assertEqual(User.objects.get(username='newuser').last_name,'Елеков')
    def test_admin_capacity_protection(self):
        self.make();self.client.force_login(self.admin);d=self.departure
        data={'tour':self.tour.pk,'start_date':d.start_date,'capacity':0,'adult_price':30000,'child_price':21000,'infant_price':6000}
        r=self.client.post(self.url('departure_edit',d.pk),data);self.assertEqual(r.status_code,200);self.assertTrue(r.context['form'].errors)
        self.assertContains(self.client.post(self.url('tour_delete',self.tour.pk)),'Удаление невозможно')
    def test_admin_creates_and_deletes(self):
        self.client.force_login(self.admin);data={'hotel':self.tour.hotel_id,'name':'Новый тур','slug':'new-route','description':'Новая программа','nights':5,'published':'on'}
        self.assertEqual(self.client.post(self.url('tour_new'),data).status_code,302);obj=Tour.objects.get(slug='new-route')
        self.assertEqual(self.client.post(self.url('tour_delete',obj.pk)).status_code,302);self.assertFalse(Tour.objects.filter(pk=obj.pk).exists())
    def test_export_and_print(self):
        b=self.make();self.assertContains(self.client.get(self.url('booking_print',b.pk)),'Памятка')
        self.client.force_login(self.manager);r=self.client.get(self.url('export'));self.assertIn('text/csv',r['Content-Type']);self.assertIn(str(b.total),r.content.decode('utf-8-sig'))
    def test_image_upload_is_validated_and_saved(self):
        import tempfile,io
        from PIL import Image
        from django.test import override_settings
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.admin)
        data={'hotel':self.tour.hotel_id,'name':'Маршрут с фото','slug':'with-photo','description':'Программа','nights':5,'published':'on'}
        with tempfile.TemporaryDirectory() as directory,override_settings(MEDIA_ROOT=directory):
            data['image']=SimpleUploadedFile('bad.jpg',b'not an image',content_type='image/jpeg')
            response=self.client.post(self.url('tour_new'),data);self.assertEqual(response.status_code,200);self.assertIn('image',response.context['form'].errors)
            buffer=io.BytesIO();Image.new('RGB',(32,32),'green').save(buffer,'PNG');data['image']=SimpleUploadedFile('place.png',buffer.getvalue(),content_type='image/png')
            self.assertEqual(self.client.post(self.url('tour_new'),data).status_code,302)
            obj=Tour.objects.get(slug='with-photo');self.assertTrue(obj.image.storage.exists(obj.image.name))
