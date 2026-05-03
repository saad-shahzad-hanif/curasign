import streamlit as st
from groq import Groq
import base64

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

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


def get_client(api_key: str = GROQ_API_KEY):
    return Groq(api_key=api_key)


def explain_from_text(text: str, api_key: str = GROQ_API_KEY) -> str:
    if not text or len(text.strip()) < 20:
        return (
            "❌ **Could not extract enough text from this PDF.**\n\n"
            "Please try:\n"
            "- A properly scanned PDF (not a photo saved as PDF)\n"
            "- A text-based PDF rather than a scanned image PDF"
        )
    try:
        client = get_client(api_key)
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "user", "content": f"{SYSTEM_PROMPT}\n\nHere is the medical document text:\n\n{text}"}
            ],
            max_tokens=1500,
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ **Error:** {str(e)}"


def explain_from_image(image_bytes: bytes, api_key: str = GROQ_API_KEY, mime_type: str = "image/jpeg") -> str:
    if not image_bytes:
        return "❌ **Empty image received.** Please upload a valid image file."
    try:
        client = get_client(api_key)
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}},
                        {"type": "text", "text": SYSTEM_PROMPT}
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ **Error:** {str(e)}"


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