import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from django.conf import settings

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

@csrf_exempt
def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
        message = data.get("message", "")

        if not message:
            return JsonResponse({"error": "Message is required"}, status=400)

        # Prepare Gemini API request
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
            response_data = response.json()
            response_text = response_data['candidates'][0]['content']['parts'][0]['text']
            return JsonResponse({"reply": response_text})
        else:
            return JsonResponse({
                "error": f"AI error: {response.status_code} - {response.text}"
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
