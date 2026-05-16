from flask import Flask,request,jsonify
from flask_cors import CORS
from pymongo import MongoClient
from src.chunker.embedder import DocumentEmbedder
from src.llm.llama3_8b_api import Llama3_8B_API
from src.llm.personality_config import DEFAULT_SYSTEM_PROMPT
import datetime

app=Flask(__name__)
CORS(app) #applying CORS 

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["ccsu_chatbot"]
sessions = db["sessions"]

# LLM and embedder initialization
embedder = DocumentEmbedder(use_gpu_config=False)
embedder.load_vector_store("./data/vector_db/go2_robot_vector_store")
llm = Llama3_8B_API()

def get_history(session_id: str):
    doc = sessions.find_one({"session_id": session_id})
    if doc:
        return doc["messages"]
    # Brand new session — seed with system prompt
    return [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]

#Create GET endpoint 
@app.route("/chat",methods=["GET"])
def getChat():
    return jsonify({"reply":"Hi Im Ollama"})

#create POST endpoint
@app.route("/chat",methods=["POST"])
def chat():
    data=request.json #get request from client
    message=data["message"] #get message property

    print("received: "+ message)

    response = ollama. chat(
        model= "llama3",
        messages=[
            {"role": "user","content": message}
        ]
    )

    reply=response["message"]["content"]
    return jsonify({"reply":reply})

if __name__=="__main__":
    app.run(port=8000,debug=True)