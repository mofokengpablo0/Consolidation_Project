from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class RegistrationForm(UserCreationForm):
    """Registration form with role selection."""
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.Select,
        help_text='Select your role'
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}), 
        required=False,
        help_text='For journalists only'
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'role', 'bio', 'password1', 'password2'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        
        if password1 and len(password1) < 8:
            raise forms.ValidationError(
                "Password must be at least 8 characters long."
            )
        
        return cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    """Profile update form."""
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_picture']
