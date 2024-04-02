import pandas as pd
import re
from django.core.management.base import BaseCommand
from papers.models import Paper  

def clean_and_split_categories(category_string):
    if not isinstance(category_string, str):
        return []
    category_string = re.sub(r'\s*\|\s*', ' | ', category_string).strip()
    while category_string.endswith(" |"):
        category_string = category_string[:-2].strip()
    categories = set(category_string.split(' | '))
    categories = [category for category in categories if category.strip()]
    return categories

def clean_authors(author_string):
    if pd.isna(author_string):
        return []
    while author_string.endswith(", "):
        author_string = author_string[:-2].strip()
    authors = author_string.split(', ')
    return authors

def load_papers_from_csv(csv_path):
    df = pd.read_csv(csv_path, dtype={'number_citations': 'Int64', 'authors': 'str', 'doi': 'str'})
    for _, row in df.iterrows():
        doi=row['doi']
        if not Paper.objects.filter(doi=doi).exists():
            Paper.objects.create(
                title=row['title_e'],
                authors=", ".join(clean_authors(row['authors'])),  # Adjust based on your model field
                year=row['year'],
                journal=row['journal'],
                doi=row['doi'],
                abstract=row['abstract'] if pd.notnull(row['abstract']) else '',
                # categories=clean_and_split_categories(row['assigned_subjects1']),  # Adjust this if you have a many-to-many field or similar
                factor=row['factor'],
                # citations=row['number_citations']
                # Include other fields as necessary
            )
        else:
            print(f"Skipping existing paper with DOI: {doi}")

class Command(BaseCommand):
    help = 'Load papers from a CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_path = kwargs['csv_path']
        load_papers_from_csv(csv_path)
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded papers from {csv_path}'))
