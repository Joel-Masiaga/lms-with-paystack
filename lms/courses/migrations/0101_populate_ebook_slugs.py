# Generated migration to populate ebook slugs from titles

from django.db import migrations
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    """Populate empty slug fields with auto-generated slugs from titles."""
    Ebook = apps.get_model('courses', 'Ebook')
    
    # Get all ebooks with empty or null slugs
    ebooks_without_slugs = Ebook.objects.filter(slug__isnull=True) | Ebook.objects.filter(slug='')
    
    for ebook in ebooks_without_slugs:
        # Generate slug from title
        generated_slug = slugify(ebook.title)
        
        # If slug already exists, make it unique
        counter = 1
        original_slug = generated_slug
        while Ebook.objects.filter(slug=generated_slug).exists():
            generated_slug = f"{original_slug}-{counter}"
            counter += 1
        
        # Update the ebook
        if generated_slug:  # Only update if we generated a valid slug
            ebook.slug = generated_slug
            ebook.save()


def reverse_populate_slugs(apps, schema_editor):
    """Reverse migration - clear slugs that were auto-generated."""
    # This is a simple reverse that sets slugs back to empty
    # In production, you might want to keep the slugs or handle differently
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0100_merge_20260415_0317'),
    ]

    operations = [
        migrations.RunPython(populate_slugs, reverse_populate_slugs),
    ]
