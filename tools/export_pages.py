"""Render the UI inventory with seeded records and real Django sessions."""
from pathlib import Path
import json,os,sys,re
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django;django.setup()
from django.test import Client,override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import F
from travel.models import Tour,Departure,Booking
from datetime import date
rows=[]
def add(key,name,role=None,args=None,query='',status=200):rows.append(dict(key=key,url=reverse('travel:'+name,args=args)+query,role=role,status=status))
for key in ['home','tours','directions','faq','contacts','login','register']:add(key,key)
add('search','search',query='?q=Алтай')
tour=Tour.objects.get(hotel__direction__name='Алтай');add('tour','tour',args=[tour.slug]);add('direction','direction',args=[tour.hotel.direction_id])
for key in ['dashboard','bookings','profile','password']:add(key,key,'tourist01')
departure=tour.departures.filter(start_date__gt=date.today()).first();add('booking_new','booking_new','tourist01',[departure.pk])
b=Booking.objects.filter(status='confirmed',paid=0,departure__start_date__gt=date.today()).select_related('user').first()
assert b,'Seed must include an editable booking'
for key in ['booking','booking_edit','booking_cancel','booking_print']:add(key,key,b.user.username,[b.pk])
p=Booking.objects.filter(status='confirmed',paid__lt=F('total')).select_related('user').first();add('payment','payment',p.user.username,[p.pk])
r=Booking.objects.filter(status='completed').select_related('user').first();add('review','review',r.user.username,[r.pk])
for key in ['manage','manage_bookings','departures','analytics']:add(key,key,'manager')
add('manage_booking','manage_booking','manager',[b.pk]);add('admin','admin','admin')
for kind,obj in [('tour',tour),('departure',departure)]:
 add(kind+'_new',kind+'_new','admin')
 for action in ['edit','delete']:add(kind+'_'+action,kind+'_'+action,'admin',[obj.pk])
rows.extend([dict(key='error404',url='/missing-page/',role=None,status=404),dict(key='error403',url=reverse('travel:manage'),role='tourist01',status=403)])
OUT=ROOT/'evidence';(OUT/'html').mkdir(parents=True,exist_ok=True)
with override_settings(DEBUG=False):
 for row in rows:
  c=Client()
  if row['role']:c.force_login(User.objects.get(username=row['role']))
  r=c.get(row['url']);assert r.status_code==row['status'],(row,r.status_code)
  html=re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]+',r'\1REDACTED',r.content.decode())
  (OUT/'html'/(row['key']+'.html')).write_text(html)
(OUT/'pages.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(len(rows),'pages captured')
