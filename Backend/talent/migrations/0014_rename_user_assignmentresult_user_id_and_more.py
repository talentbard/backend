# Generated by Django 4.2.6 on 2025-03-27 16:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('talent', '0013_assignmentresult_delete_assignmentscore'),
    ]

    operations = [
        migrations.RenameField(
            model_name='assignmentresult',
            old_name='user',
            new_name='user_id',
        ),
        migrations.RenameField(
            model_name='jobpreferences',
            old_name='user',
            new_name='user_id',
        ),
        migrations.RenameField(
            model_name='talentscore',
            old_name='user',
            new_name='user_id',
        ),
    ]
