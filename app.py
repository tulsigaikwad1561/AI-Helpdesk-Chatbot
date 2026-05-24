# ============================================================
#  IT Helpdesk AI Chatbot - Flask Backend
#  app.py
#  
#  Stack: Flask + scikit-learn (TF-IDF + Naive Bayes)
#  Dataset: support_queries.csv
# ============================================================

import os
import uuid
import random
import datetime
import json
import pandas as pd
from flask import Flask, request, jsonify, render_template
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import numpy as np

# ── App init ──────────────────────────────────────────────
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# ── Global state ──────────────────────────────────────────
model_pipeline = None   # sklearn Pipeline (TF-IDF + NB)
model_info     = {}     # accuracy, classes, report
tickets_db     = []     # In-memory ticket store

# ── Intent → human label ──────────────────────────────────
INTENT_LABELS = {
    "password_reset": "Password Reset",
    "email_issue":    "Email Issue",
    "network_issue":  "Network Issue",
    "vpn_issue":      "VPN Issue",
    "printer_issue":  "Printer Issue",
    "software_issue": "Software Issue",
}

# ── Intent → priority mapping ─────────────────────────────
INTENT_PRIORITY = {
    "password_reset": "High",
    "email_issue":    "Medium",
    "network_issue":  "High",
    "vpn_issue":      "High",
    "printer_issue":  "Low",
    "software_issue": "Medium",
}

# ── Intent → SLA (hours) ──────────────────────────────────
INTENT_SLA = {
    "password_reset": 1,
    "email_issue":    4,
    "network_issue":  2,
    "vpn_issue":      2,
    "printer_issue":  8,
    "software_issue": 8,
}

