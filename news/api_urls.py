from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView, 
    TokenRefreshView
)

from . import api_views

router = DefaultRouter()
router.register(r'articles', api_views.ArticleViewSet, basename='article')
router.register(r'publishers', api_views.PublisherViewSet, basename='publisher')
router.register(r'newsletters', api_views.NewsletterViewSet, basename='newsletter')

urlpatterns = [
    # API root
    path('', api_views.api_root, name='api-root'),
    
    # Router URLs
    path('', include(router.urls)),
    
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Registration
    path('register/', api_views.register_api, name='api-register'),
    
    # Approved articles endpoint (used by signals)
    path('approved/', api_views.approved_articles_endpoint, 
         name='approved-articles'),
    path('approved/list/', api_views.approved_articles_list, 
         name='approved-articles-list'),
    
    # User
    path('users/me/', api_views.CurrentUserView.as_view(), name='current-user'),
]
