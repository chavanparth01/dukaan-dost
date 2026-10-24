# 🏪 Dukaan Dost — आपकी दुकान का दोस्त

> A **voice-first multilingual digital ledger** for Indian shopkeepers — speak naturally in Hindi, Marathi, Bengali, Tamil, Telugu, or English to record sales, expenses, and customer credit.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app.streamlit.app)

---

## 🎯 Features

| Feature | Status |
|---|---|
| 🎙️ Voice recording (browser mic) | ✅ |
| 🧠 Sarvam STT (Saaras v4) transcription | ✅ |
| 🤖 Sarvam-105B LLM transaction parsing | ✅ |
| 🔊 Sarvam TTS (Bulbul v4-Flash) confirmations | ✅ |
| 💰 Sales / Expenses / Credit Given | ✅ |
| 👥 Customer-wise credit ledger | ✅ |
| 📊 Dashboard with daily totals | ✅ |
| 📜 Transaction history with filters | ✅ |
| 📊 Daily summary with TTS | ✅ |
| ✍️ Manual entry fallback | ✅ |
| 🌐 8 Indian languages | ✅ |
| 🎭 Demo mode (no API key needed) | ✅ |

---

## 🚀 Quick Start (Local)

### 1. Clone and set up

```bash
git clone https://github.com/your-username/dukaan-dost.git
cd dukaan-dost
pip3 install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
# Edit .env and set your Sarvam API key:
# SARVAM_API_KEY=sk_your_key_here
```

### 3. Run

```bash
streamlit run app.py
```

Open http://localhost:8501

---

## ☁️ Deploy on Streamlit Cloud

1. Push your code to a **public GitHub repository**
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**
3. Select your repo, set **Main file path** to `app.py`
4. Go to **Settings → Secrets** and add:
   ```toml
   SARVAM_API_KEY = "sk_your_actual_key_here"
   ```
5. Click **Deploy** — your app will be live in minutes!

> ⚠️ **Important:** Never commit your actual API key. Use Streamlit Secrets for deployment.

---

## 🌐 Languages Supported

| Language | Code | Flag |
|---|---|---|
| Hindi (हिंदी) | hi-IN | 🇮🇳 |
| Marathi (मराठी) | mr-IN | 🇮🇳 |
| English | en-IN | 🇬🇧 |
| Bengali (বাংলা) | bn-IN | 🇮🇳 |
| Tamil (தமிழ்) | ta-IN | 🇮🇳 |
| Telugu (తెలుగు) | te-IN | 🇮🇳 |
| Punjabi (ਪੰਜਾਬੀ) | pa-IN | 🇮🇳 |
| Gujarati (ગુજરાતી) | gu-IN | 🇮🇳 |

---

## 🎤 Example Voice Commands

```
Ramesh ne 500 rupaye udhaar liye.
आज 2000 रुपये की बिक्री हुई।
आज दुकान के लिए 300 रुपये का सामान खरीदा।
Show me how much Ramesh owes me.
आज का हिसाब बताओ।
Sunita ne 200 rupaye udhaar liye.
```

---

## 📁 Project Structure

```
dukaan-dost/
├── app.py              # Main Streamlit application
├── data_store.py       # Data model and local JSON persistence
├── sarvam_service.py   # Sarvam AI API wrappers (STT, TTS, LLM)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .env               # Your local secrets (gitignored)
├── .gitignore
├── .streamlit/
│   ├── config.toml    # Streamlit theme and server config
│   └── secrets.toml   # Streamlit Cloud secrets (gitignored)
└── README.md
```

---

## 🔑 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `SARVAM_API_KEY` | Your Sarvam AI API key from [indus.sarvam.ai](https://indus.sarvam.ai/key-management) | Yes (for voice features) |

---

## 📊 Data Model

Each transaction has:
- `id` — UUID
- `type` — `sale`, `expense`, or `credit_given`
- `amount_paise` — integer paise (100 paise = ₹1), no float errors
- `customer_name` — optional, required for credit
- `category` — optional
- `description` — optional
- `original_transcript` — voice input text
- `language` — BCP-47 language code
- `created_at` — ISO timestamp
- `confirmation_status` — `confirmed`

---

## 🛡️ Security

- API key stored **server-side only** in `.env` / Streamlit Secrets
- Never exposed in browser requests or frontend code
- `.env` and `secrets.toml` are gitignored

---

## 🙏 Built With

- [Streamlit](https://streamlit.io) — UI framework
- [Sarvam AI](https://sarvam.ai) — Saaras v4 STT, Bulbul v4-Flash TTS, Sarvam-105B LLM
- Python 3.9+

---

*Built for the Sarvam AI Hackathon 2026*
