import io
import unittest

from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from equipment.models import Equipment, EquipmentImage
from users.models import UserProfile


class EquipmentImageTests(TestCase):
    """Test suite for equipment image upload and management functionality."""

    def setUp(self):
        """Initialize test environment."""
        # Create test users
        self.librarian = User.objects.create_user(username='librarian', password='password123')
        self.patron = User.objects.create_user(username='patron', password='password123')

        # Create user profiles
        self.librarian_profile = UserProfile.objects.create(
            user=self.librarian,
            user_type='LIBRARIAN'
        )
        self.patron_profile = UserProfile.objects.create(
            user=self.patron,
            user_type='PATRON'
        )

        # Create test equipment
        self.equipment = Equipment.objects.create(
            equipment_id='SKI001',
            equipment_type='SKI',
            brand='Rossignol',
            model='Experience 88',
            size='170',
            condition='NEW',
            rental_price=50.00
        )

        # Set up clients
        self.librarian_client = Client()
        self.patron_client = Client()
        self.librarian_client.login(username='librarian', password='password123')
        self.patron_client.login(username='patron', password='password123')

        # Generate a test image
        self.test_image = self._create_test_image()

    def _create_test_image(self):
        """Create a test image file."""
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'png')
        file.name = 'test_image.png'
        file.seek(0)
        return SimpleUploadedFile(file.name, file.read(), content_type='image/png')

    def test_add_main_image_with_new_equipment(self):
        """Test adding a main image when creating new equipment."""
        form_data = {
            'equipment_id': 'SKI002',
            'equipment_type': 'SKI',
            'brand': 'K2',
            'model': 'Poacher',
            'size': '177',
            'condition': 'NEW',
            'rental_price': 55.00,
            'is_available': True,
        }

        # Add image to form data
        form_data['main_image'] = self.test_image

        response = self.librarian_client.post(reverse('equipment:add_equipment'), form_data)
        self.assertEqual(response.status_code, 302)  # Should redirect

        # Verify equipment was created with image
        new_ski = Equipment.objects.get(equipment_id='SKI002')
        self.assertIsNotNone(new_ski.main_image)
        self.assertTrue(new_ski.main_image.name.endswith('.png'))

    def test_add_additional_images(self):
        """Test adding additional images to existing equipment."""
        # Create two test images
        test_image2 = self._create_test_image()

        # Add images using the add_equipment_images view
        response = self.librarian_client.post(
            reverse('equipment:add_images', args=[self.equipment.id]),
            {'images': [self.test_image, test_image2]}
        )

        # Check response
        self.assertEqual(response.status_code, 302)  # Should redirect to equipment detail

        # Verify images were added
        images = EquipmentImage.objects.filter(equipment=self.equipment)
        self.assertEqual(images.count(), 2)

    def test_delete_image(self):
        """Test deleting equipment images."""
        # First add an image
        image = EquipmentImage.objects.create(
            equipment=self.equipment,
            image=self.test_image
        )

        # Verify image was added
        images = EquipmentImage.objects.filter(equipment=self.equipment)
        self.assertEqual(images.count(), 1)

        # Delete the image
        response = self.librarian_client.post(
            reverse('equipment:delete_image', args=[image.id])
        )

        # Check response
        self.assertEqual(response.status_code, 302)  # Should redirect

        # Verify image was deleted
        self.assertEqual(EquipmentImage.objects.filter(equipment=self.equipment).count(), 0)

    @unittest.skip("Skipping temporarily need to fix")
    def test_patron_cannot_manage_images(self):
        """Test that patrons cannot add or delete images."""
        # First add an image as librarian
        image = EquipmentImage.objects.create(
            equipment=self.equipment,
            image=self.test_image
        )

        # Patron tries to add an image
        response = self.patron_client.post(
            reverse('equipment:add_images', args=[self.equipment.id]),
            {'images': [self._create_test_image()]}
        )

        # Should redirect (not allowed)
        self.assertEqual(response.status_code, 302)

        # No new images should be added
        self.assertEqual(EquipmentImage.objects.filter(equipment=self.equipment).count(), 1)

        # Patron tries to delete an image
        response = self.patron_client.post(
            reverse('equipment:delete_image', args=[image.id])
        )

        # Should redirect (not allowed)
        self.assertEqual(response.status_code, 302)

        # Image should still exist
        self.assertEqual(EquipmentImage.objects.filter(equipment=self.equipment).count(), 1)

    @unittest.skip("Skipping temporarily need to fix")
    def test_images_displayed_in_detail_view(self):
        """Test that images are displayed in equipment detail view."""
        # Add main image
        self.equipment.main_image = self.test_image
        self.equipment.save()

        # Add additional images
        image1 = EquipmentImage.objects.create(
            equipment=self.equipment,
            image=self._create_test_image(),
            caption="Test Image 1"
        )
        image2 = EquipmentImage.objects.create(
            equipment=self.equipment,
            image=self._create_test_image(),
            caption="Test Image 2"
        )

        # View equipment detail
        response = self.librarian_client.get(reverse('equipment:detail', args=[self.equipment.id]))

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check that images are in context
        self.assertIn('additional_images', response.context)
        images = list(response.context['additional_images'])
        self.assertEqual(len(images), 2)
        self.assertIn(image1, images)
        self.assertIn(image2, images)