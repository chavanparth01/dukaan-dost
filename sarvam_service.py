"""
sarvam_service.py
Secure wrapper around Sarvam AI APIs.
API key is loaded from environment only - never passed from client code.
Valid speakers for bulbul:v4-flash (hi-IN): aayan_hi_conversational, amit_hi_conversational
"""

import os
import json
import base64
import re
import tempfile
from typing import Optional, Dict, Any, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_BASE = "https://api.sarvam.ai"
HEADERS_AUTH = {"api-subscription-key": SARVAM_API_KEY}

# Language codes supported by Sarvam
# Speakers from bulbul:v4-flash API docs
LANGUAGE_CONFIG = {
    "Hindi (हिंदी)": {
        "code": "hi-IN",
        "speaker": "aayan_hi_conversational",
        "greeting": "नमस्ते! दुकान दोस्त में आपका स्वागत है।",
        "flag": "🇮🇳",
        "short": "HI",
    },
    "Marathi (मराठी)": {
        "code": "mr-IN",
        "speaker": "aayan_hi_conversational",
        "greeting": "नमस्कार! दुकान दोस्त मध्ये आपले स्वागत आहे।",
        "flag": "🇮🇳",
        "short": "MR",
    },
    "English": {
        "code": "en-IN",
        "speaker": "aayan_hi_conversational",
        "greeting": "Welcome to Dukaan Dost! Your shop's accounts are taken care of.",
        "flag": "🇬🇧",
        "short": "EN",
    },
    "Bengali (বাংলা)": {
        "code": "bn-IN",
        "speaker": "aayan_hi_conversational",
        "greeting": "Dukaan Dost-e apnake swagata!",
        "flag": "🇮🇳",
        "short": "BN",
    },
    "Tamil (தமிழ்)": {
        "code": "ta-IN",
        "speaker": "aayan_hi_conversational",
        "greeting": "Dukaan Dost-ku varaverkirom!",
        "flag": "🇮🇳",
        "short": "TA",
    },
    "Telugu (తెలుగు)": {
        "code": "te-IN",
        "speaker": "aayan_hi_conversational",
        "greeting": "Dukaan Dost-ku swaagatam!",
        "flag": "🇮🇳",
        "short": "TE",
    },
    "Punjabi (ਪੰਜਾਬੀ)": {
        "code": "pa-IN",
        "speaker": "aayan_hi_conversational",
        "greeting": "Dukaan Dost vich tuhada swagat hai!",
        "flag": "🇮🇳",
        "short": "PA",
    },
    "Gujarati (ગુજરાતી)": {
        "code": "gu-IN",
        "speaker": "aayan_hi_conversational",
        "greeting": "Dukaan Dost maa aapnu swagat chhe!",
        "flag": "🇮🇳",
        "short": "GU",
    },
}


def _api_available() -> bool:
    return bool(SARVAM_API_KEY)


# ─── Speech to Text ────────────────────────────────────────────────────────────

def transcribe_audio(audio_bytes: bytes, language_code: str = "hi-IN") -> Tuple[Optional[str], Optional[str]]:
    """Transcribe audio bytes using Saaras v4. Returns (transcript, error_message)."""
    if not _api_available():
        return None, "Sarvam API key not configured. Please set SARVAM_API_KEY in .env"

    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            response = requests.post(
                f"{SARVAM_BASE}/speech-to-text",
                headers=HEADERS_AUTH,
                files={"file": ("audio.wav", f, "audio/wav")},
                data={"model": "saaras:v4", "mode": "transcribe"},
                timeout=30,
            )
        os.unlink(tmp_path)

        if response.status_code == 200:
            data = response.json()
            transcript = data.get("transcript", "").strip()
            return transcript if transcript else None, None
        else:
            return None, f"STT API error {response.status_code}: {response.text[:200]}"

    except requests.exceptions.Timeout:
        return None, "Transcription timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to Sarvam API. Check your internet connection."
    except Exception as e:
        return None, f"Transcription error: {str(e)}"


# ─── Regex-based Transaction Parsing (primary method) ─────────────────────────

