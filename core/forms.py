from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# IMPORTANT: Import User and all models from your local models
from .models import User, Vehicle, TripLog, FuelLog, ExpenseLog, NewCar

from .models import Vehicle

# --- USER AUTH FORMS (UPDATED: Added Phone Number) ---
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        # ONLY include 'username'. 
        # Passwords are included automatically by the parent UserCreationForm.
        fields = ('username',)

# core/forms.py
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'profile_photo']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'readonly': 'readonly'}),
            'email': forms.EmailInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'accept': 'image/*'}),
        }



class VehicleForm(forms.ModelForm):
    # 1. Make these optional in the Form Validation
    # (We will handle Make/Model manually in the View)
    make = forms.CharField(required=False)
    model_name = forms.CharField(required=False)
    
    # 2. Make Price optional (It will use the default 500000 from models.py if missing)
    purchase_price = forms.DecimalField(required=False)

    class Meta:
        model = Vehicle
        fields = [
            'category', 
            'make', 
            'model_name', 
            'license_plate', 
            'fuel_type', 
            'ownership_type', 
            'current_odometer', 
            'purchase_year', 
            'purchase_price', # Keep this here, but we made it optional above
            'insurance_expiry', 
            'pollution_expiry', 
            'fitness_expiry'
        ]
        
        widgets = {
            'insurance_expiry': forms.DateInput(attrs={'type': 'date'}),
            'pollution_expiry': forms.DateInput(attrs={'type': 'date'}),
            'fitness_expiry': forms.DateInput(attrs={'type': 'date'}),
        }
# --- TRIP LOG FORM ---
class TripLogForm(forms.ModelForm):
    class Meta:
        model = TripLog
        fields = ['vehicle', 'date', 'purpose', 'start_odometer', 'end_odometer', 'notes']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
            'start_odometer': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'end_odometer': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'date': forms.DateInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'type': 'date'}),
        }

    def __init__(self, user, *args, **kwargs):
        super(TripLogForm, self).__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(owner=user, is_active=True)

# --- EXPENSE LOG FORM ---
class ExpenseLogForm(forms.ModelForm):
    class Meta:
        model = ExpenseLog
        fields = ['vehicle', 'expense_type', 'amount', 'date']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
            'expense_type': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'date': forms.DateInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'type': 'date'}),
        }

    def __init__(self, user, *args, **kwargs):
        super(ExpenseLogForm, self).__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(owner=user, is_active=True)

# --- CAR RECOMMENDATION FORM ---


# --- TRIP CALCULATOR FORM ---
class TripCalculatorForm(forms.Form):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.none(), 
        label="Select Vehicle",
        widget=forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'})
    )
    distance_km = forms.FloatField(
        label="Trip Distance (km)",
        widget=forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'e.g. 150'})
    )
    fuel_price = forms.FloatField(
        label="Current Fuel Price (₹/L)",
        widget=forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'e.g. 102.5'})
    )
    custom_mileage = forms.FloatField(
        label="Manual Mileage (Optional)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'Leave empty to use vehicle history'})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(owner=user, is_active=True)

# --- FUEL LOG FORM ---
class FuelLogForm(forms.ModelForm):
    class Meta:
        model = FuelLog
        fields = ['odometer_reading', 'liters_filled', 'total_cost', 'date']
        widgets = {
            'odometer_reading': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'e.g. 42650'}),
            'liters_filled': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'e.g. 12.5'}),
            'total_cost': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'e.g. 1500'}),
            'date': forms.DateInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'type': 'date'}),
        }
# core/forms.py

class ExpenseLogForm(forms.ModelForm):
    # Add the receipt image field here if you want AI scanning later
    receipt_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}))

    class Meta:
        model = ExpenseLog
        fields = ['vehicle', 'expense_type', 'amount', 'date', 'receipt_image']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
            'expense_type': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'e.g. 500'}),
            'date': forms.DateInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'type': 'date'}),
        }

    # --- THIS IS THE MISSING PART CAUSING THE ERROR ---
    def __init__(self, user, *args, **kwargs):
        super(ExpenseLogForm, self).__init__(*args, **kwargs)
        # Filter vehicles to show only the ones owned by this user
        self.fields['vehicle'].queryset = Vehicle.objects.filter(owner=user, is_active=True)
from .models import NewCar

class NewCarForm(forms.ModelForm):
    class Meta:
        model = NewCar
        fields = ['make', 'model', 'car_type', 'price_lakhs', 'vehicle_image', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class CarRecommendationForm(forms.Form):
    vehicle_type = forms.ChoiceField(choices=[
        ('Any', 'Any Type'), ('Hatchback', 'Hatchback'), 
        ('Sedan', 'Sedan'), ('SUV', 'SUV'), ('EV', 'EV')
    ], required=False)
    min_price = forms.IntegerField(required=False, label="Min Price (₹)")
    max_price = forms.IntegerField(required=False, label="Max Price (₹)")
