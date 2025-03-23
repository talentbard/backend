# Generated by Django 4.2.6 on 2025-03-23 14:59

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0001_initial'),
        ('talent', '0005_alter_portfolioreferences_resume'),
    ]

    operations = [
        migrations.CreateModel(
            name='TalentScore',
            fields=[
                ('score_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('quiz_score', models.IntegerField(blank=True, null=True)),
                ('assignment_score', models.IntegerField(blank=True, null=True)),
                ('interview_score', models.IntegerField(blank=True, null=True)),
                ('work_score', models.IntegerField(blank=True, null=True)),
                ('grade', models.IntegerField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_profile.userprofile')),
            ],
        ),
    ]
