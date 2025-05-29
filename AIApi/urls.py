# voice/urls.py
from django.urls import path
from .views import (
    VoiceCallbackView,
    ProcessRecordingView,
    CallSessionListView,
    CallSessionDetailView,
    InitiateOutboundCallView,
    ConversationView,
    SessionAnalyticsView
)

urlpatterns = [
    # Africa's Talking Webhook Endpoints
    path('callback/', VoiceCallbackView.as_view(), name='voice-callback'),
    path('process-recording/', ProcessRecordingView.as_view(), name='process-recording'),
    
    # Session Management Endpoints
    path('sessions/', CallSessionListView.as_view(), name='session-list'),
    path('sessions/<str:session_id>/', CallSessionDetailView.as_view(), name='session-detail'),
    
    # Outbound Call Endpoint
    path('initiate-call/', InitiateOutboundCallView.as_view(), name='initiate-call'),
    
    # Conversation Endpoints
    path('sessions/<str:session_id>/conversations/', ConversationView.as_view(), name='conversation-list'),
    
    # Analytics Endpoint
    path('analytics/', SessionAnalyticsView.as_view(), name='session-analytics'),
]

