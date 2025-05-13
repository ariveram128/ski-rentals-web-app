from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import timedelta
from users.models import UserProfile
from decimal import Decimal

class Collection(models.Model):
    """
    A grouping of equipment items based on a theme, with public/private access control.
    """
    # Collection privacy options
    SHARING_CHOICES = [
        ('PUBLIC', 'Public - Visible to everyone'),
        ('PRIVATE', 'Private - Only visible to selected users')
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_public = models.BooleanField(default=True)
    sharing_type = models.CharField(max_length=20, choices=SHARING_CHOICES, default='PUBLIC')
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_collections', null=True, blank=True)
    authorized_users = models.ManyToManyField(User, blank=True, related_name='accessible_collections')
    
    def __str__(self):
        if self.sharing_type == 'PUBLIC':
            return f"{self.title} (Public)"
        else:
            return f"{self.title} (Private)"


class Equipment(models.Model):
    """
    Represents a piece of winter sports equipment available for rental.
    
    This model stores information about various types of winter sports equipment,
    including their specifications, condition, pricing, and rental status.
    
    Attributes:
        equipment_id (str): Unique identifier for the equipment
        equipment_type (str): Type of equipment (e.g., Skis, Snowboard)
        brand (str): Manufacturer of the equipment
        model (str): Model name/number of the equipment
        size (str): Size specification of the equipment
        condition (str): Current condition of the equipment
        date_added (DateTime): Date when equipment was added to inventory
        last_maintained (DateTime): Date of last maintenance
        next_maintenance_due (DateTime): Scheduled date for next maintenance
        is_available (bool): Current availability status
        rental_price (Decimal): Daily rental price
        rent_to_own_price (Decimal): Optional purchase price for rent-to-own
        total_rentals (int): Number of times equipment has been rented
        average_rating (Decimal): Average customer rating (0-5)
    """
    
    # Equipment types order by most frequently rented
    EQUIPMENT_TYPES = [
        ('SKI', 'Skis'),
        ('SNOWBOARD', 'Snowboard'),
        ('POLES', 'Ski Poles'),
        ('BOOTS', 'Boots'),
        ('HELMET', 'Helmet'),
        ('GOGGLES', 'Goggles'),
        ('GLOVES', 'Gloves'),
        ('JACKET', 'Jacket'),
        ('PANTS', 'Pants'),
        ('OTHER', 'Other'),
    ]
    
    # Skills levels affecting equipment recommendations
    SKILL_LEVELS = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
        ('ALL', 'All Levels'),
    ]
    
    # Condition choices for equipment
    CONDITION_CHOICES = [
        ('NEW', 'New'),
        ('EXCELLENT', 'Excellent'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
        ('MAINTENANCE', 'Needs Maintenance'),
    ]

    # Ski types for recommendations and searching
    SKI_TYPES = [
        ('POWDER', 'Powder'),
        ('ALL_MOUNTAIN', 'All Mountain'),
        ('FREESTYLE', 'Freestyle'),
        ('FREERIDE', 'Freeride'),
        ('TOURING', 'Touring'),
        ('CARVING', 'Carving'),
        ('FRONTSIDE', 'Frontside'),
        ('SKI_BLADES', 'Ski Blades'),
    ]

    equipment_id = models.CharField(max_length=50, unique=True)
    equipment_type = models.CharField(max_length=20, choices=EQUIPMENT_TYPES)
    equipment_subtype = models.CharField(max_length=20,  choices=SKI_TYPES, blank=True, null=True) # for ski types
    location = models.CharField(
        max_length=100, 
        help_text="Physical location of the equipment",
        default="Main Storage",  # Add default value
        null=True,  # Allow null values
        blank=True  # Allow blank in forms
    )
    collections = models.ManyToManyField(Collection, blank=True, related_name='items')
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    size = models.CharField(max_length=20)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    date_added = models.DateTimeField(auto_now_add=True)
    last_maintained = models.DateTimeField(auto_now=True)
    next_maintenance_due = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False, help_text="Soft delete flag")
    notes = models.TextField(blank=True)
    recommended_skill_level = models.CharField(max_length=20, choices=SKILL_LEVELS, blank=True)
    recommended_height_range = models.CharField(max_length=50, blank=True)
    rental_price = models.DecimalField(
        max_digits=6, decimal_places=2,
        validators=[MinValueValidator(0.0)]
    )
    weekly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(0.0)],
        help_text="Weekly rental rate",
        null=True, blank=True
    )
    seasonal_rate = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(0.0)],
        help_text="Seasonal rental rate",
        null=True, blank=True
    )
    rent_to_own_price = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        null=True, blank=True
    )
    total_rentals = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        default=0.0
    )
    # Default main image for the equipment
    main_image = models.ImageField(upload_to='equipment_images/', null=True, blank=True)

    def clean(self):
        """
        Validate the model fields.
        This validation will run when full_clean() is called, which happens during model validation.
        """
        super().clean()

        if not self.equipment_type or not self.size:
            return

        # Clean/normalize the size input
        size_str = str(self.size).strip().upper()

        # Validate based on equipment type
        if self.equipment_type in ['SKI', 'SNOWBOARD', 'POLES']:
            try:
                if not size_str.replace('.', '', 1).isdigit():
                    raise ValidationError({
                        'size': f"{self.get_equipment_type_display()} size must be a number (e.g., 175), without units like 'cm'."
                    })

                size_float = float(size_str)
                if size_float <= 0:
                    raise ValidationError({
                        'size': f"{self.get_equipment_type_display()} size must be a positive number in centimeters."
                    })

                # Validate within reasonable ranges
                if self.equipment_type == 'SKI' and (size_float < 70 or size_float > 200):
                    raise ValidationError({
                        'size': "Ski size should typically be between 70 and 200 cm."
                    })
                elif self.equipment_type == 'SNOWBOARD' and (size_float < 80 or size_float > 180):
                    raise ValidationError({
                        'size': "Snowboard size should typically be between 80 and 180 cm."
                    })
                elif self.equipment_type == 'POLES' and (size_float < 70 or size_float > 140):
                    raise ValidationError({
                        'size': "Pole size should typically be between 70 and 140 cm."
                    })
            except (ValueError, TypeError):
                raise ValidationError({'size': f"{self.get_equipment_type_display()} size must be a valid number."})

        elif self.equipment_type == 'BOOTS':
            # Mondopoint measurements (may include decimal)
            try:
                size_float = float(size_str)  # Only use period as decimal separator
                if size_float < 15.0 or size_float > 33.0:
                    raise ValidationError({
                        'size': "Boot size (Mondopoint) should typically be between 15.0 and 33.0."
                    })
            except (ValueError, TypeError):
                raise ValidationError({'size': "Boot size must be a Mondopoint measurement (e.g., 25.5)."})

        elif self.equipment_type in ['HELMET', 'GOGGLES', 'GLOVES', 'JACKET', 'PANTS', 'OTHER']:
            # Categorical sizes
            valid_sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
            if size_str not in valid_sizes:
                raise ValidationError({
                    'size': f"Size must be one of: {', '.join(valid_sizes)}"
                })
    
    def __str__(self):
        return f"{self.brand} {self.model} - {self.equipment_type} ({self.size})"
        
    def get_price_for_duration(self, duration):
        """
        Returns the appropriate price for the specified rental duration.
        Falls back to calculated values if specific rates aren't set.
        """
        if duration == 'DAILY':
            return self.rental_price
        
        elif duration == 'WEEKLY':
            if self.weekly_rate is not None:
                return self.weekly_rate
            # Default weekly rate to 5 times daily rate if not specifically set
            return self.rental_price * 5
        
        elif duration == 'SEASONAL':
            if self.seasonal_rate is not None:
                return self.seasonal_rate
            # Default seasonal rate to 90 times daily rate if not specifically set
            return self.rental_price * 90
        
        # Default to daily rate if unknown duration
        return self.rental_price
        
    def update_average_rating(self):
        """Update the average rating based on all reviews for this equipment"""
        reviews = self.review_set.all()
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            self.average_rating = round(total_rating / reviews.count(), 2)
        else:
            self.average_rating = 0.0
        self.save(update_fields=['average_rating'])
        
    def get_rating_distribution(self):
        """Get the distribution of ratings (1-5 stars) for this equipment"""
        reviews = self.review_set.all()
        total_reviews = reviews.count()
        
        if total_reviews == 0:
            return {
                '5': 0,
                '4': 0,
                '3': 0,
                '2': 0,
                '1': 0,
                'total': 0
            }
            
        distribution = {
            '5': reviews.filter(rating=5).count(),
            '4': reviews.filter(rating=4).count(),
            '3': reviews.filter(rating=3).count(),
            '2': reviews.filter(rating=2).count(),
            '1': reviews.filter(rating=1).count(),
            'total': total_reviews
        }
        
        # Add percentages
        for rating in ['5', '4', '3', '2', '1']:
            distribution[f'{rating}_percent'] = int((distribution[rating] / total_reviews) * 100)
            
        return distribution

    # fixes subtype if incorrect
    def save(self, *args, **kwargs):
        if self.equipment_type != 'SKI':
            self.equipment_subtype = None
        super().save(*args, **kwargs)


