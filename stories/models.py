from django.db import models
from everything.models import User
from tinymce.models import HTMLField

class Story(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')

    def __str__(self):
        return self.title


class Chapter(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=255)
    chapter_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story', 'chapter_number')
        ordering = ['chapter_number']

    def __str__(self):
        return f"{self.story.title} - Chapter {self.chapter_number}"


class Paragraph(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='paragraphs')
    text = models.TextField()
    paragraph_number = models.PositiveIntegerField()
    page = models.PositiveIntegerField(default=1)
    is_locked = models.BooleanField(default=True)
    nft_owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_paragraphs')
    text_with_links = HTMLField(blank=True, null=True)

    class Meta:
        unique_together = ('chapter', 'paragraph_number', 'page')
        ordering = ['page', 'paragraph_number']

    def __str__(self):
        return f"{self.chapter} - Paragraph {self.paragraph_number}"


class ReadingProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_progress')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='progress')
    viewed_paragraphs = models.ManyToManyField(Paragraph, related_name='viewed_by')
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'story')

    def __str__(self):
        return f"{self.user.username}'s progress in {self.story.title}"


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    paragraph = models.ForeignKey(Paragraph, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Adjust as needed for USDC
    payment_date = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - Payment for {self.paragraph}"


class NFT(models.Model):
    paragraph = models.OneToOneField(Paragraph, on_delete=models.CASCADE, related_name='nft')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nfts')
    mint_date = models.DateTimeField(auto_now_add=True)
    revenue_share_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # Default 10% revenue share

    def __str__(self):
        return f"NFT of {self.paragraph} owned by {self.owner.username}"


class ParagraphView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paragraph_views')
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    paragraph = models.ForeignKey(Paragraph, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)
    view_order = models.PositiveIntegerField()

    class Meta:
        ordering = ['user', 'view_order']
        unique_together = ('user', 'view_order')

    def __str__(self):
        return f"{self.user.username} - {self.paragraph} - View #{self.view_order}"


class Reader(models.Model):
    email = models.EmailField(unique=True)
    wallet_address = models.CharField(max_length=255)
    wallet_chain = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reader: {self.email} ({self.wallet_chain})"
