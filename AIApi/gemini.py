# voice/services/gemini.py
import google.generativeai as genai
from django.conf import settings

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_kalmai_response(self, user_input):
        """Generate compassionate response as Kalm AI - Tulia"""
        prompt = f"""
        You are Kalm AI - Tulia, a compassionate mental health assistant. 
        Respond to this user concern with empathy and kindness in 1-2 short sentences.
        Keep the tone warm and supportive. If the input is unclear, ask gently for clarification.
        
        User: {user_input}
        Kalm AI - Tulia: """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return "I'm having trouble understanding. Could you please tell me more about how you're feeling?"