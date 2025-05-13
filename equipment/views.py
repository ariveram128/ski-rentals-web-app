from django.utils import timezone
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db.models.expressions import F, Func
from django.db.models.functions import Cast
from django.db.models import FloatField
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import make_aware, is_naive
from django.contrib.auth.models import User

from django.http import JsonResponse
from django.db.models import Q, Avg, Count, Func, Value
from django.db import transaction
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib import messages
from django.urls import reverse
from django.utils.timezone import now
from .models import Equipment, EquipmentImage, Rental, Collection, Review, Cart, CartItem, CollectionAccessRequest
from users.models import UserProfile, Notification
from .forms import EquipmentForm, MultipleImageUploadForm, CollectionForm, EquipmentImageForm

# Helper functions for notifications
def create_rental_approved_notification(rental):
    """Create a notification when a rental is approved"""
    message = f"Your rental request for {rental.equipment.brand} {rental.equipment.model} has been approved."
    Notification.objects.create(
        user=rental.patron,
        notification_type='RENTAL_APPROVED',
        message=message,
        related_url=reverse('equipment:detail', args=[rental.equipment.id]),
    )

def create_rental_request_notification(rental):
    """Create a notification for librarians when a rental request is submitted"""
    message = f"{rental.patron.username} has requested to rent {rental.equipment.brand} {rental.equipment.model}."
    
    # Get all librarians
    from users.models import UserProfile
    librarians = UserProfile.objects.filter(user_type='LIBRARIAN')
    
    # Create notification for each librarian
    for librarian in librarians:
        Notification.objects.create(
            user=librarian.user,
            notification_type='RENTAL_REQUEST',
            message=message,
            related_url=reverse('librarian'),
        )

def create_rental_rejected_notification(rental):
    """Create a notification when a rental is rejected"""
    message = f"Your rental request for {rental.equipment.brand} {rental.equipment.model} has been rejected."
    Notification.objects.create(
        user=rental.patron,
        notification_type='RENTAL_DENIED',
        message=message,
        related_url=reverse('equipment:detail', args=[rental.equipment.id]),
    )

def create_rental_completed_notification(rental):
    """Create a notification when a rental is completed"""
    message = f"Your rental for {rental.equipment.brand} {rental.equipment.model} has been marked as completed."
    Notification.objects.create(
        user=rental.patron,
        notification_type='RENTAL_APPROVED',
        message=message,
        related_url=reverse('equipment:detail', args=[rental.equipment.id]),
    )

def create_collection_access_request_notification(access_request):
    """Create a notification for collection owner when access is requested"""
    message = f"{access_request.user.username} has requested access to your collection '{access_request.collection.title}'."
    Notification.objects.create(
        user=access_request.collection.creator,
        notification_type='COLLECTION_REQUEST',
        message=message,
        related_url=reverse('equipment:list_access_requests'),
    )

def create_collection_access_approved_notification(access_request):
    """Create a notification when collection access is approved"""
    message = f"Your request to access '{access_request.collection.title}' has been approved."
    Notification.objects.create(
        user=access_request.user,
        notification_type='COLLECTION_APPROVED',
        message=message,
        related_url=reverse('equipment:collection_detail', args=[access_request.collection.id]),
    )

def create_collection_access_denied_notification(access_request):
    """Create a notification when collection access is denied"""
    message = f"Your request to access '{access_request.collection.title}' has been denied."
    Notification.objects.create(
        user=access_request.user,
        notification_type='COLLECTION_DENIED',
        message=message,
    )

class RegexpReplace(Func):
    function = 'REGEXP_REPLACE'
    arity = 3  # pattern, replacement, flags

# Create your views here.

