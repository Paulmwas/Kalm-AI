# voice/serializers.py
from rest_framework import serializers
from .models import CallSession, Conversation

class CallSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallSession
        fields = ['session_id', 'caller_number', 'start_time', 'end_time', 'status']
        read_only_fields = ['start_time', 'end_time', 'status']

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'session', 'user_input', 'ai_response', 'created_at']
        read_only_fields = ['created_at']

class VoiceCallSerializer(serializers.Serializer):
    callerNumber = serializers.CharField(max_length=20)
    
    def validate_phone_number(self, value):
        if not value.startswith('+'):
            raise serializers.ValidationError("Phone number must include country code (e.g., +254...)")
        return value

class VoiceRecordingSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=100)
    recording_url = serializers.URLField()