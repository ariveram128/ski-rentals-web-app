import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from users.models import UserProfile
from .models import Equipment, Rental, Review, Collection, MaintenanceRecord

class EquipmentTests(TestCase):
    """Test suite for the Equipment model functionality."""
    
    def setUp(self):
        """
        Create a test equipment instance for use in the test methods.
        Used as a baseline for all equipment-related tests.
        """
        self.test_equipment = Equipment.objects.create(
            equipment_id='SKI001',
            equipment_type='SKI',
            brand='Rossignol',
            model='Experience 88',
            size='170cm',
            condition='NEW',
            rental_price=50.00,
            recommended_skill_level='INTERMEDIATE'
        )

    def test_equipment_creation(self):
        """
        Test that the equipment instance is created successfully.
        """
        self.assertTrue(isinstance(self.test_equipment, Equipment))
        self.assertEqual(str(self.test_equipment), 
                        'Rossignol Experience 88 - SKI (170cm)')

class RentalTests(TestCase):
    """Test suite for the Rental model functionality."""
    
    def setUp(self):
        """
        Initialize the test environment with a test user, equipment, and rental.
        """
        # Create test user with basic credentials
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create equipment available for rental
        self.test_equipment = Equipment.objects.create(
            equipment_id='SKI001',
            equipment_type='SKI',
            brand='Rossignol',
            model='Experience 88',
            size='170cm',
            condition='NEW',
            rental_price=50.00
        )
        
        # Create rental record with standard daily attributes
        self.test_rental = Rental.objects.create(
            equipment=self.test_equipment,
            patron=self.test_user,
            rental_duration='DAILY',
            rental_price=50.00,
            due_date=timezone.now() + timedelta(days=1),
            checked_out_condition='NEW'
        )

    def test_rental_creation(self):
        """
        Test that the rental instance is created successfully.
        Checks:
        - Object creation
        - Equipment and patron association
        - Rental status set to 'PENDING'
        """
        self.assertTrue(isinstance(self.test_rental, Rental))
        self.assertEqual(self.test_rental.equipment, self.test_equipment)
        self.assertEqual(self.test_rental.patron, self.test_user)
        self.assertEqual(self.test_rental.rental_status, 'PENDING')

class UserProfileTests(TestCase):
    """Test suite for the UserProfile model functionality."""
    def setUp(self):
        """
        Initialize the test environment with a test user and profile.
        """
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.test_profile = UserProfile.objects.create(
            user=self.test_user,
            user_type='PATRON',
            experience_level='BEGINNER',
            preferred_rental_duration='DAILY'
        )

    def test_profile_creation(self):
        """
        Test that the user profile instance is created successfully.
        """
        self.assertTrue(isinstance(self.test_profile, UserProfile))
        self.assertEqual(str(self.test_profile), 
                        'testuser - PATRON')
        
    # TODO: Add tests for equipment recommendations
    # def test_equipment_recommendations(self):
    #     """Test equipment recommendations based on user experience level"""
    
    # TODO: Add tests for rental history tracking
    # def test_user_rental_history(self):
    #     """Test user's rental history and preferences tracking"""
        

# TODO: Add test suite for equipment maintenance scheduling
# - Test maintenance due date calculations
# - Test maintenance status updates
# - Test equipment availability during maintenance


class EquipmentTests(TestCase):
    """Test suite for the Equipment model functionality."""
    # ...existing code...

    # TODO: Add tests for equipment availability
    # def test_equipment_availability(self):
    #     """Test equipment availability status changes during rental lifecycle"""
    
    # TODO: Add tests for equipment rating calculations
    # def test_rating_updates(self):
    #     """Test average rating updates when new reviews are added"""


# class AuthenticationTests(TestCase):
#     """Tests user authentication and correct redirects based on patron/librarian"""
#
#     def setUp(self):
#         self.client = Client()
#         self.librarian = User.objects.create_user(username='librarian', password='testpass')
#         self.patron = User.objects.create_user(username='patron', password='testpass')
#         UserProfile.objects.create(user=self.librarian, user_type='LIBRARIAN')
#         UserProfile.objects.create(user=self.patron, user_type='PATRON')
#
#     def test_login_redirects_to_correct_page_librarian(self):
#         self.client.login(username='librarian', password='testpass')
#         response = self.client.get(reverse('equipment:home'))
#         self.assertRedirects(response, reverse('equipment:librarian'))
#
#     def test_login_redirects_to_correct_page_patron(self):
#         self.client.login(username='patron', password='testpass')
#         response = self.client.get(reverse('equipment:home'))
#         self.assertRedirects(response, reverse('equipment:patron'))
#
#     def test_librarian_page_requires_login(self):
#         response = self.client.get(reverse('equipment:librarian'))
#         self.assertEqual(response.status_code, 302)
#         self.assertTrue(response.url.startswith(reverse('account_login')))
#
#     def test_patron_page_requires_login(self):
#         response = self.client.get(reverse('equipment:patron'))
#         self.assertEqual(response.status_code, 302)
#         self.assertTrue(response.url.startswith(reverse('account_login')))
#
#     def test_patron_cannot_access_librarian_page(self):
#         self.client.login(username='patron', password='testpass')
#         response = self.client.get(reverse('equipment:librarian'))
#         self.assertEqual(response.status_code, 302)
#         self.assertTrue(response.url.startswith(reverse('account_login')))
#
#     def test_librarian_cannot_access_patron_page(self):
#         self.client.login(username='librarian', password='testpass')
#         response = self.client.get(reverse('equipment:patron'))
#         self.assertEqual(response.status_code, 302)
#         self.assertTrue(response.url.startswith(reverse('account_login')))