class IndexView(generic.ListView):
    template_name = 'equipment/index.html'
    context_object_name = 'equipment_list'
    paginate_by = None  # Show 12 items per page

    def get(self, request, *args, **kwargs):
        if 'ajax' in request.GET:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            return render(request, 'equipment/_equipment_grid.html', context)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Equipment.objects.filter(is_deleted=False)

        # Filter items based on collection visibility rules
        user = self.request.user
        
        if not user.is_authenticated or not hasattr(user, 'userprofile') or user.userprofile.user_type != 'LIBRARIAN':
            # For anonymous users and patrons:
            # 1. Show items that are not in any collection
            # 2. Show items that are in PUBLIC collections
            # 3. Hide items that are in PRIVATE collections (unless the user has access)
            
            # Get all items that are in private collections
            items_in_private_collections = Equipment.objects.filter(
                collections__sharing_type='PRIVATE'
            ).distinct()
            
            if user.is_authenticated:
                # For authenticated users, get items from private collections they have access to
                accessible_private_items = Equipment.objects.filter(
                    collections__sharing_type='PRIVATE',
                    collections__authorized_users=user
                ).distinct() | Equipment.objects.filter(
                    collections__sharing_type='PRIVATE',
                    collections__creator=user
                ).distinct()
                
                # First, exclude all items in private collections
                queryset = queryset.exclude(id__in=items_in_private_collections.values_list('id', flat=True))
                # Then, add back items from accessible private collections
                # Ensure both querysets have the same distinctness by making both distinct
                queryset = queryset.distinct()
                accessible_private_items = accessible_private_items.distinct()
                queryset = queryset | accessible_private_items
            else:
                # For anonymous users, exclude all items in private collections
                queryset = queryset.exclude(id__in=items_in_private_collections.values_list('id', flat=True))
        
        # Handle search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(brand__icontains=search_query) |
                Q(model__icontains=search_query) |
                Q(equipment_type__icontains=search_query) |
                Q(notes__icontains=search_query)
            )

        # Handle equipment type filter
        equipment_type = self.request.GET.get('type')
        if equipment_type:
            queryset = queryset.filter(equipment_type=equipment_type)

        # Handle ski subtype filter for SKI type
        if equipment_type == 'SKI':
            ski_subtypes = self.request.GET.getlist('ski_subtype')
            if ski_subtypes:
                queryset = queryset.filter(equipment_subtype__in=ski_subtypes)

        # Handle skill level filter
        skill_level = self.request.GET.get('skill_level')
        if skill_level:
            queryset = queryset.filter(recommended_skill_level=skill_level)

        # Handle price range filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if min_price:
            queryset = queryset.filter(rental_price__gte=Decimal(min_price))

        if max_price and max_price != '100':
            queryset = queryset.filter(rental_price__lte=Decimal(max_price))

        # Handle availability filter
        available_only = self.request.GET.get('available_only')
        if available_only == 'true':
            queryset = queryset.filter(is_available=True)

        # Handle condition filter
        conditions = self.request.GET.getlist('condition')
        if conditions:
            queryset = queryset.filter(condition__in=conditions)

        # Handle size filters - Process multiple selected sizes with ranges
        size_filters = self.request.GET.getlist('size')
        if size_filters:
            # Split sizes into numerical ranges (like '70-99') and categorical (like 'S', 'M', 'L')
            numerical_size_filters = [s for s in size_filters if '-' in s]
            categorical_size_filters = [s for s in size_filters if '-' not in s]

            # Build Q objects for OR filtering
            size_conditions = Q()

            # Handle numerical ranges using a SQLite-compatible approach
            if numerical_size_filters:
                # For each piece of equipment, we'll check if its size (as a number) falls within any of the ranges
                for size_range in numerical_size_filters:
                    try:
                        lower, upper = map(float, size_range.split('-'))

                        # Get all equipment with sizes that could be numerical in this range
                        for digit in range(int(lower), int(upper) + 1):
                            size_conditions |= Q(size__contains=str(digit))
                    except ValueError:
                        # Skip invalid ranges
                        pass

            # Handle categorical sizes (XS, S, M, L, XL, XXL)
            if categorical_size_filters:
                for size in categorical_size_filters:
                    size_conditions |= Q(size__iexact=size)

            # Apply size filter conditions if any exist
            if size_conditions:
                queryset = queryset.filter(size_conditions)

                # For numerical ranges, we need to post-filter in Python
                # since SQLite can't properly convert and compare the size values
                if numerical_size_filters:
                    filtered_queryset = []
                    for equipment in queryset:
                        try:
                            # Extract numbers from size field
                            import re
                            size_value_match = re.search(r'[0-9]+(\.[0-9]+)?', equipment.size)
                            if size_value_match:
                                size_value = float(size_value_match.group(0))

                                # Check if size value is in any of the selected ranges
                                for size_range in numerical_size_filters:
                                    lower, upper = map(float, size_range.split('-'))
                                    if lower <= size_value <= upper:
                                        filtered_queryset.append(equipment.id)
                                        break
                        except (ValueError, TypeError):
                            # Skip if size can't be parsed
                            continue

                    # Apply the filtered IDs
                    if filtered_queryset:
                        queryset = queryset.filter(id__in=filtered_queryset)
                    else:
                        # If no equipment matches the numerical filters, return empty queryset
                        queryset = Equipment.objects.none()

        # Handle sorting
        sort_by = self.request.GET.get('sort')
        if sort_by:
            if sort_by == 'price-low':
                queryset = queryset.order_by('rental_price')
            elif sort_by == 'price-high':
                queryset = queryset.order_by('-rental_price')
            elif sort_by == 'rating':
                queryset = queryset.order_by('-average_rating')
            elif sort_by == 'newest':
                queryset = queryset.order_by('-date_added')
        else:
            # Default sort by newest
            queryset = queryset.order_by('-date_added')

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add equipment types choices
        context['equipment_types'] = Equipment.EQUIPMENT_TYPES

        # Add ski subtypes choices
        context['ski_subtypes'] = Equipment.SKI_TYPES

        #Get top 3 rated skis - apply same privacy filters as main queryset
        top_rated_query = Equipment.objects.filter(is_deleted=False, is_available=True)
        
        # Apply the same privacy filters as the main queryset
        user = self.request.user
        
        if not user.is_authenticated or not hasattr(user, 'userprofile') or user.userprofile.user_type != 'LIBRARIAN':
            # Get all items that are in private collections
            items_in_private_collections = Equipment.objects.filter(
                collections__sharing_type='PRIVATE'
            ).distinct()
            
            if user.is_authenticated:
                # For authenticated users, get items from private collections they have access to
                accessible_private_items = Equipment.objects.filter(
                    collections__sharing_type='PRIVATE',
                    collections__authorized_users=user
                ).distinct() | Equipment.objects.filter(
                    collections__sharing_type='PRIVATE',
                    collections__creator=user
                ).distinct()
                
                # First, exclude all items in private collections
                top_rated_query = top_rated_query.exclude(id__in=items_in_private_collections.values_list('id', flat=True))
                # Then, add back items from accessible private collections
                top_rated_query = top_rated_query.distinct()
                accessible_private_items = accessible_private_items.distinct()
                top_rated_query = top_rated_query | accessible_private_items
            else:
                # For anonymous users, exclude all items in private collections
                top_rated_query = top_rated_query.exclude(id__in=items_in_private_collections.values_list('id', flat=True))
        
        # Get the top rated equipment with privacy filters applied
        top_rated = top_rated_query.order_by('-average_rating')[:4]
        context['top_rated'] = top_rated
        # Add condition choices
        context['condition_choices'] = Equipment.CONDITION_CHOICES

        # Store selected filters for UI state management
        context['selected_types'] = self.request.GET.get('type', '')
        context['selected_subtypes'] = self.request.GET.getlist('ski_subtype')
        context['selected_sizes'] = self.request.GET.getlist('size')
        context['selected_skill_level'] = self.request.GET.get('skill_level', '')
        context['selected_conditions'] = self.request.GET.getlist('condition')
        context['min_price'] = self.request.GET.get('min_price', '0')
        context['max_price'] = self.request.GET.get('max_price', '100')
        context['available_only'] = self.request.GET.get('available_only') != 'false'
        context['sort_by'] = self.request.GET.get('sort', 'newest')

        # Flag for showing standard sizes (for apparel items)
        context['show_standard_sizes'] = context['selected_types'] in ['HELMET', 'GOGGLES', 'GLOVES', 'JACKET', 'PANTS']

        # Size range options for different equipment types
        context['ski_size_ranges'] = [
            {'range': '70-99', 'display': '70-99 cm'},
            {'range': '100-129', 'display': '100-129 cm'},
            {'range': '130-159', 'display': '130-159 cm'},
            {'range': '160-189', 'display': '160-189 cm'},
            {'range': '190-200', 'display': '190-200 cm'}
        ]

        context['snowboard_size_ranges'] = [
            {'range': '80-119', 'display': '80-119 cm'},
            {'range': '120-139', 'display': '120-139 cm'},
            {'range': '140-159', 'display': '140-159 cm'},
            {'range': '160-180', 'display': '160-180 cm'}
        ]

        context['boot_size_ranges'] = [
            {'range': '15.0-20.0', 'display': '15.0-20.0 (Mondopoint)'},
            {'range': '20.5-25.0', 'display': '20.5-25.0 (Mondopoint)'},
            {'range': '25.5-30.0', 'display': '25.5-30.0 (Mondopoint)'},
            {'range': '30.5-33.0', 'display': '30.5-33.0 (Mondopoint)'}
        ]

        context['pole_size_ranges'] = [
            {'range': '70-89', 'display': '70-89 cm'},
            {'range': '90-109', 'display': '90-109 cm'},
            {'range': '110-129', 'display': '110-129 cm'},
            {'range': '130-140', 'display': '130-140 cm'}
        ]

        context['standard_sizes'] = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

        # Add user recommendations if user is logged in and has preferences - TODO this is unused and could be cool!
        if self.request.user.is_authenticated:
            try:
                user_profile = self.request.user.userprofile

                # Check if user has required preferences set
                if user_profile.experience_level and user_profile.preferred_activity:
                    # Get equipment recommendations based on user's profile
                    if user_profile.preferred_activity in ['SKIING', 'BOTH']:
                        ski_recommendations = Equipment.objects.filter(
                            recommended_skill_level=user_profile.experience_level,
                            equipment_type='SKI',
                            is_available=True
                        )[:3]  # Limit to 3 recommendations
                        context['ski_recommendations'] = ski_recommendations

                    if user_profile.preferred_activity in ['SNOWBOARDING', 'BOTH']:
                        board_recommendations = Equipment.objects.filter(
                            recommended_skill_level=user_profile.experience_level,
                            equipment_type='SNOWBOARD',
                            is_available=True
                        )[:3]  # Limit to 3 recommendations
                        context['board_recommendations'] = board_recommendations

                    # Add user's appropriate boot size recommendations if provided
                    if user_profile.boot_size:
                        boots = Equipment.objects.filter(
                            equipment_type='BOOTS',
                            size__icontains=user_profile.boot_size,
                            is_available=True
                        )[:2]  # Limit to 2 boot recommendations
                        context['boot_recommendations'] = boots

                # Add flag to indicate user has complete profile
                context['has_complete_profile'] = bool(
                    user_profile.experience_level and
                    user_profile.preferred_activity
                )
            except:
                # User profile doesn't exist
                pass

        return context

