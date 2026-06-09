import streamlit as st
import json
import os
import re
from datetime import datetime
from rag_engine import generate_response, LLM_MODEL

# Set page config
st.set_page_config(
    page_title="Groww NXTLP - Facts-Only Mutual Fund Chatbot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS for premium Google Stitch styling, Google Fonts, and animations
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

/* Force App Background and Base Font */
.stApp {
    background-color: #f8fafc !important;
    background-image: radial-gradient(at 50% 0%, rgba(14, 165, 233, 0.12) 0px, transparent 50%),
                      radial-gradient(at 0% 100%, rgba(224, 242, 254, 0.15) 0px, transparent 50%) !important;
    font-family: 'Inter', sans-serif !important;
    color: #1e293b !important;
}

/* Hide Streamlit Headers, Footers, and Main Menus */
header {visibility: hidden !important;}
footer {visibility: hidden !important;}
#MainMenu {visibility: hidden !important;}

/* Center Block Container & Apply Glassmorphism Panel style */
div.block-container {
    max-width: 820px !important;
    padding: 3rem 2rem 8rem 2rem !important;
    margin: 0 auto !important;
    background: rgba(255, 255, 255, 0.85) !important;
    border: 1px solid rgba(14, 165, 233, 0.15) !important;
    border-radius: 24px !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    box-shadow: 0 20px 40px -15px rgba(14, 165, 233, 0.08) !important;
    margin-top: 30px !important;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid rgba(14, 165, 233, 0.12) !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 2rem !important;
}
section[data-testid="stSidebar"] * {
    color: #1e293b !important;
}

/* Selectbox styling */
div[data-testid="stSelectbox"] > label {
    color: #475569 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    margin-bottom: 8px !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    background-color: #ffffff !important;
    border: 1px solid rgba(14, 165, 233, 0.25) !important;
    border-radius: 10px !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
    color: #1e293b !important;
}

/* Metadata Card in Sidebar */
.meta-card {
    background: #ffffff !important;
    border: 1px solid rgba(14, 165, 233, 0.15) !important;
    border-radius: 16px !important;
    padding: 16px !important;
    margin-top: 20px !important;
    box-shadow: 0 10px 25px rgba(14, 165, 233, 0.05) !important;
}
.meta-card-title {
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    color: #0369a1 !important;
    margin-bottom: 12px !important;
    border-bottom: 1px solid rgba(14, 165, 233, 0.12) !important;
    padding-bottom: 8px !important;
}
.meta-item {
    font-size: 0.85rem !important;
    margin-bottom: 8px !important;
    color: #334155 !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
}
.meta-label {
    font-weight: 500 !important;
    color: #64748b !important;
}

/* Preset Action Chips as round pills */
div.stButton > button {
    background-color: #ffffff !important;
    color: #475569 !important;
    border: 1px solid rgba(14, 165, 233, 0.25) !important;
    border-radius: 20px !important;
    padding: 8px 16px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    transition: all 0.2s ease-in-out !important;
    text-align: center !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    box-shadow: 0 2px 4px rgba(14, 165, 233, 0.04) !important;
}
div.stButton > button:hover {
    background-color: rgba(14, 165, 233, 0.08) !important;
    border-color: #0284c7 !important;
    color: #0284c7 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15) !important;
}
div.stButton > button:active {
    transform: translateY(0) !important;
}

/* Chat Input bar layout */
div[data-testid="stChatInput"] {
    background-color: #ffffff !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(14, 165, 233, 0.25) !important;
    border-radius: 16px !important;
    box-shadow: 0 10px 30px rgba(14, 165, 233, 0.06) !important;
    margin-bottom: 20px !important;
    padding: 6px !important;
}
div[data-testid="stChatInput"] div {
    background-color: transparent !important;
}
div[data-testid="stChatInput"] textarea {
    color: #1e293b !important;
    -webkit-text-fill-color: #1e293b !important;
    background-color: transparent !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: #94a3b8 !important;
}
div[data-testid="stChatInput"] button {
    background-color: #0ea5e9 !important;
    color: white !important;
    border-radius: 10px !important;
    transition: background-color 0.2s !important;
}
div[data-testid="stChatInput"] button:hover {
    background-color: #0284c7 !important;
}

/* Chat bubble structures */
.chat-bubble-user {
    background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
    color: #ffffff !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 12px 18px !important;
    margin-bottom: 16px !important;
    max-width: 75% !important;
    margin-left: auto !important;
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.15) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    text-align: left !important;
}
.chat-bubble-bot {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border-radius: 18px 18px 18px 4px !important;
    padding: 12px 18px !important;
    margin-bottom: 16px !important;
    max-width: 75% !important;
    margin-right: auto !important;
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
    border: 1px solid rgba(14, 165, 233, 0.12) !important;
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.04) !important;
}
.chat-sender {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: #0284c7 !important;
    margin-bottom: 6px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
.chat-sender-user {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: #e0f2fe !important;
    margin-bottom: 6px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    text-align: right !important;
}
.chat-message-content {
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
    white-space: pre-wrap !important;
}
.chat-bubble-bot a {
    color: #0284c7 !important;
    text-decoration: none !important;
    font-weight: 500 !important;
    border-bottom: 1px dashed rgba(2, 132, 199, 0.4) !important;
    transition: all 0.2s !important;
}
.chat-bubble-bot a:hover {
    color: #0369a1 !important;
    border-bottom-style: solid !important;
}
.chat-footer {
    display: flex !important;
    justify-content: space-between !important;
    font-size: 0.72rem !important;
    color: #64748b !important;
    margin-top: 10px !important;
    padding-top: 6px !important;
    border-top: 1px solid rgba(14, 165, 233, 0.1) !important;
}

/* Header design */
.header-container {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(14, 165, 233, 0.1);
}
.header-main {
    display: flex;
    align-items: center;
    gap: 12px;
}
.header-title {
    font-family: 'Outfit', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    margin: 0 !important;
    letter-spacing: -0.02em;
}
.header-subtitle {
    font-size: 0.92rem;
    color: #475569;
    margin-top: 6px;
}
.header-logo {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    filter: drop-shadow(0 2px 4px rgba(14, 165, 233, 0.15));
}
.header-logo:hover {
    transform: translateY(-2px) scale(1.08);
    filter: drop-shadow(0 8px 16px rgba(14, 165, 233, 0.3));
}

/* Compact Disclaimer Alert */
.disclaimer-mini {
    background: rgba(14, 165, 233, 0.04) !important;
    border: 1px solid rgba(14, 165, 233, 0.15) !important;
    border-left: 3px solid #0ea5e9 !important;
    padding: 6px 12px !important;
    border-radius: 8px !important;
    color: #475569 !important;
    font-size: 0.8rem !important;
    margin-bottom: 16px !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}
.disclaimer-icon-mini {
    font-size: 0.9rem !important;
}
.disclaimer-text-mini {
    line-height: 1.3 !important;
}
.disclaimer-text-mini strong {
    color: #0369a1 !important;
}

.preset-section-title {
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: #475569 !important;
    margin-bottom: 16px !important;
    margin-top: 20px !important;
}

/* Centered clear chat container */
.clear-container {
    text-align: center;
    margin-top: 24px;
}
.clear-container div.stButton > button {
    background-color: rgba(239, 68, 68, 0.06) !important;
    color: #ef4444 !important;
    border: 1px solid rgba(239, 68, 68, 0.15) !important;
    border-radius: 12px !important;
    width: auto !important;
    margin: 0 auto !important;
    padding: 6px 16px !important;
}
.clear-container div.stButton > button:hover {
    background-color: rgba(239, 68, 68, 0.15) !important;
    border-color: #ef4444 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2) !important;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #f8fafc;
}
::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
</style>
""", unsafe_allow_html=True)

# Helper: Load scraped data
def load_scheme_metadata():
    json_path = os.path.join("data", "scraped_data.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading scraped_data.json: {e}")
    return []

schemes_data = load_scheme_metadata()

# Sidebar with supported schemes and metadata display control
st.sidebar.markdown("### 📋 Supported Schemes")
if schemes_data:
    # Build list of unique options
    scheme_names = []
    scheme_by_name = {}
    for scheme in schemes_data:
        content = scheme["content"]
        name_match = re.search(r"^(?:# Scheme Name:|# ETF Name:)\s*(.*)$", content, re.MULTILINE)
        name = name_match.group(1).strip() if name_match else scheme["title"].split(" - ")[0]
        scheme_names.append(name)
        scheme_by_name[name] = scheme

    selected_scheme_name = st.sidebar.selectbox("Select a scheme to view metadata card:", scheme_names)
    selected_scheme = scheme_by_name[selected_scheme_name]
    
    # Parse fields for sidebar card
    content = selected_scheme["content"]
    
    def parse_field(pattern, text):
        match = re.search(pattern, text, re.MULTILINE)
        return match.group(1).strip() if match else "N/A"
        
    category = parse_field(r"^Category:\s*(.*)$", content)
    nav = parse_field(r"^Current NAV:\s*(.*)$", content)
    aum = parse_field(r"^AUM \(Fund Size\):\s*(.*)$", content)
    expense_ratio = parse_field(r"^Expense Ratio:\s*(.*)$", content)
    exit_load = parse_field(r"^Exit Load:\s*(.*)$", content)
    managers = parse_field(r"^Fund Managers:\s*(.*)$", content)
    
    # Render Sidebar Card
    st.sidebar.markdown(f"""
    <div class="meta-card">
        <div class="meta-card-title">{selected_scheme_name}</div>
        <div class="meta-item"><span class="meta-label">Category</span> <span>{category}</span></div>
        <div class="meta-item"><span class="meta-label">Current NAV</span> <span>{nav}</span></div>
        <div class="meta-item"><span class="meta-label">Fund Size (AUM)</span> <span>{aum}</span></div>
        <div class="meta-item"><span class="meta-label">Expense Ratio</span> <span>{expense_ratio}</span></div>
        <div class="meta-item"><span class="meta-label">Exit Load</span> <span>{exit_load}</span></div>
        <div class="meta-item"><span class="meta-label">Managers</span> <span style="text-align: right; max-width: 60%;">{managers}</span></div>
        <div style="margin-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 12px; text-align: center;">
            <a href="{selected_scheme['url']}" target="_blank" style="color: #38bdf8; font-weight: 600; text-decoration: none; font-size: 0.85rem;">View Official Page ↗</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.warning("No scraped scheme metadata found. Please run the scraper first.")

# Header Layout with logo, subtitle and compact disclaimer alert
st.markdown("""
<div class="header-container">
    <div class="header-main">
        <svg class="header-logo" viewBox="0 0 44 44" width="40" height="40" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="44" height="44" rx="12" fill="rgba(0, 208, 156, 0.08)"/>
          <path d="M12 28V24C12 22.8954 12.8954 22 14 22C15.1046 22 16 22.8954 16 24V28" stroke="url(#logoGrad)" stroke-width="3.5" stroke-linecap="round"/>
          <path d="M20 28V18C20 16.8954 20.8954 16 22 16C23.1046 16 24 16.8954 24 18V28" stroke="url(#logoGrad)" stroke-width="3.5" stroke-linecap="round"/>
          <path d="M28 28V12C28 10.8954 28.8954 10 30 10C31.1046 10 32 10.8954 32 12V28" stroke="url(#logoGrad)" stroke-width="3.5" stroke-linecap="round"/>
          <path d="M14 22L22 16L30 10" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-dasharray="1.5 3"/>
          <circle cx="30" cy="10" r="3" fill="#00d09c"/>
          <defs>
            <linearGradient id="logoGrad" x1="12" y1="28" x2="32" y2="10" gradientUnits="userSpaceOnUse">
              <stop stop-color="#00d09c"/>
              <stop offset="1" stop-color="#0ea5e9"/>
            </linearGradient>
          </defs>
        </svg>
        <h1 class="header-title">Mutual Fund FAQ Assistant</h1>
    </div>
    <div class="header-subtitle">Strictly facts-only chatbot answering queries using verified source documents</div>
</div>

<div class="disclaimer-mini">
    <span class="disclaimer-icon-mini">⚠️</span>
    <div class="disclaimer-text-mini"><strong>Facts-Only. No Investment Advice.</strong> Responses are strictly objective and retrieved from official AMC sources.</div>
</div>
""", unsafe_allow_html=True)

# Helper function to convert markdown responses to clean HTML-styled layouts
def format_bot_response(text):
    # Replaces markdown links [Display](URL) with HTML anchors
    html_text = re.sub(
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',
        r'<a href="\2" target="_blank">\1</a>',
        text
    )
    
    # Extract last updated date if available in footer format
    last_updated = datetime.now().strftime("%Y-%m-%d")
    footer_match = re.search(r'Last updated from sources:\s*([\d-]+)', text, re.IGNORECASE)
    if footer_match:
        last_updated = footer_match.group(1)
        # Strip the last updated notice from the main bubble contents to avoid duplicate footers
        html_text = re.sub(r'\*?Last updated from sources:.*', '', html_text, flags=re.IGNORECASE).strip()
        # Clean trailing asterisks
        html_text = html_text.rstrip('*').strip()

    bubble_html = f"""
    <div class="chat-bubble-bot">
        <div class="chat-sender">Assistant</div>
        <div class="chat-message-content">{html_text}</div>
        <div class="chat-footer">
            <span>Model: {LLM_MODEL}</span>
            <span>Last updated: {last_updated}</span>
        </div>
    </div>
    """
    return bubble_html

def format_user_response(text):
    bubble_html = f"""
    <div class="chat-bubble-user">
        <div class="chat-sender-user">You</div>
        <div class="chat-message-content">{text}</div>
    </div>
    """
    return bubble_html

# Initialize chat session states
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show welcome page/Preset click action buttons if chat is fresh/empty
if not st.session_state.messages:
    st.markdown("<div class='preset-section-title'>💡 Click a sample question to try the RAG Engine:</div>", unsafe_allow_html=True)
    
    presets = [
        ("📋 Exit load HDFC Small Cap", "What is the exit load of HDFC Small Cap Fund?"),
        ("👨‍💼 Manager of HDFC Mid Cap", "Who is the manager of HDFC Mid Cap Fund?"),
        ("💰 NAV Groww Defence ETF", "What is the current nav of Groww Nifty India Defence ETF?"),
        ("⚖️ Advisory Test (Refusal)", "Should I invest in HDFC Large Cap Fund?"),
        ("🔒 PII Block Test", "My PAN is ABCDE1234F, show my details.")
    ]
    
    cols = st.columns(len(presets))
    for idx, (label, question) in enumerate(presets):
        if cols[idx].button(label, key=f"btn_{idx}"):
            # Add message and prompt answer generation
            st.session_state.messages.append({"role": "user", "content": question})
            with st.spinner("Retrieving facts & validating..."):
                response = generate_response(question)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

# Render Conversational Chat Log History
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(format_user_response(msg["content"]), unsafe_allow_html=True)
    else:
        st.markdown(format_bot_response(msg["content"]), unsafe_allow_html=True)

# Floating Chat Input Box at the bottom of the viewport
user_input = st.chat_input("Ask a facts-only question about HDFC or Groww schemes...")
if user_input:
    # Append User Message to conversation flow
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Trigger RAG context lookup and prompt answers
    with st.spinner("Retrieving facts & validating..."):
        response = generate_response(user_input)
        
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Render Clear Conversation Button under log lists
if st.session_state.messages:
    st.markdown('<div class="clear-container">', unsafe_allow_html=True)
    if st.button("Clear Conversation", key="clear_btn"):
        st.session_state.messages = []
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