class CollectionTests(TestCase):
    """Tests for collection-related functionality."""
    
    def setUp(self):
        # Create test users
        self.librarian_user = User.objects.create_user(username='librarian', password='password123')
        self.patron_user = User.objects.create_user(username='patron', password='password123')
        
        # Create user profiles
        self.librarian_profile = UserProfile.objects.create(
            user=self.librarian_user,
            user_type='LIBRARIAN'
        )
        self.patron_profile = UserProfile.objects.create(
            user=self.patron_user,
            user_type='PATRON'
        )
        
        # Create test equipment
        self.equipment = Equipment.objects.create(
            equipment_id="TEST123",
            equipment_type="SKI",
            brand="Test Brand",
            model="Test Model",
            size="170cm",
            condition="EXCELLENT",
            is_available=True,
            rental_price=50.00
        )
        
        # Create a test collection
        self.librarian_collection = Collection.objects.create(
            title="Test Librarian Collection",
            description="A collection created by a librarian",
            is_public=True,
            creator=self.librarian_user
        )
        self.librarian_collection.items.add(self.equipment)
        
        self.patron_collection = Collection.objects.create(
            title="Test Patron Collection",
            description="A collection created by a patron",
            is_public=True,
            creator=self.patron_user
        )
        
        # Set up clients
        self.librarian_client = Client()
        self.patron_client = Client()
        self.librarian_client.login(username='librarian', password='password123')
        self.patron_client.login(username='patron', password='password123')
    
    def test_patron_create_public_collection(self):
        """Test that patrons can create public collections"""
        response = self.patron_client.post(
            reverse('equipment:create_collection'),
            {
                'title': 'Patron Public Collection',
                'description': 'A public collection by patron',
                'is_public': 'true'
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify collection was created
        collection = Collection.objects.get(title='Patron Public Collection')
        self.assertTrue(collection.is_public)
        self.assertEqual(collection.creator, self.patron_user)
    
    def test_patron_cannot_create_private_collection(self):
        """Test that patrons cannot create private collections"""
        response = self.patron_client.post(
            reverse('equipment:create_collection'),
            {
                'title': 'Patron Private Collection',
                'description': 'A private collection by patron',
                'sharing_type': 'PRIVATE'  # Try to make it private
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # In the current implementation, patrons can create collections marked as private
        # but they are automatically converted to public
        self.assertTrue(response_data['success'])
        
        # Verify collection was created but as PUBLIC
        collection = Collection.objects.get(title='Patron Private Collection')
        self.assertTrue(collection.is_public)  # Should be public regardless
        self.assertEqual(collection.sharing_type, 'PUBLIC')  # Should be public
        self.assertEqual(collection.creator, self.patron_user)
    
    def test_librarian_create_private_collection(self):
        """Test that librarians can create private collections"""
        response = self.librarian_client.post(
            reverse('equipment:create_collection'),
            {
                'title': 'Librarian Private Collection',
                'description': 'A private collection by librarian',
                'sharing_type': 'PRIVATE'  # Use sharing_type instead of is_public
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify collection was created
        collection = Collection.objects.get(title='Librarian Private Collection')
        self.assertFalse(collection.is_public)
        self.assertEqual(collection.sharing_type, 'PRIVATE')
        self.assertEqual(collection.creator, self.librarian_user)
    
    def test_only_creator_can_modify_collection(self):
        """Test that only the creator can add/remove items from a collection"""
        # Patron trying to add to librarian collection (should fail)
        response = self.patron_client.post(
            reverse('equipment:add_to_collection', kwargs={'equipment_id': self.equipment.id}),
            {'collection_id': self.librarian_collection.id}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Only the creator can add items', response_data['message'])
        
        # Patron trying to add to their own collection (should succeed)
        response = self.patron_client.post(
            reverse('equipment:add_to_collection', kwargs={'equipment_id': self.equipment.id}),
            {'collection_id': self.patron_collection.id}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify item was added
        self.assertTrue(self.equipment in self.patron_collection.items.all())

