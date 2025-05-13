import unittest

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from equipment.models import Equipment, Rental, Cart
from users.models import UserProfile


class RentalTests(TestCase):
    """Test suite for the Rental model functionality."""

    def setUp(self):
        """Initialize test environment with users, equipment, and rentals."""
        self.patron = User.objects.create_user(username='patron', password='password123')
        self.librarian = User.objects.create_user(username='librarian', password='password123')

        self.patron_profile = UserProfile.objects.create(
            user=self.patron,
            user_type='PATRON'
        )
        self.librarian_profile = UserProfile.objects.create(
            user=self.librarian,
            user_type='LIBRARIAN'
        )

        self.ski = Equipment.objects.create(
            equipment_id='SKI001',
            equipment_type='SKI',
            equipment_subtype='POWDER',
            brand='Rossignol',
            model='Soul 7',
            size='180cm',
            condition='NEW',
            rental_price=60.00,
            is_available=True
        )

        self.snowboard = Equipment.objects.create(
            equipment_id='BOARD001',
            equipment_type='SNOWBOARD',
            brand='Burton',
            model='Custom',
            size='158cm',
            condition='EXCELLENT',
            rental_price=45.00,
            is_available=True
        )

        self.rental = Rental.objects.create(
            equipment=self.ski,
            patron=self.patron,
            rental_duration='DAILY',
            rental_price=60.00,
            due_date=timezone.localtime() + timedelta(days=1),
            checked_out_condition='NEW'
        )

        self.patron_client = Client()
        self.librarian_client = Client()
        self.patron_client.login(username='patron', password='password123')
        self.librarian_client.login(username='librarian', password='password123')

    def test_rental_creation(self):
        """Test that the rental instance is created successfully."""
        self.assertTrue(isinstance(self.rental, Rental))
        self.assertEqual(self.rental.equipment, self.ski)
        self.assertEqual(self.rental.patron, self.patron)
        self.assertEqual(self.rental.rental_status, 'PENDING')

    def test_rental_approval_workflow(self):
        """Test the complete rental approval workflow."""
        # Initial state - equipment should be available, rental pending
        self.assertEqual(self.rental.rental_status, 'PENDING')
        self.assertTrue(self.ski.is_available)

        # Librarian approves the rental
        response = self.librarian_client.post(
            reverse('equipment:approve_rental', args=[self.rental.id])
        )
        self.assertEqual(response.status_code, 302)  # Should redirect

        # Refresh objects from database
        self.rental.refresh_from_db()
        self.ski.refresh_from_db()

        # After approval - rental should be active, equipment unavailable
        self.assertEqual(self.rental.rental_status, 'ACTIVE')
        self.assertFalse(self.ski.is_available)

        # Librarian completes the rental
        response = self.librarian_client.post(
            reverse('equipment:complete_rental', args=[self.rental.id]),
            {'return_condition': 'GOOD', 'return_notes': 'Returned with minor scratches'}
        )
        self.assertEqual(response.status_code, 302)

        self.rental.refresh_from_db()
        self.ski.refresh_from_db()

        # After completion - rental should be completed, equipment available again
        self.assertEqual(self.rental.rental_status, 'COMPLETED')
        self.assertEqual(self.rental.return_condition, 'GOOD')
        self.assertEqual(self.rental.return_notes, 'Returned with minor scratches')
        self.assertTrue(self.ski.is_available)
        self.assertEqual(self.ski.total_rentals, 1)

    def test_rental_rejection(self):
        """Test rental rejection workflow."""
        # Librarian rejects the rental
        response = self.librarian_client.post(
            reverse('equipment:reject_rental', args=[self.rental.id])
        )
        self.assertEqual(response.status_code, 302)

        # Refresh objects
        self.rental.refresh_from_db()
        self.ski.refresh_from_db()

        # After rejection - rental should be cancelled, equipment still available
        self.assertEqual(self.rental.rental_status, 'CANCELLED')
        self.assertTrue(self.ski.is_available)

    def test_patron_cancellation(self):
        """Test patron's ability to cancel their own pending rental."""
        # Patron cancels the rental
        response = self.patron_client.post(
            reverse('equipment:cancel_rental', args=[self.rental.id])
        )
        self.assertEqual(response.status_code, 302)

        # Refresh objects
        self.rental.refresh_from_db()

        # After cancellation - rental should be cancelled
        self.assertEqual(self.rental.rental_status, 'CANCELLED')
        self.assertTrue(self.ski.is_available)

    def test_patron_cannot_cancel_active_rental(self):
        """Test that patrons cannot cancel already active rentals."""
        # First, make the rental active
        self.rental.rental_status = 'ACTIVE'
        self.rental.save()
        self.ski.is_available = False
        self.ski.save()

        # Attempt to cancel
        response = self.patron_client.post(
            reverse('equipment:cancel_rental', args=[self.rental.id])
        )

        # Refresh objects
        self.rental.refresh_from_db()

        # Should not change the rental status
        self.assertEqual(self.rental.rental_status, 'ACTIVE')
        self.assertFalse(self.ski.is_available)

    def test_patron_cannot_approve_rentals(self):
        """Test that patrons cannot approve rentals."""
        # Create a new rental request
        new_rental = Rental.objects.create(
            equipment=self.snowboard,
            patron=self.patron,
            rental_duration='DAILY',
            rental_price=45.00,
            due_date=timezone.localtime() + timedelta(days=1),
            checked_out_condition='EXCELLENT'
        )

        # Patron tries to approve the rental
        response = self.patron_client.post(
            reverse('equipment:approve_rental', args=[new_rental.id])
        )

        # Refresh objects
        new_rental.refresh_from_db()

        # Status should remain pending
        self.assertEqual(new_rental.rental_status, 'PENDING')

    def test_librarian_manage_rentals_view(self):
        """Test the librarian's rental management view with filters and permissions."""

        active_rental = Rental.objects.create(
            equipment=self.snowboard,
            patron=self.patron,
            rental_duration='DAILY',
            rental_price=45.00,
            due_date=timezone.localtime() + timedelta(days=1),
            checked_out_condition='EXCELLENT',
            rental_status='ACTIVE'
        )

        completed_rental = Rental.objects.create(
            equipment=self.ski,
            patron=self.patron,
            rental_duration='WEEKLY',
            rental_price=200.00,
            due_date=timezone.localtime() - timedelta(days=7),
            checked_out_condition='NEW',
            rental_status='COMPLETED',
            return_date=timezone.localtime() - timedelta(days=1),
            return_condition='GOOD'
        )

        pending_rental = Rental.objects.create(
            equipment=self.snowboard,
            patron=self.patron,
            rental_duration='DAILY',
            rental_price=50.00,
            due_date=timezone.localtime() + timedelta(days=2),
            checked_out_condition='GOOD',
            rental_status='PENDING'
        )

        # Test unfiltered view
        response = self.librarian_client.get(reverse('equipment:manage_rentals'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(active_rental, response.context['rentals'])
        self.assertIn(completed_rental, response.context['rentals'])
        self.assertIn(pending_rental, response.context['rentals'])

        # Test pending filter
        response = self.librarian_client.get(
            reverse('equipment:manage_rentals'),
            {'status': 'pending'}
        )
        self.assertEqual(response.status_code, 200)
        rentals = list(response.context['rentals'])
        self.assertIn(pending_rental, rentals)
        self.assertNotIn(active_rental, rentals)
        self.assertNotIn(completed_rental, rentals)

        # Test active filter
        response = self.librarian_client.get(
            reverse('equipment:manage_rentals'),
            {'status': 'active'}
        )
        self.assertEqual(response.status_code, 200)
        rentals = list(response.context['rentals'])
        self.assertIn(active_rental, rentals)
        self.assertNotIn(pending_rental, rentals)
        self.assertNotIn(completed_rental, rentals)

        # Patron should not be able to access this page
        response = self.patron_client.get(reverse('equipment:manage_rentals'))
        self.assertEqual(len(response.context['rentals']), 0)

    # TODO: Add tests for rental history tracking
    # def test_user_rental_history(self):
    #     """Test user's rental history and preferences tracking"""

    # TODO: Add test suite for equipment maintenance scheduling
    # - Test maintenance due date calculations
    # - Test maintenance status updates
    # - Test equipment availability during maintenance

class RentalWorkflowTests(TestCase):
    """Comprehensive tests for the entire rental workflow."""

    def setUp(self):
        """Initialize test environment."""
        # Create test users
        self.patron = User.objects.create_user(username='patron', password='password123')
        self.librarian = User.objects.create_user(username='librarian', password='password123')

        # Create user profiles
        self.patron_profile = UserProfile.objects.create(
            user=self.patron,
            user_type='PATRON',
            experience_level='INTERMEDIATE',
            preferred_activity='SKIING',
            preferred_rental_duration='DAILY'
        )
        self.librarian_profile = UserProfile.objects.create(
            user=self.librarian,
            user_type='LIBRARIAN'
        )

        # Create test equipment
        self.ski = Equipment.objects.create(
            equipment_id='SKI001',
            equipment_type='SKI',
            brand='Rossignol',
            model='Experience 88',
            size='170cm',
            condition='EXCELLENT',
            rental_price=50.00,
            is_available=True
        )

        self.snowboard = Equipment.objects.create(
            equipment_id='BOARD001',
            equipment_type='SNOWBOARD',
            brand='Burton',
            model='Custom',
            size='158cm',
            condition='NEW',
            rental_price=60.00,
            is_available=True
        )

        # Set up clients
        self.patron_client = Client()
        self.librarian_client = Client()
        self.patron_client.login(username='patron', password='password123')
        self.librarian_client.login(username='librarian', password='password123')

    @unittest.skip('static file missing')
    def test_full_rental_lifecycle(self):
        """Test the complete lifecycle of a rental from browsing to return."""

        # Patron browses equipment
        response = self.patron_client.get(reverse('equipment:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rossignol Experience 88')
        self.assertContains(response, 'Burton Custom')

        # Patron views equipment detail
        response = self.patron_client.get(reverse('equipment:detail', args=[self.ski.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rossignol Experience 88')

        # Patron adds equipment to cart
        today = timezone.localtime().date()
        end_date = today + timedelta(days=3)

        response = self.patron_client.post(
            reverse('equipment:add_to_cart', args=[self.ski.id]),
            {
                'start_date': today.isoformat(),
                'end_date': end_date.isoformat(),
                'rental_duration': 'DAILY'
            }
        )

        # Should redirect to cart
        self.assertEqual(response.status_code, 302)

        # Patron views cart
        response = self.patron_client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rossignol Experience 88')

        # Patron adds another item to cart
        response = self.patron_client.post(
            reverse('equipment:add_to_cart', args=[self.snowboard.id]),
            {
                'start_date': today.isoformat(),
                'end_date': end_date.isoformat(),
                'rental_duration': 'DAILY'
            }
        )

        # Should now have 2 items in cart
        cart = Cart.objects.get(user=self.patron)
        self.assertEqual(cart.items.count(), 2)

        # Patron submits rental request
        response = self.patron_client.post(reverse('equipment:submit_rental_request'))

        # Should redirect to patron dashboard
        self.assertEqual(response.status_code, 302)

        # Cart should be empty now
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 0)

        # Two rental requests should be created
        rentals = Rental.objects.filter(patron=self.patron)
        self.assertEqual(rentals.count(), 2)

        ski_rental = rentals.get(equipment=self.ski)
        snowboard_rental = rentals.get(equipment=self.snowboard)

        self.assertEqual(ski_rental.rental_status, 'PENDING')
        self.assertEqual(snowboard_rental.rental_status, 'PENDING')

        # Equipment should still be available until approved
        self.ski.refresh_from_db()
        self.snowboard.refresh_from_db()
        self.assertTrue(self.ski.is_available)
        self.assertTrue(self.snowboard.is_available)

        # Librarian views pending requests
        response = self.librarian_client.get(reverse('equipment:manage_rentals'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rossignol Experience 88')
        self.assertContains(response, 'Burton Custom')

        # Librarian approves ski rental
        response = self.librarian_client.post(
            reverse('equipment:approve_rental', args=[ski_rental.id])
        )

        # Should redirect to librarian dashboard
        self.assertEqual(response.status_code, 302)

        # Ski rental should be active now
        ski_rental.refresh_from_db()
        self.assertEqual(ski_rental.rental_status, 'ACTIVE')

        # Ski should be marked as unavailable
        self.ski.refresh_from_db()
        self.assertFalse(self.ski.is_available)

        # Librarian rejects snowboard rental
        response = self.librarian_client.post(
            reverse('equipment:reject_rental', args=[snowboard_rental.id])
        )

        # Should redirect to librarian dashboard
        self.assertEqual(response.status_code, 302)

        # Snowboard rental should be cancelled
        snowboard_rental.refresh_from_db()
        self.assertEqual(snowboard_rental.rental_status, 'CANCELLED')

        # Snowboard should still be available
        self.snowboard.refresh_from_db()
        self.assertTrue(self.snowboard.is_available)

        # Patron views active rentals
        response = self.patron_client.get(reverse('patron'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rossignol Experience 88')
        self.assertNotContains(response, 'PENDING')  # No more pending rentals

        # Librarian marks rental as completed
        response = self.librarian_client.post(
            reverse('equipment:complete_rental', args=[ski_rental.id]),
            {
                'return_condition': 'GOOD',
                'return_notes': 'Returned with minor wear and tear'
            }
        )

        # Should redirect to librarian dashboard
        self.assertEqual(response.status_code, 302)

        # Ski rental should be completed
        ski_rental.refresh_from_db()
        self.assertEqual(ski_rental.rental_status, 'COMPLETED')
        self.assertEqual(ski_rental.return_condition, 'GOOD')
        self.assertEqual(ski_rental.return_notes, 'Returned with minor wear and tear')

        # Ski should be available again
        self.ski.refresh_from_db()
        self.assertTrue(self.ski.is_available)

        # Rental count should be incremented
        self.assertEqual(self.ski.total_rentals, 1)

        # Step 13: Patron adds a review
        response = self.patron_client.post(
            reverse('equipment:add_review', args=[self.ski.id]),
            {
                'rating': 5,
                'comment': 'Excellent skis, would definitely rent again!'
            }
        )

        # Should redirect to equipment detail
        self.assertEqual(response.status_code, 302)

        # Equipment rating should be updated
        self.ski.refresh_from_db()
        self.assertEqual(self.ski.average_rating, 5.0)

    @unittest.skip('static file missing')
    def test_quick_rent_functionality(self):
        """Test the quick rent feature."""
        # Patron uses quick rent feature
        response = self.patron_client.get(
            reverse('equipment:quick_rent', args=[self.ski.id])
        )

        # Should redirect to cart
        self.assertEqual(response.status_code, 302)

        # Check cart
        cart = Cart.objects.get(user=self.patron)
        self.assertEqual(cart.items.count(), 1)

        # Verify item details
        cart_item = cart.items.first()
        self.assertEqual(cart_item.equipment, self.ski)
        self.assertEqual(cart_item.rental_duration, 'DAILY')  # From user preference

        # Dates should be today and tomorrow by default for daily
        today = timezone.localtime().date()
        self.assertEqual(cart_item.start_date.date(), today)
        self.assertEqual(cart_item.end_date.date(), today + timedelta(days=1))

    def test_multiple_active_rentals_for_same_equipment(self):
        """Test handling of concurrent rental requests for the same equipment."""
        # Create another patron
        other_patron = User.objects.create_user(username='other_patron', password='password123')
        UserProfile.objects.create(user=other_patron, user_type='PATRON')
        other_patron_client = Client()
        other_patron_client.login(username='other_patron', password='password123')

        # First patron rents the ski
        today = timezone.localtime().date()
        rental1 = Rental.objects.create(
            equipment=self.ski,
            patron=self.patron,
            rental_duration='DAILY',
            rental_status='PENDING',
            rental_price=50.00,
            due_date=timezone.localtime() + timedelta(days=3),
            checked_out_condition='EXCELLENT'
        )

        # Librarian approves the rental
        self.librarian_client.post(
            reverse('equipment:approve_rental', args=[rental1.id])
        )

        # Equipment should now be unavailable
        self.ski.refresh_from_db()
        self.assertFalse(self.ski.is_available)

        # Second patron tries to rent the same ski
        response = other_patron_client.post(
            reverse('equipment:add_to_cart', args=[self.ski.id]),
            {
                'start_date': today.isoformat(),
                'end_date': (today + timedelta(days=3)).isoformat(),
                'rental_duration': 'DAILY'
            }
        )

        self.assertFalse(Cart.objects.filter(user=other_patron).exists())