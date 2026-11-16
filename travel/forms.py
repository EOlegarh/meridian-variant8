from django import forms
from .models import Direction
class SearchForm(forms.Form):
    q=forms.CharField(label='Название или место',required=False,max_length=160)
    direction=forms.ModelChoiceField(label='Направление',queryset=Direction.objects.all(),required=False,empty_label='Все направления')
    date=forms.DateField(label='Заезды с даты',required=False,widget=forms.DateInput(attrs={'type':'date'}))
    budget=forms.DecimalField(label='Бюджет до, ₽',required=False,min_value=0,max_digits=12,decimal_places=2)
    nights=forms.IntegerField(label='Не больше ночей',required=False,min_value=1,max_value=30)
