import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from rag_pipeline import generate_response  # Import RAG pipeline function

# Load Environment Variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Error: GEMINI_API_KEY is missing in .env file!")

# Flask App Setup
app = Flask(__name__)
CORS(app)

CONVERSATION_HISTORY_FILE = "conversation_history.json"

# Gemini API Endpoint
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateText?key={API_KEY}"

def load_conversation_history():
    """讀取對話歷史，若檔案不存在則回傳空列表"""
    if os.path.exists(CONVERSATION_HISTORY_FILE):
        with open(CONVERSATION_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 保存對話歷史
def save_conversation_history(history):
    """將對話歷史保存至 JSON 檔案"""
    with open(CONVERSATION_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

@app.route("/api/gemini", methods=["POST"])
def gemini_chat():
    """ Handle user query, run RAG pipeline, and get AI response. """
    try:
        # Get User Input from Request
        data = request.get_json()
        user_input = data.get("input", "")

        if not user_input:
            return jsonify({"error": "Input text is required"}), 400
        
        conversation_history = load_conversation_history()

        history_prompt = "\n".join(conversation_history[-5:])  # 只取最後 5 筆對話
        prompt = f"""
        You are a travel agent AI. Continue the conversation considering the context below:

        {history_prompt}

        User: {user_input}
        AI:"""

        # Run RAG Pipeline to get Contextual Response
        # ai_response = generate_response(user_input)
        ai_response = generate_response(prompt)

        conversation_history.append(f"User: {user_input}")
        conversation_history.append(f"AI: {ai_response}")

        # 限制對話歷史長度，最多保留 20 筆
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        # 保存對話歷史
        save_conversation_history(conversation_history)

        # Return AI-generated Response
        return jsonify({"query": user_input, "response": ai_response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    """ Health check endpoint. """
    return "AI Travel Planner Backend is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
