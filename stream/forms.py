from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
    full_name = forms.CharField(max_length=100, label="Full Name")
    mobile_no = forms.CharField(max_length=15, label="Mobile Number")
    email = forms.EmailField(label="Email Address")
    password = forms.CharField(widget=forms.PasswordInput(), label="Password")

    class Meta:
        model = User
        fields = ['full_name', 'email', 'mobile_no', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]  # Email serves as username
        
        # Split full name for Django's built-in fields
        names = self.cleaned_data["full_name"].split(" ", 1)
        user.first_name = names[0]
        user.last_name = names[1] if len(names) > 1 else ""
        
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user