# ── Automated response templates ─────────────────────────
RESPONSES = {
    "password_reset": [
        "I've detected a **password or account access issue**. I can trigger an automated Active Directory reset for your account.\n\n"
        "**Immediate steps:**\n"
        "1. Visit `selfservice.corp.internal/reset` to reset via the self-service portal.\n"
        "2. If your account is locked, IT will unlock it within **1 hour** (SLA).\n"
        "3. Ensure your new password meets: 8+ chars, uppercase, number, special character.\n\n"
        "A ticket has been created and assigned to the **Identity & Access Management** team.",

        "Your **account lockout or password reset** request has been received.\n\n"
        "**Auto-resolution steps initiated:**\n"
        "- Active Directory lookup: ✅ Account located\n"
        "- Lockout status check: 🔍 In progress\n"
        "- Reset email dispatched to your registered recovery address.\n\n"
        "Expected resolution: **Within 1 hour**. A ticket has been raised for tracking.",
    ],
    "email_issue": [
        "I've identified an **email or Outlook issue** with your account.\n\n"
        "**Diagnostic steps performed:**\n"
        "- Exchange server connectivity: ✅ Online\n"
        "- Mailbox health check: 🔍 Running\n"
        "- SMTP relay status: ✅ Operational\n\n"
        "**Try these steps while your ticket is being processed:**\n"
        "1. Restart Outlook and click **Send/Receive All Folders (F9)**.\n"
        "2. Check your mailbox quota: File → Account Information.\n"
        "3. If using webmail, try `mail.corp.internal`.\n\n"
        "Ticket escalated to the **Messaging & Collaboration** team. SLA: **4 hours**.",

        "Your **email service issue** has been logged.\n\n"
        "**Common fixes for your issue:**\n"
        "- Outlook not syncing: Remove and re-add your account under File → Account Settings.\n"
        "- Emails in Outbox: Check your internet connection and retry.\n"
        "- Quota full: Archive old emails to your local PST or online archive.\n\n"
        "An engineer from the **Email Support** team will contact you within **4 hours**.",
    ],
    "network_issue": [
        "A **network connectivity issue** has been detected at your workstation.\n\n"
        "**Auto-diagnostics initiated:**\n"
        "- Infrastructure status: ✅ Core network operational\n"
        "- DHCP server: ✅ Responding\n"
        "- DNS resolution: ✅ Healthy\n\n"
        "**Steps to try now:**\n"
        "1. Run `ipconfig /release` then `ipconfig /renew` in Command Prompt.\n"
        "2. Try `netsh winsock reset` and restart your PC.\n"
        "3. Check if the ethernet cable is securely plugged in.\n\n"
        "Ticket assigned to **Network Operations**. SLA: **2 hours**.",

        "Your **network issue** has been escalated to the NOC (Network Operations Centre).\n\n"
        "**Preliminary checks:**\n"
        "- Building network status: ✅ No outage reported\n"
        "- Your device IP: Being traced\n"
        "- Packet loss test: Queued\n\n"
        "Please try connecting via ethernet if on WiFi, or vice versa. A network engineer will assess your port/AP within **2 hours**.",
    ],
    "vpn_issue": [
        "Your **VPN connectivity issue** has been logged and is being assessed.\n\n"
        "**Common VPN fixes:**\n"
        "1. Disconnect and reconnect — sometimes resolves transient gateway issues.\n"
        "2. Check your MFA/OTP token is generating correctly.\n"
        "3. Reinstall the VPN client: Download from `software.corp.internal/vpn`.\n"
        "4. Ensure your device date/time is correct (VPN certificates are time-sensitive).\n\n"
        "**VPN Gateway Status:** ✅ Operational\n\n"
        "Ticket assigned to **Network Security** team. SLA: **2 hours**.",

        "I've flagged a **VPN authentication or connectivity failure**.\n\n"
        "**Automated checks:**\n"
        "- VPN gateway (gw-east-04): ✅ Reachable\n"
        "- Your VPN licence: ✅ Active\n"
        "- Certificate validity: 🔍 Checking\n\n"
        "If you're getting *Error 619*, your VPN client may need updating. Latest version: **6.3.4** — available on the IT portal.\n\n"
        "An engineer will contact you within **2 hours**.",
    ],
    "printer_issue": [
        "Your **printer issue** has been registered in the ITSM system.\n\n"
        "**Quick fixes to try:**\n"
        "1. Restart the printer and wait 30 seconds.\n"
        "2. Clear the print queue: Start → Printers → Right-click → Cancel All Documents.\n"
        "3. Reinstall the driver: `\\\\printserver\\drivers` on your network.\n"
        "4. For paper jams, open all access panels and gently remove jammed paper.\n\n"
        "Ticket assigned to the **Desktop Support** team. SLA: **8 hours** (next business day for non-critical).",

        "I've logged your **printer or printing issue**.\n\n"
        "**Remote diagnostics:**\n"
        "- Printer spooler service: 🔍 Checking on your device\n"
        "- Network printer connection: 🔍 Verifying\n"
        "- Toner/ink levels: Requires physical check\n\n"
        "Try setting the printer **offline then back online** via Control Panel → Printers. A technician will attend your desk within **8 business hours**.",
    ],
    "software_issue": [
        "Your **software installation or application issue** has been raised.\n\n"
        "**Self-service options:**\n"
        "1. Access approved software via the **Company Software Portal**: `apps.corp.internal`.\n"
        "2. For licence keys, submit a request via the IT Portal with manager approval.\n"
        "3. If an app is crashing, try running as Administrator or clearing the app cache.\n\n"
        "**Note:** Admin rights are required for installations — your request has been flagged for approval.\n\n"
        "Ticket raised with the **Software & Applications** team. SLA: **8 hours**.",

        "I've detected a **software or application issue** on your device.\n\n"
        "**Automated steps triggered:**\n"
        "- Software catalogue check: ✅ Completed\n"
        "- Licence availability: 🔍 Verifying\n"
        "- Compatibility check for your OS: 🔍 In progress\n\n"
        "For urgent needs, contact your line manager to expedite approval. Standard deployment time is **same business day** for approved software.\n\n"
        "Ticket assigned to **IT Service Desk**.",
    ],
}

# ── Ticket status workflow ────────────────────────────────
TICKET_STATUSES = ["Open", "In Progress", "Pending User", "Resolved", "Closed"]


