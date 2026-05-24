# 🤖 Aegis ITSM – AI-Powered IT Helpdesk & Diagnostics Hub
> **Academic Project Submission | Specialization: MBA in Artificial Intelligence & Digital Transformation**

Aegis ITSM is a high-fidelity, industry-grade **AI-powered IT Helpdesk Chatbot & Service Management (ITSM) web application**. It leverages a machine learning pipeline (`scikit-learn` TF-IDF + Multinomial Naive Bayes) trained on historical support datasets to automatically classify user IT incidents, estimate confidence, routing to designated support groups, calculate SLA target resolution deadlines, and simulate ticket lifecycle state transitions (ServiceNow/Jira-style).

---

## 🎯 Key Project Features

### 1. **Persistent Live AI Chat Desk**
* Modern chat client with micro-animations, loading/typing indicators, and auto-scrolling.
* Direct AI chatbot feedback with troubleshooting guidelines based on incident routing.
* Automated ticket generation system yielding a unique tracker code (e.g., `INC-2026-X8F9`) directly attached inside the chat thread with a **"Manage Ticket"** redirection hook.

### 2. **Real-Time Inference HUD (Heads-Up Display)**
* Watch the Naive Bayes model calculate outputs in real time on the right-hand panel of the chat.
* Displays: **Classified Intent, Confidence Score (%) with glowing progress bars, Target Urgency Priority, SLA Target, and Assigned Support Group**.
* Renders a live sorted probability breakdown for **all 6 intent classes** (every text token typed triggers custom inference).

### 3. **Interactive ITSM Ticket Desk (Jira/ServiceNow Simulator)**
* Searchable and filterable dashboard listing all logged active incidents.
* Timeline-based **Lifecycle Audit History** logging who updated the state, when, and comments.
* State Transition Sandbox allowing specialists to transition tickets through: `Open` ➔ `In Progress` ➔ `Pending User` ➔ `Resolved` ➔ `Closed`.

### 4. **Model Diagnostics & Viva Sandbox (Viva Specialization)**
* Displays actual **scikit-learn Classification Report metrics** (Precision, Recall, F1-Score, Support) in a clean table loaded from validation splits.
* Showcases model parameters: TF-IDF vectorizer details, Multinomial Naive Bayes configuration, validation splits, and exact accuracy levels.
* **Test Arena**: An isolated playground that allows examiners to type custom phrases (e.g., *"my device is on fire"* or *"can't access database"*) and inspect the raw probability distributions *without* logging a ticket.

### 5. **ITSM Analytics Panel**
* High-level executive KPIs (Average Confidence, Incident Volume, deflection metrics).
* Interactive bar charts indicating ticket distribution by **Intent Category, Urgency Priority, and Workflow Status**.

---

## 🏗️ Architecture & Technology Stack

```
                     +---------------------------------------+
                     |    Web Browser (HTML5/CSS3/ES6 JS)    |
                     +---+-------------------------------+---+
                         |                               ^
               POST /chat| (User input text)             | JSON Response
               GET /stats| (Analytics)                   | (Inference, Tickets,
               GET /model| (Diagnostics)                 |  Model parameters)
                         v                               |
                     +---+-------------------------------+---+
                     |       Python Flask REST Server        |
                     +---+-------------------------------+---+
                         |                               |
                         | Train / Predict               | In-Memory DB
                         v                               v
             +-----------+-----------+       +-----------+-----------+
             | scikit-learn Pipeline |       |  Tickets Data Store   |
             | TF-IDF + Naive Bayes  |       |       (Python list)   |
             +-----------+-----------+       +-----------------------+
                         |
                         | Reads
                         v
             +-----------+-----------+
             |  support_queries.csv  |
             |   (120+ IT incidents) |
             +-----------------------+
```

* **Frontend:** Single-Page Application, Vanilla HTML5, Vanilla CSS3 (Glassmorphism theme, Inter/Outfit typography, HSL variables), Vanilla ES6 JavaScript (Fetch API, DOM controllers).
* **Backend:** Python Flask framework (RESTful service).
* **Machine Learning & NLP Pipeline:**
  * **Text Preprocessing:** TF-IDF (Term Frequency-Inverse Document Frequency) Vectorizer, capturing **unigrams & bigrams**, normalized sublinear TF scaling, and custom English stop-words filtering.
  * **Classifier:** `MultinomialNB` (Multinomial Naive Bayes) with Laplace smoothing (`alpha=0.3`) to prevent zero-probability issues for new keywords.
  * **Validation Split:** 80% Training, 20% Holdout Testing (Stratified by intent classes).

