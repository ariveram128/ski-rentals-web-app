from django import forms
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from equipment.models import Equipment, EquipmentImage, Collection
from users.models import UserProfile

class EquipmentForm(ModelForm):
    is_available = forms.BooleanField(initial=True, required=False)

    class Meta:
        model = Equipment
        exclude = ("average_rating", "total_rentals")
        widgets = {
            'rental_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'weekly_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'seasonal_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'rent_to_own_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter appropriate size',
                'id': 'id_size_input',
            }),
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    # We'll add a size_select field that will be shown for categorical sizes
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['size_select'] = forms.ChoiceField(
            choices=[('', '-- Select Size --')] + [
                ('XS', 'XS'),
                ('S', 'S'),
                ('M', 'M'),
                ('L', 'L'),
                ('XL', 'XL'),
                ('XXL', 'XXL'),
            ],
            required=False,
            widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_size_select'}),
        )

        # Add information text to help users with size formats
        self.fields['size'].help_text = 'For skis, snowboards, poles: enter cm size (e.g., 175). For boots: enter Mondopoint (e.g., 25.5).'

    def clean(self):
        cleaned_data = super().clean()
        equipment_type = cleaned_data.get('equipment_type')
        size = cleaned_data.get('size')
        rental_price = cleaned_data.get('rental_price')
        rent_to_own_price = cleaned_data.get('rent_to_own_price')
        brand = cleaned_data.get('brand')
        model = cleaned_data.get('model')

        # Validate brand and model lengths
        if brand and len(brand) > 50:
            self.add_error('brand', "Brand name should be 50 characters or less.")

        if model and len(model) > 50:
            self.add_error('model', "Model name should be 50 characters or less.")

        # Validate rent-to-own price is higher than rental price
        if rental_price and rent_to_own_price and rent_to_own_price <= rental_price:
            self.add_error('rent_to_own_price', "Rent-to-own price should be higher than the daily rental price.")

        if not equipment_type or not size:
            return cleaned_data

        # Clean/normalize the size input
        size_str = str(size).strip().upper()

        # Validate based on equipment type
        if equipment_type in ['SKI', 'SNOWBOARD', 'POLES']:
            # These should be numerical cm values
            try:
                if not size_str.replace('.', '', 1).isdigit():
                    self.add_error('size',
                                   f"{equipment_type} size must be a number (e.g., 175), without units like 'cm'.")
                else:
                    size_float = float(size_str)
                    if size_float <= 0:
                        self.add_error('size', f"{equipment_type} size must be a positive number in centimeters.")
                    else:
                        # Validate within reasonable ranges
                        if equipment_type == 'SKI' and (size_float < 70 or size_float > 200):
                            self.add_error('size', "Ski size should typically be between 70 and 200 cm.")
                        elif equipment_type == 'SNOWBOARD' and (size_float < 80 or size_float > 180):
                            self.add_error('size', "Snowboard size should typically be between 80 and 180 cm.")
                        elif equipment_type == 'POLES' and (size_float < 70 or size_float > 140):
                            self.add_error('size', "Pole size should typically be between 70 and 140 cm.")
            except ValueError:
                self.add_error('size', f"{equipment_type} size must be a valid number.")

        elif equipment_type == 'BOOTS':
            # Mondopoint measurements (may include decimal)
            try:
                size_float = float(size_str)  # Only use period as decimal separator
                if size_float < 15.0 or size_float > 33.0:
                    self.add_error('size', "Boot size (Mondopoint) should typically be between 15.0 and 33.0.")
            except ValueError:
                self.add_error('size', "Boot size must be a Mondopoint measurement (e.g., 25.5).")

        elif equipment_type in ['HELMET', 'GOGGLES', 'GLOVES', 'JACKET', 'PANTS', 'OTHER']:
            # Categorical sizes
            valid_sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
            if size_str not in valid_sizes:
                self.add_error('size', f"Size must be one of: {', '.join(valid_sizes)}")

        return cleaned_data

class CollectionForm(ModelForm):
    class Meta:
        model = Collection
        fields = ['title', 'description', 'sharing_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'sharing_type': forms.Select(attrs={'class': 'form-control'})
        }
    
    def save(self, commit=True):
        collection = super().save(commit=False)
        
        # Set is_public based on sharing_type
        collection.is_public = (collection.sharing_type == 'PUBLIC')
        
        if commit:
            collection.save()
            
        return collection

class EquipmentImageForm(ModelForm):
    class Meta:
        model = EquipmentImage
        fields = ('image', 'caption')

# Form for multiple images at once
class MultipleImageUploadForm(forms.Form):
    images = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={}),
    )
    
    def clean_images(self):
        """Handle multiple image uploads by accessing request.FILES directly in the view"""
        # This empty clean method prevents validation errors
        # The actual file handling will happen in the view
        return self.cleaned_data.get('images')
    
class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'profile_picture', 'phone_number', 'address', 'height', 'weight', 
            'experience_level', 'preferred_rental_duration', 'boot_size', 
            'preferred_activity', 'preferred_terrain', 'insurance_preference',
            'receive_email_reminders', 'receive_sms_reminders', 'receive_marketing_emails'
        ]