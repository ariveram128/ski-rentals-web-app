import unittest

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from equipment.models import Equipment, Review
from users.models import UserProfile


class ReviewTests(TestCase):
    """Test suite for equipment review functionality."""

    def setUp(self):
        """Initialize test environment with users, equipment, and reviews."""
        # Create test users
        self.patron = User.objects.create_user(username='patron', password='password123')
        self.other_patron = User.objects.create_user(username='other_patron', password='password123')

        # Create user profiles
        self.patron_profile = UserProfile.objects.create(
            user=self.patron,
            user_type='PATRON'
        )
        self.other_patron_profile = UserProfile.objects.create(
            user=self.other_patron,
            user_type='PATRON'
        )

        # Create test equipment
        self.equipment = Equipment.objects.create(
            equipment_id='SKI001',
            equipment_type='SKI',
            brand='Rossignol',
            model='Experience 88',
            size='170cm',
            condition='NEW',
            rental_price=50.00,
            recommended_skill_level='INTERMEDIATE'
        )

        # Set up clients
        self.patron_client = Client()
        self.other_patron_client = Client()
        self.patron_client.login(username='patron', password='password123')
        self.other_patron_client.login(username='other_patron', password='password123')

    def test_add_review(self):
        """Test adding a review to equipment."""
        # Check initial average rating
        self.assertEqual(self.equipment.average_rating, 0.0)

        # Add review
        response = self.patron_client.post(
            reverse('equipment:add_review', args=[self.equipment.id]),
            {'rating': 4, 'comment': 'Great skis!'}
        )

        # Should redirect back to equipment detail
        self.assertEqual(response.status_code, 302)

        # Verify review was added
        review = Review.objects.get(equipment=self.equipment, user=self.patron)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Great skis!')

        # Check that average rating was updated
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.average_rating, 4.0)

    def test_update_review(self):
        """Test updating an existing review."""
        # Create initial review
        Review.objects.create(
            equipment=self.equipment,
            user=self.patron,
            rating=3,
            comment='Decent skis'
        )
        self.equipment.update_average_rating()

        # Check initial average rating
        self.assertEqual(self.equipment.average_rating, 3.0)

        # Update review
        response = self.patron_client.post(
            reverse('equipment:add_review', args=[self.equipment.id]),
            {'rating': 5, 'comment': 'Much better than I thought!'}
        )

        # Should redirect back to equipment detail
        self.assertEqual(response.status_code, 302)

        # Verify review was updated
        review = Review.objects.get(equipment=self.equipment, user=self.patron)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Much better than I thought!')

        # Check that average rating was updated
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.average_rating, 5.0)

    def test_multiple_reviews(self):
        """Test multiple reviews from different users."""
        # Add first review
        self.patron_client.post(
            reverse('equipment:add_review', args=[self.equipment.id]),
            {'rating': 5, 'comment': 'Excellent skis!'}
        )

        # Add second review
        self.other_patron_client.post(
            reverse('equipment:add_review', args=[self.equipment.id]),
            {'rating': 3, 'comment': 'Good but not great.'}
        )

        # Check that both reviews exist
        reviews = Review.objects.filter(equipment=self.equipment)
        self.assertEqual(reviews.count(), 2)

        # Check that average rating is correct
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.average_rating, 4.0)  # (5+3)/2 = 4.0

    @unittest.skip('skipping test fix static file problem')
    def test_review_display_in_detail_view(self):
        """Test that reviews are displayed on equipment detail page."""
        # Add reviews
        Review.objects.create(
            equipment=self.equipment,
            user=self.patron,
            rating=5,
            comment='Excellent skis!'
        )
        Review.objects.create(
            equipment=self.equipment,
            user=self.other_patron,
            rating=3,
            comment='Good but not great.'
        )
        self.equipment.update_average_rating()

        # View equipment detail
        response = self.patron_client.get(reverse('equipment:detail', args=[self.equipment.id]))
        self.assertEqual(response.status_code, 200)

        # Check that reviews are in context
        self.assertIn('reviews', response.context)
        reviews = list(response.context['reviews'])
        self.assertEqual(len(reviews), 2)

        # Check rating distribution
        self.assertIn('rating_distribution', response.context)
        rating_dist = response.context['rating_distribution']
        self.assertEqual(rating_dist['total'], 2)
        self.assertEqual(rating_dist['5'], 1)  # One 5-star review
        self.assertEqual(rating_dist['3'], 1)  # One 3-star review

        # Check that user's own review is identified
        self.assertIn('user_review', response.context)
        self.assertEqual(response.context['user_review'].rating, 5)

    def test_review_permissions(self):
        """Test that only authenticated users can review equipment."""
        # Anonymous client
        anonymous_client = Client()
        response = anonymous_client.post(
            reverse('equipment:add_review', args=[self.equipment.id]),
            {'rating': 4, 'comment': 'Not going to work'}
        )

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/accounts/login/?next={reverse("equipment:add_review", args=[self.equipment.id])}',
            fetch_redirect_response=False
        )

        # No review should be created
        self.assertEqual(Review.objects.count(), 0)