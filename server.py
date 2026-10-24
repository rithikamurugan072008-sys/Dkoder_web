#!/usr/bin/env python3
"""
DKoder 2.0 — Production-Ready Placement LMS Server
Starts Django development server on http://localhost:8000
Serving frontend, static assets, and REST API endpoints.
"""

import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    import django
    django.setup()
    from django.core.management import execute_from_command_line
    
    # Run seed if database is empty
    try:
        from core.models import CodingProblem
        if not CodingProblem.objects.exists():
            print("Detected empty database, running seed...")
            from core.seed_data import run_seed
            run_seed()
    except Exception as e:
        print(f"Seed check: {e}")

    print("\n" + "="*70)
    print(" [DKODER 2.0] AI-POWERED CODING, LEARNING & PLACEMENT PLATFORM")
    print("="*70)
    print(" * Application URL: http://localhost:8080/")
    print(" * REST API Base:   http://localhost:8080/api/")
    print(" * Admin Panel:     http://localhost:8080/django-admin/")
    print(" * Role Accounts:   Alex (Student) | Priya (Moderator) | Admin")
    print("="*70 + "\n")

    sys.argv = ['manage.py', 'runserver', '0.0.0.0:8080']
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