class DetailView(generic.DetailView):
    model = Equipment
    template_name = 'equipment/detail.html'
    context_object_name = 'equipment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add today's date for calendar min date
        from datetime import date, timedelta
        today = date.today()
        context['today_date'] = today.isoformat()

        # Add future dates for the next 30 days to help with availability display
        equipment = self.get_object()

        # Check for rentals of this equipment
        future_rentals = Rental.objects.filter(
            equipment=equipment,
            checkout_date__gte=today,
            rental_status__in=['ACTIVE', 'PENDING']
        ).order_by('checkout_date')

        # Get all unavailable dates (equipment is already booked)
        unavailable_dates = []
        for rental in future_rentals:
            current_date = rental.checkout_date
            end_date = rental.due_date or current_date + timedelta(days=1)

            while current_date <= end_date:
                unavailable_dates.append(current_date.isoformat())
                current_date += timedelta(days=1)

        context['unavailable_dates'] = unavailable_dates

        # Add rating distribution data
        context['rating_distribution'] = equipment.get_rating_distribution()

        # Check if the user has already reviewed this equipment
        if self.request.user.is_authenticated:
            user_review = Review.objects.filter(equipment=equipment, user=self.request.user).first()
            context['user_review'] = user_review

        # Get additional images
        context['additional_images'] = equipment.images.all()

        # Get reviews
        context['reviews'] = equipment.review_set.all().order_by('-date_posted')

        return context

class AddView(LoginRequiredMixin, generic.CreateView):
    form_class = EquipmentForm
    template_name = "equipment/add_equipment.html"
    success_url = "/equipment/"

    def get_context_data(self, **kwargs):
        context = super(AddView, self).get_context_data(**kwargs)
        context['image_form'] = MultipleImageUploadForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        image_form = MultipleImageUploadForm(self.request.POST, self.request.FILES)

        # Basic Django form and image form validation
        if form.is_valid() and image_form.is_valid():
            return self.form_valid(form, image_form)
        else:
            return self.form_invalid(form, image_form)

    def form_valid(self, form, image_form):
        self.object = form.save(commit=False)
        self.object.is_available = True

        # Clear equipment_subtype if the equipment type is not SKI
        if self.object.equipment_type != 'SKI':
            self.object.equipment_subtype = None

        try:
            # This will trigger the clean method and validate ski sizes
            self.object.full_clean()
            self.object.save()

            # Handle main image upload
            if 'main_image' in self.request.FILES:
                self.object.main_image = self.request.FILES['main_image']
                self.object.save()

            # Handle additional images
            if 'images' in self.request.FILES:
                files = self.request.FILES.getlist('images')
                for f in files:
                    EquipmentImage.objects.create(
                        equipment=self.object,
                        image=f
                    )

            messages.success(self.request, 'Equipment added successfully.')
            return redirect(self.get_success_url())
        except ValidationError as e:
            # Add the validation errors to the form for display
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            
            return self.form_invalid(form, image_form)

    def form_invalid(self, form, image_form):
        return render(self.request, self.template_name, {
            'form': form,
            'image_form': image_form
        })

    #Redirect users other than librarians to the home page when trying to add equipment
    def dispatch(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return self.handle_no_permission()
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.user_type != 'LIBRARIAN':
                return redirect('equipment:index')
        except UserProfile.DoesNotExist:
                return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class EditView(LoginRequiredMixin, generic.UpdateView):
    model = Equipment  # important: we need the model when updating
    form_class = EquipmentForm
    template_name = "equipment/edit_equipment.html"  # You can reuse add_equipment.html if you want
    success_url = "/equipment/"

    def get_context_data(self, **kwargs):
        context = super(EditView, self).get_context_data(**kwargs)
        context['image_form'] = MultipleImageUploadForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        image_form = MultipleImageUploadForm(self.request.POST, self.request.FILES)

        if form.is_valid() and image_form.is_valid():
            return self.form_valid(form, image_form)
        else:
            return self.form_invalid(form, image_form)

    def form_valid(self, form, image_form):
        self.object = form.save(commit=False)

        self.object.full_clean()

        #Make sure old availability status gets saved
        self.object.is_available = Equipment.objects.get(pk=self.object.pk).is_available
        print(Equipment.objects.get(pk=self.object.pk).is_available)

        # Clear equipment_subtype if equipment_type is not SKI
        if self.object.equipment_type != 'SKI':
            self.object.equipment_subtype = None

        try:

            self.object.save()

            # If user uploads a new main image, update it
            if 'main_image' in self.request.FILES:
                self.object.main_image = self.request.FILES['main_image']
                self.object.save()

            # Handle additional images
            if 'images' in self.request.FILES:
                files = self.request.FILES.getlist('images')
                for f in files:
                    EquipmentImage.objects.create(
                        equipment=self.object,
                        image=f
                    )

            messages.success(self.request, 'Equipment updated successfully.')
            return redirect(self.get_success_url())

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)

            return self.form_invalid(form, image_form)

    def form_invalid(self, form, image_form):
        return self.render_to_response(
            self.get_context_data(form=form, image_form=image_form)
        )

    def dispatch(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return self.handle_no_permission()
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.user_type != 'LIBRARIAN':
                return redirect('equipment:index')
        except UserProfile.DoesNotExist:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)



@login_required
def add_equipment_images(request, equipment_id):
    """Add additional images to existing equipment."""
    equipment = get_object_or_404(Equipment, id=equipment_id)

    # Check if user is a librarian
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'LIBRARIAN':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to upload images.'
            })
        messages.error(request, 'You do not have permission to upload images.')
        return redirect('equipment:detail', pk=equipment_id)

    if request.method == 'POST':
        form = MultipleImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Handle multiple files
            files = request.FILES.getlist('images')

            if not files:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Please select at least one image to upload.'
                    })
                messages.error(request, 'Please select at least one image to upload.')
                return render(request, 'equipment/add_images.html', {
                    'form': form,
                    'equipment': equipment
                })

            for f in files:
                EquipmentImage.objects.create(
                    equipment=equipment,
                    image=f
                )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Images uploaded successfully!',
                    'count': len(files)
                })

            messages.success(request, 'Images added successfully!')
            return redirect('equipment:detail', pk=equipment_id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid form submission. Please check file types and sizes.'
                })
    else:
        form = MultipleImageUploadForm()

    return render(request, 'equipment/add_images.html', {
        'form': form,
        'equipment': equipment
    })

@login_required
def delete_equipment_image(request, image_id):
    """Delete an equipment image."""
    image = get_object_or_404(EquipmentImage, id=image_id)
    equipment_id = image.equipment.id

    # Ensure the user has permissions (librarian check)
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'LIBRARIAN':
        messages.error(request, 'You do not have permission to delete images.')
        return redirect('equipment:detail', pk=equipment_id)

    # Delete the image
    image.delete()
    messages.success(request, 'Image deleted successfully.')
    return redirect('equipment:detail', pk=equipment_id)

