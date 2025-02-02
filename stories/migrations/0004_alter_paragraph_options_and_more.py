# Generated by Django 5.1.2 on 2024-11-02 04:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0003_paragraphview'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='paragraph',
            options={'ordering': ['page', 'paragraph_number']},
        ),
        migrations.AlterUniqueTogether(
            name='paragraph',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='paragraph',
            name='page',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterUniqueTogether(
            name='paragraph',
            unique_together={('chapter', 'paragraph_number', 'page')},
        ),
    ]
