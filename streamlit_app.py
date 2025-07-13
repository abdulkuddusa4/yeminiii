import streamlit as st
import base64
from datetime import datetime
import os
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from openai import OpenAI
from pinecone import Pinecone
import uuid

# Load API keys from environment (or set directly)
os.environ["OPENAI_API_KEY"] = "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"
os.environ["PINECONE_API_KEY"] = "pcsk_5tsJkP_uNsvdQ8DnawJypKfKzbxZRU1Cb5o4C2i392CYQDhX5jUdBJnPJtrwsFYrwCVMx" # Replace with your actual Pinecone API key

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Setup embeddings + vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PineconeVectorStore.from_existing_index(
    index_name="rag-assistant", # Ensure this Pinecone index name is correct
    embedding=embeddings
)

# Page Config
st.set_page_config(
    page_title="SingAI Unified Government Chatbot",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'input_key' not in st.session_state:
    st.session_state.input_key = str(uuid.uuid4())
if 'last_user_input_content' not in st.session_state:
    st.session_state.last_user_input_content = ""

# --- Load and encode all images ---
logo_base64 = ""
try:
    with open("logo.png", "rb") as img_file: # Assuming this is your small lion logo
        logo_base64 = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    st.warning("Logo file 'logo.png' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"An error occurred while loading the logo: {e}")

header_image_base64 = ""
try:
    with open("image_204982.png", "rb") as img_file: # "UNIFYING GOVERNMENT INTELLIGENCE" image
        header_image_base64 = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    st.warning("Header image 'image_204982.png' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"Error loading header image: {e}")

brain_image_base64 = ""
try:
    with open("image_204563.png", "rb") as img_file: # Brain image for background
        brain_image_base64 = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    st.warning("Brain image 'image_204563.png' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"Error loading brain image: {e}")

# --- Custom CSS ---
st.markdown(f"""
<style>
    /* Main app styling with transparent brain image background */
    .stApp {{
        background: linear-gradient(135deg, rgba(26, 43, 43, 0.8) 0%, rgba(42, 64, 48, 0.8) 50%, rgba(26, 53, 53, 0.8) 100%);
        min-height: 100vh;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        position: relative; /* Needed for pseudo-element positioning */
    }}

    .stApp::before {{
        content: "";
        background-image: url('data:image/png;base64,{brain_image_base64}');
        background-repeat: no-repeat;
        background-position: center center;
        background-size: cover;
        position: fixed; /* Ensure it covers the whole background and doesn't scroll */
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.3; /* Adjust this value for desired transparency */
        z-index: -1; /* Place it behind the main content */
    }}

    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Chat container */
    .chat-container {{
        max-width: 950px;
        margin: auto;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 90%;
        height: 80vh;
        display: flex;
        flex-direction: column;
        background: rgba(26, 43, 43, 0.9); /* Keep this opaque enough for chat content readability */
        border: 2px solid rgba(42, 64, 48, 0.4);
        border-radius: 25px;
        box-shadow: 0 0 50px rgba(42, 64, 48, 0.3),
                    inset 0 0 25px rgba(42, 64, 48, 0.15);
        overflow: hidden;
        backdrop-filter: blur(10px);
    }}

    /* Header */
    .chat-header {{
        background: linear-gradient(90deg, rgba(42, 64, 48, 0.4) 0%, rgba(26, 53, 53, 0.4) 100%);
        padding: 25px;
        text-align: center;
        border-bottom: 2px solid rgba(42, 64, 48, 0.5);
        position: relative;
    }}

    /* New header image styling */
    .header-image {{
        max-width: 80%; /* Adjust size as needed */
        height: auto;
        display: block; /* Remove extra space below image */
        margin: 0 auto; /* Center the image */
        filter: drop-shadow(0 0 10px rgba(255, 255, 0, 0.7)); /* Subtle glow for the yellow text */
    }}

    /* Messages area */
    .messages-area {{
        flex: 1;
        overflow-y: auto;
        padding: 25px 35px;
        display: flex;
        flex-direction: column;
        gap: 20px;
        background: rgba(26, 43, 43, 0.8);
        min-height: 0;
    }}

    /* Message bubbles */
    .message {{
        max-width: 75%;
        padding: 18px 25px;
        border-radius: 20px;
        position: relative;
        animation: fadeIn 0.6s ease-out;
        font-size: 17px;
        line-height: 1.6;
        color: #E0E7E9;
    }}

    .user-message {{
        align-self: flex-start;
        background: linear-gradient(135deg, rgba(46, 74, 74, 0.6) 0%, rgba(34, 51, 34, 0.6) 100%);
        border: 1px solid rgba(46, 74, 74, 0.7);
        box-shadow: 0 6px 20px rgba(46, 74, 74, 0.5);
        margin-right: auto;
        margin-left: 0;
    }}

    .bot-message {{
        align-self: flex-end;
        background: linear-gradient(135deg, rgba(64, 96, 64, 0.6) 0%, rgba(46, 74, 74, 0.6) 100%);
        border: 1px solid rgba(64, 96, 64, 0.7);
        box-shadow: 0 6px 20px rgba(64, 96, 64, 0.5);
        margin-left: auto;
        margin-right: 0;
    }}

    .message-time {{
        font-size: 11px;
        color: rgba(255, 255, 255, 0.5);
        margin-top: 10px;
    }}

    .user-message .message-time {{
        text-align: right;
    }}

    .bot-message .message-time {{
        text-align: left;
    }}

    /* Welcome message */
    .welcome-message {{
        text-align: center;
        margin: auto;
        color: #E0E7E9;
        padding: 30px;
    }}

    .welcome-message h2 {{
        font-size: 30px;
        margin-bottom: 15px;
        color: #E0E7E9;
        font-weight: 700;
        letter-spacing: 1.5px;
    }}

    .welcome-message p {{
        font-size: 20px;
        color: #C0C8CA;
        font-weight: 500;
        line-height: 1.7;
    }}

    /* Input area - now a flex container for input and button */
    .input-container {{
        padding: 25px 30px;
        background: rgba(26, 43, 43, 0.95);
        border-top: 2px solid rgba(42, 64, 48, 0.5);
        display: flex;
        align-items: center;
        gap: 15px;
    }}

    /* Target Streamlit's div wrappers for flex behavior */
    .stTextInput {{
        flex-grow: 1;
        min-width: 150px;
    }}

    .stButton {{
        flex-shrink: 0;
    }}

    /* Custom input styling with 3D effect */
    .stTextInput > div > div > input {{
        background: rgba(34, 51, 34, 0.9) !important;
        border: 2px solid rgba(64, 96, 64, 0.6) !important;
        color: #E0E7E9 !important;
        border-radius: 25px !important;
        padding: 18px 25px !important;
        font-size: 17px !important;
        transition: all 0.4s ease !important;
        /* 3D/inset shading */
        box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.4), /* Dark shadow for top-left (depth) */
                    inset -2px -2px 5px rgba(255, 255, 255, 0.1); /* Light shadow for bottom-right (highlight) */
        caret-color: white !important; /* ✨ FIX FOR WHITE CURSOR ✨ */
    }}

    /* Fix for red border and enhanced 3D/glow on focus */
    .stTextInput > div > div > input:focus,
    .stTextInput > div > div > input:focus-visible, /* Target this specifically */
    .stTextInput > div > div > input:active {{ /* And this for good measure */
        border-color: rgba(64, 96, 64, 0.9) !important; /* Keeps the green border if you want it */
        box-shadow: 0 0 30px rgba(255, 255, 255, 0.8), /* ✨ FIX FOR WHITE OUTER GLOW ON FOCUS ✨ */
                    inset 2px 2px 8px rgba(0, 0, 0, 0.6), /* Deeper dark inset */
                    inset -2px -2px 8px rgba(255, 255, 255, 0.15) !important; /* Brighter light inset */
        outline: none !important; /* Crucial for removing default outlines */
    }}

    .stTextInput > div > div > input::placeholder {{
        color: rgba(255, 255, 255, 0.4) !important;
    }}

    /* Button styling */
    .stButton > button {{
        background: linear-gradient(90deg, #4CAF50 0%, #388E3C 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 18px 35px !important; /* Adjusted vertical padding to match text input */
        font-size: 17px !important;
        font-weight: 700 !important;
        letter-spacing: 1.2px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 5px 25px rgba(50, 150, 50, 0.5) !important;
        cursor: pointer;
    }}

    .stButton > button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 30px rgba(50, 150, 50, 0.7) !important;
        filter: brightness(1.1);
    }}

    /* Scrollbar styling */
    .messages-area::-webkit-scrollbar {{
        width: 12px;
    }}

    .messages-area::-webkit-scrollbar-track {{
        background: rgba(0, 0, 0, 0.3);
        border-radius: 10px;
    }}

    .messages-area::-webkit-scrollbar-thumb {{
        background: linear-gradient(180deg, #4CAF50 0%, #388E3C 100%);
        border-radius: 10px;
        border: 2px solid rgba(0,0,0,0.1);
    }}

    /* Animation */
    @keyframes fadeIn {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    /* Logo styling - Fixed at top-left */
    .logo-container {{
        position: fixed; /* Keep logo fixed on scroll */
        top: 25px;
        left: 25px;
        z-index: 1000;
        opacity: 0.95;
    }}

    /* Glow effect for logo */
    .logo-glow {{
        filter: drop-shadow(0 0 20px rgba(64, 96, 64, 0.8));
    }}

    /* Typing indicator for "..." */
    .message.bot-message .typing-dots {{
        display: inline-flex;
        align-items: center;
    }}

    .message.bot-message .typing-dots span {{
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #C0C8CA;
        border-radius: 50%;
        margin: 0 2px;
        animation: typing 1.4s infinite ease-in-out;
    }}

    .message.bot-message .typing-dots span:nth-child(1) {{
        animation-delay: 0s;
    }}
    .message.bot-message .typing-dots span:nth-child(2) {{
        animation-delay: 0.2s;
    }}
    .message.bot-message .typing-dots span:nth-child(3) {{
        animation-delay: 0.4s;
    }}

    @keyframes typing {{
        0%, 80%, 100% {{
            transform: translateY(0);
            opacity: 0.6;
        }}
        40% {{
            transform: translateY(-5px);
            opacity: 1;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# --- Display small lion logo (fixed) ---
if logo_base64:
    st.markdown(f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_base64}" width="80" class="logo-glow">
        </div>
    """, unsafe_allow_html=True)

# Main chat interface
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# --- Header with new image ---
st.markdown(f"""
    <div class="chat-header">
        {'<img src="data:image/png;base64,' + header_image_base64 + '" class="header-image">' if header_image_base64 else '<h1 class="chat-title">SingAI Unified Government Chatbot</h1><p class="chat-subtitle">CPF • HDB • Singapore Public Policy</p>'}
    </div>
""", unsafe_allow_html=True)

# Messages display area
st.markdown('<div class="messages-area">', unsafe_allow_html=True)

# Display conversation or welcome message
if not st.session_state.conversation:
    st.markdown("""
        <div class="welcome-message">
            <h2>Welcome to SingAI</h2>
            <p>Ask me anything about CPF, HDB, or public policies</p>
        </div>
    """, unsafe_allow_html=True)
else:
    for message in st.session_state.conversation:
        message_class = "user-message" if message["role"] == "user" else "bot-message"
        st.markdown(f"""
            <div class="message {message_class}">
                <div>{message["content"]}</div>
                <div class="message-time">{message["timestamp"]}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Input area
st.markdown('<div class="input-container">', unsafe_allow_html=True)

user_input = st.text_input(
    "Type your message",
    placeholder="Ask about CPF, HDB, or public policies...",
    key=st.session_state.input_key,
    label_visibility="collapsed"
)

send_button = st.button("Send", key="send_button_fixed")

st.markdown('</div>', unsafe_allow_html=True) # Close input-container

# --- Handle User Message Logic ---
# Check if send button is clicked OR if Enter key was pressed in the text input
# This logic ensures the input clears and the message is processed.
if send_button or (user_input and user_input.strip() != "" and user_input != st.session_state.last_user_input_content):
    if user_input.strip() != "":
        timestamp = datetime.now().strftime("%I:%M %p")

        # Add user message
        st.session_state.conversation.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })

        # Add 'typing...' bubble
        st.session_state.conversation.append({
            "role": "bot",
            "content": '<div class="typing-dots"><span></span><span></span><span></span></div>',
            "timestamp": datetime.now().strftime("%I:%M %p")
        })

        # Generate a new unique key for the text input to clear it
        st.session_state.input_key = str(uuid.uuid4())
        # Reset last_user_input_content to allow new identical inputs after clearing
        st.session_state.last_user_input_content = ""
        st.rerun()

# --- RAG Pipeline ---
if st.session_state.conversation and st.session_state.conversation[-1]["role"] == "bot" and '<div class="typing-dots">' in st.session_state.conversation[-1]["content"]:
    user_msg = next((m["content"] for m in reversed(st.session_state.conversation) if m["role"] == "user"), "")

    try:
        search_results = vectorstore.similarity_search(user_msg, k=5)
        context = "\n".join([doc.page_content for doc in search_results])

        if not context.strip():
            prompt = f"""
You are a helpful assistant for Singapore government policies (CPF, HDB, Public Policy).
The user asked: "{user_msg}"
I could not find specific relevant information in my knowledge base for this query.
Please respond politely, stating that you may not have information on this specific topic or suggesting they try rephrasing their question, while still being helpful within your domain. Do not make up information.
            """
        else:
            prompt = f"""
You are a highly intelligent assistant capable of analyzing complex queries related to Singapore government policies (CPF, HDB, Public Policy). When you receive a question, first analyze it to determine whether it requires:

1. A factual, concise answer (e.g., direct data or information based on the given context).
2. An elaborate discussion (e.g., a broader explanation, making relations between various topics, or a detailed understanding of the subject).

If the query requires an elaborate discussion, you should connect the context provided with other related topics, offering a comprehensive response. For example, if the query relates to housing rules in the context of the Factories Act or other regulations, you can reference the specific sections (e.g., Section 88 of the Factories Act) or any relevant reference numbers in your response. Discuss the topic thoroughly, but stay focused on answering the user's query.

If the query only requires factual information, respond with precision and clarity based on the context, and ensure to include any relevant reference, such as section numbers, rule numbers, or regulatory references.

If a section, rule, or reference number is mentioned in the context, make sure to incorporate it into your response to add credibility and clarity.

Context:
{context}

Question:
{user_msg}

Answer:
"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for Singapore government policies."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature= 0.5
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"⚠️ Error generating response: {str(e)} Please try again or rephrase your question."

    # Remove the typing indicator message
    if st.session_state.conversation and st.session_state.conversation[-1]["role"] == "bot" and '<div class="typing-dots">' in st.session_state.conversation[-1]["content"]:
        st.session_state.conversation.pop()

    # Add the actual bot response
    st.session_state.conversation.append({
        "role": "bot",
        "content": answer,
        "timestamp": datetime.now().strftime("%I:%M %p")
    })
    st.rerun()

# Auto-scroll to bottom script (outside chat-container)
st.markdown("""
<script>
    const messagesArea = document.querySelector('.messages-area');
    if (messagesArea) {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }
</script>
""", unsafe_allow_html=True)