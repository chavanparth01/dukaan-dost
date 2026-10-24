"""
app.py  -  Dukaan Dost
A voice-first multilingual ledger for Indian shopkeepers.
Built with Streamlit + Sarvam AI APIs.
"""

import base64
import os
from datetime import datetime, date, timedelta

import streamlit as st
from dotenv import load_dotenv

from data_store import (
    make_transaction, save_transaction, get_all_transactions,
    get_transactions_today, get_dashboard_totals, get_all_customers_outstanding,
    paise_to_rupees, rupees_to_paise, seed_sample_data, delete_transaction,
    get_transactions_by_customer,
)
from sarvam_service import (
    transcribe_audio, parse_transaction, text_to_speech,
    get_confirmation_text, LANGUAGE_CONFIG, SARVAM_API_KEY,
    CONFIRMATION_TEMPLATES,
)

load_dotenv()

# Page Config
st.set_page_config(
    page_title="Dukaan Dost - Aapki Dukaan Ka Hisaab",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter','Noto Sans Devanagari',sans-serif; }
  .stApp { background: linear-gradient(135deg,#fefdf8 0%,#f0f9f0 100%); }
  #MainMenu, footer, header { visibility: hidden; }

  .brand-header {
    background: linear-gradient(135deg,#1a5c36 0%,#2d8653 100%);
    border-radius: 16px; padding: 24px 32px; margin-bottom: 24px;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 4px 24px rgba(26,92,54,0.18);
  }
  .brand-title { color:#fff; font-size:2rem; font-weight:700; margin:0; letter-spacing:-0.5px; }
  .brand-subtitle { color:#a8e6c1; font-size:0.95rem; margin:4px 0 0 0; }
  .brand-badge {
    background:rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.3);
    border-radius:24px; padding:8px 16px; color:white; font-size:0.85rem; font-weight:600;
  }
  .demo-banner {
    background:linear-gradient(90deg,#f59e0b,#f97316); color:white;
    padding:10px 20px; border-radius:10px; text-align:center; font-weight:600;
    font-size:0.9rem; margin-bottom:16px;
  }
  .metric-card {
    background:white; border-radius:16px; padding:20px 24px;
    box-shadow:0 2px 12px rgba(0,0,0,0.06); border-left:5px solid #2d8653;
    margin-bottom:12px; transition:transform 0.2s,box-shadow 0.2s;
  }
  .metric-card:hover { transform:translateY(-2px); box-shadow:0 6px 20px rgba(0,0,0,0.10); }
  .metric-card.expense { border-left-color:#e05c2e; }
  .metric-card.credit  { border-left-color:#7c3aed; }
  .metric-card.outstanding { border-left-color:#0369a1; }
  .metric-label { color:#6b7280; font-size:0.8rem; font-weight:600; text-transform:uppercase; letter-spacing:0.6px; margin-bottom:4px; }
  .metric-value { color:#111827; font-size:1.8rem; font-weight:700; margin:0; line-height:1.1; }
  .metric-icon { font-size:1.4rem; float:right; opacity:0.6; }

  .mic-container {
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    padding:32px; background:white; border-radius:24px;
    box-shadow:0 4px 24px rgba(0,0,0,0.08); margin-bottom:20px;
  }
  .mic-label { color:#374151; font-size:1.1rem; font-weight:500; margin-bottom:20px; text-align:center; }

  .tx-preview {
    background:linear-gradient(135deg,#f0fdf4 0%,#dcfce7 100%);
    border:2px solid #86efac; border-radius:16px; padding:20px 24px; margin-bottom:16px;
  }
  .tx-badge {
    display:inline-block; padding:4px 14px; border-radius:20px;
    font-size:0.8rem; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:10px;
  }
  .tx-badge.sale     { background:#dcfce7; color:#166534; }
  .tx-badge.expense  { background:#fee2e2; color:#991b1b; }
  .tx-badge.credit   { background:#ede9fe; color:#5b21b6; }
  .tx-amount { font-size:1.8rem; font-weight:700; color:#111827; }
  .tx-transcript {
    background:#f9fafb; border-left:3px solid #d1d5db;
    padding:8px 12px; border-radius:0 8px 8px 0;
    font-style:italic; color:#6b7280; font-size:0.85rem; margin-top:10px;
  }
  .ambiguous-warning {
    background:#fef3c7; border:1px solid #fcd34d;
    border-radius:10px; padding:12px 16px; color:#92400e; font-size:0.88rem; margin-top:10px;
  }

  .tx-row {
    background:white; border-radius:12px; padding:14px 18px; margin-bottom:8px;
    display:flex; align-items:center; box-shadow:0 1px 4px rgba(0,0,0,0.05);
    border-left:4px solid #e5e7eb;
  }
  .tx-row.sale    { border-left-color:#22c55e; }
  .tx-row.expense { border-left-color:#ef4444; }
  .tx-row.credit  { border-left-color:#8b5cf6; }

  .audio-confirm {
    background:linear-gradient(135deg,#1a5c36,#2d8653);
    border-radius:16px; padding:20px 24px; color:white; margin-top:16px;
  }
  .audio-confirm h4 { color:#a8e6c1; margin:0 0 8px 0; font-size:0.9rem; }
  .audio-msg { color:white; font-size:1.05rem; font-weight:500; }

  .customer-card {
    background:white; border-radius:14px; padding:16px 20px; margin-bottom:10px;
    box-shadow:0 2px 8px rgba(0,0,0,0.06); display:flex; align-items:center; justify-content:space-between;
  }
  .customer-name { font-weight:600; color:#111827; font-size:1rem; }
  .customer-amount { font-weight:700; color:#7c3aed; font-size:1.2rem; }

  .status-ok   { color:#16a34a; font-weight:600; }
  .status-err  { color:#dc2626; font-weight:600; }

  div.stButton > button { border-radius:10px !important; font-weight:600 !important; transition:all 0.2s !important; }
  div.stButton > button:hover { transform:translateY(-1px); }
  ::-webkit-scrollbar { width:6px; }
  ::-webkit-scrollbar-thumb { background:#888; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# Session State Init
def init_state():
    defaults = {
        "language": "Hindi (हिंदी)",
        "pending_tx": None,
        "last_transcript": "",
        "last_audio": None,
        "last_confirmation_text": "",
        "demo_mode": not bool(SARVAM_API_KEY),
        "active_tab": "dashboard",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
seed_sample_data()

# Helpers
def lang_code():
    return LANGUAGE_CONFIG[st.session_state.language]["code"]

def lang_speaker():
    return LANGUAGE_CONFIG[st.session_state.language]["speaker"]

def fmt_datetime(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return iso_str

def type_label(tx_type):
    return {"sale": "💰 Sale", "expense": "📦 Expense", "credit_given": "🤝 Credit Given"}.get(tx_type, tx_type)

def type_color(tx_type):
    return {"sale": "sale", "expense": "expense", "credit_given": "credit"}.get(tx_type, "")

def play_audio_html(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    return f'<audio controls autoplay style="width:100%;margin-top:8px;"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>'

def render_metric(label, value, icon, card_class=""):
    st.markdown(f"""
    <div class="metric-card {card_class}">
      <span class="metric-icon">{icon}</span>
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def generate_tts_and_store(text):
    if not st.session_state.demo_mode and SARVAM_API_KEY:
        audio_bytes, err = text_to_speech(text, lang_code(), lang_speaker())
        if audio_bytes:
            st.session_state.last_audio = audio_bytes
            st.session_state.last_confirmation_text = text
            return audio_bytes, None
        return None, err
    else:
        st.session_state.last_audio = None
        st.session_state.last_confirmation_text = text
        return None, None


# Sidebar
with st.sidebar:
    st.markdown("## 🏪 Dukaan Dost")
    st.markdown("---")
    st.markdown("**🌐 Language / भाषा**")
    lang_options = list(LANGUAGE_CONFIG.keys())
    selected_lang = st.selectbox(
        "Language",
        lang_options,
        index=lang_options.index(st.session_state.language) if st.session_state.language in lang_options else 0,
        label_visibility="collapsed",
    )
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()

    lang_cfg = LANGUAGE_CONFIG[st.session_state.language]
    st.markdown(f"<span style='background:rgba(45,134,83,0.1);border:1px solid #2d8653;border-radius:20px;padding:4px 12px;color:#1a5c36;font-size:0.85rem;font-weight:600;'>{lang_cfg['flag']} {lang_cfg['short']} — {lang_cfg['code']}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**📋 Navigation**")
    tabs = [
        ("🏠 Dashboard", "dashboard"),
        ("📝 Record Transaction", "record"),
        ("📜 History", "history"),
        ("👥 Customer Ledger", "customers"),
        ("📊 Daily Summary", "summary"),
    ]
    for label, tab_id in tabs:
        if st.button(label, use_container_width=True,
                     type="primary" if st.session_state.active_tab == tab_id else "secondary"):
            st.session_state.active_tab = tab_id
            st.rerun()

    st.markdown("---")
    if SARVAM_API_KEY:
        st.markdown("<span class='status-ok'>✅ Sarvam API Connected</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='status-err'>⚠️ Demo Mode (No API Key)</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**💡 Example Voice Commands**")
    st.code("Ramesh ne 500 rupaye udhaar liye", language=None)
    st.code("Aaj 2000 ki bikri hui", language=None)
    st.code("300 rupaye ka samaan kharida", language=None)
    st.code("Show me Ramesh outstanding", language=None)


# Main Content Header
lang_cfg = LANGUAGE_CONFIG[st.session_state.language]
st.markdown(f"""
<div class="brand-header">
  <div>
    <div class="brand-title">🏪 दुकान दोस्त</div>
    <div class="brand-subtitle">Speak naturally. Your shop's accounts are taken care of.</div>
  </div>
  <div class="brand-badge">{lang_cfg['flag']} {lang_cfg['short']} &nbsp;|&nbsp; {lang_cfg['code']}</div>
</div>
""", unsafe_allow_html=True)

if st.session_state.demo_mode:
    st.markdown("""
    <div class="demo-banner">
      🎭 DEMO MODE — Sample data loaded. Add your SARVAM_API_KEY to .env to enable voice features.
    </div>
    """, unsafe_allow_html=True)


# ── DASHBOARD ──────────────────────────────────────────────────────────────────
if st.session_state.active_tab == "dashboard":
    totals = get_dashboard_totals()
    today_txs = get_transactions_today()
    st.markdown("### 📊 Today's Overview")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric("Sales Today", paise_to_rupees(totals["sales_today_paise"]), "💰")
    with c2:
        render_metric("Expenses Today", paise_to_rupees(totals["expenses_today_paise"]), "📦", "expense")
    with c3:
        render_metric("Credit Given Today", paise_to_rupees(totals["credit_given_today_paise"]), "🤝", "credit")
    with c4:
        render_metric("Total Outstanding", paise_to_rupees(totals["total_outstanding_paise"]), "📋", "outstanding")

    st.markdown("---")
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 📝 Today's Transactions")
        if not today_txs:
            st.info("No transactions today. Click **Record Transaction** in the sidebar to add one!")
        else:
            for tx in sorted(today_txs, key=lambda t: t.get("created_at", ""), reverse=True):
                tc = type_color(tx.get("type", ""))
                desc = tx.get("description") or tx.get("category") or "—"
                cust = f"  👤 {tx['customer_name']}" if tx.get("customer_name") else ""
                time_str = fmt_datetime(tx.get("created_at", ""))
                st.markdown(f"""
                <div class="tx-row {tc}">
                  <div style="flex:1">
                    <div style="font-weight:600;color:#111">{type_label(tx.get('type',''))}</div>
                    <div style="color:#6b7280;font-size:0.85rem">{desc}{cust}</div>
                    <div style="color:#9ca3af;font-size:0.75rem">{time_str}</div>
                  </div>
                  <div style="font-size:1.25rem;font-weight:700;color:#111">{paise_to_rupees(tx.get('amount_paise',0))}</div>
                </div>
                """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 👥 Top Credit Customers")
        outstanding = get_all_customers_outstanding()
        if not outstanding:
            st.info("No outstanding credits.")
        else:
            for name, paise in sorted(outstanding.items(), key=lambda x: -x[1])[:5]:
                st.markdown(f"""
                <div class="customer-card">
                  <span class="customer-name">👤 {name}</span>
                  <span class="customer-amount">{paise_to_rupees(paise)}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("➕ Record New Transaction", type="primary", use_container_width=True):
            st.session_state.active_tab = "record"
            st.rerun()

    if st.session_state.last_audio and st.session_state.last_confirmation_text:
        st.markdown("---")
        st.markdown(f"""
        <div class="audio-confirm">
          <h4>🔊 Last Confirmation — Click Play to Replay</h4>
          <div class="audio-msg">{st.session_state.last_confirmation_text}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(play_audio_html(st.session_state.last_audio), unsafe_allow_html=True)


# ── RECORD TRANSACTION ─────────────────────────────────────────────────────────
elif st.session_state.active_tab == "record":
    st.markdown("### 🎙️ Record a Transaction")

    st.markdown("""
    <div class="mic-container">
      <div class="mic-label">
        🎙️ Click the microphone, speak your transaction, then click Stop.<br>
        <small style="color:#9ca3af">Examples: "Ramesh ne 500 rupaye udhaar liye" | "Aaj 2000 ki bikri hui" | "300 rupaye ka samaan kharida"</small>
      </div>
    </div>
    """, unsafe_allow_html=True)

    audio_bytes = None
    try:
        from audio_recorder_streamlit import audio_recorder
        audio_bytes = audio_recorder(
            text="🎙️ Click to Record",
            recording_color="#2d8653",
            neutral_color="#1a5c36",
            icon_name="microphone",
            icon_size="3x",
            pause_threshold=3.0,
            sample_rate=16000,
        )
    except ImportError:
        st.warning("Voice recorder not available. Please use Manual Entry below.")

    if audio_bytes and len(audio_bytes) > 2000:
        with st.spinner("🎧 Transcribing your voice..."):
            transcript, err = transcribe_audio(audio_bytes, lang_code())

        if err:
            st.error(f"🚫 Transcription failed: {err}")
            if "not configured" in err:
                st.info("💡 Add SARVAM_API_KEY to .env to enable voice features. Use Manual Entry below for now.")
        elif transcript:
            st.session_state.last_transcript = transcript
            st.success(f"📝 **Heard:** {transcript}")

            with st.spinner("🧠 Understanding your transaction..."):
                parsed, parse_err = parse_transaction(transcript, lang_code())

            if parse_err:
                st.error(f"Could not understand: {parse_err}")
            elif parsed:
                amount_r = parsed.get("amount_rupees")
                is_ambiguous = parsed.get("ambiguous", False) or amount_r is None
                st.session_state.pending_tx = {
                    "type": parsed.get("type", "sale"),
                    "amount_rupees": amount_r,
                    "customer_name": parsed.get("customer_name"),
                    "category": parsed.get("category"),
                    "description": parsed.get("description", ""),
                    "original_transcript": transcript,
                    "confidence": parsed.get("confidence", "medium"),
                    "ambiguous": is_ambiguous,
                }
        else:
            st.warning("No speech detected. Please try again and speak clearly.")

    st.markdown("---")

    # Confirmation Panel
    if st.session_state.pending_tx:
        ptx = st.session_state.pending_tx
        tx_type = ptx.get("type", "sale")
        badge_class = type_color(tx_type)
        amount_r = ptx.get("amount_rupees")
        amount_str = paise_to_rupees(rupees_to_paise(amount_r)) if amount_r else "⚠️ Amount not detected"

        st.markdown("### ✅ Confirm Transaction")

        warn_html = ""
        if ptx.get("ambiguous") or amount_r is None:
            warn_html = '<div class="ambiguous-warning">⚠️ I am not fully confident. Please review and edit before saving.</div>'

        transcript_html = ""
        if ptx.get("original_transcript"):
            transcript_html = f'<div class="tx-transcript">🎙️ &quot;{ptx["original_transcript"]}&quot;</div>'

        extras = ""
        if ptx.get("customer_name"):
            extras += f"<br><small>👤 Customer: {ptx['customer_name']}</small>"
        if ptx.get("category"):
            extras += f"<br><small>📦 Category: {ptx['category']}</small>"
        if ptx.get("description"):
            extras += f"<br><small>📝 {ptx['description']}</small>"

        st.markdown(f"""
        <div class="tx-preview">
          <span class="tx-badge {badge_class}">{type_label(tx_type)}</span>
          <div class="tx-amount">{amount_str}</div>
          {extras}
          {transcript_html}
          {warn_html}
        </div>
        """, unsafe_allow_html=True)

        with st.expander("✏️ Edit Transaction Details", expanded=bool(ptx.get("ambiguous", False))):
            col1, col2 = st.columns(2)
            with col1:
                new_type = st.selectbox(
                    "Transaction Type",
                    ["sale", "expense", "credit_given"],
                    index=["sale", "expense", "credit_given"].index(tx_type),
                    format_func=lambda x: type_label(x),
                    key="edit_type"
                )
                new_amount = st.number_input(
                    "Amount (₹)",
                    min_value=0.0,
                    value=float(amount_r) if amount_r else 0.0,
                    step=1.0, format="%.2f",
                    key="edit_amount"
                )
            with col2:
                new_customer = st.text_input("Customer Name", value=ptx.get("customer_name") or "", key="edit_cust")
                new_desc = st.text_input("Description", value=ptx.get("description") or "", key="edit_desc")
                new_cat = st.text_input("Category", value=ptx.get("category") or "", key="edit_cat")

            if st.button("💾 Update Preview", key="update_preview"):
                st.session_state.pending_tx.update({
                    "type": new_type,
                    "amount_rupees": new_amount,
                    "customer_name": new_customer or None,
                    "description": new_desc,
                    "category": new_cat or None,
                    "ambiguous": False,
                })
                st.rerun()

        col_confirm, col_discard = st.columns(2)
        with col_confirm:
            confirm_disabled = not ptx.get("amount_rupees") or ptx.get("amount_rupees", 0) <= 0
            if st.button("✅ Confirm & Save", type="primary", use_container_width=True, disabled=confirm_disabled):
                ptx = st.session_state.pending_tx
                if ptx.get("type") == "credit_given" and not ptx.get("customer_name"):
                    st.error("Please enter the customer name for a credit transaction.")
                else:
                    tx = make_transaction(
                        type=ptx["type"],
                        amount_paise=rupees_to_paise(ptx["amount_rupees"]),
                        customer_name=ptx.get("customer_name"),
                        category=ptx.get("category"),
                        description=ptx.get("description"),
                        original_transcript=ptx.get("original_transcript"),
                        language=lang_code(),
                    )
                    save_transaction(tx)
                    confirm_text = get_confirmation_text(
                        tx["type"], paise_to_rupees(tx["amount_paise"]),
                        lang_code(), tx.get("customer_name", ""),
                    )
                    audio_tts, tts_err = generate_tts_and_store(confirm_text)
                    st.session_state.pending_tx = None
                    st.success(f"🎉 Transaction saved!")
                    if audio_tts:
                        st.markdown(f"""
                        <div class="audio-confirm">
                          <h4>🔊 Sarvam Confirmation</h4>
                          <div class="audio-msg">{confirm_text}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(play_audio_html(audio_tts), unsafe_allow_html=True)
                    else:
                        st.info(f"💬 {confirm_text}")
                    st.balloons()

        with col_discard:
            if st.button("🗑️ Discard", use_container_width=True):
                st.session_state.pending_tx = None
                st.session_state.last_transcript = ""
                st.rerun()

    st.markdown("---")

    # Manual Entry fallback
    with st.expander("✍️ Manual Entry (fallback)", expanded=False):
        mc1, mc2 = st.columns(2)
        with mc1:
            m_type = st.selectbox("Type", ["sale", "expense", "credit_given"],
                                  format_func=lambda x: type_label(x), key="m_type")
            m_amount = st.number_input("Amount (₹)", min_value=1.0, value=100.0, step=1.0, key="m_amount")
        with mc2:
            m_customer = st.text_input("Customer Name", key="m_customer", placeholder="Required for Credit Given")
            m_desc = st.text_input("Description", key="m_desc", placeholder="e.g. morning sales")
            m_cat = st.text_input("Category", key="m_cat", placeholder="e.g. Supplies")

        if st.button("💾 Save Manual Transaction", type="primary", use_container_width=True):
            if m_type == "credit_given" and not m_customer.strip():
                st.error("Customer name is required for credit transactions.")
            elif m_amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                tx = make_transaction(
                    type=m_type,
                    amount_paise=rupees_to_paise(m_amount),
                    customer_name=m_customer.strip() or None,
                    category=m_cat.strip() or None,
                    description=m_desc.strip() or None,
                    language=lang_code(),
                )
                save_transaction(tx)
                confirm_text = get_confirmation_text(m_type, paise_to_rupees(tx["amount_paise"]),
                                                     lang_code(), m_customer.strip())
                audio_m, _ = generate_tts_and_store(confirm_text)
                st.success(f"✅ Saved!")
                if audio_m:
                    st.markdown(play_audio_html(audio_m), unsafe_allow_html=True)
                else:
                    st.info(f"💬 {confirm_text}")
                st.balloons()


# ── TRANSACTION HISTORY ────────────────────────────────────────────────────────
elif st.session_state.active_tab == "history":
    st.markdown("### 📜 Transaction History")
    all_txs = get_all_transactions()

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_type = st.selectbox("Filter by Type", ["All", "sale", "expense", "credit_given"],
                                   format_func=lambda x: "All Types" if x == "All" else type_label(x))
    with col_f2:
        filter_days = st.selectbox("Filter by Period", ["Today", "7 days", "30 days", "All time"])
    with col_f3:
        search_name = st.text_input("Search Customer", placeholder="Type name...")

    filtered = all_txs[:]
    if filter_type != "All":
        filtered = [t for t in filtered if t.get("type") == filter_type]
    if filter_days == "Today":
        today_str = date.today().isoformat()
        filtered = [t for t in filtered if t.get("created_at", "").startswith(today_str)]
    elif filter_days == "7 days":
        cutoff = (date.today() - timedelta(days=7)).isoformat()
        filtered = [t for t in filtered if t.get("created_at", "") >= cutoff]
    elif filter_days == "30 days":
        cutoff = (date.today() - timedelta(days=30)).isoformat()
        filtered = [t for t in filtered if t.get("created_at", "") >= cutoff]
    if search_name:
        filtered = [t for t in filtered if search_name.lower() in (t.get("customer_name","") or "").lower()]

    filtered = sorted(filtered, key=lambda t: t.get("created_at",""), reverse=True)
    st.markdown(f"**{len(filtered)} transaction(s) found**")
    st.markdown("---")

    if not filtered:
        st.info("No transactions match your filters.")
    else:
        for tx in filtered:
            tc = type_color(tx.get("type",""))
            desc = tx.get("description") or tx.get("category") or "—"
            cust = f" | 👤 {tx['customer_name']}" if tx.get("customer_name") else ""
            time_str = fmt_datetime(tx.get("created_at",""))
            transcript = tx.get("original_transcript","")
            t_line = f'<div style="color:#9ca3af;font-size:0.78rem;font-style:italic">🎙️ {transcript}</div>' if transcript else ""

            with st.container():
                col_info, col_amt, col_del = st.columns([4, 1.5, 0.5])
                with col_info:
                    st.markdown(f"""
                    <div class="tx-row {tc}">
                      <div style="flex:1">
                        <div style="font-weight:600;color:#111">{type_label(tx.get('type',''))}</div>
                        <div style="color:#6b7280;font-size:0.85rem">{desc}{cust}</div>
                        <div style="color:#9ca3af;font-size:0.75rem">{time_str}</div>
                        {t_line}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_amt:
                    st.markdown(f"<br><b>{paise_to_rupees(tx.get('amount_paise',0))}</b>", unsafe_allow_html=True)
                with col_del:
                    if st.button("🗑️", key=f"del_{tx['id']}", help="Delete this transaction"):
                        delete_transaction(tx["id"])
                        st.rerun()


# ── CUSTOMER LEDGER ────────────────────────────────────────────────────────────
elif st.session_state.active_tab == "customers":
    st.markdown("### 👥 Customer Credit Ledger")
    st.caption("Outstanding = money owed TO YOU (not yet collected)")

    outstanding = get_all_customers_outstanding()
    if not outstanding:
        st.info("No outstanding credit transactions yet.")
    else:
        total_outstanding = sum(outstanding.values())
        render_metric("Total Outstanding (All Customers)", paise_to_rupees(total_outstanding), "📋", "outstanding")
        st.markdown("---")

        search = st.text_input("🔍 Search customer", placeholder="Type name...")
        for name, paise in sorted(outstanding.items(), key=lambda x: -x[1]):
            if search and search.lower() not in name.lower():
                continue
            with st.expander(f"👤 {name}  —  {paise_to_rupees(paise)} outstanding"):
                txs = get_transactions_by_customer(name)
                for tx in sorted([t for t in txs if t.get("type") == "credit_given"],
                                  key=lambda t: t.get("created_at",""), reverse=True):
                    dt = fmt_datetime(tx.get("created_at",""))
                    desc = tx.get("description") or "Credit given"
                    st.markdown(f"- **{paise_to_rupees(tx['amount_paise'])}** — {desc} _{dt}_")

                templates = CONFIRMATION_TEMPLATES.get(lang_code(), CONFIRMATION_TEMPLATES["en-IN"])
                query_text = templates["query_credit"].format(customer=name, amount=paise_to_rupees(paise))

                if st.button(f"🔊 Speak Balance", key=f"tts_{name}"):
                    if SARVAM_API_KEY:
                        audio_b, err = text_to_speech(query_text, lang_code(), lang_speaker())
                        if audio_b:
                            st.markdown(play_audio_html(audio_b), unsafe_allow_html=True)
                        else:
                            st.error(f"TTS error: {err}")
                    else:
                        st.info(f"💬 [Demo] {query_text}")


# ── DAILY SUMMARY ──────────────────────────────────────────────────────────────
elif st.session_state.active_tab == "summary":
    st.markdown("### 📊 Daily Summary")

    totals = get_dashboard_totals()
    today_txs = get_transactions_today()
    outstanding = get_all_customers_outstanding()
    today_str = date.today().strftime("%A, %d %B %Y")

    st.markdown(f"**📅 {today_str}**")

    sales = paise_to_rupees(totals["sales_today_paise"])
    expenses = paise_to_rupees(totals["expenses_today_paise"])
    total_os = paise_to_rupees(totals["total_outstanding_paise"])
    net_paise = totals["sales_today_paise"] - totals["expenses_today_paise"]
    net = paise_to_rupees(abs(net_paise))
    arrow = "▲" if net_paise >= 0 else "▼"
    icon = "📈" if net_paise >= 0 else "📉"

    col1, col2 = st.columns(2)
    with col1:
        render_metric("Sales Today", sales, "💰")
        render_metric(f"Net Cash ({arrow})", f"{arrow} {net}", icon)
    with col2:
        render_metric("Expenses Today", expenses, "📦", "expense")
        render_metric("Total Outstanding", total_os, "🤝", "outstanding")

    st.markdown("---")
    templates = CONFIRMATION_TEMPLATES.get(lang_code(), CONFIRMATION_TEMPLATES["en-IN"])
    summary_text = templates["summary"].format(sales=sales, expenses=expenses, outstanding=total_os)
    st.info(f"📋 **Summary:** {summary_text}")

    if st.button("🔊 Speak Daily Summary", type="primary"):
        if SARVAM_API_KEY:
            with st.spinner("Generating speech..."):
                audio_b, err = text_to_speech(summary_text, lang_code(), lang_speaker())
            if audio_b:
                st.session_state.last_audio = audio_b
                st.session_state.last_confirmation_text = summary_text
                st.markdown(f"""
                <div class="audio-confirm">
                  <h4>🔊 Sarvam Daily Summary</h4>
                  <div class="audio-msg">{summary_text}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(play_audio_html(audio_b), unsafe_allow_html=True)
            else:
                st.error(f"TTS error: {err}")
        else:
            st.info(f"💬 [Demo Mode] {summary_text}")

    if st.session_state.last_audio and st.session_state.last_confirmation_text == summary_text:
        st.markdown("**🔄 Replay:**")
        st.markdown(play_audio_html(st.session_state.last_audio), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Transaction Breakdown")
    sale_c = sum(1 for t in today_txs if t.get("type") == "sale")
    exp_c = sum(1 for t in today_txs if t.get("type") == "expense")
    cred_c = sum(1 for t in today_txs if t.get("type") == "credit_given")
    bc1, bc2, bc3 = st.columns(3)
    with bc1: st.metric("Sales", sale_c)
    with bc2: st.metric("Expenses", exp_c)
    with bc3: st.metric("Credits Given", cred_c)

    st.markdown("---")
    st.markdown("#### Outstanding by Customer")
    if outstanding:
        for name, paise in sorted(outstanding.items(), key=lambda x: -x[1]):
            st.markdown(f"""
            <div class="customer-card">
              <span class="customer-name">👤 {name}</span>
              <span class="customer-amount">{paise_to_rupees(paise)}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No outstanding credits.")


# Footer
st.markdown("---")
st.markdown(
    "<center><small style='color:#9ca3af'>🏪 Dukaan Dost — Powered by Sarvam AI &nbsp;|&nbsp; "
    "Saaras v4 STT &nbsp;·&nbsp; Bulbul v4-Flash TTS &nbsp;·&nbsp; Sarvam-105B LLM</small></center>",
    unsafe_allow_html=True,
)
