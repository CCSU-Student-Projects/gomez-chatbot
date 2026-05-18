from flask import Flask,request,jsonify
from flask_cors import CORS
from src.chunker.embedder import DocumentEmbedder
from src.llm.llama3_8b_api import Llama3_8B_API
from src.llm.personality_config import DEFAULT_SYSTEM_PROMPT
import datetime

app=Flask(__name__)
CORS(app) #applying CORS 

# LLM and embedder initialization
embedder = DocumentEmbedder(use_gpu_config=False)
embedder.load_vector_store("./data/vector_db/go2_robot_vector_store") # load prebuilt vector db 
llm = Llama3_8B_API()

active_session={} # new session each time not storing 

def needs_rag(user_input: str):
    check_prompt = [
        {"role": "system", "content": "Decide if the question needs RAG documents. Answer YES or NO."},
        {"role": "user", "content": f"Question: {user_input}"}
    ]
    response = llm.generate_response(check_prompt)
    return "yes" in response.lower()

#Create GET endpoint 
@app.route("/chat",methods=["GET"])
def getChat():
    return jsonify({"reply":"Hi Im Ollama"})

#create POST endpoint
@app.route("/chat",methods=["POST"])
def chat():
    data=request.json #get request from client
    message=data["message"] #get message property

    messages = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": message})

    if needs_rag(message):
        docs = embedder.search_similar(message, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
        messages.append({"role": "system", "content": f"Relevant context:\n{context}"})

    response = llm.generate_response(messages)

    return jsonify({"reply":response})

if __name__=="__main__":
    app.run(port=8000,debug=True)