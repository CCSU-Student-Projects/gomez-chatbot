import { useState } from 'react'
import './App.css'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import SendIcon from '@mui/icons-material/Send';
import { Button, TextField } from '@mui/material';

function App() {

  const [chatHistory, setChatHistory] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  /* get our chat response */
  const sendMessage = async (e: React.MouseEvent<HTMLButtonElement>) => {

    e.preventDefault();

    if (message && message.trim().length > 0) {

      setChatHistory((prev) => [...prev, message]);
      const userMessage = {
        message: message
      }

      const response = await fetch("http://127.0.0.1:8000/chat", {

        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(userMessage),
        method: "POST",
      });

      /*Reset Input*/
      setMessage("");
      const data = await response.json();//waiting for response to be converted to json 
      setChatHistory((prev) => [...prev, data.reply]);
    }
    else {
      setError("You haven't typed anything");
    }
  };


  return (
    <>
      <header>
        <div className="text-left m-5 font-bold"> CCSU AI</div>
      </header>
      {
        chatHistory.length > 0 ? (
          <section className="chatHistorySection">
            {chatHistory.map((message, index) => (
              <p key={index} className={(index + 1) % 2 == 0 ? "response" : "query"}>{message}</p>
            ))}
          </section>
        ) : (
          <section className='my-10 main'>
            <AutoAwesomeIcon fontSize='large' color='warning' ></AutoAwesomeIcon>
            <h1 className='mb-10'> Ask me anything</h1>
          </section>
        )}

      <section className='flex justify-center gap-10'>
        <TextField
          id="standard-basic"
          label="type your question here"
          variant="standard"
          className='my-10 w-2x1'
          onChange={(e) => {
            setMessage(e.target.value)
          }}
          value={message}
        ></TextField>
        <Button
          variant='contained'
          className='w-42.5'
          color="primary"
          endIcon={<SendIcon />}
          onClick={sendMessage}
        >Ask</Button>

      </section>
    </>
  )

}

export default App