# Number words in multiple languages
NUMBER_WORDS = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "panch": 5,
    "chhe": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "bees": 20, "tees": 30, "chalis": 40, "pachaas": 50,
    "saath": 70, "assi": 80, "nabbe": 90,
    "sau": 100, "hazaar": 1000, "lakh": 100000,
    "ek sau": 100, "do sau": 200, "teen sau": 300,
    "panch sau": 500, "ek hazaar": 1000, "do hazaar": 2000,
}

CREDIT_KEYWORDS = [
    "udhaar", "udhar", "credit", "baaki", "baki", "owe", "owes",
    "liye", "liya", "diya", "di", "due", "borrow",
    "उधार", "बाकी", "लिए", "लिया",
]

EXPENSE_KEYWORDS = [
    "kharida", "kharche", "kharch", "expense", "spend", "spent",
    "saman", "samaan", "kharid", "purchase", "paid", "buy", "bought",
    "खरीदा", "खर्च", "सामान", "खरीदी",
]

SALE_KEYWORDS = [
    "bikri", "bikrehi", "sale", "bechna", "becha", "sold",
    "collection", "revenue", "income", "aaya", "mila", "milai",
    "बिक्री", "बेचा", "आया", "मिला",
]


def _extract_amount_from_text(text: str) -> Optional[float]:
    """Extract a numeric amount from a transcript."""
    text_lower = text.lower()

    # Look for digits optionally followed by k/K/lakh/thousand/rupaye/rs/INR
    patterns = [
        r'(\d+(?:[,\d]*\d)?(?:\.\d+)?)\s*(?:rupaye?|rupees?|rs\.?|inr|₹)',
        r'(?:rupaye?|rupees?|rs\.?|inr|₹)\s*(\d+(?:[,\d]*\d)?(?:\.\d+)?)',
        r'(\d+(?:[,\d]*\d)?(?:\.\d+)?)\s*(?:k\b)',  # 2k = 2000
        r'(\d+(?:[,\d]*\d)?(?:\.\d+)?)',  # bare number
    ]
    for p in patterns:
        m = re.search(p, text_lower)
        if m:
            num_str = m.group(1).replace(",", "")
            try:
                val = float(num_str)
                # Handle 'k' suffix
                if re.search(r'\d+\s*k\b', text_lower):
                    val *= 1000
                if val > 0:
                    return val
            except ValueError:
                continue

    # Try number words
    for word, value in sorted(NUMBER_WORDS.items(), key=lambda x: -x[1]):
        if word in text_lower:
            return float(value)

    return None


def _detect_type(text: str) -> str:
    """Detect transaction type from text."""
    text_lower = text.lower()
    # Check credit first (most specific)
    for kw in CREDIT_KEYWORDS:
        if kw in text_lower:
            return "credit_given"
    for kw in EXPENSE_KEYWORDS:
        if kw in text_lower:
            return "expense"
    for kw in SALE_KEYWORDS:
        if kw in text_lower:
            return "sale"
    return "sale"  # default


