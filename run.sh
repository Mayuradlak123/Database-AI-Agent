#!/bin/bash

echo "Cleaning up __pycache__ and .pyc files..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

echo "Applying migrations..."
python manage.py migrate
echo "Starting Django Server..."
python manage.py runserver 0.0.0.0:8000
