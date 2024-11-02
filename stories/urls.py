from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'stories', views.StoryViewSet)
router.register(r'chapters', views.ChapterViewSet)
router.register(r'paragraphs', views.ParagraphViewSet)
router.register(r'reading-progress', views.ReadingProgressViewSet, basename='reading-progress')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'nfts', views.NFTViewSet, basename='nft')
router.register(r'auth', views.AuthViewSet, basename='auth')

urlpatterns = [
    path('', views.StoryReaderView.as_view(), name='story-reader'),
    path('api/', include(router.urls)),
    path('api/reading-progress/mark_viewed/', 
         views.ReadingProgressViewSet.as_view({'post': 'mark_viewed'}), 
         name='mark-viewed'),
    path('api/chapters/<int:pk>/generate_next_page/',
         views.ChapterViewSet.as_view({'post': 'generate_next_page'}),
         name='generate-next-page'),
]
