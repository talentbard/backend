# Generated by Django 4.2.6 on 2025-05-23 08:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0002_emailotp'),
        ('talent', '0019_remove_talentscore_score_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='talentscore',
            name='user_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='user_profile.userprofile', unique=True),
        ),
    ]
