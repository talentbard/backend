# Generated by Django 4.2.6 on 2025-03-24 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('talent', '0007_quizresult'),
    ]

    operations = [
        migrations.AddField(
            model_name='skillsexpertise',
            name='demo',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
