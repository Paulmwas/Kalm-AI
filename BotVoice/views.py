from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRequestSerializer
from django.conf import settings
import requests

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

class ChatbotAPIView(APIView):
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            message = serializer.validated_data['message']

            payload = {
                "contents": [{
                    "parts": [{
                        "text": message
                    }]
                }]
            }

            response = requests.post(
                f"{GEMINI_API_URL}?key={settings.GEMINI_API_KEY}",
                json=payload
            )

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    response_text = response_data['candidates'][0]['content']['parts'][0]['text']
                    return Response({"reply": response_text})
                except (KeyError, IndexError):
                    return Response({"error": "Invalid AI response format"}, status=500)
            else:
                return Response({"error": f"AI error: {response.status_code} - {response.text}"}, status=500)

        return Response(serializer.errors, status=400)
