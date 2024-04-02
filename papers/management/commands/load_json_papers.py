import os
import django
import pandas as pd
import json
import re
from django.core.management.base import BaseCommand, CommandError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "soop.settings")
django.setup()

from papers.models import Paper, Tag  

Paper.objects.all().delete()
Tag.objects.all().delete()
print("Cleared existing Paper and Tag data.")

def clean_and_split_categories(category_string):
    if not category_string:
        return []
    category_string = re.sub(r'\s*\|\s*', ' | ', category_string).strip()
    while category_string.endswith(" |"):
        category_string = category_string[:-2].strip()
    categories = set(category_string.split(' | '))
    categories = [category.strip() for category in categories if category.strip()]
    return categories

def clean_authors(author_string):
    if pd.isna(author_string):
        return []
    while author_string.endswith(", "):
        author_string = author_string[:-2].strip()
    authors = author_string.split(', ')
    return authors



class Command(BaseCommand):
    help = 'Loads papers from a JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file containing the papers data')

    def handle(self, *args, **kwargs):
        json_file_path = kwargs['json_file']
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                papers_data = json.load(file)
                for paper_data in papers_data:
                    # Create the Paper instance
                    paper_instance = Paper.objects.create(
                        pmid=paper_data['pmid'],
                        title=paper_data['title_e'],
                        authors=clean_authors(paper_data.get('authors', '')),
                        abstract=paper_data.get('abstract', ''),
                        year=paper_data.get('year'),
                        doi=paper_data.get('doi')
                    )
                    # Process and add categories
                    categories = clean_and_split_categories(paper_data.get('assigned_subjects1', ''))
                    for category_name in categories:
                        category, _ = Tag.objects.get_or_create(name=category_name)
                        paper_instance.categories.add(category)  

                self.stdout.write(self.style.SUCCESS(f'Successfully loaded papers from {json_file_path}'))
        except FileNotFoundError:
            raise CommandError(f'File "{json_file_path}" does not exist.')
