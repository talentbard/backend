# Generated by Django 4.2.6 on 2025-03-19 15:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('talent', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='skillsexpertise',
            old_name='certificate_image',
            new_name='certificate_images',
        ),
        migrations.RenameField(
            model_name='skillsexpertise',
            old_name='primary_skill',
            new_name='primary_skills',
        ),
    ]
