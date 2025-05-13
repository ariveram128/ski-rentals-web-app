from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from datetime import datetime
from django.contrib import messages
from django.core.paginator import Paginator

from equipment.models import UserProfile, Cart, Rental, Equipment, User, Review


# Create your views here.

def home(request):
    # Start with available equipment
    featured_query = Equipment.objects.filter(is_available=True)
    
    # Apply collection visibility filters for anonymous users and patrons
    user = request.user
    
    if not user.is_authenticated or not hasattr(user, 'userprofile') or user.userprofile.user_type != 'LIBRARIAN':
        # For anonymous users and patrons:
        # Hide items that are in private collections (unless the user has access)
        
        # Start by excluding all items in private collections
        items_in_private_collections = Equipment.objects.filter(
            collections__sharing_type='PRIVATE'
        ).distinct()
        
        if user.is_authenticated:
            # For authenticated users, add back items from private collections they have access to
            accessible_private_items = Equipment.objects.filter(
                collections__sharing_type='PRIVATE',
                collections__authorized_users=user
            )
            
            creator_private_items = Equipment.objects.filter(
                collections__sharing_type='PRIVATE',
                collections__creator=user
            )
            
            # Remove items in private collections first
            featured_query = featured_query.exclude(id__in=items_in_private_collections.values('id'))
            
            # Add back accessible items and creator items
            accessible_ids = set(accessible_private_items.values_list('id', flat=True))
            creator_ids = set(creator_private_items.values_list('id', flat=True))
            private_item_ids = accessible_ids.union(creator_ids)
            
            if private_item_ids:
                # Ensure both querysets have the same distinctness property
                featured_query = featured_query.distinct()
                private_items_query = Equipment.objects.filter(id__in=private_item_ids).distinct()
                featured_query = featured_query | private_items_query
        else:
            # For anonymous users, just exclude all items in private collections
            featured_query = featured_query.exclude(id__in=items_in_private_collections.values('id'))
    
    # Get featured equipment (random order) with visibility filters applied
    featured_equipment = featured_query.distinct().order_by('?')[:3]
    
    # Get popular equipment for the home page - Apply the same visibility filters
    popular_query = Equipment.objects.all().order_by('-average_rating')
    
    # Apply the same visibility filters to popular equipment
    if not user.is_authenticated or not hasattr(user, 'userprofile') or user.userprofile.user_type != 'LIBRARIAN':
        if user.is_authenticated:
            # Remove items in private collections
            popular_query = popular_query.exclude(id__in=items_in_private_collections.values('id'))
            
            # Add back items from accessible private collections
            if private_item_ids:
                # Ensure both querysets have the same distinctness property
                popular_query = popular_query.distinct()
                private_items_query = Equipment.objects.filter(id__in=private_item_ids).order_by('-average_rating').distinct()
                popular_query = popular_query | private_items_query
        else:
            # For anonymous users, exclude all items in private collections
            popular_query = popular_query.exclude(id__in=items_in_private_collections.values('id'))
    
    popular_equipment = popular_query.distinct().order_by('-average_rating')[:6]
    
    return render(request, 'home.html', {
        'featured_equipment': featured_equipment,
        'popular_equipment': popular_equipment
    })

def logout_view(request):
    logout(request)
    return redirect("home")

@login_required
def role_based_redirect(request):
    print("DEBUG: Redirecting logged-in user to appropriate dashboard")
    if request.user.is_superuser:
        return redirect('/admin')
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'user_type':'PATRON'})
    if not user_profile.user_type:
        user_profile.user_type = 'PATRON'
        user_profile.save()
    if user_profile.user_type == 'LIBRARIAN':
        return redirect('librarian')
    else:
        return redirect('patron')