@login_required
def add_to_cart(request, equipment_id):
    """Add an equipment item to the user's cart."""
    if request.method == 'POST':
        equipment = get_object_or_404(Equipment, id=equipment_id)
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        rental_duration = request.POST.get('rental_duration', 'DAILY')  # Default to daily if not provided

        if not all([start_date, end_date]):
            messages.error(request, 'Please select both start and end dates.')
            return redirect('equipment:detail', pk=equipment_id)

        # Convert string dates to date objects with timezone awareness
        from django.utils.timezone import make_aware
        from datetime import datetime
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')

            if is_naive(start_dt):
                start_date = make_aware(start_dt)
            else:
                start_date = start_dt

            if is_naive(end_dt):
                end_date = make_aware(end_dt)
            else:
                end_date = end_dt
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('equipment:detail', pk=equipment_id)

        # Validate dates
        if start_date > end_date:
            messages.error(request, 'End date must be after start date.')
            return redirect('equipment:detail', pk=equipment_id)

        # Check if equipment is still available
        if not equipment.is_available:
            messages.error(request, 'This item is no longer available.')
            return redirect('equipment:detail', pk=equipment_id)

        # Get or create user's cart
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Check if equipment is already in cart
        if cart.items.filter(equipment=equipment).exists():
            messages.warning(request, 'This item is already in your cart.')
            return redirect('cart')

        # Create cart item
        CartItem.objects.create(
            cart=cart,
            equipment=equipment,
            start_date=start_date,
            end_date=end_date,
            rental_duration=rental_duration
        )

        messages.success(request, 'Item added to cart successfully!')
        return redirect('cart')

    # If not POST method
    messages.error(request, 'Invalid request method.')
    return redirect('equipment:detail', pk=equipment_id)

@login_required
def remove_from_cart(request, item_id):
    """Remove an item from the user's cart."""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()

        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart successfully.'
        })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })

@login_required
def clear_cart(request):
    """Clear all items from the user's cart."""
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        cart.clear()

        return JsonResponse({
            'success': True,
            'message': 'Cart cleared successfully.'
        })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })

class CartView(LoginRequiredMixin, generic.TemplateView):
    """Display the user's cart contents."""
    template_name = 'users/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        context['cart'] = cart
        context['cart_items'] = cart.items.all()
        return context

