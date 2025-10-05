import streamlit as st
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
import random
import threading
import os
import time
import pandas as pd

# -----------------------------
# Flask app setup
# -----------------------------
flask_app = Flask(__name__)
DB = "sampark.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            message TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# Simple chatbot logic
# -----------------------------
def generate_response(user_message):
    user_message = user_message.lower().strip()
    if "side effect" in user_message:
        return "🤒 Common side effects: nausea, vomiting, constipation. Try small meals + hydration."
    elif "dose" in user_message:
        return "💉 Wegovy is taken once weekly as prescribed. Don’t change dose without consulting your doctor."
    elif "storage" in user_message:
        return "🧊 Store in refrigerator (2–8°C). Keep away from light. Do not freeze."
    elif "doctor" in user_message:
        return "👩‍⚕️ You can contact your healthcare provider for personalized medical advice."
    else:
        options = [
            "💡 You can ask me about side effects, dose, or storage.",
            "👩‍⚕️ For medical advice, please consult your healthcare provider.",
            "📞 In case of emergency, contact your doctor immediately."
        ]
        return random.choice(options)

# -----------------------------
# Flask routes
# -----------------------------
@flask_app.route("/incoming", methods=["POST"])
def incoming_sms():
    try:
        sender = request.form.get("From")
        message = request.form.get("Body")
        response_text = generate_response(message)

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO messages (sender, message, response) VALUES (?, ?, ?)",
            (sender, message, response_text),
        )
        conn.commit()
        conn.close()

        resp = MessagingResponse()
        resp.message(response_text)
        return Response(str(resp), mimetype="application/xml")

    except Exception as e:
        return str(e), 500

@flask_app.route("/")
def index():
    return "✅ Flask WhatsApp Bot is running inside Streamlit!"

# -----------------------------
# Run Flask in background thread
# -----------------------------
def run_flask():
    port = int(os.environ.get("PORT", 8000))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

thread = threading.Thread(target=run_flask, daemon=True)
thread.start()

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Wegovy WhatsApp Bot", page_icon="💬", layout="centered")
st.title("💬 Wegovy (Semaglutide) Doctor Assistant Chatbot")
st.markdown("""
This Streamlit app runs a Flask server in the background to handle **Twilio WhatsApp** messages.  
Use the webhook URL below in your **Twilio Sandbox settings** 👇
""")

app_url = st.text_input(
    "🌐 Enter your Streamlit App URL (for webhook setup)",
    placeholder="https://nova-nordisk-wegovy-sampark.streamlit.app",
)
if app_url:
    st.code(f"{app_url}/incoming", language="bash")

st.divider()
st.subheader("📡 Live WhatsApp Message Monitor")

# Auto-refresh every few seconds
refresh_rate = st.slider("Auto-refresh every (seconds)", 5, 60, 10)

placeholder = st.empty()

while True:
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM messages ORDER BY id DESC LIMIT 10", conn)
    conn.close()

    with placeholder.container():
        if len(df) > 0:
            for _, row in df.iterrows():
                st.markdown(f"**📱 {row['sender']}** — {row['timestamp']}")
                st.write(f"**User:** {row['message']}")
                st.write(f"**Bot:** {row['response']}")
                st.markdown("---")
        else:
            st.info("No messages received yet.")
    time.sleep(refresh_rate)
