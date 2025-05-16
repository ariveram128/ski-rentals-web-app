#!/usr/bin/env python
import os
import django
import random
from datetime import timedelta, date

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skirentals.settings')
django.setup()

# Import models after Django setup
from django.contrib.auth.models import User
from equipment.models import Equipment, Collection
from django.utils import timezone
from django.core.files.base import ContentFile
import requests

def create_demo_equipment():
    # Get or create a librarian user to be the owner of the equipment
    librarian, created = User.objects.get_or_create(
        username='demo_librarian',
        defaults={
            'email': 'demo@example.com',
            'is_staff': True,
        }
    )
    if created:
        librarian.set_password('password123')
        librarian.save()
        print(f"Created demo librarian: {librarian.username}")
    else:
        print(f"Using existing librarian: {librarian.username}")
    
    # Equipment types and their subtypes
    equipment_types = {
        'SKI': ['POWDER', 'ALL_MOUNTAIN', 'FREESTYLE', 'FREERIDE', 'TOURING'],
        'SNOWBOARD': [],
        'POLES': [],
        'BOOTS': [],
        'HELMET': [],
        'JACKET': [],
        'PANTS': [],
        'GOGGLES': [],
        'GLOVES': []
    }
    
    # Skill levels
    skill_levels = ['BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT']
    
    # Sizes
    sizes = ['S', 'M', 'L', 'XL', 'XXL']
    
    # Brand names
    brands = [
        'Alpine Pro', 'Snowbird', 'Mountain King', 'Powder Perfect', 
        'Nordic Trail', 'Summit Gear', 'Freeride', 'Avalanche', 
        'IceBreaker', 'Peak Performance'
    ]
    
    # Create equipment items
    equipment_created = 0
    
    for eq_type, subtypes in equipment_types.items():
        # Create multiple items for each type
        for i in range(1, 6):  # Create 5 of each type
            # For skis, add subtypes
            if eq_type == 'SKI' and subtypes:
                subtype = random.choice(subtypes)
            else:
                subtype = None
            
            # Generate equipment name and model
            brand = random.choice(brands)
            model_name = f"{eq_type.capitalize()} Pro {random.randint(100, 999)}"
            
            if eq_type in ['SKI', 'SNOWBOARD', 'POLES', 'BOOTS']:
                skill_level = random.choice(skill_levels)
            else:
                skill_level = None
                
            if eq_type in ['JACKET', 'PANTS', 'GLOVES']:
                size = random.choice(sizes)
            elif eq_type in ['SKI', 'SNOWBOARD']:
                # Length in cm
                size = str(random.randint(140, 190))
            elif eq_type == 'BOOTS':
                # Mondopoint
                size = str(random.randint(22, 30)) + ".5"
            elif eq_type == 'POLES':
                size = str(random.randint(100, 140))
            else:
                size = random.choice(['S', 'M', 'L', 'XL'])
            
            # Set appropriate pricing
            if eq_type in ['SKI', 'SNOWBOARD']:
                rental_price = random.randint(40, 80)
                weekly_rate = rental_price * 5
                seasonal_rate = weekly_rate * 4
            elif eq_type in ['BOOTS', 'HELMET']:
                rental_price = random.randint(15, 30)
                weekly_rate = rental_price * 5
                seasonal_rate = weekly_rate * 4
            else:
                rental_price = random.randint(5, 15)
                weekly_rate = rental_price * 5
                seasonal_rate = weekly_rate * 4
            
            # Create equipment
            equipment = Equipment.objects.create(
                equipment_id=f"{eq_type[0:2]}{i:03d}",
                equipment_type=eq_type,
                equipment_subtype=subtype,
                brand=brand,
                model=model_name,
                size=size,
                condition="EXCELLENT",
                is_available=True,
                recommended_skill_level=skill_level,
                rental_price=rental_price,
                weekly_rate=weekly_rate,
                seasonal_rate=seasonal_rate
            )
            
            equipment_created += 1
            print(f"Created: {equipment.brand} {equipment.model} (ID: {equipment.equipment_id})")
    
    print(f"Total equipment created: {equipment_created}")
    
    # Create collections
    collection_names = [
        "Beginner Ski Package", 
        "Advanced Alpine Bundle", 
        "Snowboard Essentials",
        "Winter Safety Gear",
        "Kids Ski Equipment"
    ]
    
    collections_created = 0
    
    for name in collection_names:
        collection = Collection.objects.create(
            title=name,
            description=f"A carefully curated collection of {name.lower()} for the best winter experience.",
            creator=librarian,
            sharing_type='PUBLIC'
        )
        
        # Add 3-5 random equipment items to each collection
        equipment_to_add = random.sample(list(Equipment.objects.all()), random.randint(3, 5))
        for eq in equipment_to_add:
            collection.items.add(eq)
        
        collections_created += 1
        print(f"Created collection: {collection.title} with {collection.items.count()} items")
    
    print(f"Total collections created: {collections_created}")

if __name__ == '__main__':
    create_demo_equipment() 