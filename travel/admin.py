from django.contrib import admin
from .models import Direction,Hotel,Tour,ExtraService,TourService,Departure,Booking,BookingTourist,BookingExtra,Payment,Review
admin.site.site_header='Меридиан · Турагентство'
admin.site.site_title='Вариант 8'
admin.site.index_title='Данные учебного проекта'
class TouristInline(admin.TabularInline):
    model=BookingTourist;extra=0
    readonly_fields=['full_name','birth_date','tariff','price']
    can_delete=False
    def has_add_permission(self,request,obj=None):return False
class ExtraInline(admin.TabularInline):
    model=BookingExtra;extra=0
    readonly_fields=['service','unit_price','quantity']
    can_delete=False
    def has_add_permission(self,request,obj=None):return False
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display=['id','user','departure','status','seats','total','paid']
    list_filter=['status','departure__tour__hotel__direction']
    search_fields=['user__username','tourists__full_name']
    inlines=[TouristInline,ExtraInline]
    readonly_fields=['user','departure','status','seats','total','paid','created_at']
    def has_add_permission(self,request):return False
    def has_delete_permission(self,request,obj=None):return False
@admin.register(Departure)
class DepartureAdmin(admin.ModelAdmin):
    list_display=['tour','start_date','capacity','reserved','adult_price','child_price','infant_price']
    readonly_fields=['reserved']
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display=['reference','booking','amount','created_at']
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False
for model in [Direction,Hotel,Tour,ExtraService,TourService,Review]:admin.site.register(model)
