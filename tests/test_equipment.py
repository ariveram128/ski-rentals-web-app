import unittest

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse

from equipment.forms import EquipmentForm
from equipment.models import Equipment, Review
from users.models import UserProfile


class EquipmentModelTests(TestCase):
    """Test suite for the Equipment model functionality."""

    def setUp(self):
        """Create test equipment instances for use in the test methods."""
        self.test_ski = Equipment.objects.create(
            equipment_id='SKI001',
            equipment_type='SKI',
            equipment_subtype='POWDER',
            brand='Rossignol',
            model='Experience 88',
            size='170cm',
            condition='NEW',
            rental_price=50.00,
            recommended_skill_level='INTERMEDIATE'
        )

        self.test_snowboard = Equipment.objects.create(
            equipment_id='BOARD001',
            equipment_type='SNOWBOARD',
            brand='Burton',
            model='Custom',
            size='158cm',
            condition='EXCELLENT',
            rental_price=45.00,
            recommended_skill_level='ADVANCED'
        )

    def test_equipment_creation(self):
        """Test that the equipment instance is created successfully."""
        self.assertTrue(isinstance(self.test_ski, Equipment))
        self.assertEqual(str(self.test_ski), 'Rossignol Experience 88 - SKI (170cm)')

    def test_price_for_duration_with_default_rates(self):
        """Test price calculation with default multipliers when no custom rates are set."""
        self.assertEqual(self.test_ski.get_price_for_duration('DAILY'), 50.00)
        self.assertEqual(self.test_ski.get_price_for_duration('WEEKLY'), 50.00 * 5)
        self.assertEqual(self.test_ski.get_price_for_duration('SEASONAL'), 50.00 * 90)
        self.assertEqual(self.test_ski.get_price_for_duration('INVALID'), 50.00)

    def test_price_for_duration_with_custom_rates(self):
        """Test price calculation with explicitly set custom rates."""
        self.test_ski.weekly_rate = 200.00
        self.test_ski.seasonal_rate = 1000.00
        self.test_ski.save()

        self.assertEqual(self.test_ski.get_price_for_duration('WEEKLY'), 200.00)
        self.assertEqual(self.test_ski.get_price_for_duration('SEASONAL'), 1000.00)

    def test_equipment_average_rating(self):
        """Test that average rating is correctly calculated."""
        user = User.objects.create_user(username='testuser', password='password123')

        self.assertEqual(self.test_ski.average_rating, 0.0)

        review1 = Review.objects.create(
            equipment=self.test_ski,
            user=user,
            rating=4,
            comment='Great skis!'
        )
        self.test_ski.update_average_rating()
        self.assertEqual(self.test_ski.average_rating, 4.0)

        user2 = User.objects.create_user(username='testuser2', password='password123')
        review2 = Review.objects.create(
            equipment=self.test_ski,
            user=user2,
            rating=5,
            comment='Amazing skis!'
        )
        self.test_ski.update_average_rating()
        self.assertEqual(self.test_ski.average_rating, 4.5)  # (4+5)/2 = 4.5

    def test_rating_distribution(self):
        """Test the calculation of rating distribution."""
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        user3 = User.objects.create_user(username='user3', password='pass')
        user4 = User.objects.create_user(username='user4', password='pass')
        user5 = User.objects.create_user(username='user5', password='pass')

        Review.objects.create(equipment=self.test_ski, user=user1, rating=5)
        Review.objects.create(equipment=self.test_ski, user=user2, rating=5)
        Review.objects.create(equipment=self.test_ski, user=user3, rating=4)
        Review.objects.create(equipment=self.test_ski, user=user4, rating=3)
        Review.objects.create(equipment=self.test_ski, user=user5, rating=1)

        distribution = self.test_ski.get_rating_distribution()

        self.assertEqual(distribution['5'], 2)
        self.assertEqual(distribution['4'], 1)
        self.assertEqual(distribution['3'], 1)
        self.assertEqual(distribution['2'], 0)
        self.assertEqual(distribution['1'], 1)
        self.assertEqual(distribution['total'], 5)

        self.assertEqual(distribution['5_percent'], 40)  # 2/5 = 40%
        self.assertEqual(distribution['4_percent'], 20)  # 1/5 = 20%
        self.assertEqual(distribution['3_percent'], 20)  # 1/5 = 20%
        self.assertEqual(distribution['2_percent'], 0)  # 0/5 = 0%
        self.assertEqual(distribution['1_percent'], 20)  # 1/5 = 20%

    def test_non_ski_subtype_is_removed_on_save(self):
        self.test_snowboard.equipment_subtype = 'POWDER'
        self.test_snowboard.save()
        self.assertIsNone(self.test_snowboard.equipment_subtype)


