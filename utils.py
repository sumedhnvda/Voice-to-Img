import openai
import requests
import time
from io import BytesIO
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def transcribe_audio(file_bytes, filename):
    audio = BytesIO(file_bytes)
    audio.name = filename
    client = openai.OpenAI()
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio,
        response_format="text"
    )
    return transcript

def split_into_scenes(text):
    system_prompt = """You are a helpful assistant that breaks down dream descriptions into clear, simple scenes. Keep each scene exactly as the dreamer describes it, without adding extra interpretations or embellishments."""

    user_prompt = f"""Break this dream description into simple, clear scenes. 
    
    Important:
    - Keep each scene exactly as described in the original text
    - Don't add extra details or interpretations
    - Maintain the original sequence of events
    - Use simple, clear language
    - Each scene should be 1-2 sentences maximum
    
    Dream to process:
    {text}
    
    Format: Number each scene (Scene 1:, Scene 2:, etc.) and keep descriptions simple and true to the original."""

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4.1-nano-2025-04-14",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1000,
        temperature=0.3  # Lower temperature for more consistent output
    )
    scenes_text = response.choices[0].message.content
    scenes = [line.strip("- ").strip() for line in scenes_text.split('\n') if line.strip()]
    return scenes

def call_banana_api(prompt, context_image_bytes=None):
    """Generate image using Google's Gemini model with enhanced dream context"""
    api_key = os.getenv('GOOGLE_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image-preview:generateContent?key={api_key}"
    
    enhanced_prompt = f"""A clear, realistic photograph of: {prompt}
    
    Style: Natural and realistic
    Quality: High detail
    Perspective: Normal eye level
    Lighting: Clear and natural"""
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": enhanced_prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.85,
            "topP": 0.9,
            "topK": 45,
            "maxOutputTokens": 2048
        },
        "safety_settings": [
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if "candidates" in result and len(result["candidates"]) > 0:
            image_part = next((part for part in result["candidates"][0]["content"]["parts"] 
                             if "inlineData" in part), None)
            if image_part:
                return [{"image": image_part["inlineData"]["data"]}]
            else:
                print(f"Debug - No image part found in response: {result}")  
                return {"error": "No image generated in response"}
        else:
            print(f"Debug - Unexpected response structure: {result}")  
            return {"error": "No candidates in response"}
            
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Debug - API Error response: {error_detail}") 
                error_message = error_detail.get('error', {}).get('message', str(e))
            except:
                pass
        return {"error": error_message}

