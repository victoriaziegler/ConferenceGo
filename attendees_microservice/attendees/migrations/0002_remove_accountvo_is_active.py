# Generated by Django 4.0.3 on 2022-07-18 17:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attendees', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accountvo',
            name='is_active',
        ),
    ]
