# Generated by Django 5.0.7 on 2024-08-21 07:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0012_alter_notification_notification_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hashtag",
            name="name",
            field=models.CharField(max_length=25, unique=True),
        ),
    ]