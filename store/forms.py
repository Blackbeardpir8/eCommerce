from django import forms
from store.models import *
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django import forms 
from django.forms import modelformset_factory
from store.models import Product

# Register user form
class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
# Login form
class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Username', max_length=254)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'password']





#Product Form

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'category', 'subcategory', 'stock']


ProductImageFormSet = modelformset_factory(
    ProductImage,
    fields=('image',),
    extra=1,  # number of image fields shown
    max_num=1,
)