class EquipmentImage(models.Model):
    """
    Represents additional images for equipment items.
    
    This model allows for storing multiple images per equipment item.
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='equipment_images/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return f"Image for {self.equipment} ({self.id})"


class MaintenanceRecord(models.Model):
    """
    Tracks maintenance history for equipment items.
    
    Records details about maintenance activities performed on equipment,
    including who performed the maintenance and when the next maintenance is due.
    
    Attributes:
        equipment (Equipment): Reference to the maintained equipment
        date_maintained (DateTime): When maintenance was performed
        maintained_by (User): Staff member who performed maintenance
        maintenance_type (str): Type of maintenance performed
        notes (str): Additional maintenance details
        next_maintenance_due (DateTime): When next maintenance is scheduled
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_history')
    date_maintained = models.DateTimeField(auto_now_add=True)
    maintained_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    maintenance_type = models.CharField(max_length=100)
    notes = models.TextField()
    next_maintenance_due = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.equipment} - {self.maintenance_type} - {self.date_maintained.date()}"


class Rental(models.Model):
    """
    Manages equipment rental transactions.
    
    Tracks the complete lifecycle of a rental from checkout to return,
    including conditions, notes, and rental status.
    
    Attributes:
        equipment (Equipment): Equipment being rented
        patron (User): User renting the equipment
        rental_duration (str): Length of rental period
        rental_status (str): Current status of the rental
        rental_price (Decimal): Total price for the rental
        checkout_date (DateTime): When equipment was checked out
        due_date (DateTime): When equipment is due back
        return_date (DateTime): When equipment was actually returned
        extension_requested (bool): Whether extension was requested
        checked_out_condition (str): Condition at checkout
        return_condition (str): Condition at return
    """
    
    # Rental duration options for equipment
    RENTAL_DURATIONS = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('SEASONAL', 'Seasonal'),
    ]
    
    # Status codes affecting equipment availability
    RENTAL_STATUS = [
        ('PENDING', 'Pending'),     # Reserved but not yet picked up
        ('ACTIVE', 'Active'),       # Checked out and in use
        ('OVERDUE', 'Overdue'),     # Not returned by due date
        ('COMPLETED', 'Completed'), # Returned and checked in
        ('CANCELLED', 'Cancelled'), # Reservation cancelled
    ]
    
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT)
    patron = models.ForeignKey(User, on_delete=models.PROTECT)
    rental_duration = models.CharField(max_length=20, choices=RENTAL_DURATIONS)
    rental_status = models.CharField(max_length=20, choices=RENTAL_STATUS, default='PENDING')
    rental_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.0)]
    )
    checkout_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(blank=True, null=True)
    extension_requested = models.BooleanField(default=False)
    checked_out_condition = models.CharField(
        max_length=20, choices=Equipment.CONDITION_CHOICES
    )
    return_condition = models.CharField(
        max_length=20, choices=Equipment.CONDITION_CHOICES,
        null=True, blank=True
    )
    checkout_notes = models.TextField(blank=True)
    return_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.equipment} - {self.patron.username} ({self.checkout_date.date()})"


