#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skirentals.settings')
django.setup()

# Import models after Django setup
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os

def setup_site_and_social_app():
    # Create or update the Site entry for Heroku
    site, created = Site.objects.update_or_create(
        id=2,
        defaults={
            'domain': 'skirentals-app-4cbe371f19f9.herokuapp.com',
            'name': 'Ski Rentals Heroku'
        }
    )
    print(f"Site {'created' if created else 'updated'}: {site.domain}")

    # Get OAuth credentials from environment
    client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')

    if not client_id:
        print("Error: GOOGLE_OAUTH_CLIENT_ID not found in environment")
        return
    
    # Create or update the SocialApp entry for Google OAuth
    social_app, created = SocialApp.objects.update_or_create(
        provider='google',
        defaults={
            'name': 'Google',
            'client_id': client_id,
            'secret': client_secret or '',
        }
    )
    print(f"SocialApp {'created' if created else 'updated'}: {social_app.name}")

    # Make sure the site is associated with the social app
    social_app.sites.add(site)
    print(f"Associated site {site.domain} with {social_app.name}")

if __name__ == '__main__':
    setup_site_and_social_app() 