from flask import Flask,request,jsonify
from flask_cors import CORS
import ollama

app=Flask(__name__)
CORS(app) #applying CORS 

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