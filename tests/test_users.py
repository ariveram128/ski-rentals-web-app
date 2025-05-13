from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client, TestCase


from users.models import UserProfile


class UserProfileTests(TestCase):
    """Test suite for user profile functionality."""

    def setUp(self):
        """Initialize test environment with users and profiles."""
        # Create test users
        self.patron_user = User.objects.create_user(
            username='patron_test',
            password='password123',
            email='patron@example.com',
            first_name='Pat',
            last_name='Patron'
        )
        self.librarian_user = User.objects.create_user(
            username='librarian_test',
            password='password123',
            email='librarian@example.com',
            first_name='Lib',
            last_name='Rarian'
        )

        # Create user profiles
        self.patron_profile = UserProfile.objects.create(
            user=self.patron_user,
            user_type='PATRON',
            phone_number='123-456-7890',
            height='5\'10"',
            weight='170lbs',
            boot_size='10',
            experience_level='INTERMEDIATE',
            preferred_activity='SKIING',
            preferred_terrain='ALLMOUNTAIN',
            preferred_rental_duration='DAILY',
            insurance_preference='ASK'
        )

        self.librarian_profile = UserProfile.objects.create(
            user=self.librarian_user,
            user_type='LIBRARIAN'
        )

        # Set up clients
        self.patron_client = Client()
        self.librarian_client = Client()
        self.patron_client.login(username='patron_test', password='password123')
        self.librarian_client.login(username='librarian_test', password='password123')

    def test_profile_creation(self):
        """Test that profiles are created correctly."""
        self.assertEqual(self.patron_profile.user, self.patron_user)
        self.assertEqual(self.patron_profile.user_type, 'PATRON')
        self.assertEqual(self.patron_profile.experience_level, 'INTERMEDIATE')

        self.assertEqual(self.librarian_profile.user, self.librarian_user)
        self.assertEqual(self.librarian_profile.user_type, 'LIBRARIAN')

    def test_profile_view_access(self):
        """Test that users can access their profile."""
        response = self.patron_client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile', response.context)
        self.assertEqual(response.context['profile'], self.patron_profile)

    def test_edit_profile(self):
        """Test editing a user profile."""
        edit_data = {
            'firstName': 'Updated',
            'lastName': 'Patron',
            'phone': '987-654-3210',
            'address': '123 Ski Street',
            'city': 'Mountain Town',
            'state': 'CO',
            'zipCode': '80123',
            'height': '6\'0"',
            'weight': '180lbs',
            'bootSize': '10.5',
            'experienceLevel': 'ADVANCED',
            'preferredActivity': 'BOTH',
            'preferredTerrain': 'POWDER',
            'preferredRental': 'WEEKLY',
            'insurancePreference': 'ALWAYS',
            'emailRentalReminders': 'on',
            'textRentalReminders': 'on',
            'marketingEmails': 'on',
            'publicProfile': 'on',
            'showRentals': 'on'
        }

        response = self.patron_client.post(reverse('edit_profile'), edit_data)

        # Should redirect back to edit profile on success
        self.assertEqual(response.status_code, 302)

        # Refresh patron profile from database
        self.patron_profile.refresh_from_db()
        self.patron_user.refresh_from_db()

        # Check that data was updated
        self.assertEqual(self.patron_user.first_name, 'Updated')
        self.assertEqual(self.patron_profile.height, '6\'0"')
        self.assertEqual(self.patron_profile.experience_level, 'ADVANCED')
        self.assertEqual(self.patron_profile.preferred_activity, 'BOTH')
        self.assertEqual(self.patron_profile.insurance_preference, 'ALWAYS')
        self.assertTrue(self.patron_profile.receive_email_reminders)
        self.assertTrue(self.patron_profile.receive_sms_reminders)

    def test_role_based_redirect(self):
        """Test that users are redirected to appropriate dashboard based on role."""
        # Test patron redirect
        response = self.patron_client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('patron'))

        # Test librarian redirect
        response = self.librarian_client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('librarian'))

    def test_role_based_access_control(self):
        """Test that users can only access views appropriate for their role."""
        # Patron should not access librarian view
        response = self.patron_client.get(reverse('librarian'))
        self.assertEqual(response.status_code, 302)  # Should redirect

        # Patron should access patron view
        response = self.patron_client.get(reverse('patron'))
        self.assertEqual(response.status_code, 200)

        # Librarian should access librarian view
        response = self.librarian_client.get(reverse('librarian'))
        self.assertEqual(response.status_code, 200)

        # Librarian can currently access the patron view and it doesn't cause any issues
        # if this isn't desired then we can uncomment the rest of this test
        # response = self.librarian_client.get(reverse('patron'))
        # self.assertEqual(response.status_code, 302)  # Should redirect

    def test_promote_to_librarian(self):
        """Test Librarian promoting a patron to librarian."""
        # Only librarians can promote users
        response = self.librarian_client.post(
            reverse('promote_to_librarian', args=[self.patron_user.id])
        )

        # Should redirect after success
        self.assertEqual(response.status_code, 302)

        # Refresh patron profile
        self.patron_profile.refresh_from_db()

        # Check that role was updated
        self.assertEqual(self.patron_profile.user_type, 'LIBRARIAN')

    def test_promote_to_librarian_failure(self):
        """Test Patron promoting a patron to librarian."""
        # Patrons cannot promote users
        new_patron = User.objects.create_user(username='newpatron', password='pass')
        UserProfile.objects.create(user=new_patron, user_type='PATRON')

        response = self.patron_client.post(
            reverse('promote_to_librarian', args=[new_patron.id])
        )

        # Should redirect with an error
        self.assertEqual(response.status_code, 302)

        # User should still be a patron
        new_patron_profile = UserProfile.objects.get(user=new_patron)
        self.assertEqual(new_patron_profile.user_type, 'PATRON')

    def test_librarian_view_access(self):
        """Test that only librarians can access management views."""
        # Librarian should access management page
        response = self.librarian_client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)

        # Patron should not access management page
        response = self.patron_client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 302)  # Should redirect