class EquipmentFormTests(TestCase):
    """Test suite for the EquipmentForm functionality."""

    def test_valid_equipment_form(self):
        """Test that valid data creates a valid form."""
        form_data = {
            'equipment_id': 'SKI002',
            'equipment_type': 'SKI',
            'equipment_subtype': 'POWDER',
            'brand': 'Rossignol',
            'model': 'Soul 7',
            'size': '180',
            'condition': 'NEW',
            'rental_price': 60.00,
            'recommended_skill_level': 'ADVANCED',
            'is_available': True,
        }
        form = EquipmentForm(data=form_data)
        self.assertTrue(form.is_valid())

    @unittest.skip("Skipping this test for now")
    def test_equipment_subtype_for_skis(self):
        """Test that equipment_subtype is only set when type is SKI."""
        # Create a ski with a subtype
        ski_data = {
            'equipment_id': 'SKI003',
            'equipment_type': 'SKI',
            'equipment_subtype': 'FREESTYLE',
            'brand': 'K2',
            'model': 'Poacher',
            'size': '177',
            'condition': 'NEW',
            'rental_price': 55.00,
        }
        form = EquipmentForm(data=ski_data)
        self.assertTrue(form.is_valid())
        ski = form.save()
        self.assertEqual(ski.equipment_subtype, 'FREESTYLE')

    @unittest.skip("Skipping this test for now")
    def test_equipment_subtype_for_not_ski(self):
        # Create a snowboard - subtype should be ignored
        snowboard_data = {
            'equipment_id': 'BOARD002',
            'equipment_type': 'SNOWBOARD',
            'equipment_subtype': 'FREESTYLE',  # This should be ignored
            'brand': 'Burton',
            'model': 'Process',
            'size': '155cm',
            'condition': 'NEW',
            'rental_price': 48.00,
        }
        form = EquipmentForm(data=snowboard_data)
        self.assertTrue(form.is_valid())
        snowboard = form.save()
        self.assertEqual(snowboard.equipment_type, 'SNOWBOARD')
        self.assertIsNone(snowboard.equipment_subtype)

    def test_missing_required_equipment_id(self):
        """Test validation for missing required fields."""
        # Form with missing equipment_id
        form_data = {
            'equipment_type': 'SKI',
            'brand': 'Rossignol',
            'model': 'Soul 7',
            'size': '180',  # Changed from '180cm' to just '180' for ski validation
            'condition': 'NEW',
            'rental_price': 60.00,
        }
        form = EquipmentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('equipment_id', form.errors)

    def test_missing_required_rental_price(self):
        # Form with missing rental_price
        form_data = {
            'equipment_id': 'SKI004',
            'equipment_type': 'SKI',
            'brand': 'Rossignol',
            'model': 'Soul 7',
            'size': '180',  # Changed from '180cm' to just '180' for ski validation
            'condition': 'NEW',
        }
        form = EquipmentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rental_price', form.errors)

    def test_negative_price_validation(self):
        """Test that negative prices are rejected."""
        form_data = {
            'equipment_id': 'SKI005',
            'equipment_type': 'SKI',
            'brand': 'Rossignol',
            'model': 'Soul 7',
            'size': '180',  # Changed from '180cm' to just '180' for ski validation
            'condition': 'NEW',
            'rental_price': -10.00,  # Negative price - should be invalid
        }
        form = EquipmentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rental_price', form.errors)


