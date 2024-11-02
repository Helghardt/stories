from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Paragraph
from .tasks import analyze_and_add_links

@receiver(post_save, sender=Paragraph)
def process_paragraph_links(sender, instance, created, **kwargs):
    """
    When a new paragraph is created, analyze it for potential links.
    """
    if created and not instance.text_with_links:  # Only process if it's new and doesn't have links yet
        analyze_and_add_links(instance.id)
