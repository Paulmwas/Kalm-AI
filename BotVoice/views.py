from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from defusedxml import ElementTree as ET
import requests
from django.conf import settings
import re

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

@csrf_exempt
def chatbot_api(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        # Parse XML request
        xml_data = request.body
        root = ET.fromstring(xml_data)
        message = root.find('message').text
        
        # Prepare Gemini API request - Using API key as URL parameter
        payload = {
            "contents": [{
                "parts": [{
                    "text": message
                }]
            }]
        }
        
        # Call Gemini API with key as URL parameter
        response = requests.post(
            f"{GEMINI_API_URL}?key={settings.GEMINI_API_KEY}",
            json=payload
        )
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                response_text = response_data['candidates'][0]['content']['parts'][0]['text']
                status = "success"
            except (KeyError, IndexError):
                response_text = "AI service error: Invalid response format"
                status = "ai_error"
        else:
            response_text = f"AI service error: {response.status_code} - {response.text}"
            status = "ai_error"
        
        # Clean and escape response for XML
        clean_text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', response_text)
        escaped_text = clean_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Create XML response
        response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<response>`
    <status>{status}</status>
    <message>{escaped_text}</message>
</response>
"""
        return HttpResponse(response_xml, content_type='application/xml; charset=utf-8')
    
    except ET.ParseError:
        error_xml = """<?xml version="1.0" encoding="UTF-8"?>
<response>
    <status>error</status>
    <message>Invalid XML format</message>
</response>
"""
        return HttpResponse(error_xml, content_type='application/xml; charset=utf-8', status=400)
    except Exception as e:
        error_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
    <status>error</status>
    <message>Server error: {str(e)}</message>
</response>
"""
        return HttpResponse(error_xml, content_type='application/xml; charset=utf-8', status=500)