def _extract_customer_name(text: str) -> Optional[str]:
    """Try to extract a customer name from Hindi/English credit phrases."""
    # Pattern: "Name ne X rupaye udhaar liye" or "give credit to Name"
    patterns = [
        r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+ne\b',  # "Ramesh ne ..."
        r'to\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b',   # "credit to Ramesh"
        r'([A-Z][a-z]+)\s+(?:ka|ki|ke)\s+(?:udhaar|baaki)',  # "Ramesh ka udhaar"
        r'(?:give|gave|given)\s+(?:to\s+)?([A-Z][a-z]+)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            name = m.group(1).strip()
            if name and name.lower() not in ("aaj", "aap", "mai", "main", "hum", "tum", "yeh", "woh"):
                return name

    # Looser: first capitalized word if credit transaction
    words = text.split()
    for w in words:
        if w and w[0].isupper() and len(w) > 2 and w.isalpha():
            skip = {"Aaj", "Kuch", "Show", "Yeh", "Woh", "Aap", "Main", "Hum", "Tum", "Rupaye", "Sale", "Expense"}
            if w not in skip:
                return w
    return None


def parse_transaction_local(transcript: str) -> Dict[str, Any]:
    """Local regex-based parser as fallback when LLM is unavailable."""
    tx_type = _detect_type(transcript)
    amount = _extract_amount_from_text(transcript)
    customer_name = _extract_customer_name(transcript) if tx_type == "credit_given" else None
    ambiguous = amount is None

    # Build description
    type_map = {"sale": "Sale", "expense": "Expense", "credit_given": "Credit Given"}
    desc = f"{type_map[tx_type]}"
    if customer_name:
        desc += f" — {customer_name}"

    return {
        "type": tx_type,
        "amount_rupees": amount,
        "customer_name": customer_name,
        "category": None,
        "description": desc,
        "confidence": "medium" if amount else "low",
        "ambiguous": ambiguous,
    }


# ─── LLM Transaction Parsing ──────────────────────────────────────────────────

PARSE_SYSTEM_PROMPT = """You are a transaction parser for an Indian shopkeeper app. Extract transaction details from the shopkeeper's voice input.

Output ONLY a valid JSON object (no markdown, no explanation):
{"type":"sale","amount_rupees":500,"customer_name":null,"category":null,"description":"Morning sale","confidence":"high","ambiguous":false}

Rules:
- type: "sale" (cash collected), "expense" (money spent), "credit_given" (money given on credit/udhaar)
- amount_rupees: positive number or null if unclear
- customer_name: person's name for credit transactions, null otherwise
- ambiguous: true if amount or type is unclear
- description: short summary in same language as input
Output ONLY JSON."""


def parse_transaction(transcript: str, language_code: str = "hi-IN") -> Tuple[Optional[Dict], Optional[str]]:
    """
    Parse a transcript into a structured transaction.
    First tries Sarvam-105B LLM, falls back to local regex parser.
    Returns (parsed_dict, error_message).
    """
    # Try LLM first if API is available
    if _api_available():
        try:
            payload = {
                "model": "sarvam-105b",
                "messages": [
                    {"role": "system", "content": PARSE_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Input: {transcript}"},
                ],
                "temperature": 0.0,
                "max_tokens": 5000,
            }
            response = requests.post(
                f"{SARVAM_BASE}/v1/chat/completions",
                headers={**HEADERS_AUTH, "Content-Type": "application/json"},
                json=payload,
                timeout=45,
            )

            if response.status_code == 200:
                choices = response.json().get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content")
                    if content:
                        content = content.strip()
                        content = re.sub(r"^```(?:json)?\s*", "", content)
                        content = re.sub(r"\s*```$", "", content)
                        # Extract JSON from content
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            parsed = json.loads(json_match.group(0))
                            return parsed, None
        except Exception:
            pass  # Fall through to local parser

    # Local regex fallback
    parsed = parse_transaction_local(transcript)
    return parsed, None


# ─── Text to Speech ────────────────────────────────────────────────────────────

def text_to_speech(text: str, language_code: str = "hi-IN", speaker: str = "aayan_hi_conversational") -> Tuple[Optional[bytes], Optional[str]]:
    """Convert text to speech using Bulbul v4-Flash. Returns (wav_bytes, error_message)."""
    if not _api_available():
        return None, "Sarvam API key not configured."

    try:
        payload = {
            "text": text[:500],
            "language_code": language_code,
            "model": "bulbul:v4-flash",
            "speaker": speaker,
        }
        response = requests.post(
            f"{SARVAM_BASE}/text-to-speech",
            headers={**HEADERS_AUTH, "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            audios = data.get("audios", [])
            if audios:
                audio_bytes = base64.b64decode("".join(audios))
                return audio_bytes, None
            return None, "No audio returned from TTS API."
        elif response.status_code == 400:
            # Speaker not supported for this language - try default
            err_text = response.text
            if "Speaker" in err_text and "not recognized" in err_text:
                # Try without speaker field
                payload2 = {k: v for k, v in payload.items() if k != "speaker"}
                r2 = requests.post(
                    f"{SARVAM_BASE}/text-to-speech",
                    headers={**HEADERS_AUTH, "Content-Type": "application/json"},
                    json=payload2,
                    timeout=30,
                )
                if r2.status_code == 200:
                    data = r2.json()
                    audios = data.get("audios", [])
                    if audios:
                        return base64.b64decode("".join(audios)), None
            return None, f"TTS API error {response.status_code}: {response.text[:200]}"
        else:
            return None, f"TTS API error {response.status_code}: {response.text[:200]}"

    except requests.exceptions.Timeout:
        return None, "TTS timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to Sarvam API."
    except Exception as e:
        return None, f"TTS error: {str(e)}"


# ─── Confirmation Messages ────────────────────────────────────────────────────

CONFIRMATION_TEMPLATES = {
    "hi-IN": {
        "sale": "बिक्री दर्ज हो गई: {amount}",
        "expense": "खर्च दर्ज हो गई: {amount}",
        "credit_given": "{customer} को {amount} उधार दिया गया।",
        "summary": "आज की कुल बिक्री {sales}। कुल खर्च {expenses}। कुल बकाया {outstanding}।",
        "query_credit": "{customer} का कुल बकाया {amount} है।",
        "demo_mode": "[डेमो मोड] API उपलब्ध नहीं है।",
    },
    "mr-IN": {
        "sale": "विक्री नोंदवली: {amount}",
        "expense": "खर्च नोंदवला: {amount}",
        "credit_given": "{customer} ला {amount} उधार दिले.",
        "summary": "आजची विक्री {sales}. खर्च {expenses}. थकबाकी {outstanding}.",
        "query_credit": "{customer} ची थकबाकी {amount} आहे.",
        "demo_mode": "[डेमो मोड] API उपलब्ध नाही.",
    },
    "en-IN": {
        "sale": "Sale recorded: {amount}",
        "expense": "Expense recorded: {amount}",
        "credit_given": "Credit of {amount} given to {customer}.",
        "summary": "Today: sales {sales}, expenses {expenses}, outstanding {outstanding}.",
        "query_credit": "{customer} owes you {amount}.",
        "demo_mode": "[Demo Mode] API not available.",
    },
    "bn-IN": {
        "sale": "Bikroy notha: {amount}",
        "expense": "Khoroch notha: {amount}",
        "credit_given": "{customer} ke {amount} baki te deoa hoyeche.",
        "summary": "Aj bikroy {sales}. Khoroch {expenses}. Baaki {outstanding}.",
        "query_credit": "{customer} er baaki {amount}.",
        "demo_mode": "[Demo] API paoa jacche na.",
    },
    "ta-IN": {
        "sale": "Vittanam pathivu: {amount}",
        "expense": "Selavai pathivu: {amount}",
        "credit_given": "{customer} ku {amount} kadanaga kodukkapattadu.",
        "summary": "Inday vittanam {sales}. Selavu {expenses}. Niluvaiku {outstanding}.",
        "query_credit": "{customer} kadan {amount}.",
        "demo_mode": "[Demo] API kidaikkavil lai.",
    },
    "te-IN": {
        "sale": "Ammakam nondavinchabaindi: {amount}",
        "expense": "Kharchu nondavinchabaindi: {amount}",
        "credit_given": "{customer} ki {amount} appuga ivvabaindi.",
        "summary": "Neti ammakalu {sales}. Kharchu {expenses}. Baaki {outstanding}.",
        "query_credit": "{customer} baaki {amount}.",
        "demo_mode": "[Demo] API andubatulo ledu.",
    },
    "pa-IN": {
        "sale": "Vikri darj: {amount}",
        "expense": "Kharach darj: {amount}",
        "credit_given": "{customer} nu {amount} udhaar ditta.",
        "summary": "Aj vikri {sales}. Kharach {expenses}. Baaki {outstanding}.",
        "query_credit": "{customer} da baaki {amount}.",
        "demo_mode": "[Demo] API upalabdh nahi.",
    },
    "gu-IN": {
        "sale": "Vechan nondhu: {amount}",
        "expense": "Kharcho nondhu: {amount}",
        "credit_given": "{customer} ne {amount} udhaar aapyo.",
        "summary": "Aj vechan {sales}. Kharcho {expenses}. Baaki {outstanding}.",
        "query_credit": "{customer} no baaki {amount}.",
        "demo_mode": "[Demo] API upalabdh nathi.",
    },
}


def get_confirmation_text(tx_type: str, amount_str: str, language_code: str, customer_name: str = "") -> str:
    templates = CONFIRMATION_TEMPLATES.get(language_code, CONFIRMATION_TEMPLATES["en-IN"])
    template = templates.get(tx_type, templates.get("sale", "Recorded: {amount}"))
    return template.format(amount=amount_str, customer=customer_name or "Customer")
