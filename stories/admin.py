from django.contrib import admin
from .models import Story, Chapter, Paragraph, ReadingProgress, Payment, NFT, ParagraphView

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'author__username')
    list_filter = ('created_at',)

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('story', 'title', 'chapter_number', 'created_at')
    search_fields = ('title', 'story__title')
    list_filter = ('created_at',)
    ordering = ['story', 'chapter_number']

@admin.register(Paragraph)
class ParagraphAdmin(admin.ModelAdmin):
    list_display = ('chapter', 'page', 'paragraph_number', 'is_locked', 'nft_owner', 'preview_text')
    search_fields = ('chapter__title', 'text')
    list_filter = ('is_locked', 'chapter__story', 'page')
    ordering = ['chapter', 'page', 'paragraph_number']

    def preview_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    preview_text.short_description = 'Text Preview'

@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'story', 'last_accessed', 'viewed_count')
    search_fields = ('user__username', 'story__title')
    list_filter = ('last_accessed', 'story')
    filter_horizontal = ('viewed_paragraphs',)

    def viewed_count(self, obj):
        return obj.viewed_paragraphs.count()
    viewed_count.short_description = 'Paragraphs Viewed'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'paragraph', 'amount', 'payment_date', 'successful')
    search_fields = ('user__username', 'paragraph__chapter__story__title')
    list_filter = ('successful', 'payment_date')
    ordering = ['-payment_date']

@admin.register(NFT)
class NFTAdmin(admin.ModelAdmin):
    list_display = ('paragraph', 'owner', 'mint_date', 'revenue_share_percentage')
    search_fields = ('owner__username', 'paragraph__chapter__story__title')
    list_filter = ('mint_date', 'revenue_share_percentage')
    ordering = ['-mint_date']

@admin.register(ParagraphView)
class ParagraphViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'story', 'chapter', 'paragraph', 'view_order', 'viewed_at')
    search_fields = ('user__username', 'story__title', 'chapter__title')
    list_filter = ('viewed_at', 'story', 'chapter')
    ordering = ['user', 'view_order']
    raw_id_fields = ('user', 'story', 'chapter', 'paragraph')  # Helps with performance for large datasets

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'story', 'chapter', 'paragraph'
        )  # Optimize database queries
