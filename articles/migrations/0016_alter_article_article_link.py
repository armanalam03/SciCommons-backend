# Generated by Django 5.0.7 on 2024-07-18 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0015_article_article_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='article_link',
            field=models.URLField(blank=True, null=True, unique=True),
        ),
    ]