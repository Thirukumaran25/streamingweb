from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class RegisterForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=100, 
        label="Full Name",
        widget=forms.TextInput(attrs={
            'placeholder': 'Full Name',
            # JavaScript to block numbers and special characters on press
            'onkeypress': "return (event.charCode > 64 && event.charCode < 91) || (event.charCode > 96 && event.charCode < 123) || event.charCode == 32"
        }),
        validators=[RegexValidator(r'^[a-zA-Z\s]*$', 'Numbers and special characters are not allowed.')]
    )
    
    mobile_no = forms.CharField(
        max_length=10, 
        min_length=10,
        label="Mobile Number",
        widget=forms.TextInput(attrs={
            'placeholder': '10-Digit Mobile Number',
            'type': 'tel',
            # JavaScript to block anything that isn't a number
            'onkeypress': "return event.charCode >= 48 && event.charCode <= 57"
        }),
        validators=[RegexValidator(r'^\d{10}$', 'Mobile number must be exactly 10 digits.')]
    )
    
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'})
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'id': 'regPassword'}), 
        label="Password"
    )

    class Meta:
        model = User
        fields = ['full_name', 'email', 'mobile_no', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]
        
        names = self.cleaned_data["full_name"].split(" ", 1)
        user.first_name = names[0]
        user.last_name = names[1] if len(names) > 1 else ""
        
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user