# voice/views.py
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from .services import AfricasTalkingService, GeminiTherapistService, SessionManager
from .models import CallSession, Conversation
from .serializers import (
    CallSessionSerializer,
    ConversationSerializer,
    VoiceCallSerializer,
    VoiceRecordingSerializer
)
import logging
import json

# Enhanced logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add request logging middleware or debug helper
def log_request_data(request):
    logger.debug("=== Request Debug Info ===")
    logger.debug(f"POST data: {request.POST}")
    logger.debug(f"Body: {request.body}")
    try:
        logger.debug(f"JSON data: {json.loads(request.body)}")
    except:
        pass
    logger.debug(f"Content-Type: {request.content_type}")
    logger.debug("========================")

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
# voice/views.py - Fixed VoiceCallbackView

class DebugWebhookView(APIView):
    """Debug endpoint to see what data is being sent"""
    
    @csrf_exempt
    def post(self, request):
        logger.info("=== DEBUG WEBHOOK ===")
        logger.info(f"Method: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"POST data: {dict(request.POST)}")
        logger.info(f"GET data: {dict(request.GET)}")
        
        # Only access request.data if we haven't accessed request.body
        try:
            # Try to get raw body first (before accessing request.data)
            if hasattr(request, '_body'):
                logger.info(f"Raw body: {request._body}")
            
            # Now try request.data
            data = request.data
            logger.info(f"Parsed data: {data}")
        except Exception as e:
            logger.error(f"Error accessing request data: {e}")
        
        logger.info("=== END DEBUG ===")
        
        return Response(
            data="<?xml version='1.0' encoding='UTF-8'?><Response><Say>Debug data logged</Say></Response>",
            content_type='text/xml',
            status=status.HTTP_200_OK
        )
    
    def get(self, request):
        """Also handle GET requests for testing"""
        logger.info("=== DEBUG GET REQUEST ===")
        logger.info(f"GET data: {dict(request.GET)}")
        logger.info("=== END DEBUG GET ===")
        return Response({"message": "Debug GET logged"})


# Alternative: If you want to use serializer validation, create a specific one for Africa's Talking
class AfricasTalkingCallSerializer(serializers.Serializer):
    sessionId = serializers.CharField(max_length=100)
    callerNumber = serializers.CharField(max_length=20)
    # Add other fields that Africa's Talking sends if needed
    
    def validate_callerNumber(self, value):
        # Add phone number validation logic here
        if not value.startswith('+'):
            # Handle local numbers
            pass
        return value

# Then use it like this in your view:
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class VoiceCallbackView(APIView):
    """Handle incoming voice calls and create new session"""
    
    def post(self, request):
        try:
            # Debug: Log all incoming data (avoid accessing both request.data and request.body)
            logger.info(f"Request method: {request.method}")
            logger.info(f"Content type: {request.content_type}")
            logger.info(f"All headers: {dict(request.headers)}")
            
            # First try request.POST (for form data)
            logger.info(f"Request POST data: {dict(request.POST)}")
            logger.info(f"Request GET data: {dict(request.GET)}")
            
            # Try different possible field names that Africa's Talking might use
            session_id = (
                request.POST.get('sessionId') or 
                request.POST.get('session_id') or 
                request.POST.get('SessionId') or
                request.POST.get('callSessionState') or
                request.GET.get('sessionId') or 
                request.GET.get('session_id')
            )
            
            caller_number = (
                request.POST.get('callerNumber') or 
                request.POST.get('caller_number') or 
                request.POST.get('CallerNumber') or
                request.POST.get('phoneNumber') or
                request.POST.get('phone_number') or
                request.POST.get('from') or
                request.GET.get('callerNumber') or 
                request.GET.get('caller_number')
            )
            
            logger.info(f"Extracted from POST/GET - sessionId: {session_id}, callerNumber: {caller_number}")
            
            # If no data in POST/GET, try request.data (JSON)
            if not session_id and not caller_number:
                try:
                    data = request.data
                    logger.info(f"Request data (JSON): {data}")
                    
                    session_id = (
                        data.get('sessionId') or 
                        data.get('session_id') or
                        data.get('SessionId') or
                        data.get('callSessionState')
                    )
                    
                    caller_number = (
                        data.get('callerNumber') or 
                        data.get('caller_number') or 
                        data.get('CallerNumber') or
                        data.get('phoneNumber') or
                        data.get('phone_number') or
                        data.get('from')
                    )
                    
                    logger.info(f"Extracted from JSON - sessionId: {session_id}, callerNumber: {caller_number}")
                except Exception as e:
                    logger.error(f"Error accessing request.data: {e}")
            
            # Validate required fields
            if not session_id or not caller_number:
                logger.error(f"Missing required fields after all attempts. sessionId: {session_id}, callerNumber: {caller_number}")
                # Log what we actually received to help debug
                logger.error(f"Available POST keys: {list(request.POST.keys())}")
                logger.error(f"Available GET keys: {list(request.GET.keys())}")
                
                at_service = AfricasTalkingService()
                error_response = at_service.create_say_response("Unable to process call. Please try again.")
                
                from django.http import HttpResponse
                return HttpResponse(
                    error_response,
                    content_type='text/xml',
                    status=200
                )
            
            # Create or get existing session using CallSessionSerializer
            session_data = {
                'session_id': session_id,
                'caller_number': caller_number
            }
            
            # Try to get existing session or create new one
            try:
                session = CallSession.objects.get(session_id=session_id)
                logger.info(f"Found existing session: {session_id}")
            except CallSession.DoesNotExist:
                # Create new session
                session_serializer = CallSessionSerializer(data=session_data)
                if session_serializer.is_valid():
                    session = session_serializer.save()
                    logger.info(f"Created new session: {session_id}")
                else:
                    logger.error(f"Invalid session data: {session_serializer.errors}")
                    at_service = AfricasTalkingService()
                    error_response = at_service.create_say_response("Unable to create session. Please try again.")
                    
                    from django.http import HttpResponse
                    return HttpResponse(
                        error_response,
                        content_type='text/xml',
                        status=200
                    )
            
            # Generate welcome message and setup recording
            at_service = AfricasTalkingService()
            welcome_message = """Hello and welcome to Kalm AI. I'm here to listen and support you. 
            Please tell me how you're feeling today after the beep, then press # when you're done."""
            
            callback_url = f"{settings.APP_BASE_URL}/api/process-recording/"
            xml_response = at_service.create_record_response(welcome_message, callback_url)
            
            # Log the session start if you have SessionManager
            # SessionManager.add_message(session, 'system', 'Call initiated - welcome message played')
            
            # Return raw XML response for Africa's Talking
            from django.http import HttpResponse
            return HttpResponse(
                xml_response,
                content_type='text/xml',
                status=200
            )
            
        except Exception as e:
            logger.error(f"Error in VoiceCallbackView: {str(e)}")
            at_service = AfricasTalkingService()
            error_response = at_service.create_say_response("We're having technical difficulties. Please call back later.")
            
            from django.http import HttpResponse
            return HttpResponse(
                error_response,
                content_type='text/xml',
                status=200
            )


@method_decorator(csrf_exempt, name='dispatch')
class ProcessRecordingView(APIView):
    """Process voice recordings and generate therapeutic responses"""
    
    def post(self, request):
        try:
            # Validate incoming recording data
            serializer = VoiceRecordingSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Invalid recording data: {serializer.errors}")
                at_service = AfricasTalkingService()
                return Response(
                    data=at_service.create_say_response("Sorry, we couldn't process your request."),
                    content_type='text/xml',
                    status=status.HTTP_200_OK
                )
            
            # Get the session
            session_id = serializer.validated_data['session_id']
            recording_url = serializer.validated_data['recording_url']
            
            try:
                session = CallSession.objects.get(session_id=session_id)
            except CallSession.DoesNotExist:
                logger.error(f"Session not found: {session_id}")
                at_service = AfricasTalkingService()
                return Response(
                    data=at_service.create_say_response("Session not found. Please call back to start a new conversation."),
                    content_type='text/xml',
                    status=status.HTTP_200_OK
                )
            
            # Transcribe the recording (simplified - implement actual transcription service)
            at_service = AfricasTalkingService()
            user_text = at_service.transcribe_recording(recording_url)
            
            if not user_text:
                logger.warning(f"Empty transcription for session {session_id}")
                user_text = "I didn't catch that. Could you please repeat?"
            
            # Add user message to conversation
            SessionManager.add_message(
                session,
                'user',
                user_text,
                audio_url=recording_url
            )
            
            # Get conversation history
            conversation_history = SessionManager.get_conversation_history(session)
            
            # Generate therapeutic response
            gemini_service = GeminiTherapistService()
            therapeutic_response = gemini_service.get_therapeutic_response(
                conversation_history,
                session.therapy_stage,
                session.current_mood
            )
            
            # Handle crisis detection
            if therapeutic_response['crisis_detected']:
                session.crisis_flag = True
                session.save()
                crisis_response = """I'm concerned about what you've shared. Your safety is important. 
                Please consider reaching out to a crisis helpline at 1-800-273-8255 or emergency services at 911."""
                
                SessionManager.add_message(session, 'assistant', crisis_response)
                
                return Response(
                    data=at_service.create_say_response(crisis_response),
                    content_type='text/xml',
                    status=status.HTTP_200_OK
                )
            
            # Update session stage
            session.therapy_stage = therapeutic_response['next_stage']
            session.save()
            
            # Add AI response to conversation
            SessionManager.add_message(session, 'assistant', therapeutic_response['response'])
            
            # Determine next action
            if session.therapy_stage == 'completed':
                # End session
                session.is_completed = True
                session.save()
                xml_response = at_service.create_say_response(therapeutic_response['response'])
            else:
                # Continue conversation
                continue_prompt = f"{therapeutic_response['response']} Please share more about how you're feeling."
                callback_url = f"{settings.APP_BASE_URL}/voice/process-recording/"
                xml_response = at_service.create_record_response(continue_prompt, callback_url)
            
            return Response(
                data=xml_response,
                content_type='text/xml',
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error in ProcessRecordingView: {str(e)}")
            at_service = AfricasTalkingService()
            return Response(
                data=at_service.create_say_response("Sorry, we're experiencing technical difficulties."),
                content_type='text/xml',
                status=status.HTTP_200_OK
            )

class CallSessionListView(APIView):
    """API endpoint to list and create call sessions"""
    
    def get(self, request):
        sessions = CallSession.objects.all().order_by('-created_at')
        serializer = CallSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = CallSessionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CallSessionDetailView(APIView):
    """API endpoint to retrieve, update or delete a call session"""
    
    def get(self, request, session_id):
        try:
            session = CallSession.objects.get(session_id=session_id)
            serializer = CallSessionSerializer(session)
            
            # Get conversation history
            conversations = Conversation.objects.filter(session=session).order_by('created_at')
            conversation_serializer = ConversationSerializer(conversations, many=True)
            
            response_data = serializer.data
            response_data['conversations'] = conversation_serializer.data
            
            return Response(response_data)
        except CallSession.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class InitiateOutboundCallView(APIView):
    """API endpoint to initiate outbound calls"""
    
    def post(self, request):
        serializer = VoiceCallSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone_number = serializer.validated_data['callerNumber']
        
        try:
            at_service = AfricasTalkingService()
            result = at_service.initiate_call(phone_number)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error initiating outbound call: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ConversationView(APIView):
    """API endpoint to retrieve conversation messages"""
    
    def get(self, request, session_id):
        try:
            session = CallSession.objects.get(session_id=session_id)
            conversations = Conversation.objects.filter(session=session).order_by('created_at')
            serializer = ConversationSerializer(conversations, many=True)
            return Response(serializer.data)
        except CallSession.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class SessionAnalyticsView(APIView):
    """API endpoint for session analytics"""
    
    def get(self, request):
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        # Basic stats
        total_sessions = CallSession.objects.count()
        completed_sessions = CallSession.objects.filter(is_completed=True).count()
        crisis_sessions = CallSession.objects.filter(crisis_flag=True).count()
        
        # Mood distribution
        mood_distribution = (
            CallSession.objects
            .values('current_mood')
            .annotate(count=Count('current_mood'))
            .order_by('-count')
        )
        
        # Recent activity
        recent_sessions = (
            CallSession.objects
            .filter(created_at__gte=datetime.now() - timedelta(days=7))
            .count()
        )
        
        return Response({
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'completion_rate': (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            'crisis_sessions': crisis_sessions,
            'mood_distribution': mood_distribution,
            'recent_sessions_7days': recent_sessions
        })