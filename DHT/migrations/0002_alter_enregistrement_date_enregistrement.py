# Generated by Django 4.2.16 on 2024-12-25 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DHT', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enregistrement',
            name='date_enregistrement',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
