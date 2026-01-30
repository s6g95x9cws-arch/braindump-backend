import google.generativeai as genai
import json
from datetime import datetime
from app.core.config import settings
from app.models.schemas import BrainDumpResponse
import time
import re

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Try to use a stable model name suitable for the API key tier
        # Updated to use stable aliases which should have quota
        self.model_flash = genai.GenerativeModel('gemini-flash-latest')
        self.model_pro = genai.GenerativeModel('gemini-pro-latest')

    async def process_audio(self, audio_file_path: str) -> BrainDumpResponse:
        """
        Uploads audio to Gemini and gets structured JSON response.
        """
        # Upload the file to Gemini
        # Note: In a real prod scenario, we might manage file lifecycle (delete after use).
        # For MVP, we upload and process.
        sample_audio = genai.upload_file(audio_file_path)
        
        current_time = datetime.now().isoformat()
        
        # Try with Flash first, fallback to Pro
        # Implementing simple retry logic for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model_flash.generate_content(
                    [system_prompt, sample_audio],
                    generation_config={"response_mime_type": "application/json"}
                )
                break # Success
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Quota exceeded" in error_str:
                    print(f"Rate limit hit, waiting 5s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(5)
                    if attempt == max_retries - 1:
                        # Last attempt failed, try fallback
                        print("Primary model exhausted, trying fallback...")
                        response = self.model_pro.generate_content(
                            [system_prompt, sample_audio],
                            generation_config={"response_mime_type": "application/json"}
                        )
                else:
                    print(f"Primary model error: {e}, switching to fallback immediately.")
                    response = self.model_pro.generate_content(
                        [system_prompt, sample_audio],
                        generation_config={"response_mime_type": "application/json"}
                    )
                    break

        # Parse JSON
        return self._parse_response(response)

    async def process_text(self, text: str) -> BrainDumpResponse:
        """
        Process text directly without audio.
        """
        current_time = datetime.now().isoformat()
        
        system_prompt = self._get_system_prompt(current_time)
        
        # Try with Flash first, fallback to Pro
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model_flash.generate_content(
                    [system_prompt, text],
                    generation_config={"response_mime_type": "application/json"}
                )
                break
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Quota exceeded" in error_str:
                    print(f"Rate limit hit, waiting 5s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(5)
                    if attempt == max_retries - 1:
                         # Last attempt failed, try fallback
                        print("Primary model exhausted, trying fallback...")
                        response = self.model_pro.generate_content(
                            [system_prompt, text],
                            generation_config={"response_mime_type": "application/json"}
                        )
                else:
                    print(f"Primary model error: {e}, switching to fallback immediately.")
                    response = self.model_pro.generate_content(
                        [system_prompt, text],
                        generation_config={"response_mime_type": "application/json"}
                    )
                    break
        
        return self._parse_response(response)

        return self._parse_response(response)

    async def process_image(self, image_file_path: str) -> BrainDumpResponse:
        """
        Uploads an image to Gemini and gets structured JSON response.
        """
        # Upload the file to Gemini
        # MIME type inference is usually automatic by file extension
        sample_image = genai.upload_file(image_file_path)
        
        current_time = datetime.now().isoformat()
        system_prompt = self._get_vision_system_prompt(current_time)
        
        # Try with Flash (it supports vision)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model_flash.generate_content(
                    [system_prompt, sample_image],
                    generation_config={"response_mime_type": "application/json"}
                )
                break
            except Exception as e:
                print(f"Vision error (Attempt {attempt+1}): {e}")
                time.sleep(2)
                if attempt == max_retries - 1:
                    # Fallback to Pro if Flash fails (Pro also supports vision)
                    response = self.model_pro.generate_content(
                        [system_prompt, sample_image],
                        generation_config={"response_mime_type": "application/json"}
                    )
        
        return self._parse_response(response)

    async def answer_question(self, context_actions: list, question: str) -> str:
        try:
            # Flatten context for the LLM
            context_str = "\n".join([
                f"- [{a.created_at.strftime('%Y-%m-%d %H:%M')}] {a.type} ({a.category or 'General'}): {a.content}"
                for a in context_actions
            ])

            prompt = f"""
            You are a helpful personal assistant called "BrainDump".
            You have access to the user's recent logs and actions.

            USER'S DATA (CONTEXT):
            {context_str}

            USER'S QUESTION:
            "{question}"

            INSTRUCTIONS:
            1. Answer the question based ONLY on the provided context.
            2. If the answer is not in the context, say "Kayıtlarımda buna dair bir bilgi bulamadım." (I couldn't find information about this in my records).
            3. Be concise and friendly.
            4. Reply in Turkish (unless the user asks in English).
            """

            response = await self.model_flash.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Q&A Error: {e}")
            return "Üzgünüm, şu an cevap veremiyorum."

    def _get_system_prompt(self, current_time: str) -> str:
        return f"""
        You are the intelligence behind "BrainDump". 
        Your goal is to extract structured actions from a user's stream-of-consciousness speech (or text).
        
        User Context:
        - Current Date/Time: {current_time}
        - Language: Turkish (mostly), but handle mixed English if needed.
        
        Instructions:
        1. Analyze the input accurately.
        2. Break down compound sentences into separate distinct actions.
        3. Classify each action into one of these categories:
            - CALENDAR_EVENT: Events with a specific time/place (e.g., meetings, sports, social).
            - SHOPPING_ITEM: Things to buy.
            - TODO: Tasks without a specific hard deadline (e.g., "clean the garage").
            - NOTE: General thoughts, feelings, or ideas (e.g., "Annem hasta", "Film fikri").
            - ALARM: Specific requests to wake up or time-critical alerts (e.g., "Wake me up at 9").
            - REMINDER: Time-specific tasks (e.g., "Take medicine at 1").

        4. Extract precise dates and times relative to the current time provided above.
           - If user says "tomorrow", calculate the date.
           - If user says "next tuesday", calculate the date.

        5. Return ONLY a JSON object matching this schema.
        
        Schema:
        {{
          "summary": "Short summary of the input",
          "actions": [
            {{
              "type": "CALENDAR_EVENT" | "SHOPPING_ITEM" | "TODO" | "NOTE" | "ALARM" | "REMINDER",
              "content": "The action description",
              "category": "Optional category (e.g., Health, Work, Personal)",
              "datetime_iso": "ISO 8601 date string or null",
              "priority": "HIGH" | "MEDIUM" | "LOW" | null,
              "confidence": 0.0 to 1.0
            }}
          ]
        }}
        """

    def _get_vision_system_prompt(self, current_time: str) -> str:
        return f"""
        You are the visual cortex of "BrainDump".
        Your goal is to analyze images and extract actionable items for the user.
        
        User Context:
        - Current Date/Time: {current_time}
        - Language: Turkish (output in Turkish content unless text is strictly English).
        
        Instructions:
        1. Analyze the IMAGE content deeply.
        2. Extract relevant actions based on what you see:
           - EVENT INVITATION (Wedding, Party, Meeting) -> Create CALENDAR_EVENT.
           - RECEIPT / POWER BILL / INVOICE -> Create TODO (Pay bill) or NOTE (Expense record).
           - EMPTY FRIDGE / PANTRY -> Create SHOPPING_ITEMs for missing essentials.
           - HANDWRITTEN NOTE -> Transcribe to NOTE or TODO.
           - SCREENSHOT OF CHAT -> Extract tasks/events mentioned.
           
        3. If there is a date explicitly visible in the image (like on an invitation), use that for 'datetime_iso'.
        4. Return ONLY a JSON object matching the BrainDump schema.
        
        Schema (Same as audio/text):
        {{
          "summary": "Brief description of the image content",
          "actions": [
            {{
              "type": "CALENDAR_EVENT" | "SHOPPING_ITEM" | "TODO" | "NOTE" | "ALARM" | "REMINDER",
              "content": "Description of the action extracted from image",
              "category": "Vision",
              "datetime_iso": "ISO 8601 date string or null",
              "priority": "HIGH" | "MEDIUM" | "LOW" | null,
              "confidence": 0.0 to 1.0
            }}
          ]
        }}
        """

    def _parse_response(self, response) -> BrainDumpResponse:
        try:
            # Handle potential markdown code blocks
            text = response.text
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            result = json.loads(text)
            return BrainDumpResponse(**result)
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            print(f"Raw response: {response.text}")
            raise e

ai_service = AIService()
