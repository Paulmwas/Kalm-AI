import africastalking
import google.generativeai as genai
import logging
from django.conf import settings
from .models import CallSession, Conversation

logger = logging.getLogger(__name__)

class AfricasTalkingService:
    def __init__(self):
        africastalking.initialize(
            api_key=settings.AT_API_KEY,
            username=settings.AT_USERNAME
        )
        self.voice = africastalking.Voice
    
    def create_say_response(self, text: str, voice: str = "woman") -> str:
        """Create XML response for text-to-speech"""
        return f"""<?xml version='1.0' encoding='UTF-8'?>
        <Response>
            <Say voice="{voice}" playBeep="false">
                <speak>{text}</speak>
            </Say>
        </Response>"""
    
    def create_record_response(self, prompt: str, callback_url: str, max_length: int = 30) -> str:
        """Create XML response for audio recording"""
        return f"""<?xml version='1.0' encoding='UTF-8'?>
        <Response>
            <Record 
                finishOnKey="#" 
                maxLength="{max_length}" 
                timeout="10" 
                trimSilence="true" 
                playBeep="true" 
                callbackUrl="{callback_url}">
                <Say voice="woman">{prompt}</Say>
            </Record>
        </Response>"""
    
    def create_menu_response(self, prompt: str, callback_url: str, timeout: int = 10) -> str:
        """Create XML response for DTMF menu"""
        return f"""<?xml version='1.0' encoding='UTF-8'?>
        <Response>
            <GetDigits timeout="{timeout}" finishOnKey="#" callbackUrl="{callback_url}">
                <Say voice="woman">{prompt}</Say>
            </GetDigits>
            <Say voice="woman">I didn't receive your input. Please call back to try again.</Say>
        </Response>"""

class GeminiTherapistService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def get_system_prompt(self, stage: str, mood: str = None) -> str:
        """Get system prompt based on therapy stage and mood"""
        base_prompt = """You are Kalm AI, a compassionate and professional AI therapy assistant. 
        You provide mental health support through voice conversations. Your responses should be:
        - Warm, empathetic, and non-judgmental
        - Concise (2-3 sentences max for voice delivery)
        - Professionally therapeutic but accessible
        - Focused on active listening and validation
        - Encouraging without being dismissive
        - Crisis-aware (identify if immediate help is needed)
        
        IMPORTANT: If you detect signs of self-harm, suicide ideation, or crisis, immediately recommend calling emergency services or a crisis hotline.
        """
        
        stage_prompts = {
            'greeting': base_prompt + "\nThis is the beginning of the session. Warmly welcome the caller and ask how they're feeling today.",
            'mood_assessment': base_prompt + f"\nThe caller's current mood appears to be {mood}. Acknowledge their feelings and ask gentle follow-up questions.",
            'active_therapy': base_prompt + "\nEngage in active therapeutic conversation. Use techniques like reflective listening, cognitive reframing, and emotional validation.",
            'coping_strategies': base_prompt + "\nProvide practical coping strategies and mindfulness techniques appropriate for their situation.",
            'closing': base_prompt + "\nWrap up the session positively. Summarize key insights and encourage the caller."
        }
        
        return stage_prompts.get(stage, base_prompt)
    
    def get_therapeutic_response(self, conversation_history: list, current_stage: str, mood: str = None) -> dict:
        """Get therapeutic response from Gemini"""
        try:
            system_prompt = self.get_system_prompt(current_stage, mood)
            
            # Format conversation for Gemini
            formatted_conversation = f"{system_prompt}\n\nConversation History:\n"
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                role = "Human" if msg['role'] == 'user' else "Kalm AI"
                formatted_conversation += f"{role}: {msg['content']}\n"
            
            formatted_conversation += "\nKalm AI:"
            
            response = self.model.generate_content(formatted_conversation)
            
            response_text = response.text.strip()
            
            # Analyze for crisis indicators
            crisis_keywords = ['suicide', 'kill myself', 'end it all', 'hurt myself', 'no point living']
            crisis_detected = any(keyword in response_text.lower() for keyword in crisis_keywords)
            
            # Determine next stage based on response
            next_stage = self._determine_next_stage(current_stage, response_text)
            
            return {
                'response': response_text,
                'crisis_detected': crisis_detected,
                'next_stage': next_stage,
                'confidence': 0.8  # Placeholder for response confidence
            }
            
        except Exception as e:
            logger.error(f"Error getting Gemini response: {str(e)}")
            return {
                'response': "I understand you're going through something difficult. Would you like to take a moment to breathe together?",
                'crisis_detected': False,
                'next_stage': current_stage,
                'confidence': 0.5
            }
    
    def _determine_next_stage(self, current_stage: str, _unused: str = None) -> str:
        """Determine next therapy stage based on current stage"""
        stage_transitions = {
            'greeting': 'mood_assessment',
            'mood_assessment': 'active_therapy',
            'active_therapy': 'coping_strategies',
            'coping_strategies': 'closing',
            'closing': 'completed'
        }
        return stage_transitions.get(current_stage, current_stage)

class SessionManager:
    @staticmethod
    def get_or_create_session(session_id: str, caller_number: str) -> CallSession:
        """Get existing session or create new one"""
        session, _ = CallSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'caller_number': caller_number,
                'therapy_stage': 'greeting'
            }
        )
        return session
    
    @staticmethod
    def add_message(session: CallSession, role: str, content: str, transcription: str = None, audio_url: str = None):
        """Add message to conversation"""
        return Conversation.objects.create(
            session=session,
            role=role,
            content=content,
            transcription=transcription,
            audio_url=audio_url
        )
    
    @staticmethod
    def get_conversation_history(session: CallSession) -> list:
        """Get conversation history for session"""
        messages = session.messages.all().order_by('created_at')
        return [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.created_at.isoformat()
            }
            for msg in messages
        ]