class Review(models.Model):
    """
    Stores customer reviews and ratings for equipment.
    
    Allows users to rate and comment on equipment they have rented.
    Each user can only review a specific piece of equipment once.
    
    Attributes:
        equipment (Equipment): Equipment being reviewed
        user (User): User writing the review
        rating (int): Rating from 1-5
        comment (str): Optional review text
        date_posted (DateTime): When review was submitted
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    date_posted = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['equipment', 'user']
        
    def __str__(self):
        return f"{self.equipment} - {self.rating}/5 by {self.user.username}"


class Cart(models.Model):
    """
    Represents a user's shopping cart.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.user.username}"
    
    def get_total_price(self):
        return sum(item.get_subtotal() for item in self.items.all())
    
    def clear(self):
        self.items.all().delete()
    
    def get_subtotal_with_insurance(self):
        """Calculate subtotal including insurance fee"""
        return self.get_total_price() + Decimal('25.00')
    
    def get_tax_amount(self):
        """Calculate tax amount based on subtotal with insurance"""
        return round(self.get_subtotal_with_insurance() * Decimal('0.085'), 2)
    
    def get_total_with_tax(self):
        """Calculate final total including insurance and tax"""
        return round(self.get_subtotal_with_insurance() + self.get_tax_amount(), 2)


