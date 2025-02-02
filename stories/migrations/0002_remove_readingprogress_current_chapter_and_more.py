# Generated by Django 5.1.2 on 2024-11-02 03:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='readingprogress',
            name='current_chapter',
        ),
        migrations.RemoveField(
            model_name='readingprogress',
            name='current_paragraph',
        ),
        migrations.AddField(
            model_name='readingprogress',
            name='viewed_paragraphs',
            field=models.ManyToManyField(related_name='viewed_by', to='stories.paragraph'),
        ),
    ]
