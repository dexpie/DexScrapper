from openai import OpenAI
import logging
import json

logger = logging.getLogger(__name__)

def parse_with_ai(content, prompt, api_key):
    """
    Uses OpenAI to parse unstructured content into JSON based on a prompt.
    """
    if not api_key:
        logger.warning("No API Key provided for AI Extraction.")
        return None

    try:
        client = OpenAI(api_key=api_key)
        
        system_prompt = "You are a helpful data extraction assistant. You only output valid JSON. No markdown formatting."
        user_msg = f"Extract data from the following text based on this instruction: '{prompt}'.\n\nText:\n{content[:15000]}" # Limit context window

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        return json.loads(result_text)

    except Exception as e:
        logger.error(f"AI Extraction Failed: {e}")
        return {"error": str(e)}
