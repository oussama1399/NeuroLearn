import requests



class ModelInterface:
    def __init__(self, model_config, api_url="http://localhost:80"):
        self.model_config = model_config  # dict with role, system_prompt, model, rag_file, etc.
        self.api_url = api_url           # Ollama API endpoint
        self.history = []                # To store conversation history for chat
        # Optionally, you could add:
        # import requests
        # self.session = requests.Session()  # For efficient HTTP requests
        
    def prepare_message(self, user_message, rag_content=None):
        message = []
        # Start with system prompt
        if self.model_config.get("system_prompt"):
            message.append({"role": "system", "content": self.model_config["system_prompt"]})
        # Always add user message, optionally prepending RAG content
        if rag_content:
            content = f"{rag_content}\n\n{user_message}"
        else:
            content = user_message
        message.append({"role": "user", "content": content})
        return message
    
    
    def send_message(self, user_message, rag_content=None):
        # Prepare the message list (system, user, RAG)
        messages = self.prepare_message(user_message, rag_content)
        
        # Optionally include conversation history for multi-turn chat
        full_history = self.history + messages

        # Build the payload for Ollama API
        payload = {
            "model": self.model_config["model"],
            "messages": full_history,
            "stream": False
        }

        # Send the POST request to Ollama's /api/chat endpoint
        try:
            response = requests.post(f"{self.api_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            # Extract the assistant's reply (adjust key as needed for Ollama's response format)
            assistant_reply = data.get("message", {}).get("content", "")
            # Update history
            self.history.extend(messages)
            self.history.append({"role": "assistant", "content": assistant_reply})
            return assistant_reply
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            return None
        
        
        
    
        
        
        
        
        
        
        
        

"""
ModelInterface - Classe pour l'interaction avec l'API Ollama.

Permet d'envoyer des messages à un modèle LLM, gérer l'historique de chat, et intégrer du contexte RAG.
Compatible avec APIUtils pour l'orchestration via endpoints API.
"""