from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
import streamlit as st

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

print("KEY LENGTH:", len(GEMINI_API_KEY))


def get_client(api_key: str = GEMINI_API_KEY):
    return genai.Client(api_key=api_key)


SYSTEM_PROMPT = """
You are a friendly and knowledgeable medical assistant helping non-medical users understand their medical documents.

Your job:
1. First, identify what type of document this is (Blood Report, Prescription, Lab Report, or Other Medical Document).
2. Explain everything in extremely simple language — as if explaining to someone with zero medical knowledge.
3. Be structured, clear, and reassuring in tone.

For a BLOOD REPORT:
- List each test found, its value, and whether it is Normal, High, or Low.
- Explain what each test measures in one simple sentence.
- Give an overall summary of what the report suggests.
- Mention any values that need attention (without causing panic).

For a PRESCRIPTION:
- List each medicine found.
- Explain what each medicine is generally used for.
- Note dosage and frequency in simple terms.
- Give general advice (e.g., take with food, complete the course).

Always end with:
⚠️ Disclaimer: This explanation is for informational purposes only. Always follow your doctor's advice and consult a healthcare professional for medical decisions.

If the document is completely unreadable or not a medical document, say so honestly.
"""


def _handle_error(e: Exception) -> str:
    if isinstance(e, ClientError):
        code = getattr(e, "code", None)
        if code in (400, 401, 403):
            return "❌ **Invalid API Key.** Please check your Gemini API key and try again."
        if code == 429:
            return "❌ **API quota exceeded.** You've hit the free tier limit. Try again later."
        if code == 404:
            return "❌ **Model not found.** Please ensure you are using `gemini-2.0-flash`."
        return f"❌ **API error {code}:** {str(e)}"

    if isinstance(e, ServerError):
        return "❌ **Gemini API is temporarily unavailable.** Please try again in a moment."

    return f"❌ **Unexpected error:** {str(e)}"


def explain_from_text(text: str, api_key: str = GEMINI_API_KEY) -> str:
    if not text or len(text.strip()) < 20:
        return (
            "❌ **Could not extract enough text from this PDF.**\n\n"
            "Please try:\n"
            "- A properly scanned PDF (not a photo saved as PDF)\n"
            "- A text-based PDF rather than a scanned image PDF"
        )
    try:
        client = get_client(api_key)
        prompt = f"{SYSTEM_PROMPT}\n\nHere is the medical document text:\n\n{text}"
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return _handle_error(e)


def explain_from_image(image_bytes: bytes, api_key: str = GEMINI_API_KEY, mime_type: str = "image/jpeg") -> str:
    if not image_bytes:
        return "❌ **Empty image received.** Please upload a valid image file."
    try:
        client = get_client(api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(text=SYSTEM_PROMPT),
            ],
        )
        return response.text
    except Exception as e:
        return _handle_error(e)


def get_image_mime_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".png"):
        return "image/png"
    elif name.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    elif name.endswith(".webp"):
        return "image/webp"
    elif name.endswith(".bmp"):
        return "image/bmp"
    elif name.endswith(".tiff"):
        return "image/tiff"
    return "image/jpeg"