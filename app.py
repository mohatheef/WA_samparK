from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
import random
import os

app = Flask(__name__)
DB = "sampark.db"

# -----------------------------
# Database setup
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            message TEXT,
            response TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# Helper response generator
# -----------------------------
def generate_response(user_message):
    user_message = user_message.lower().strip()
    if "side effect" in user_message:
        return "🤒 Common side effects: nausea, vomiting, constipation. Try small meals + hydration."
    elif "dose" in user_message:
        return "💉 Wegovy is taken once weekly as prescribed. Don’t change dose without consulting your doctor."
    elif "storage" in user_message:
        return "🧊 Store in refrigerator (2–8°C). Keep away from light. Do not freeze."
    else:
        options = [
            "💡 You can ask me about side effects, dose, or storage.",
            "👩‍⚕️ For medical advice, please consult your healthcare provider.",
            "📞 In case of emergency, contact your doctor immediately."
        ]
        return random.choice(options)

# -----------------------------
# WhatsApp webhook
# -----------------------------
@app.route("/incoming", methods=["POST"])
def incoming_sms():
    try:
        sender = request.form.get("From")
        message = request.form.get("Body")
        response_text = generate_response(message)

        # Save to DB
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender, message, response) VALUES (?, ?, ?)",
                  (sender, message, response_text))
        conn.commit()
        conn.close()

        # Twilio reply
        resp = MessagingResponse()
        resp.message(response_text)
        return Response(str(resp), mimetype="application/xml")

    except Exception as e:
        return str(e), 500

# -----------------------------
# Root endpoint
# -----------------------------
@app.route("/")
def index():
    return "✅ Flask WhatsApp Bot is running!"

# -----------------------------
# Run app (dynamic port fix)
# -----------------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