---

## 📂 Project Directory Structure

```
it-helpdesk-flask/
├── app.py                   # Main Flask backend server (Trains model on startup, exposes REST API)
├── support_queries.csv      # Training corpus (120+ structured samples, 6 intent classes)
├── templates/
│   └── index.html           # Elegant dashboard frontend structure (responsive sidebar tabs)
├── static/
│   ├── style.css            # Custom CSS system (Glassmorphism layout, animations, priority tags)
│   └── app.js               # Front-end JavaScript logic (REST fetching, State HUD, Timelines, Charts)
└── README.md                # Comprehensive project guide (this file)
```

---

## 🚀 Installation & Local Setup

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your system. 

### 2. Install Required Python Libraries
Run the following command in your terminal or Command Prompt to install the Flask server and Machine Learning dependencies:
```bash
pip install flask pandas scikit-learn numpy
```

### 3. Run the Application
Navigate to the project root directory and start the Flask development server:
```bash
python app.py
```

### 4. Open in Web Browser
Once the model training confirmation message prints in your terminal:
```
=======================================================
  Model trained successfully!
  Accuracy : 95.83%
  Samples  : 120 (train=96, test=24)
  Classes  : ['email_issue', 'network_issue', 'password_reset', 'printer_issue', 'software_issue', 'vpn_issue']
=======================================================
🌐  Running on http://127.0.0.1:5000
```
Open your browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🎓 Viva Voce Preparation Guide (For MBA AI Specialization)

Here are the top technical questions examiners ask during viva presentations, customized for this application's implementation:

### ❓ Q1: Why did you choose Naive Bayes instead of deep learning (e.g., Transformers/LLMs) for this chatbot?
* **Answer:** *"For an enterprise IT routing task, a Multinomial Naive Bayes classifier is highly appropriate due to its **extreme efficiency, low computational footprint, and explainability**. It trains instantly (under 5ms) on CPU, requires zero expensive GPU resources, and delivers over 90%+ accuracy on specific classification targets. It acts as an excellent, lightweight first-line defense before escalating to larger, slower generative models."*

### ❓ Q2: What is the role of TF-IDF in this application?
* **Answer:** *"TF-IDF stands for **Term Frequency-Inverse Document Frequency**. It converts raw user text into numerical vectors that the Naive Bayes algorithm can understand. 
1. **Term Frequency (TF):** Measures how often a word appears in a query.
2. **Inverse Document Frequency (IDF):** Reduces the weight of common IT terms that appear across all categories (like 'issue', 'problem', 'help') while scaling up the weight of highly specific diagnostic terms (like 'VPN', 'toner', 'SMTP', 'password')."*

### ❓ Q3: Why did you include unigrams and bigrams (`ngram_range=(1, 2)`)?
* **Answer:** *"Using single words (unigrams) sometimes loses context. For example, in 'I can **not login**', a unigram vectorizes 'not' and 'login' separately. By enabling bigrams, the vectorizer captures '**not login**' and '**password reset**' as single tokens, which preserves the sequence meaning and significantly boosts the model's classification accuracy."*

### ❓ Q4: What is Laplace Smoothing and why is `alpha=0.3` important?
* **Answer:** *"Laplace smoothing adds a small value (alpha) to word count estimates. If a student types a completely new word during the viva (e.g., 'supercalifragilistic'), the model's standard count probability for that word would be 0, causing the entire Bayesian product calculation to crash to 0. Laplace smoothing ensures no term ever has a zero probability, keeping the inference system robust."*

### ❓ Q5: How do you interpret the Classification Report (Precision, Recall, F1-Score)?
* **Answer:** 
* **Precision:** *"Out of all tickets the AI classified as 'VPN Issue', how many were actually VPN issues? High precision prevents routing tickets to the wrong department."*
* **Recall:** *"Out of all actual VPN issues submitted, how many did the AI successfully catch? High recall ensures no critical network issues go unnoticed."*
* **F1-Score:** *"The harmonic mean of Precision and Recall. It provides a balanced single metric showing how robust the model is on each intent."*

---

## 👨‍💻 Created by
* **Active User / Analyst:** Tulsi Gaikwad (`IT Specialist`)
* Aegis IT Service Management AI Hub Core Project
