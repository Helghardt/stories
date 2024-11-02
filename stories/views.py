from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Story, Chapter, Paragraph, ReadingProgress, Payment, NFT, ParagraphView, Reader
from .serializers import StorySerializer, ChapterSerializer, ParagraphSerializer, ReadingProgressSerializer, PaymentSerializer, NFTSerializer
from django.views.generic import TemplateView
from django.db.models import Max
from .tasks import generate_next_paragraph, generate_next_page, create_wallet
from django.contrib.auth import login
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

class StoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing stories.
    """
    queryset = Story.objects.all()
    serializer_class = StorySerializer

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def chapters(self, request, pk=None):
        story = self.get_object()
        chapters = story.chapters.all()
        serializer = ChapterSerializer(chapters, many=True)
        return Response(serializer.data)


class ChapterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing chapters of a story.
    """
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def paragraphs(self, request, pk=None):
        chapter = self.get_object()
        page = request.query_params.get('page', 1)
        paragraphs = chapter.paragraphs.filter(page=page)
        
        # Add pagination information
        has_next = chapter.paragraphs.filter(page=int(page) + 1).exists()
        
        serializer = ParagraphSerializer(paragraphs, many=True)
        return Response({
            'results': serializer.data,
            'has_next': has_next
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def generate_paragraph(self, request, pk=None):
        """
        Generate a new paragraph for the chapter using AI.
        """
        chapter = self.get_object()
        
        # Get the current page from query params or default to the last page
        current_page = request.query_params.get('page')
        if current_page:
            current_page = int(current_page)
        else:
            # Find the last page for this chapter
            last_page = chapter.paragraphs.aggregate(Max('page'))['page__max'] or 1
            current_page = last_page

        # Get the last paragraph on the current page
        last_paragraph = chapter.paragraphs.filter(
            page=current_page
        ).order_by('-paragraph_number').first()
        
        last_paragraph_id = last_paragraph.id if last_paragraph else None

        try:
            new_paragraph = generate_next_paragraph(chapter.id, last_paragraph_id)
            serializer = ParagraphSerializer(new_paragraph)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": f"Failed to generate paragraph: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def generate_next_page(self, request, pk=None):
        """
        Generate the first paragraph of a new page for the chapter using AI.
        """
        chapter = self.get_object()
        current_page = int(request.data.get('current_page', 1))
        
        try:
            new_paragraph = generate_next_page(chapter.id, current_page)
            serializer = ParagraphSerializer(new_paragraph)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": f"Failed to generate next page: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ParagraphViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing and unlocking paragraphs.
    """
    queryset = Paragraph.objects.all()
    serializer_class = ParagraphSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        # Get the paragraph
        paragraph = self.get_object()
        
        # Get the next view order number for this user
        last_view = ParagraphView.objects.filter(user=request.user).aggregate(Max('view_order'))
        next_order = (last_view['view_order__max'] or 0) + 1

        # Create the paragraph view record
        ParagraphView.objects.create(
            user=request.user,
            story=paragraph.chapter.story,
            chapter=paragraph.chapter,
            paragraph=paragraph,
            view_order=next_order
        )

        # Update reading progress
        progress, _ = ReadingProgress.objects.get_or_create(
            user=request.user,
            story=paragraph.chapter.story
        )
        progress.viewed_paragraphs.add(paragraph)
        
        serializer = self.get_serializer(paragraph)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlock(self, request, pk=None):
        """
        Unlocks a paragraph by processing a payment.
        """
        paragraph = self.get_object()
        if not paragraph.is_locked:
            return Response({"detail": "Paragraph already unlocked"}, status=status.HTTP_400_BAD_REQUEST)

        # Simulate a payment process here (e.g., interact with payment gateway or blockchain)
        amount = request.data.get('amount')
        if not amount:
            return Response({"detail": "Amount required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Record payment
        payment = Payment.objects.create(
            user=request.user,
            paragraph=paragraph,
            amount=amount,
            successful=True
        )
        # Unlock paragraph
        paragraph.is_locked = False
        paragraph.save()

        return Response({"detail": "Paragraph unlocked successfully"}, status=status.HTTP_200_OK)


class ReadingProgressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user reading progress.
    """
    serializer_class = ReadingProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReadingProgress.objects.filter(user=self.request.user)

    def create(self, request):
        """Handle POST requests to /api/reading-progress/"""
        try:
            story_id = request.data.get('story')
            chapter_id = request.data.get('current_chapter')
            paragraph_id = request.data.get('current_paragraph')

            # Get or create reading progress
            progress, _ = ReadingProgress.objects.get_or_create(
                user=request.user,
                story_id=story_id
            )

            if paragraph_id:
                progress.viewed_paragraphs.add(paragraph_id)

            return Response({'status': 'success'})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def mark_viewed(self, request):
        """Handle POST requests to /api/reading-progress/mark_viewed/"""
        try:
            story_id = request.data.get('story')
            chapter_id = request.data.get('chapter')
            paragraph_id = request.data.get('paragraph')

            if not all([story_id, paragraph_id]):
                return Response(
                    {"error": "Story and paragraph IDs are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get or create reading progress
            progress, _ = ReadingProgress.objects.get_or_create(
                user=request.user,
                story_id=story_id
            )
            
            # Add paragraph to viewed paragraphs
            progress.viewed_paragraphs.add(paragraph_id)
            
            return Response({'status': 'success'})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def viewed_paragraphs(self, request):
        story_id = request.query_params.get('story')
        progress = get_object_or_404(
            ReadingProgress,
            user=request.user,
            story_id=story_id
        )
        viewed = list(progress.viewed_paragraphs.values_list('id', flat=True))
        return Response({'viewed_paragraphs': viewed})

    @action(detail=False, methods=['get'])
    def navigation_history(self, request):
        """Get user's navigation history for a story"""
        story_id = request.query_params.get('story')
        if not story_id:
            return Response({"detail": "Story ID required"}, status=status.HTTP_400_BAD_REQUEST)

        history = ParagraphView.objects.filter(
            user=request.user,
            story_id=story_id
        ).order_by('view_order').values(
            'paragraph_id',
            'chapter_id',
            'view_order',
            'viewed_at'
        )
        
        return Response(list(history))


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view user payments for unlocking paragraphs.
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class NFTViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view NFTs owned by the user.
    """
    serializer_class = NFTSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NFT.objects.filter(owner=self.request.user)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def revenue(self, request, pk=None):
        """
        View revenue generated by the NFT.
        """
        nft = self.get_object()
        revenue = nft.paragraph.payments.aggregate(total_revenue=models.Sum('amount'))['total_revenue']
        return Response({"revenue": revenue or 0.0})


class StoryReaderView(TemplateView):
    """
    View to render the main story reader application.
    """
    template_name = 'stories/home.html'


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get('email')
        if not email:
            logger.warning("Login attempt failed: No email provided")
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Login attempted for email: {email}")
        
        # Get or create reader
        try:
            reader, created = Reader.objects.get_or_create(
                email=email
            )
            
            if created:
                logger.info(f"New reader created with email: {email}")
                try:
                    wallet_data = create_wallet()
                    reader.wallet_address = wallet_data['address']
                    reader.wallet_chain = wallet_data['type']
                    reader.save()
                    logger.info(f"Wallet created for reader {email}: {wallet_data['address']}")
                except Exception as e:
                    logger.error(f"Wallet creation failed for reader {email}: {str(e)}", exc_info=True)
                    reader.delete()
                    return Response(
                        {'error': f'Failed to create wallet: {str(e)}'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                logger.info(f"Existing reader logged in: {email}")

            # Store reader info in session
            request.session['reader_email'] = reader.email
            request.session['reader_id'] = reader.id
            
            return Response({
                'email': reader.email,
                'is_new_reader': created,
                'wallet_address': reader.wallet_address
            })
            
        except Exception as e:
            logger.error(f"Login failed for email {email}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Login failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )