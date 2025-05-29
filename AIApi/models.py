# voice/models.py
from django.db import models

class CallSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    caller_number = models.CharField(max_length=20)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='active')

class Conversation(models.Model):
    session = models.ForeignKey(CallSession, on_delete=models.CASCADE)
    user_input = models.TextField()
    ai_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)