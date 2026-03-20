"""
Terminal User Interface (TUI) for RAG Application

This module provides a simple terminal based conversational interface
for interacting with the RAG system.
"""
import os
import sys
import time
from typing import Optional
# Add the parent directory to sys.path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.llama3_8b_api import Llama3_8B_API
import random

from src.chunker.embedder import DocumentEmbedder
from src.llm.personality_config import AGENT_NAME, THINKING_MESSAGES, APP_TITLE, APP_DISCLAIMER, USER_INPUT_LIMIT, DEFAULT_SYSTEM_PROMPT

# ANSI color codes for terminal output
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_colored(text: str, color: str):
    print(f"{color}{text}{Colors.END}")

def print_agent_message(message: str):
    print(f"\n{Colors.GREEN}[{AGENT_NAME}]{Colors.END} {message}")

def print_user_message(message: str):
    print(f"\n{Colors.BLUE}[USER]{Colors.END} {message}")

def print_system_message(message: str):
    print(f"\n{Colors.YELLOW}[SYSTEM]{Colors.END} {message}")

def print_typing_effect(text: str, delay: float = 0.01):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def print_introduction():
    intro_text = f"""
{Colors.BOLD}{APP_TITLE}{Colors.END}

{Colors.BOLD}Instructions:{Colors.END}
- Type your questions and press ENTER to submit
- Enter 'quit' to exit

{Colors.BOLD}Session Limit:{Colors.END} {USER_INPUT_LIMIT} queries per session
{Colors.BOLD}Questions?{Colors.END} Contact Thomas L. King at KingTL@ccsu.edu

{APP_DISCLAIMER}
"""
    print(intro_text)

class TUI:
    def __init__(self, embedder: DocumentEmbedder, system_prompt=DEFAULT_SYSTEM_PROMPT):
        self.embedder = embedder
        self.history = []
        self.exit_commands = ["quit",]
        self.input_count = 0
        self.llm = Llama3_8B_API()
        
        # Default system prompt and role settings
        self.system_prompt = system_prompt
        self.user_role = "user"
        self.assistant_role = "assistant"
        self.system_role = "system"

    def needs_rag(self, user_input, conversation_messages):
        check_prompt = [
            {"role": "system", "content": "You are an expert assistant. Decide if the user's question needs information from Unitree research documents. Answer YES or NO."},
            {"role": "user", "content": f"Question: {user_input}"}
        ]
        response = self.llm.generate_response(check_prompt)
        return "yes" in response.lower()
        
    def run(self):
        try:
            clear_screen()
            print_introduction()
            # Initialize conversation messages with configurable system prompt
            conversation_messages = [
                {"role": self.system_role, "content": self.system_prompt}
            ]
            
            while True:
                if self.input_count >= USER_INPUT_LIMIT:
                    print_system_message(f"User input limit of {USER_INPUT_LIMIT} reached. Session will now end.")
                    break
                user_input = input(f"\n{Colors.BLUE}[USER]{Colors.END} ")
                if user_input.lower().strip() in self.exit_commands:
                    print_system_message("Exiting the application.")
                    break
                if not user_input.strip():
                    continue  # Disregard empty input
                # Add user message to conversation history
                conversation_messages.append({"role": self.user_role, "content": user_input})
                self.history.append(f"User: {user_input}")
                
                if random.random() < 0.3:
                    print_agent_message(random.choice(THINKING_MESSAGES))

                if self.needs_rag(user_input, conversation_messages):
                    docs = self.embedder.search_similar(user_input, k=3)
                    context = "\n\n".join([doc.page_content for doc in docs])
                    conversation_messages.append({
                        "role": "system",
                        "content": f"Relevant Unitree research context:\n{context}\n\nUse this information to answer the user's question."
                    })

                response = self.llm.generate_response(conversation_messages)
                
                print_agent_message(response)
                
                # Add assistant response to conversation history
                conversation_messages.append({"role": self.assistant_role, "content": response})
                self.history.append(f"Agent: {response}")
                self.input_count += 1
                
        except KeyboardInterrupt:
            print("\n")
            print_system_message("Interrupted by user. Exiting gracefully...")
        except Exception as e:
            print_system_message(f"An error occurred: {str(e)}")
        finally:
            if hasattr(self.llm, 'unload_model'):
                self.llm.unload_model()

def main():
    # Initialize embedder
    embedder = DocumentEmbedder(use_gpu_config=False)
    embedder.load_vector_store("./data/vector_db/go2_robot_vector_store") # Here we load the vector store. In this case it's the unitree research documents.

    custom_prompt = DEFAULT_SYSTEM_PROMPT

    tui = TUI(embedder, system_prompt=custom_prompt)
    tui.run()

if __name__ == "__main__":
    main()