@login_required
def librarian_view(request):
    """
    Display the librarian dashboard, showing pending rental requests and maintenance tasks.
    """
    # Check if user is a librarian and redirect back to home if not
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'LIBRARIAN':
            return redirect('home')
    except UserProfile.DoesNotExist:
        return redirect('home')

    # Get today's date
    today_date = datetime.now().date()
    
    # Get pending rental requests, active rentals, and equipment due for return
    pending_rentals = Rental.objects.filter(rental_status='PENDING').order_by('-checkout_date')
    active_rentals = Rental.objects.filter(rental_status='ACTIVE').order_by('-checkout_date')

    # Get user's rental requests
    rental_requests = Rental.objects.filter(patron=request.user).order_by('-checkout_date')

    # Separate rentals by status
    your_active_rentals = rental_requests.filter(rental_status='ACTIVE')
    your_pending_rentals = rental_requests.filter(rental_status='PENDING')
    your_completed_rentals = rental_requests.filter(rental_status__in=['COMPLETED', 'CANCELLED'])
    
    # Count equipment requiring maintenance
    maintenance_equipment = Equipment.objects.filter(condition='MAINTENANCE')
    
    # Count total equipment, users, active rentals
    total_equipment = Equipment.objects.filter(is_deleted=False).count()
    total_users = User.objects.filter(userprofile__user_type='PATRON').count()
    active_rentals_count = active_rentals.count()
    
    context = {
        'pending_rentals': pending_rentals,
        'active_rentals': active_rentals,
        'maintenance_equipment': maintenance_equipment,
        'total_equipment': total_equipment,
        'total_users': total_users,
        'active_rentals_count': active_rentals_count,
        'today_date': today_date,
        #For the your rentals section:
        'your_active_rentals': your_active_rentals,
        'your_pending_rentals': your_pending_rentals,
        'your_completed_rentals': your_completed_rentals,
    }
    
    return render(request, 'users/librarian.html', context)

@login_required
def patron_view(request):
    """
    Display the patron dashboard, showing rental history and active requests.
    """

    # Check if user is a patron and redirect back to home if not
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type == 'LIBRARIAN':
            return redirect('librarian')
    except UserProfile.DoesNotExist:
        return redirect('home')

    # Get today's date
    today_date = datetime.now().date()
    
    # Get user's rental requests
    rental_requests = Rental.objects.filter(patron=request.user).order_by('-checkout_date')
    
    # Separate rentals by status
    active_rentals = rental_requests.filter(rental_status='ACTIVE')
    pending_rentals = rental_requests.filter(rental_status='PENDING')
    completed_rentals = rental_requests.filter(rental_status__in=['COMPLETED', 'CANCELLED'])
    
    context = {
        'active_rentals': active_rentals,
        'pending_rentals': pending_rentals,
        'completed_rentals': completed_rentals,
        'today_date': today_date,
    }
    
    return render(request, 'users/patron.html', context)

@login_required
def cart_view(request):
    # Get or create the user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get all items in the cart
    cart_items = cart.items.all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items
    }
    
    return render(request, 'users/cart.html', context)

@login_required
def help_view(request):
    return render(request, 'users/help.html')