class CollectionListView(generic.ListView):
    """
    Display a list of public collections and user's private collections.
    """
    model = Collection
    template_name = 'equipment/collections.html'
    context_object_name = 'collections'

    def get_queryset(self):
        # Get all public collections
        queryset = Collection.objects.filter(sharing_type='PUBLIC')

        # Librarians see all collections
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'LIBRARIAN':
            return Collection.objects.all().order_by('-created_date')

        # If user is authenticated, also include their private collections
        if self.request.user.is_authenticated:
            # Private collections created by this user
            private_collections = Collection.objects.filter(
                creator=self.request.user,
                sharing_type='PRIVATE'
            )

            # Private collections where user has been granted access
            accessible_collections = Collection.objects.filter(
                sharing_type='PRIVATE',
                authorized_users=self.request.user
            )

            # For patrons, also include titles of all private collections they don't have access to
            # This is only for display, not for accessing content
            if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'PATRON':
                other_private_collections = Collection.objects.filter(
                    sharing_type='PRIVATE'
                ).exclude(
                    creator=self.request.user
                ).exclude(
                    authorized_users=self.request.user
                )
                # Ensure all querysets have the same distinctness property
                queryset = queryset.distinct()
                private_collections = private_collections.distinct()
                accessible_collections = accessible_collections.distinct()
                other_private_collections = other_private_collections.distinct()
                queryset = queryset | private_collections | accessible_collections | other_private_collections
            else:
                # Ensure all querysets have the same distinctness property
                queryset = queryset.distinct()
                private_collections = private_collections.distinct()
                accessible_collections = accessible_collections.distinct()
                queryset = queryset | private_collections | accessible_collections

        return queryset.distinct().order_by('-created_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add equipment types for filtering
        context['equipment_types'] = Equipment.EQUIPMENT_TYPES
        return context

class CollectionDetailView(generic.DetailView):
    """
    Display the details of a collection, including all equipment items in it.
    """
    model = Collection
    template_name = 'equipment/collection_detail.html'
    context_object_name = 'collection'

    def get_queryset(self):
        queryset = super().get_queryset()

        # Librarians see all collections
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'LIBRARIAN':
            return Collection.objects.all()

        # Filter for public collections, user's own collections, or collections user has access to
        if self.request.user.is_authenticated:
            # For titles of private collections, we need to allow patrons to see them
            # even if they don't have access to the contents
            return queryset
        else:
            return queryset.filter(sharing_type='PUBLIC')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add equipment types for filtering
        context['equipment_types'] = Equipment.EQUIPMENT_TYPES

        # Get search query parameter
        search_query = self.request.GET.get('collection_search', '')
        context['search_query'] = search_query

        collection = self.get_object()

        # Filter items based on search query if provided
        if search_query and collection.items.exists():
            # Filter collection items by search query
            filtered_items = collection.items.filter(
                Q(brand__icontains=search_query) |
                Q(model__icontains=search_query) |
                Q(equipment_type__icontains=search_query) |
                Q(notes__icontains=search_query) |
                Q(equipment_id__icontains=search_query)
            ).distinct()

            context['filtered_items'] = filtered_items
            context['is_search'] = True
        else:
            # No search query, return all items
            context['filtered_items'] = collection.items.all()
            context['is_search'] = False

        # Add flag to check if user can request access
        if self.request.user.is_authenticated:
            collection = self.get_object()

            # User can request access if:
            # 1. Collection is PRIVATE
            # 2. User is not the creator
            # 3. User is not already an authorized user
            can_request = (
                collection.sharing_type == 'PRIVATE' and
                collection.creator != self.request.user and
                self.request.user not in collection.authorized_users.all()
            )

            # Check if there's already a pending request
            has_pending_request = CollectionAccessRequest.objects.filter(
                collection=collection,
                user=self.request.user,
                status='PENDING'
            ).exists()

            context['can_request_access'] = can_request and not has_pending_request
            context['has_pending_request'] = has_pending_request

            # Add flag to indicate if user has access to view contents
            has_content_access = (
                collection.sharing_type == 'PUBLIC' or
                collection.creator == self.request.user or
                (collection.sharing_type == 'PRIVATE' and self.request.user in collection.authorized_users.all())
            )
            context['has_content_access'] = has_content_access

        return context

@login_required
def create_collection(request):
    """
    Create a new equipment collection.
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        sharing_type = request.POST.get('sharing_type', 'PUBLIC')
        
        # Check if user is a Patron and trying to create a non-public collection
        is_patron = request.user.userprofile.user_type == 'PATRON'
        if is_patron and sharing_type != 'PUBLIC':
            # Force patrons to create public collections only
            sharing_type = 'PUBLIC'
            messages.info(request, "As a patron, you can only create public collections.")

        if title and description:
            # Set is_public based on sharing_type
            is_public = (sharing_type == 'PUBLIC')

            collection = Collection.objects.create(
                title=title,
                description=description,
                sharing_type=sharing_type,
                is_public=is_public,
                creator=request.user
            )

            # If not public, add current user to authorized users
            if sharing_type != 'PUBLIC':
                collection.authorized_users.add(request.user)

            return JsonResponse({
                'success': True,
                'message': 'Collection created successfully.',
                'collection_id': collection.id
            })

        return JsonResponse({
            'success': False,
            'message': 'Title and description are required.'
        })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })

@login_required
def edit_collection(request, collection_id):
    """
    Edit a collection.
    """
    collection = get_object_or_404(Collection, id=collection_id)

    # Only the creator can edit the collection
    if collection.creator != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to edit this collection.'
            })
        else:
            messages.error(request, 'You do not have permission to edit this collection.')
            return redirect('equipment:collections')
        
    if request.method == 'POST':
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            title = request.POST.get('title')
            description = request.POST.get('description')
            sharing_type = request.POST.get('sharing_type')

            # Validate required fields
            if not title:
                return JsonResponse({
                    'success': False,
                    'message': 'Title is required.'
                })

            if not description:
                return JsonResponse({
                    'success': False,
                    'message': 'Description is required.'
                })

            # Validate sharing_type
            if sharing_type not in ['PUBLIC', 'PRIVATE']:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid sharing type. Must be PUBLIC or PRIVATE.'
                })

            # Check if user is a patron and trying to make a private collection
            if request.user.userprofile.user_type == 'PATRON' and sharing_type == 'PRIVATE':
                sharing_type = 'PUBLIC'  # Force to public for patrons

            # Update the collection fields
            collection.title = title
            collection.description = description
            
            # Check if changing from public to private
            if collection.sharing_type == 'PUBLIC' and sharing_type == 'PRIVATE':
                # Check if any items in this collection are in other collections
                for item in collection.items.all():
                    if item.collections.exclude(id=collection.id).exists():
                        return JsonResponse({
                            'success': False,
                            'message': 'Cannot change to private: Some items in this collection are in other collections. Private collections can only contain exclusive items.'
                        })

            collection.sharing_type = sharing_type
            collection.is_public = (sharing_type == 'PUBLIC')
            collection.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Collection updated successfully.'
            })
        else:
            # Handle regular form submission
            form = CollectionForm(request.POST, instance=collection)
            if form.is_valid():
                # Check if changing from public to private
                if collection.sharing_type == 'PUBLIC' and form.cleaned_data['sharing_type'] == 'PRIVATE':
                    # Check if any items in this collection are in other collections
                    for item in collection.items.all():
                        if item.collections.exclude(id=collection.id).exists():
                            messages.error(request, f'Cannot change to private: Some items in this collection are in other collections. Private collections can only contain exclusive items.')
                            return render(request, 'equipment/edit_collection.html', {'form': form, 'collection': collection})

                collection = form.save()
                messages.success(request, 'Collection updated successfully.')
                return redirect('equipment:collection_detail', pk=collection.id)
    else:
        form = CollectionForm(instance=collection)

    return render(request, 'equipment/edit_collection.html', {'form': form, 'collection': collection})

@login_required
def delete_collection(request, collection_id):
    """
    Delete an equipment collection.
    """
    try:
        collection = Collection.objects.get(id=collection_id)
    except Collection.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Collection not found.'
        })
        
    # Check if user is the creator of the collection
    if collection.creator != request.user:
        return JsonResponse({
            'success': False,
            'message': 'Only the creator can delete this collection.'
        })
        
    if request.method == 'POST':
        # Store the title for the success message
        title = collection.title
        
        # Delete the collection
        collection.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Collection "{title}" has been deleted.'
        })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })

@login_required
def add_to_collection(request, equipment_id):
    """
    Add an equipment item to a collection.
    """
    if request.method == 'POST':
        equipment = get_object_or_404(Equipment, id=equipment_id)
        collection_id = request.POST.get('collection_id')

        try:
            collection = Collection.objects.get(id=collection_id)
            
            # Check if user is the creator of the collection
            if collection.creator != request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'Only the creator can add items to this collection.'
                })
                
            # Check if user has access - this is different from being the creator
            if collection.sharing_type == 'PRIVATE' and not collection.authorized_users.filter(id=request.user.id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'You do not have access to this collection.'
                })
        except Collection.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Collection not found.'
            })

        # Check if equipment is already in a private collection
        private_collections = equipment.collections.filter(sharing_type='PRIVATE')
        if private_collections.exists():
            private_collection = private_collections.first()
            return JsonResponse({
                'success': False,
                'message': f'This item is already in private collection "{private_collection.title}". An item can only be in one private collection.'
            })

        # Check if the target collection is private and the equipment is in any other collection
        if collection.sharing_type == 'PRIVATE' and equipment.collections.exists():
            return JsonResponse({
                'success': False,
                'message': 'This item is already in another collection. Items in private collections cannot be in any other collection.'
            })

        # Add equipment to collection if not already in it
        if equipment not in collection.items.all():
            collection.items.add(equipment)
            return JsonResponse({
                'success': True,
                'message': f'Added {equipment.brand} {equipment.model} to {collection.title}.'
            })

        return JsonResponse({
            'success': False,
            'message': 'This item is already in the collection.'
        })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })

@login_required
def remove_from_collection(request, equipment_id, collection_id):
    """
    Remove an equipment item from a collection.
    """
    if request.method == 'POST':
        equipment = get_object_or_404(Equipment, id=equipment_id)

        # Get the collection
        try:
            collection = Collection.objects.get(id=collection_id)
            
            # Check if user is the creator of the collection
            if collection.creator != request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'Only the creator can remove items from this collection.'
                })
                
            # Check if user has access - this is different from being the creator
            if collection.sharing_type == 'PRIVATE' and not collection.authorized_users.filter(id=request.user.id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'You do not have access to this collection.'
                })
        except Collection.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Collection not found.'
            })

        # Remove equipment from collection
        collection.items.remove(equipment)
        return JsonResponse({
            'success': True,
            'message': f'Removed {equipment.brand} {equipment.model} from {collection.title}.'
        })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })

@login_required
def add_review(request, equipment_id):
    """
    Handle adding or updating a review for equipment
    """
    equipment = get_object_or_404(Equipment, pk=equipment_id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if not rating:
            messages.error(request, 'Rating is required')
            return redirect('equipment:detail', pk=equipment_id)

        # Check if user already has a review for this equipment
        existing_review = Review.objects.filter(equipment=equipment, user=request.user).first()

        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
            messages.success(request, 'Your review has been updated')
        else:
            # Create new review
            Review.objects.create(
                equipment=equipment,
                user=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Your review has been added')

        # Update the average rating
        equipment.update_average_rating()

        return redirect(f"{reverse('equipment:detail', kwargs={'pk': equipment_id})}#reviews-tab")

    # GET request shouldn't reach here, but just in case
    return redirect('equipment:detail', pk=equipment_id)

@login_required
def submit_rental_request(request):
    """
    Convert all items in the user's cart to formal rental requests.
    This will create Rental objects with a PENDING status for each cart item.
    """
    if request.method == 'POST':
        # Get the user's cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            messages.error(request, "You don't have any items in your cart.")
            return redirect('cart')

        # Check if the cart is empty
        if not cart.items.exists():
            messages.error(request, "Your cart is empty. Please add items before submitting a request.")
            return redirect('equipment:index')

        # Process each cart item
        request_count = 0
        for item in cart.items.all():
            # Check if the equipment is still available (this would need more robust logic in a real system)
            if not item.equipment.is_available:
                messages.warning(
                    request,
                    f"{item.equipment.brand} {item.equipment.model} is no longer available. It has been removed from your cart."
                )
                item.delete()
                continue

            # Create a rental request with PENDING status
            rental = Rental.objects.create(
                equipment=item.equipment,
                patron=request.user,
                rental_duration=item.rental_duration,  # Use the cart item's rental duration
                rental_status='PENDING',
                rental_price=item.get_subtotal(),
                due_date= make_aware(datetime.combine(item.end_date, datetime.min.time())),  # Convert date to datetime
                checked_out_condition=item.equipment.condition  # Use current condition
            )
            
            # Notify librarians about the rental request
            create_rental_request_notification(rental)
            
            request_count += 1

        # Clear the cart after creating all rental requests
        if request_count > 0:
            cart.clear()
            messages.success(
                request,
                f"Your rental request has been submitted for {request_count} item(s). A librarian will review your request shortly."
            )
        else:
            messages.error(request, "No items could be requested. Please check equipment availability.")

        return redirect('patron')  # Redirect to the user's dashboard

    # If not a POST request, redirect to cart
    return redirect('cart')

@login_required
def approve_rental(request, rental_id):
    """
    Approve a pending rental request.
    Only librarians can approve rentals.
    """
    # Check if user is a librarian
    try:
        if request.user.userprofile.user_type != 'LIBRARIAN':
            messages.error(request, "You don't have permission to approve rental requests.")
            return redirect('patron')
    except:
        messages.error(request, "You don't have permission to approve rental requests.")
        return redirect('home')

    if request.method == 'POST':
        rental = get_object_or_404(Rental, id=rental_id)

        # Only pending rentals can be approved
        if rental.rental_status != 'PENDING':
            messages.error(request, "This rental request cannot be approved because it is not pending.")
            return redirect('librarian')

        # Check if equipment is still available
        if not rental.equipment.is_available:
            messages.error(request, "This equipment is no longer available.")
            rental.rental_status = 'CANCELLED'
            rental.save()
            return redirect('librarian')

        # Set the rental status to ACTIVE
        rental.rental_status = 'ACTIVE'
        rental.save()

        # Update equipment availability
        equipment = rental.equipment
        equipment.is_available = False
        equipment.save()

        # Create notification for the patron
        create_rental_approved_notification(rental)

        messages.success(request, f"Rental request for {rental.equipment.brand} {rental.equipment.model} has been approved.")

        # TODO: Send notification to user (could be email, in-app notification, etc.)

        return redirect('librarian')

    return redirect('librarian')

@login_required
def reject_rental(request, rental_id):
    """
    Reject a pending rental request.
    Only librarians can reject rentals.
    """
    # Check if user is a librarian
    try:
        if request.user.userprofile.user_type != 'LIBRARIAN':
            messages.error(request, "You don't have permission to reject rental requests.")
            return redirect('patron')
    except:
        messages.error(request, "You don't have permission to reject rental requests.")
        return redirect('home')

    if request.method == 'POST':
        rental = get_object_or_404(Rental, id=rental_id)

        # Only pending rentals can be rejected
        if rental.rental_status != 'PENDING':
            messages.error(request, "This rental request cannot be rejected because it is not pending.")
            return redirect('librarian')

        # Set the rental status to CANCELLED
        rental.rental_status = 'CANCELLED'
        rental.save()

        # Create notification for the patron
        create_rental_rejected_notification(rental)

        messages.success(request, f"Rental request for {rental.equipment.brand} {rental.equipment.model} has been rejected.")

        # TODO: Send notification to user (could be email, in-app notification, etc.)

        return redirect('librarian')

    return redirect('librarian')

@login_required
def complete_rental(request, rental_id):
    """
    Mark a rental as completed (returned).
    Only librarians can complete rentals.
    """
    # Check if user is a librarian
    try:
        if request.user.userprofile.user_type != 'LIBRARIAN':
            messages.error(request, "You don't have permission to complete rental returns.")
            return redirect('patron')
    except:
        messages.error(request, "You don't have permission to complete rental returns.")
        return redirect('home')

    if request.method == 'POST':
        rental = get_object_or_404(Rental, id=rental_id)

        # Only active rentals can be completed
        if rental.rental_status != 'ACTIVE':
            messages.error(request, "This rental cannot be completed because it is not active.")
            return redirect('librarian')

        # Set the rental status to COMPLETED
        rental.rental_status = 'COMPLETED'
        rental.return_date = now()

        # Get return condition from form
        return_condition = request.POST.get('return_condition', rental.checked_out_condition)
        return_notes = request.POST.get('return_notes', '')

        rental.return_condition = return_condition
        rental.return_notes = return_notes
        rental.save()

        # Update equipment availability and condition
        equipment = rental.equipment
        equipment.is_available = True

        # If condition has worsened, update equipment condition
        if (list(Equipment.CONDITION_CHOICES).index((return_condition, dict(Equipment.CONDITION_CHOICES)[return_condition])) >
            list(Equipment.CONDITION_CHOICES).index((equipment.condition, dict(Equipment.CONDITION_CHOICES)[equipment.condition]))):
            equipment.condition = return_condition

        equipment.total_rentals += 1
        equipment.save()

        # Create notification for the patron
        create_rental_completed_notification(rental)

        messages.success(request, f"Rental for {rental.equipment.brand} {rental.equipment.model} has been marked as returned.")

        return redirect('librarian')

    return redirect('librarian')

@login_required
def cancel_rental(request, rental_id):
    """
    Cancel a pending rental request.
    Users can cancel their own pending rentals.
    """
    rental = get_object_or_404(Rental, id=rental_id, patron=request.user)

    # Only pending rentals can be cancelled by users
    if rental.rental_status != 'PENDING':
        messages.error(request, "This rental request cannot be cancelled because it is not pending.")
        return redirect('patron')

    if request.method == 'POST':
        # Set the rental status to CANCELLED
        rental.rental_status = 'CANCELLED'
        rental.save()

        # Make sure equipment stays available
        equipment = rental.equipment
        equipment.is_available = True
        equipment.save()

        messages.success(request, f"Your rental request for {rental.equipment.brand} {rental.equipment.model} has been cancelled.")

        return redirect('patron')

    return render(request, 'equipment/confirm_cancel.html', {
        'rental': rental
    })

class ManageRentalsView(LoginRequiredMixin, generic.ListView):
    """
    Display and manage all rental requests for librarians.
    """
    model = Rental
    template_name = 'equipment/manage_rentals.html'
    context_object_name = 'rentals'

    def get_queryset(self):
        """
        Only librarians can access this view.
        """
        try:
            if self.request.user.userprofile.user_type != 'LIBRARIAN':
                # Return empty queryset for non-librarians
                return Rental.objects.none()
        except:
            return Rental.objects.none()

        # Get rental status filter
        status = self.request.GET.get('status', 'all')

        # Base queryset
        queryset = Rental.objects.all().order_by('-checkout_date')

        # Apply status filter
        if status != 'all':
            queryset = queryset.filter(rental_status=status.upper())

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today_date'] = datetime.now().date()

        # Count rentals by status
        context['pending_count'] = Rental.objects.filter(rental_status='PENDING').count()
        context['active_count'] = Rental.objects.filter(rental_status='ACTIVE').count()
        context['completed_count'] = Rental.objects.filter(rental_status='COMPLETED').count()
        context['cancelled_count'] = Rental.objects.filter(rental_status='CANCELLED').count()

        return context

@login_required
def quick_rent(request, equipment_id):
    """
    Quickly add an item to the cart from recommendations or past rentals.
    This skips the equipment detail page for a streamlined experience.
    """
    equipment = get_object_or_404(Equipment, pk=equipment_id)

    if not equipment.is_available:
        messages.error(request, f"Sorry, {equipment.brand} {equipment.model} is currently not available for rent.")
        return redirect('equipment:index')

    # Get or create user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Get user's profile for default rental duration
    try:
        user_profile = request.user.userprofile
        # Use user's preferred rental duration if it exists
        default_duration = user_profile.preferred_rental_duration if user_profile.preferred_rental_duration else 'DAILY'
    except:
        default_duration = 'DAILY'

    # Calculate default dates
    today = datetime.now().date()

    # Set end date based on rental duration
    if default_duration == 'DAILY':
        end_date = today + timedelta(days=1)
    elif default_duration == 'WEEKLY':
        end_date = today + timedelta(days=7)
    elif default_duration == 'SEASONAL':
        end_date = today + timedelta(days=90)  # Roughly a season
    else:
        end_date = today + timedelta(days=1)  # Default to daily

    # Make datetimes timezone aware
    start_datetime = make_aware(datetime.combine(today, datetime.min.time()))
    end_datetime = make_aware(datetime.combine(end_date, datetime.min.time()))

    # Check if item already in cart
    existing_item = CartItem.objects.filter(cart=cart, equipment=equipment).first()

    if existing_item:
        messages.info(request, f"{equipment.brand} {equipment.model} is already in your cart.")
    else:
        # Add to cart with default dates
        cart_item = CartItem(
            cart=cart,
            equipment=equipment,
            start_date=start_datetime,
            end_date=end_datetime,
            rental_duration=default_duration
        )
        cart_item.save()
        messages.success(request, f"Added {equipment.brand} {equipment.model} to your cart!")

    return redirect('cart')


@login_required
def delete_equipment(request, equipment_id):
    """
    Hard delete an equipment item and its related records.
    Only accessible by librarians.
    """
    # Check if user is a librarian
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'LIBRARIAN':
            messages.error(request, "You don't have permission to delete equipment.")
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, "You don't have permission to delete equipment.")
        return redirect('home')

    # Only allow POST requests
    if request.method != 'POST':
        return redirect('equipment:index')

    # Get the equipment
    equipment = get_object_or_404(Equipment, id=equipment_id)
    equipment_name = f"{equipment.brand} {equipment.model}"

    try:
        # Begin a transaction to ensure all operations complete or none do
        with transaction.atomic():
            # Delete related rentals first (handle the PROTECT constraint)
            related_rentals = Rental.objects.filter(equipment=equipment)
            related_rentals.delete()

            # Delete related images
            equipment.images.all().delete()

            # Delete related reviews
            equipment.review_set.all().delete()

            # Remove from any collections
            for collection in equipment.collections.all():
                collection.items.remove(equipment)

            # Remove from any carts
            CartItem.objects.filter(equipment=equipment).delete()

            # Finally delete the equipment itself
            equipment.delete()

        messages.success(request, f"{equipment_name} has been permanently deleted from the catalog.")
        return redirect('equipment:index')

    except Exception as e:
        messages.error(request, f"Error deleting equipment: {str(e)}")
        return redirect('equipment:detail', pk=equipment_id)

    except Exception as e:
        messages.error(request, f"Error deleting {equipment_name}: {str(e)}")

    return redirect('equipment:index')

# Views by Charles - may not be properly structured

def home(request):
    return redirect("account_login")

def logout_view(request):
    logout(request)
    return redirect("account_login")

@login_required
def role_based_redirect(request):
    if request.user.is_superuser:
        return redirect('/admin')
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'user_type':'PATRON'})
    if not user_profile.user_type:
        user_profile.user_type = 'PATRON'
        user_profile.save()
    if user_profile.user_type == 'LIBRARIAN':
        return redirect('equipment:librarian')
    else:
        return redirect('equipment:patron')

@login_required
def librarian_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.user_type != 'LIBRARIAN':
        return redirect('account_login')
    return render(request, 'equipment/librarian.html')

@login_required
def patron_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.user_type != 'PATRON':
        return redirect('account_login')
    return render(request, 'equipment/patron.html')

def search_equipment(request):
    """
    API endpoint to search for equipment. Returns JSON results.
    """
    search_term = request.GET.get('q', '')
    
    if len(search_term) < 2:
        return JsonResponse({'equipment': []})
    
    equipment_list = Equipment.objects.filter(
        Q(brand__icontains=search_term) |
        Q(model__icontains=search_term) |
        Q(equipment_type__icontains=search_term) |
        Q(notes__icontains=search_term)
    ).distinct()
    
    # Apply collection visibility rules - similar to what we do in IndexView
    user = request.user
    
    if not user.is_authenticated or not hasattr(user, 'userprofile') or user.userprofile.user_type != 'LIBRARIAN':
        # For anonymous users and patrons:
        # Hide items that are in private collections (unless the user has access)
        
        # Get all items that are in private collections
        items_in_private_collections = Equipment.objects.filter(
            collections__sharing_type='PRIVATE'
        ).distinct()
        
        if user.is_authenticated:
            # For authenticated users, get items from private collections they have access to
            accessible_private_items = Equipment.objects.filter(
                collections__sharing_type='PRIVATE',
                collections__authorized_users=user
            ).distinct() | Equipment.objects.filter(
                collections__sharing_type='PRIVATE',
                collections__creator=user
            ).distinct()
            
            # First, exclude all items in private collections
            equipment_list = equipment_list.exclude(id__in=items_in_private_collections.values_list('id', flat=True))
            # Then, add back items from accessible private collections
            equipment_list = equipment_list.distinct()
            accessible_private_items = accessible_private_items.distinct()
            equipment_list = equipment_list | accessible_private_items
        else:
            # For anonymous users, exclude all items in private collections
            equipment_list = equipment_list.exclude(id__in=items_in_private_collections.values_list('id', flat=True))
    
    # Limit to 20 results
    equipment_list = equipment_list.distinct()[:20]
    
    results = []
    for item in equipment_list:
        results.append({
            'id': item.id,
            'brand': item.brand,
            'model': item.model,
            'equipment_type': item.get_equipment_type_display(),
            'size': item.size,
            'rental_price': float(item.rental_price),
            'is_available': item.is_available
        })
    
    return JsonResponse({'equipment': results})

@login_required
def request_collection_access(request, collection_id):
    """
    Allow users to request access to a private collection.
    """
    collection = get_object_or_404(Collection, id=collection_id)

    # Check if collection is public (no need to request access)
    if collection.sharing_type == 'PUBLIC':
        messages.warning(request, "This is a public collection. No access request needed.")
        return redirect('equipment:collection_detail', pk=collection_id)

    # Check if user already has access
    if request.user in collection.authorized_users.all():
        messages.info(request, "You already have access to this collection.")
        return redirect('equipment:collection_detail', pk=collection_id)

    # Check if there's already a pending request
    existing_request = CollectionAccessRequest.objects.filter(
        collection=collection,
        user=request.user,
        status='PENDING'
    ).first()

    if existing_request:
        messages.info(request, "You have already requested access to this collection. Please wait for a response.")
        return redirect('equipment:collections')

    # Check if there's a denied request that can be resubmitted
    denied_request = CollectionAccessRequest.objects.filter(
        collection=collection,
        user=request.user,
        status='DENIED'
    ).first()

    if denied_request and request.method == 'POST':
        # Resubmit the request
        denied_request.status = 'PENDING'
        denied_request.request_date = timezone.now()
        denied_request.response_date = None
        denied_request.response_note = ''
        denied_request.save()
        messages.success(request, f"Access request for '{collection.title}' has been resubmitted.")
        return redirect('equipment:collections')

    if request.method == 'POST':
        # Use get_or_create to handle existing requests (prevents duplicate key errors)
        access_request, created = CollectionAccessRequest.objects.get_or_create(
            collection=collection,
            user=request.user,
            defaults={'status': 'PENDING'}
        )

        # If not created, it means an existing request was found, update it
        if not created:
            access_request.status = 'PENDING'
            access_request.request_date = timezone.now()
            access_request.response_date = None
            access_request.response_note = ''
            access_request.save()

        # Create notification for collection owner
        create_collection_access_request_notification(access_request)

        messages.success(request, f"Access request for '{collection.title}' has been submitted.")
        return redirect('equipment:collections')

    # GET request: Show confirmation form
    context = {
        'collection': collection,
        'denied_request': denied_request
    }
    return render(request, 'equipment/request_access.html', context)

@login_required
def list_access_requests(request):
    """
    List access requests for collections created by the current user.
    """
    # For librarians
    if request.user.userprofile.user_type == 'LIBRARIAN':
        # Get collections created by this user
        my_collections = Collection.objects.filter(creator=request.user, sharing_type__in=['PRIVATE', 'SHARED'])
        # Get pending access requests for these collections
        pending_requests = CollectionAccessRequest.objects.filter(
            collection__in=my_collections,
            status='PENDING'
        ).order_by('-request_date')

        # Also get requests made by this user
        my_requests = CollectionAccessRequest.objects.filter(
            user=request.user
        ).order_by('-request_date')
    else:
        # For patrons (just show their own requests)
        pending_requests = []
        my_requests = CollectionAccessRequest.objects.filter(
            user=request.user
        ).order_by('-request_date')

    context = {
        'pending_requests': pending_requests,
        'my_requests': my_requests
    }
    return render(request, 'equipment/access_requests.html', context)

@login_required
def approve_access_request(request, request_id):
    """
    Approve a request for collection access.
    """
    access_request = get_object_or_404(CollectionAccessRequest, id=request_id)
    collection = access_request.collection

    # Security check: Only the collection creator can approve requests
    if collection.creator != request.user:
        messages.error(request, "You don't have permission to approve this request.")
        return redirect('equipment:list_access_requests')

    if request.method == 'POST':
        # Add user to authorized users
        collection.authorized_users.add(access_request.user)

        # Update request status
        access_request.status = 'APPROVED'
        access_request.response_date = timezone.now()
        access_request.response_note = request.POST.get('note', '')
        access_request.save()

        # Create notification for the requestor
        create_collection_access_approved_notification(access_request)

        messages.success(request, f"Access request approved for {access_request.user.username}.")

        # Check where the request came from to redirect properly
        referer = request.META.get('HTTP_REFERER', '')
        if 'manage-users' in referer:
            return redirect('equipment:manage_collection_users', collection_id=collection.id)
        return redirect('equipment:list_access_requests')

    # redirect to access requests list if it's a GET request because of modals usage
    messages.info(request, "Please use the approve button to approve access requests.")
    return redirect('equipment:list_access_requests')

@login_required
def deny_access_request(request, request_id):
    """
    Deny a request for collection access.
    """
    access_request = get_object_or_404(CollectionAccessRequest, id=request_id)
    collection = access_request.collection

    # Security check: Only the collection creator can deny requests
    if collection.creator != request.user:
        messages.error(request, "You don't have permission to deny this request.")
        return redirect('equipment:list_access_requests')

    if request.method == 'POST':
        # Update request status
        access_request.status = 'DENIED'
        access_request.response_date = timezone.now()
        access_request.response_note = request.POST.get('note', '')
        access_request.save()

        # Create notification for the requestor
        create_collection_access_denied_notification(access_request)

        messages.success(request, f"Access request denied for {access_request.user.username}.")

        # Check where the request came from to redirect properly
        referer = request.META.get('HTTP_REFERER', '')
        if 'manage-users' in referer:
            return redirect('equipment:manage_collection_users', collection_id=collection.id)
        return redirect('equipment:list_access_requests')

    # Just redirect to access requests list if it's a GET request because of modals usage
    messages.info(request, "Please use the deny button to deny access requests.")
    return redirect('equipment:list_access_requests')

@login_required
def manage_collection_users(request, collection_id):
    """
    Add or remove users from a collection's authorized users.
    """
    collection = get_object_or_404(Collection, id=collection_id)

    # Security check: Only the collection creator can manage users
    if collection.creator != request.user:
        messages.error(request, "You don't have permission to manage users for this collection.")
        return redirect('equipment:collection_detail', pk=collection_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            username = request.POST.get('username')
            if username:
                # Check if user is trying to add themselves
                if username == request.user.username:
                    messages.error(request, "You cannot add yourself as you already own this collection.")
                else:
                    try:
                        user = User.objects.get(username=username)

                        # Check if user already has access
                        if user in collection.authorized_users.all():
                            messages.error(request, f"{user.username} already has access to this collection.")
                        else:
                            collection.authorized_users.add(user)
                            messages.success(request, f"{user.username} has been granted access to this collection.")
                    except User.DoesNotExist:
                        messages.error(request, f"User '{username}' does not exist.")
            else:
                messages.error(request, "Username is required.")

        elif action == 'remove':
            user_id = request.POST.get('user_id')
            if user_id:
                user = get_object_or_404(User, id=user_id)
                collection.authorized_users.remove(user)
                messages.success(request, f"{user.username}'s access has been revoked.")

        return redirect('equipment:manage_collection_users', collection_id=collection_id)

    # Get all authorized users for this collection
    authorized_users = collection.authorized_users.all()

    # Get pending access requests
    pending_requests = CollectionAccessRequest.objects.filter(
        collection=collection,
        status='PENDING'
    )

    context = {
        'collection': collection,
        'authorized_users': authorized_users,
        'pending_requests': pending_requests
    }
    return render(request, 'equipment/manage_collection_users.html', context)

@login_required
def get_notifications(request):
    """Get all notifications for the current user"""
    # Get all notifications for the user
    all_notifications = Notification.objects.filter(user=request.user)
    
    # Count all notifications
    total_count = all_notifications.count()
    
    # Count unread notifications separately
    unread_count = all_notifications.filter(is_read=False).count()
    
    # Check if we should return all notifications
    view_all = request.GET.get('all') == 'true'
    
    # Get the notifications based on the view_all parameter
    if view_all:
        notifications = all_notifications.order_by('-created_at')
    else:
        notifications = all_notifications.order_by('-created_at')[:10]
    
    if request.method == 'POST':
        # Mark notifications as read
        notification_id = request.POST.get('notification_id')
        if notification_id:
            # Mark specific notification as read
            try:
                notification = Notification.objects.get(id=notification_id, user=request.user)
                notification.is_read = True
                notification.save()
                return JsonResponse({'success': True})
            except Notification.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Notification not found'})
        else:
            # Mark all notifications as read
            all_notifications.filter(is_read=False).update(is_read=True)
            return JsonResponse({'success': True})
    
    # Format notifications for the response
    notifications_list = []
    for notification in notifications:
        notifications_list.append({
            'id': notification.id,
            'type': notification.notification_type,
            'message': notification.message,
            'url': notification.related_url,
            'created_at': notification.created_at.strftime('%b %d, %Y %H:%M'),
            'is_read': notification.is_read
        })
    
    return JsonResponse({
        'notifications': notifications_list,
        'unread_count': unread_count,
        'total_count': total_count
    })





