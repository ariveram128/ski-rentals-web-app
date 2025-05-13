from django.core.management.base import BaseCommand
from equipment.models import Equipment
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Creates sample equipment data for testing'

    def handle(self, *args, **options):
        # Sample data for equipment
        equipment_data = [
            {
                'equipment_id': 'SKI001',
                'equipment_type': 'SKI',
                'brand': 'Rossignol',
                'model': 'Experience 88',
                'size': '176cm',
                'condition': 'EXCELLENT',
                'is_available': True,
                'notes': 'Versatile all-mountain skis perfect for intermediate to advanced skiers. These skis handle well on groomed runs and can tackle some light powder conditions. Tuned recently with new bindings.',
                'recommended_skill_level': 'INTERMEDIATE',
                'recommended_height_range': '170-185cm',
                'rental_price': Decimal('45.00'),
                'rent_to_own_price': Decimal('450.00'),
                'total_rentals': 12,
                'average_rating': Decimal('4.5'),
            },
            {
                'equipment_id': 'SKI002',
                'equipment_type': 'SKI',
                'brand': 'Salomon',
                'model': 'QST 92',
                'size': '169cm',
                'condition': 'GOOD',
                'is_available': True,
                'notes': 'All-mountain skis with good float in powder. Great for skiers looking to explore the entire mountain.',
                'recommended_skill_level': 'ADVANCED',
                'recommended_height_range': '165-175cm',
                'rental_price': Decimal('50.00'),
                'rent_to_own_price': Decimal('500.00'),
                'total_rentals': 8,
                'average_rating': Decimal('4.2'),
            },
            {
                'equipment_id': 'SNOWBOARD001',
                'equipment_type': 'SNOWBOARD',
                'brand': 'Burton',
                'model': 'Custom Flying V',
                'size': '156cm',
                'condition': 'NEW',
                'is_available': True,
                'notes': 'Versatile snowboard suitable for all terrain. Perfect for intermediate riders looking to progress.',
                'recommended_skill_level': 'INTERMEDIATE',
                'recommended_height_range': '165-175cm',
                'rental_price': Decimal('40.00'),
                'rent_to_own_price': Decimal('400.00'),
                'total_rentals': 5,
                'average_rating': Decimal('4.8'),
            },
            {
                'equipment_id': 'BOOTS001',
                'equipment_type': 'BOOTS',
                'brand': 'Atomic',
                'model': 'Hawx Prime 120',
                'size': '27.5',
                'condition': 'EXCELLENT',
                'is_available': True,
                'notes': 'Comfortable ski boots with medium flex. Good for intermediate skiers with medium-width feet.',
                'recommended_skill_level': 'INTERMEDIATE',
                'recommended_height_range': '',
                'rental_price': Decimal('25.00'),
                'rent_to_own_price': Decimal('250.00'),
                'total_rentals': 15,
                'average_rating': Decimal('4.0'),
            },
            {
                'equipment_id': 'HELMET001',
                'equipment_type': 'HELMET',
                'brand': 'Smith',
                'model': 'Holt',
                'size': 'M',
                'condition': 'GOOD',
                'is_available': True,
                'notes': 'Lightweight helmet with good ventilation. Includes adjustable dial for perfect fit.',
                'recommended_skill_level': '',
                'recommended_height_range': '',
                'rental_price': Decimal('15.00'),
                'rent_to_own_price': Decimal('100.00'),
                'total_rentals': 20,
                'average_rating': Decimal('4.3'),
            },
            {
                'equipment_id': 'POLES001',
                'equipment_type': 'POLES',
                'brand': 'Black Diamond',
                'model': 'Traverse',
                'size': '120cm',
                'condition': 'GOOD',
                'is_available': True,
                'notes': 'Durable aluminum ski poles suitable for all-mountain skiing.',
                'recommended_skill_level': '',
                'recommended_height_range': '170-180cm',
                'rental_price': Decimal('10.00'),
                'rent_to_own_price': Decimal('60.00'),
                'total_rentals': 25,
                'average_rating': Decimal('4.1'),
            },
            {
                'equipment_id': 'GOGGLES001',
                'equipment_type': 'GOGGLES',
                'brand': 'Oakley',
                'model': 'Flight Deck',
                'size': 'One Size',
                'condition': 'EXCELLENT',
                'is_available': True,
                'notes': 'Wide-view goggles with anti-fog coating. Includes interchangeable lenses for different light conditions.',
                'recommended_skill_level': '',
                'recommended_height_range': '',
                'rental_price': Decimal('12.00'),
                'rent_to_own_price': Decimal('120.00'),
                'total_rentals': 18,
                'average_rating': Decimal('4.7'),
            },
            {
                'equipment_id': 'SNOWBOARD002',
                'equipment_type': 'SNOWBOARD',
                'brand': 'GNU',
                'model': 'Money',
                'size': '159cm',
                'condition': 'GOOD',
                'is_available': False,  # Currently rented out
                'notes': 'All-mountain freestyle board. Great for park and all-mountain riding.',
                'recommended_skill_level': 'ADVANCED',
                'recommended_height_range': '175-185cm',
                'rental_price': Decimal('45.00'),
                'rent_to_own_price': Decimal('420.00'),
                'total_rentals': 10,
                'average_rating': Decimal('4.4'),
            },
        ]

        # Create equipment
        for data in equipment_data:
            equipment = Equipment.objects.create(**data)
            self.stdout.write(self.style.SUCCESS(f'Created {equipment.brand} {equipment.model} ({equipment.equipment_id})'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(equipment_data)} equipment items')) 