@login_required
def edit_profile_view(request):
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'user_type': 'PATRON'}
    )
    
    # Handle form submission
    if request.method == 'POST':
        # Process address information
        address_parts = []
        street = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        zipcode = request.POST.get('zipCode', '').strip()
        
        if street:
            address_parts.append(street)
        if city and state:
            address_parts.append(f"{city}, {state}")
        if zipcode:
            address_parts.append(zipcode)
        
        full_address = '\n'.join(address_parts)
        
        # Update user information
        request.user.first_name = request.POST.get('firstName', '')
        request.user.last_name = request.POST.get('lastName', '')
        request.user.save()
        
        # Handle profile picture upload
        if 'profilePicture' in request.FILES:
            try:
                profile_pic = request.FILES['profilePicture']
                user_profile.profile_picture = profile_pic
                print(f"Profile picture uploaded: {profile_pic.name}, size: {profile_pic.size}")
            except Exception as e:
                print(f"Error uploading profile picture: {str(e)}")
                messages.error(request, f"Error uploading profile picture: {str(e)}")
        else:
            print("No profile picture in request.FILES")
            print(f"FILES keys: {list(request.FILES.keys())}")
        
        # Update profile information
        user_profile.phone_number = request.POST.get('phone', '')
        user_profile.address = full_address
        user_profile.height = request.POST.get('height', '')
        user_profile.weight = request.POST.get('weight', '')
        user_profile.boot_size = request.POST.get('bootSize', '')
        user_profile.experience_level = request.POST.get('experienceLevel', '')
        user_profile.preferred_activity = request.POST.get('preferredActivity', '')
        user_profile.preferred_terrain = request.POST.get('preferredTerrain', '')
        user_profile.preferred_rental_duration = request.POST.get('preferredRental', '')
        user_profile.insurance_preference = request.POST.get('insurancePreference', '')
        
        # Update notification preferences
        user_profile.receive_email_reminders = request.POST.get('emailRentalReminders') == 'on'
        user_profile.receive_sms_reminders = request.POST.get('textRentalReminders') == 'on'
        user_profile.receive_marketing_emails = request.POST.get('marketingEmails') == 'on'
        
        # Update privacy settings
        user_profile.is_public_profile = request.POST.get('publicProfile') == 'on'
        user_profile.show_rental_history = request.POST.get('showRentals') == 'on'
        
        user_profile.save()
        
        # Redirect to profile with success message
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('edit_profile')
    
    # Parse address for display
    address_lines = user_profile.address.split('\n')
    street_address = address_lines[0] if address_lines else ''
    
    city_state_zip = ''
    if len(address_lines) > 1:
        city_state_zip = address_lines[1]
    
    city = ''
    state = ''
    zipcode = ''
    
    if city_state_zip:
        # Try to parse city, state from the second line
        city_state_parts = city_state_zip.split(',')
        if len(city_state_parts) > 1:
            city = city_state_parts[0].strip()
            state_zip = city_state_parts[1].strip().split()
            if state_zip:
                state = state_zip[0].strip()
                if len(state_zip) > 1:
                    zipcode = state_zip[1].strip()
        elif len(address_lines) > 2:
            # If zipcode is on its own line
            zipcode = address_lines[2].strip()
    
    # US states for the dropdown
    states = [
        ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
        ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
        ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
        ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
        ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
        ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
        ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
        ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
        ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
        ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
        ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
        ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'), ('WY', 'Wyoming'), ('DC', 'District of Columbia')
    ]
    
    context = {
        'profile': user_profile,
        'street_address': street_address,
        'city': city,
        'state': state,
        'zipcode': zipcode,
        'states': states,
    }
    
    return render(request, 'users/edit-profile.html', context)

