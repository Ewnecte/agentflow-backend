from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('conversations', views.ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
    path('chat/', views.chat_stream, name='chat-stream'),
]
