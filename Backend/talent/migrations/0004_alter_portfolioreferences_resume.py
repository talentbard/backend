# Generated by Django 4.2.6 on 2025-03-23 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('talent', '0003_alter_workexperience_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portfolioreferences',
            name='resume',
            field=models.CharField(blank=True, null=True),
        ),
    ]
