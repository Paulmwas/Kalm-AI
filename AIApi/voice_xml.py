# voice/utils/voice_xml.py
from xml.etree import ElementTree as ET

def generate_voice_xml(text=None, record=False, callback_url=None):
    """Generate Africa's Talking compatible Voice XML"""
    response = ET.Element('Response')
    
    if record:
        # Ask user to speak and record their message
        say = ET.SubElement(response, 'Say')
        say.set('voice', 'woman')
        say.text = "Please tell me how you're feeling. Speak clearly and press hash when done."
        
        record = ET.SubElement(response, 'Record')
        record.set('finishOnKey', '#')
        record.set('maxLength', '60')
        record.set('playBeep', 'true')
        record.set('callbackUrl', callback_url)
    elif text:
        # Speak text response
        say = ET.SubElement(response, 'Say')
        say.set('voice', 'woman')
        say.text = text
    
    return ET.tostring(response, encoding='unicode')