class CartItem(models.Model):
    """
    Represents an item in a user's cart.
    
    Stores the equipment, rental period, and calculated price for each item.
    """
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    rental_duration = models.CharField(
        max_length=20, 
        choices=Rental.RENTAL_DURATIONS,
        default='DAILY'
    )
    
    def __str__(self):
        return f"{self.equipment.brand} {self.equipment.model} ({self.start_date} to {self.end_date})"
    
    def get_rental_days(self):
        """Calculate the number of days between start and end date (inclusive)"""
        # Convert to date objects to ignore time component
        start = self.start_date.date()
        end = self.end_date.date()
        return (end - start).days + 1
    
    def get_subtotal(self):
        """Calculate the subtotal based on the rental duration and time period"""
        if self.rental_duration == 'DAILY':
            # Daily rate multiplied by number of days
            return self.equipment.get_price_for_duration('DAILY') * self.get_rental_days()
        
        elif self.rental_duration == 'WEEKLY':
            # Weekly rate applies to each week or partial week
            weeks = (self.get_rental_days() + 6) // 7  # Round up to nearest week
            return self.equipment.get_price_for_duration('WEEKLY') * weeks
        
        elif self.rental_duration == 'SEASONAL':
            # Seasonal rate is flat regardless of exact duration
            return self.equipment.get_price_for_duration('SEASONAL')
        
        # Default to daily rate if unknown duration
        return self.equipment.rental_price * self.get_rental_days()
    
    def get_rental_duration_display(self):
        """Return the human-readable rental duration."""
        return dict(Rental.RENTAL_DURATIONS).get(self.rental_duration, 'Daily')
    
    class Meta:
        unique_together = ['cart', 'equipment']  # Prevent duplicate equipment in cart


class CollectionAccessRequest(models.Model):
    """
    Manages requests from patrons to access private collections.
    
    When patrons want to access a private collection, they can submit a request,
    which the collection owner can approve or deny.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied')
    ]
    
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='access_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collection_requests')
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    response_date = models.DateTimeField(null=True, blank=True)
    response_note = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['collection', 'user']
        
    def __str__(self):
        return f"Access request for {self.collection.title} by {self.user.username} ({self.status})"