from django import forms
from django.forms import ModelForm
from .models import Group

class GroupForm(ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'papers']  # Adjust accordingly

class SetOperationForm(forms.Form):
    operation_choices = [
        ('union', 'Union'),
        ('intersection', 'Intersection'),
        ('difference', 'Difference'),
    ]
    operation = forms.ChoiceField(choices=operation_choices)
    group1 = forms.ModelChoiceField(queryset=Group.objects.all())
    group2 = forms.ModelChoiceField(queryset=Group.objects.all())


from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