# ============================================================
#  MODEL TRAINING
# ============================================================
def train_model():
    """Load CSV, train TF-IDF + Multinomial Naive Bayes pipeline."""
    global model_pipeline, model_info

    csv_path = os.path.join(os.path.dirname(__file__), "support_queries.csv")
    df = pd.read_csv(csv_path)
    df.dropna(inplace=True)
    df.columns = df.columns.str.strip()

    X = df["query"].astype(str).str.strip()
    y = df["intent"].astype(str).str.strip()

    # Train / test split (80 / 20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Pipeline: TF-IDF → Multinomial Naive Bayes
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),      # unigrams + bigrams
            max_features=5000,
            sublinear_tf=True,       # log-normalise TF
            stop_words="english",
        )),
        ("clf", MultinomialNB(alpha=0.3)),  # Laplace smoothing
    ])

    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred   = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report   = classification_report(y_test, y_pred, output_dict=True)

    model_pipeline = pipeline
    model_info = {
        "accuracy":       round(accuracy * 100, 2),
        "train_samples":  len(X_train),
        "test_samples":   len(X_test),
        "total_samples":  len(X),
        "classes":        list(pipeline.classes_),
        "vectorizer":     "TF-IDF (unigrams + bigrams, max_features=5000)",
        "classifier":     "Multinomial Naive Bayes (alpha=0.3)",
        "report":         report,
        "trained_at":     datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    print(f"\n{'='*55}")
    print(f"  Model trained successfully!")
    print(f"  Accuracy : {accuracy*100:.2f}%")
    print(f"  Samples  : {len(X)} (train={len(X_train)}, test={len(X_test)})")
    print(f"  Classes  : {list(pipeline.classes_)}")
    print(f"{'='*55}\n")


# ============================================================
#  PREDICTION HELPERS
# ============================================================
def predict_intent(text: str):
    """
    Returns dict with:
      intent, label, confidence, all_scores, response,
      priority, sla_hours, ticket_id, timestamp
    """
    if model_pipeline is None:
        raise RuntimeError("Model not trained yet.")

    # Class probabilities
    proba   = model_pipeline.predict_proba([text])[0]
    classes = model_pipeline.classes_
    idx     = int(np.argmax(proba))
    intent  = classes[idx]
    confidence = float(proba[idx])

    # All scores sorted desc
    all_scores = sorted(
        [{"intent": c, "label": INTENT_LABELS.get(c, c), "score": round(float(p) * 100, 2)}
         for c, p in zip(classes, proba)],
        key=lambda x: x["score"], reverse=True
    )

    # Pick a response template
    response = random.choice(RESPONSES.get(intent, ["I've logged your request. An agent will be in touch."]))

    return {
        "intent":      intent,
        "label":       INTENT_LABELS.get(intent, intent),
        "confidence":  round(confidence * 100, 2),
        "all_scores":  all_scores,
        "response":    response,
        "priority":    INTENT_PRIORITY.get(intent, "Medium"),
        "sla_hours":   INTENT_SLA.get(intent, 8),
    }


def generate_ticket_id():
    """Generate a Jira/ServiceNow-style ticket ID."""
    prefix = "INC"
    year   = datetime.datetime.now().year
    uid    = str(uuid.uuid4()).replace("-", "").upper()[:6]
    return f"{prefix}-{year}-{uid}"


# ============================================================
#  FLASK ROUTES
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ── POST /chat ─────────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    data    = request.get_json(force=True)
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Empty message"}), 400

    try:
        result = predict_intent(message)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Create ticket
    ticket_id = generate_ticket_id()
    now       = datetime.datetime.now()
    sla_due   = now + datetime.timedelta(hours=result["sla_hours"])

    ticket = {
        "id":          ticket_id,
        "user_query":  message,
        "intent":      result["intent"],
        "label":       result["label"],
        "priority":    result["priority"],
        "status":      "Open",
        "confidence":  result["confidence"],
        "created_at":  now.strftime("%Y-%m-%d %H:%M:%S"),
        "sla_due":     sla_due.strftime("%Y-%m-%d %H:%M:%S"),
        "sla_hours":   result["sla_hours"],
        "assignee":    assign_team(result["intent"]),
        "history": [
            {
                "status":    "Open",
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "note":      "Ticket created by AI Chatbot. Awaiting triage.",
            }
        ],
    }
    tickets_db.insert(0, ticket)

    return jsonify({
        "ticket_id":  ticket_id,
        "intent":     result["intent"],
        "label":      result["label"],
        "confidence": result["confidence"],
        "all_scores": result["all_scores"],
        "response":   result["response"],
        "priority":   result["priority"],
        "sla_hours":  result["sla_hours"],
        "assignee":   ticket["assignee"],
        "created_at": ticket["created_at"],
        "sla_due":    ticket["sla_due"],
    })


# ── GET /tickets ───────────────────────────────────────────
@app.route("/tickets", methods=["GET"])
def get_tickets():
    return jsonify(tickets_db)


# ── GET /tickets/<id> ──────────────────────────────────────
@app.route("/tickets/<ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    ticket = next((t for t in tickets_db if t["id"] == ticket_id), None)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    return jsonify(ticket)


# ── PUT /tickets/<id> — update status ─────────────────────
@app.route("/tickets/<ticket_id>", methods=["PUT"])
def update_ticket(ticket_id):
    ticket = next((t for t in tickets_db if t["id"] == ticket_id), None)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    data       = request.get_json(force=True)
    new_status = data.get("status")
    note       = data.get("note", f"Status updated to {new_status}")

    if new_status not in TICKET_STATUSES:
        return jsonify({"error": f"Invalid status. Must be one of: {TICKET_STATUSES}"}), 400

    ticket["status"] = new_status
    ticket["history"].append({
        "status":    new_status,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "note":      note,
    })

    return jsonify(ticket)


# ── GET /model/info ────────────────────────────────────────
@app.route("/model/info", methods=["GET"])
def get_model_info():
    if not model_info:
        return jsonify({"error": "Model not loaded"}), 503
    return jsonify(model_info)


# ── GET /model/test ────────────────────────────────────────
@app.route("/model/test", methods=["POST"])
def test_model():
    """Ad-hoc test: classify a custom query without creating a ticket."""
    data    = request.get_json(force=True)
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400
    try:
        result = predict_intent(message)
        return jsonify({
            "intent":     result["intent"],
            "label":      result["label"],
            "confidence": result["confidence"],
            "all_scores": result["all_scores"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GET /stats ─────────────────────────────────────────────
@app.route("/stats", methods=["GET"])
def get_stats():
    total = len(tickets_db)
    if total == 0:
        return jsonify({"total": 0, "by_intent": {}, "by_status": {}, "by_priority": {}})

    by_intent   = {}
    by_status   = {}
    by_priority = {}

    for t in tickets_db:
        by_intent[t["label"]]      = by_intent.get(t["label"], 0)      + 1
        by_status[t["status"]]     = by_status.get(t["status"], 0)     + 1
        by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1

    avg_conf = round(sum(t["confidence"] for t in tickets_db) / total, 2)

    return jsonify({
        "total":       total,
        "avg_confidence": avg_conf,
        "by_intent":   by_intent,
        "by_status":   by_status,
        "by_priority": by_priority,
    })


# ── Helpers ───────────────────────────────────────────────
def assign_team(intent: str) -> str:
    teams = {
        "password_reset": "Identity & Access Management",
        "email_issue":    "Messaging & Collaboration",
        "network_issue":  "Network Operations (NOC)",
        "vpn_issue":      "Network Security",
        "printer_issue":  "Desktop Support",
        "software_issue": "Software & Applications",
    }
    return teams.get(intent, "IT Service Desk")


# ============================================================
#  ENTRY POINT
# ============================================================
if __name__ == "__main__":
    print("\n🤖  IT Helpdesk AI Chatbot — Starting up...")
    train_model()
    print("🌐  Running on http://127.0.0.1:5000\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