class EquipmentAddTests(TestCase):
    """Tests for adding and updating equipment."""

    def setUp(self):
        """Set up environment for equipment add tests."""
        # Create test users
        self.librarian_user = User.objects.create_user(username='librarian', password='pass')
        self.patron_user = User.objects.create_user(username='patron', password='pass')

        # Create user profiles
        self.librarian_profile = UserProfile.objects.create(
            user=self.librarian_user,
            user_type='LIBRARIAN'
        )
        self.patron_profile = UserProfile.objects.create(
            user=self.patron_user,
            user_type='PATRON'
        )

        # Set up clients
        self.librarian_client = Client()
        self.patron_client = Client()
        self.librarian_client.login(username='librarian', password='pass')
        self.patron_client.login(username='patron', password='pass')

        # Create a test image for reuse
        self.test_image = self._create_test_image()

    def _create_test_image(self):
        """Create a test image file."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        import io
        from PIL import Image

        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'png')
        file.name = 'test_image.png'
        file.seek(0)
        return SimpleUploadedFile(file.name, file.read(), content_type='image/png')

    def test_add_equipment_form_with_ski_subtype(self):
        """Test adding new equipment with ski subtype through the form."""
        # Submit form data
        form_data = {
            'equipment_id': 'SKI004',
            'equipment_type': 'SKI',
            'equipment_subtype': 'CARVING',
            'brand': 'Atomic',
            'model': 'Redster X9',
            'size': '175',  # Changed from '175cm' to just '175' to pass validation
            'condition': 'NEW',
            'rental_price': 65.00,
            'recommended_skill_level': 'EXPERT',
            'is_available': True,
            'main_image': self.test_image,  # Add a test image to pass validation
        }

        response = self.librarian_client.post(reverse('equipment:add_equipment'), form_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after successful submission

        # Verify the equipment was created correctly
        new_ski = Equipment.objects.get(equipment_id='SKI004')
        self.assertEqual(new_ski.equipment_type, 'SKI')
        self.assertEqual(new_ski.equipment_subtype, 'CARVING')
        self.assertEqual(new_ski.brand, 'Atomic')
        self.assertEqual(new_ski.rental_price, 65.00)

    @unittest.skip("Skipping this test for now")
    def test_add_equipment_form_with_ignored_subtype(self):
        """Test adding new equipment with ignored subtype through the form."""
        # Test adding snowboard (should have no subtype)
        form_data = {
            'equipment_id': 'BOARD002',
            'equipment_type': 'SNOWBOARD',
            'equipment_subtype': 'FREESTYLE',  # This should be ignored
            'brand': 'Burton',
            'model': 'Process',
            'size': '155cm',  # Keep as is - not a ski so no validation needed
            'condition': 'NEW',
            'rental_price': 48.00,
            'is_available': True,
            'main_image': self.test_image,  # Add a test image to pass validation
        }

        response = self.librarian_client.post(reverse('equipment:add_equipment'), form_data)
        self.assertEqual(response.status_code, 302)

        # Verify the snowboard doesn't have a subtype
        new_board = Equipment.objects.get(equipment_id='BOARD002')
        self.assertEqual(new_board.equipment_type, 'SNOWBOARD')
        self.assertIsNone(new_board.equipment_subtype)

    def test_patron_cannot_add_equipment(self):
        """Test that patrons cannot add equipment."""
        form_data = {
            'equipment_id': 'SKI005',
            'equipment_type': 'SKI',
            'equipment_subtype': 'POWDER',
            'brand': 'Rossignol',
            'model': 'Soul 7',
            'size': '180',  # Changed from '180cm' to just '180' for ski validation
            'condition': 'NEW',
            'rental_price': 60.00,
            'is_available': True,
            'main_image': self.test_image,  # Add a test image to pass validation
        }

        response = self.patron_client.post(reverse('equipment:add_equipment'), form_data)
        self.assertEqual(response.status_code, 302)  # Should redirect

        # Verify no equipment was created
        with self.assertRaises(Equipment.DoesNotExist):
            Equipment.objects.get(equipment_id='SKI005')

    def test_add_equipment_with_images(self):
        """Test adding equipment with images."""
        # TODO: add image tests


from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Q

from equipment.models import Equipment
from users.models import UserProfile


class EquipmentViewTests(TestCase):
    """Test suite for equipment views functionality."""

    def setUp(self):
        """Set up test data for equipment views."""
        # Create test users
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.librarian_user = User.objects.create_user(username='librarian', password='pass')

        # Create user profiles
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            user_type='PATRON',
            experience_level='INTERMEDIATE',
            preferred_activity='SKIING'
        )
        self.librarian_profile = UserProfile.objects.create(
            user=self.librarian_user,
            user_type='LIBRARIAN'
        )

        # Create test equipment items of different types and subtypes
        self.powder_ski = Equipment.objects.create(
            equipment_id='SKI001',
            equipment_type='SKI',
            equipment_subtype='POWDER',
            brand='Rossignol',
            model='Soul 7',
            size='180',
            condition='NEW',
            rental_price=60.00,
            recommended_skill_level='ADVANCED',
            is_available=True
        )

        self.freestyle_ski = Equipment.objects.create(
            equipment_id='SKI002',
            equipment_type='SKI',
            equipment_subtype='FREESTYLE',
            brand='K2',
            model='Poacher',
            size='177',
            condition='NEW',
            rental_price=55.00,
            recommended_skill_level='INTERMEDIATE',
            is_available=True
        )

        self.all_mountain_ski = Equipment.objects.create(
            equipment_id='SKI003',
            equipment_type='SKI',
            equipment_subtype='ALL_MOUNTAIN',
            brand='Atomic',
            model='Bent 100',
            size='184',
            condition='EXCELLENT',
            rental_price=50.00,
            recommended_skill_level='INTERMEDIATE',
            is_available=True
        )

        self.snowboard = Equipment.objects.create(
            equipment_id='BOARD001',
            equipment_type='SNOWBOARD',
            brand='Burton',
            model='Custom',
            size='158',
            condition='EXCELLENT',
            rental_price=45.00,
            recommended_skill_level='ADVANCED',
            is_available=True
        )

        # Set up clients
        self.client = Client()
        self.librarian_client = Client()
        self.librarian_client.login(username='librarian', password='pass')
        self.user_client = Client()
        self.user_client.login(username='testuser', password='pass')

    @unittest.skip("Skipping this test for now")
    def test_index_view_with_no_filters(self):
        """Test that index view displays all equipment when no filters are applied."""
        response = self.client.get(reverse('equipment:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['equipment_list']), 4)
        self.assertIn(self.powder_ski, response.context['equipment_list'])
        self.assertIn(self.freestyle_ski, response.context['equipment_list'])
        self.assertIn(self.all_mountain_ski, response.context['equipment_list'])
        self.assertIn(self.snowboard, response.context['equipment_list'])

    @unittest.skip("Skipping this test for now")
    def test_index_view_with_type_filter(self):
        """Test filtering by equipment type."""
        # Filter for skis only
        response = self.client.get(reverse('equipment:index'), {'type': 'SKI'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['equipment_list']), 3)
        self.assertIn(self.powder_ski, response.context['equipment_list'])
        self.assertIn(self.freestyle_ski, response.context['equipment_list'])
        self.assertIn(self.all_mountain_ski, response.context['equipment_list'])
        self.assertNotIn(self.snowboard, response.context['equipment_list'])

    @unittest.skip("Skipping this test for now")
    def test_index_view_with_ski_subtype_filter(self):
        """Test filtering by ski subtype."""
        # Filter for powder skis only
        response = self.client.get(reverse('equipment:index'), {'type': 'SKI', 'ski_subtype': 'POWDER'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['equipment_list']), 1)
        self.assertIn(self.powder_ski, response.context['equipment_list'])
        self.assertNotIn(self.freestyle_ski, response.context['equipment_list'])
        self.assertNotIn(self.all_mountain_ski, response.context['equipment_list'])

    @unittest.skip("Skipping this test for now")
    def test_index_view_with_skill_level_filter(self):
        """Test filtering by skill level."""
        # Filter for intermediate skill level
        response = self.client.get(reverse('equipment:index'), {'skill_level': 'INTERMEDIATE'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['equipment_list']), 2)
        self.assertIn(self.freestyle_ski, response.context['equipment_list'])
        self.assertIn(self.all_mountain_ski, response.context['equipment_list'])
        self.assertNotIn(self.powder_ski, response.context['equipment_list'])

    @unittest.skip("Skipping this test for now")
    def test_index_view_with_two_filters(self):
        """Test applying multiple filters together."""
        # Filter for intermediate skis
        response = self.client.get(reverse('equipment:index'),
                                   {'type': 'SKI', 'skill_level': 'INTERMEDIATE'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['equipment_list']), 2)
        self.assertIn(self.freestyle_ski, response.context['equipment_list'])
        self.assertIn(self.all_mountain_ski, response.context['equipment_list'])
        self.assertNotIn(self.powder_ski, response.context['equipment_list'])

    @unittest.skip("Skipping this test for now")
    def test_index_view_with_three_filters(self):
        """Test applying three filters together."""
        # Filter for intermediate all-mountain skis
        response = self.client.get(reverse('equipment:index'),
                                   {'type': 'SKI',
                                    'ski_subtype': 'ALL_MOUNTAIN',
                                    'skill_level': 'INTERMEDIATE'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['equipment_list']), 1)
        self.assertIn(self.all_mountain_ski, response.context['equipment_list'])
        self.assertNotIn(self.freestyle_ski, response.context['equipment_list'])
        self.assertNotIn(self.powder_ski, response.context['equipment_list'])

    @unittest.skip("Skipping this test for now")
    def test_index_view_sorting_low_to_high(self):
        """Test sorting options."""
        # Sort by price low to high
        response = self.client.get(reverse('equipment:index'), {'sort': 'price-low'})
        self.assertEqual(response.status_code, 200)
        equipment_list = list(response.context['equipment_list'])
        self.assertEqual(equipment_list[0], self.snowboard)  # Lowest price
        self.assertEqual(equipment_list[3], self.powder_ski)  # Highest price

    @unittest.skip("Skipping this test for now")
    def test_index_view_sorting_high_to_low(self):
        """Test sorting options."""
        # Sort by price high to low
        response = self.client.get(reverse('equipment:index'), {'sort': 'price-high'})
        self.assertEqual(response.status_code, 200)
        equipment_list = list(response.context['equipment_list'])
        self.assertEqual(equipment_list[0], self.powder_ski)  # Highest price
        self.assertEqual(equipment_list[3], self.snowboard)  # Lowest price

    @unittest.skip("Skipping this test for now")
    def test_search(self):
        """Test the equipment search functionality."""
        # Search by brand
        response = self.client.get(reverse('equipment:index'), {'search': 'rossignol'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['equipment_list']), 1)
        self.assertIn(self.powder_ski, response.context['equipment_list'])

    @unittest.skip('static file missing')
    def test_user_recommendations(self):
        """Test user-specific equipment recommendations."""
        # Login as test user with skiing preference
        response = self.user_client.get(reverse('equipment:index'))
        self.assertEqual(response.status_code, 200)

        # Check if ski recommendations are provided based on user preferences
        self.assertIn('has_complete_profile', response.context)
        self.assertTrue(response.context['has_complete_profile'])

        # Since user is INTERMEDIATE and likes SKIING, should recommend intermediate skis
        if 'ski_recommendations' in response.context:
            ski_recommendations = response.context['ski_recommendations']
            for ski in ski_recommendations:
                self.assertEqual(ski.equipment_type, 'SKI')
                self.assertEqual(ski.recommended_skill_level, 'INTERMEDIATE')

    @unittest.skip("Skipping this test for now")
    def test_add_equipment_view_anonymous(self):
        """Test the add equipment view permissions."""
        # Anonymous user should be redirected to login
        add_url = reverse('equipment:add_equipment')
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    @unittest.skip("Skipping this test for now")
    def test_add_equipment_view_patron(self):
        """Test the add equipment view permissions."""
        # Patron should not be able to access
        add_url = reverse('equipment:add_equipment')
        response = self.user_client.get(add_url)
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_add_equipment_view_librarian(self):
        """Test the add equipment view permissions."""
        # Librarian should be able to access
        add_url = reverse('equipment:add_equipment')
        response = self.librarian_client.get(add_url)
        self.assertEqual(response.status_code, 200)