@login_required
def profile_view(request):
    """
    Display the user's profile information and preferences.
    """
    # Get the user's profile
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'user_type': 'PATRON'}
    )
    
    # Check if profile is incomplete and show a helpful message (only once)
    message_text = "Complete your profile to get personalized equipment recommendations and faster rentals."
    existing_messages = [msg.message for msg in messages.get_messages(request)]
    
    if (not user_profile.experience_level or not user_profile.preferred_activity) and message_text not in existing_messages:
        messages.info(request, message_text)
    
    # Get user's rental history
    past_rentals = Rental.objects.filter(
        patron=request.user,
        rental_status='COMPLETED'
    ).order_by('-return_date')[:5]  # Get the 5 most recent completed rentals
    
    # Get equipment recommendations based on user's preferences
    recommended_equipment = None
    if user_profile.experience_level and user_profile.preferred_activity:
        if user_profile.preferred_activity in ['SKIING', 'BOTH']:
            recommended_equipment = Equipment.objects.filter(
                recommended_skill_level=user_profile.experience_level,
                equipment_type='SKI',
                is_available=True
            )[:3]  # Limit to 3 recommendations
        elif user_profile.preferred_activity == 'SNOWBOARDING':
            recommended_equipment = Equipment.objects.filter(
                recommended_skill_level=user_profile.experience_level,
                equipment_type='SNOWBOARD',
                is_available=True
            )[:3]  # Limit to 3 recommendations
    
    context = {
        'profile': user_profile,
        'profile_user': request.user,
        'past_rentals': past_rentals,
        'recommended_equipment': recommended_equipment,
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def manage_users_view(request):
    """
    Display a list of users that can be managed by librarians.
    Allows librarians to promote patrons to librarian status.
    """
    # Check if the current user is a librarian
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        if user_profile.user_type != 'LIBRARIAN':
            messages.error(request, "You don't have permission to access user management.")
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, "You don't have permission to access user management.")
        return redirect('home')
    
    # Get all user profiles ordered by join date (newest first)
    all_profiles = UserProfile.objects.all().order_by('-date_joined')
    
    # Set up pagination
    paginator = Paginator(all_profiles, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    user_profiles = paginator.get_page(page_number)
    
    # Count patrons and librarians
    patrons_count = UserProfile.objects.filter(user_type='PATRON').count()
    librarians_count = UserProfile.objects.filter(user_type='LIBRARIAN').count()
    
    context = {
        'user_profiles': user_profiles,
        'patrons_count': patrons_count,
        'librarians_count': librarians_count,
    }
    
    return render(request, 'users/manage_users.html', context)

@login_required
def promote_to_librarian(request, user_id):
    """
    Promote a patron to librarian status.
    Only accessible by librarians.
    """
    # Check if the current user is a librarian
    try:
        current_user_profile = UserProfile.objects.get(user=request.user)
        if current_user_profile.user_type != 'LIBRARIAN':
            messages.error(request, "You don't have permission to promote users.")
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, "You don't have permission to promote users.")
        return redirect('home')
    
    # Only allow POST requests
    if request.method != 'POST':
        return redirect('manage_users')
    
    # Get the user to promote
    user_to_promote = get_object_or_404(User, id=user_id)
    profile_to_promote = get_object_or_404(UserProfile, user=user_to_promote)
    
    # Check if user is already a librarian
    if profile_to_promote.user_type == 'LIBRARIAN':
        messages.info(request, f"{user_to_promote.get_full_name() or user_to_promote.username} is already a librarian.")
        return redirect('manage_users')
    
    # Update user type to librarian
    profile_to_promote.user_type = 'LIBRARIAN'
    profile_to_promote.save()
    
    messages.success(request, f"{user_to_promote.get_full_name() or user_to_promote.username} has been promoted to librarian.")
    return redirect('manage_users')

@login_required
def demote_to_patron(request, user_id):
    """
    Demote a librarian to patron status.
    Only accessible by librarians.
    """
    # Check if the current user is a librarian
    try:
        current_user_profile = UserProfile.objects.get(user=request.user)
        if current_user_profile.user_type != 'LIBRARIAN':
            messages.error(request, "You don't have permission to demote users.")
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, "You don't have permission to demote users.")
        return redirect('home')
    
    # Only allow POST requests
    if request.method != 'POST':
        return redirect('manage_users')
    
    # Get the user to demote
    user_to_demote = get_object_or_404(User, id=user_id)
    profile_to_demote = get_object_or_404(UserProfile, user=user_to_demote)
    
    # Prevent demoting yourself
    if user_to_demote.id == request.user.id:
        messages.error(request, "You cannot demote yourself.")
        return redirect('manage_users')
    
    # Check if user is already a patron
    if profile_to_demote.user_type == 'PATRON':
        messages.info(request, f"{user_to_demote.get_full_name() or user_to_demote.username} is already a patron.")
        return redirect('manage_users')
    
    # Update user type to patron
    profile_to_demote.user_type = 'PATRON'
    profile_to_demote.save()
    
    messages.success(request, f"{user_to_demote.get_full_name() or user_to_demote.username} has been demoted to patron.")
    return redirect('manage_users')


