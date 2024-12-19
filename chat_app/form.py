from django import forms

class MobileLoginForm(forms.Form):
    mobile_number = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)
