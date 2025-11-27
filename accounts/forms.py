from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from classes.models import Grade, ClassRoom

class StudentRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    grade = forms.ModelChoiceField(queryset=Grade.objects.all())
    class_room = forms.ModelChoiceField(queryset=ClassRoom.objects.filter(name__in=['A', 'B', 'C', 'D']), required=False)