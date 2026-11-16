from django import forms
from .models import Direction
class SearchForm(forms.Form):
    q=forms.CharField(label='Название или место',required=False,max_length=160)
    direction=forms.ModelChoiceField(label='Направление',queryset=Direction.objects.all(),required=False,empty_label='Все направления')
    date=forms.DateField(label='Заезды с даты',required=False,widget=forms.DateInput(attrs={'type':'date'}))
    budget=forms.DecimalField(label='Бюджет до, ₽',required=False,min_value=0,max_digits=12,decimal_places=2)
    nights=forms.IntegerField(label='Не больше ночей',required=False,min_value=1,max_value=30)

from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import Booking,ExtraService,Tour,Departure,Review
User=get_user_model()
class RegisterForm(UserCreationForm):
    email=forms.EmailField(label='Электронная почта',max_length=254)
    first_name=forms.CharField(label='Имя',max_length=150)
    class Meta: model=User;fields=['username','first_name','email','password1','password2']
    def clean_email(self):
        value=self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=value).exists():raise forms.ValidationError('Эта почта уже зарегистрирована.')
        return value
class ProfileForm(forms.ModelForm):
    email=forms.EmailField(label='Электронная почта',max_length=254)
    class Meta:model=User;fields=['first_name','last_name','email']
    def clean_email(self):
        value=self.cleaned_data['email'].lower()
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=value).exists():raise forms.ValidationError('Эта почта уже используется.')
        return value
class ContactForm(forms.Form):
    name=forms.CharField(label='Как к вам обращаться',max_length=100)
    email=forms.EmailField(label='Электронная почта',max_length=254)
    phone=forms.CharField(label='Телефон',max_length=25,validators=[RegexValidator(r'^\+?[0-9 ()-]{10,25}$','Укажите телефон: от 10 до 15 цифр, можно с +, пробелами и скобками.')],widget=forms.TextInput(attrs={'type':'tel','autocomplete':'tel','data-phone':'true'}))
    text=forms.CharField(label='Ваш вопрос',max_length=2000,widget=forms.Textarea(attrs={'rows':5}))
    def clean_phone(self):
        value=self.cleaned_data['phone']
        if not 10<=sum(c.isdigit() for c in value)<=15:raise forms.ValidationError('Телефон должен содержать от 10 до 15 цифр.')
        return value
class TouristForm(forms.Form):
    full_name=forms.CharField(label='ФИО туриста',max_length=180)
    birth_date=forms.DateField(label='Дата рождения',widget=forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d'))
    def clean_birth_date(self):
        value=self.cleaned_data['birth_date']
        if value>date.today() or (date.today()-value).days>121*366:raise forms.ValidationError('Проверьте дату рождения.')
        return value
TouristFormSet=forms.formset_factory(TouristForm,extra=0,min_num=1,validate_min=True,max_num=10,validate_max=True,absolute_max=10,can_delete=True)
class BookingForm(forms.Form):
    services=forms.ModelMultipleChoiceField(label='Дополнительные услуги',queryset=ExtraService.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    def __init__(self,*args,departure,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['services'].queryset=departure.tour.services.all()
class PaymentForm(forms.Form):
    amount=forms.DecimalField(label='Сумма, ₽',min_value='.01',max_digits=12,decimal_places=2)
    reference=forms.CharField(label='Идентификатор платежа',max_length=100,help_text='Уникальный номер учебного платежа. Повторная отправка с тем же номером не спишет сумму дважды.')
class ReviewForm(forms.ModelForm):
    class Meta:model=Review;fields=['rating','text','image'];widgets={'text':forms.Textarea(attrs={'rows':5,'maxlength':3000})}
class TourForm(forms.ModelForm):
    class Meta:model=Tour;fields=['name','slug','hotel','description','nights','published','image'];widgets={'description':forms.Textarea(attrs={'rows':6})}
class DepartureForm(forms.ModelForm):
    class Meta:model=Departure;fields=['tour','start_date','capacity','adult_price','child_price','infant_price'];widgets={'start_date':forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d')}
    def clean_capacity(self):
        value=self.cleaned_data['capacity']
        if value<(self.instance.reserved or 0):raise forms.ValidationError('Вместимость не может быть меньше числа занятых мест.')
        return value
    def clean_start_date(self):
        value=self.cleaned_data['start_date']
        if not self.instance.pk and value<=date.today():raise forms.ValidationError('Выберите будущую дату.')
        return value
