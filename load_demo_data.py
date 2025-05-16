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
        'SKI': ['ALPINE', 'NORDIC', 'FREESTYLE', 'TOURING', 'POWDER'],
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
            
            # Generate equipment name
            brand = random.choice(brands)
            
            if eq_type in ['SKI', 'SNOWBOARD', 'POLES', 'BOOTS']:
                skill_level = random.choice(skill_levels)
            else:
                skill_level = None
                
            if eq_type in ['JACKET', 'PANTS', 'GLOVES']:
                size = random.choice(sizes)
            else:
                size = None
            
            name = f"{brand} {eq_type.title()}"
            if subtype:
                name += f" {subtype.title()}"
            if skill_level:
                name += f" {skill_level.title()}"
            if size:
                name += f" ({size})"
            
            # Set appropriate pricing
            if eq_type in ['SKI', 'SNOWBOARD']:
                daily_rate = random.randint(40, 80)
                weekly_rate = daily_rate * 6
                monthly_rate = weekly_rate * 3.5
            elif eq_type in ['BOOTS', 'HELMET']:
                daily_rate = random.randint(15, 30)
                weekly_rate = daily_rate * 6
                monthly_rate = weekly_rate * 3.5
            else:
                daily_rate = random.randint(5, 15)
                weekly_rate = daily_rate * 6
                monthly_rate = weekly_rate * 3.5
            
            # Create equipment
            equipment = Equipment.objects.create(
                equipment_id=f"{eq_type[0:2]}{i:03d}",
                name=name,
                description=f"High-quality {eq_type.lower()} for {skill_level.lower() if skill_level else 'all'} level skiers and snowboarders.",
                equipment_type=eq_type,
                equipment_subtype=subtype,
                skill_level=skill_level,
                size=size,
                brand=brand,
                daily_rate=daily_rate,
                weekly_rate=weekly_rate,
                monthly_rate=monthly_rate,
                condition="EXCELLENT",
                available=True,
                acquired_date=timezone.now() - timedelta(days=random.randint(30, 365)),
            )
            
            equipment_created += 1
            print(f"Created: {equipment.name} (ID: {equipment.equipment_id})")
    
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