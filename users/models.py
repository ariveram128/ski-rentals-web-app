from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    # User types for profile differentiation
    USER_TYPES = [
        ('PATRON', 'Patron'),       # Equipment renter
        ('LIBRARIAN', 'Librarian'), # Equipment manager
    ]
    
    # Activity preferences
    ACTIVITY_CHOICES = [
        ('SKIING', 'Skiing'),
        ('SNOWBOARDING', 'Snowboarding'),
        ('BOTH', 'Both'),
    ]
    
    # Terrain preferences
    TERRAIN_CHOICES = [
        ('GROOMED', 'Groomed runs'),
        ('POWDER', 'Powder'),
        ('PARK', 'Park and pipe'),
        ('ALLMOUNTAIN', 'All-mountain'),
        ('BACKCOUNTRY', 'Backcountry'),
    ]
    
    # Insurance preferences
    INSURANCE_CHOICES = [
        ('ALWAYS', 'Always add insurance'),
        ('ASK', 'Ask each time'),
        ('NEVER', 'Never add insurance'),
    ]
    
    # Skill levels
    SKILL_LEVELS = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
    ]
    
    # Rental durations
    RENTAL_DURATIONS = [
        ('HOURLY', 'Hourly'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('SEASONAL', 'Seasonal'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='PATRON')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    height = models.CharField(max_length=10, blank=True, help_text="Height in cm or feet/inches")
    weight = models.CharField(max_length=10, blank=True, help_text="Weight in kg or lbs")
    experience_level = models.CharField(max_length=20, choices=SKILL_LEVELS, blank=True)
    preferred_rental_duration = models.CharField(max_length=20, choices=RENTAL_DURATIONS, blank=True)
    boot_size = models.CharField(max_length=10, blank=True, help_text="Boot size (US, EU, etc.)")
    preferred_activity = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, blank=True)
    preferred_terrain = models.CharField(max_length=20, choices=TERRAIN_CHOICES, blank=True)
    insurance_preference = models.CharField(max_length=20, choices=INSURANCE_CHOICES, blank=True, default='ASK')
    receive_email_reminders = models.BooleanField(default=True)
    receive_sms_reminders = models.BooleanField(default=False)
    receive_marketing_emails = models.BooleanField(default=True)
    is_public_profile = models.BooleanField(default=True)
    show_rental_history = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
        
    def get_recommended_equipment(self):
        """
        Returns a queryset of equipment recommended for this user based on their preferences
        """
        from equipment.models import Equipment
        
        if not self.experience_level or not self.preferred_activity:
            return Equipment.objects.none()
            
        # Get equipment matching the user's experience level and preferred activity
        equipment_type = 'SKI' if self.preferred_activity in ['SKIING', 'BOTH'] else 'SNOWBOARD'
        return Equipment.objects.filter(
            recommended_skill_level=self.experience_level,
            equipment_type=equipment_type,
            is_available=True
        )
        
    def get_past_rentals(self):
        """
        Returns a queryset of the user's past rentals in descending order
        """
        from equipment.models import Rental
        
        return Rental.objects.filter(
            patron=self.user,
            rental_status='COMPLETED'
        ).order_by('-return_date')


class Notification(models.Model):
    """
    Model to store notifications for users
    """
    NOTIFICATION_TYPES = [
        ('RENTAL_REQUEST', 'Rental Request'),
        ('RENTAL_APPROVED', 'Rental Approved'),
        ('RENTAL_DENIED', 'Rental Denied'),
        ('COLLECTION_REQUEST', 'Collection Access Request'),
        ('COLLECTION_APPROVED', 'Collection Access Approved'),
        ('COLLECTION_DENIED', 'Collection Access Denied'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    related_url = models.CharField(max_length=255, blank=True)  # URL to redirect when clicked
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.notification_type} for {self.user.username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        
    def mark_as_read(self):
        self.is_read = True
        self.save()
