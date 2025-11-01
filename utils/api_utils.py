import http.server 

"""
APIUtils - Module pour la gestion des endpoints API du ChatbotFactory.

Ce module expose des endpoints pour :
- Créer, éditer, lister, supprimer des modèles
- Chatter avec un modèle via l'API

Utilise ModelManager et ModelInterface pour orchestrer la logique métier.
"""
import requests
from utils.model_manager import ModelManager
from utils.ModelInterface import ModelInterface

class APIUtils:
    """
    Classe utilitaire pour exposer les endpoints API du ChatbotFactory.
    Utilise ModelManager pour la gestion des modèles et ModelInterface pour l'interaction LLM.
    """
    def __init__(self, model_file="models.json"):
        """
        Initialise le serveur API et connecte les gestionnaires de modèles.
        Args:
            model_file (str): Chemin du fichier JSON des modèles.
        """
        self.model_manager = ModelManager(model_file)
        self.model_interfaces = {}  # Cache des interfaces par modèle

    def setup_routes(self, app):
        """
        Définit tous les endpoints API sur l'objet serveur (ex: FastAPI).
        Args:
            app: Instance du serveur web (FastAPI, Flask, etc.)
        """
        # Exemple FastAPI:
        # @app.post("/create_model")
        # def create_model(...):
        #     return self.create_model_endpoint(...)
        # @app.post("/chat")
        # def chat(...):
        #     return self.chat_endpoint(...)
        pass

    def start_server(self, port=99):
        """
        Démarre le serveur web sur le port spécifié.
        Args:
            port (int): Port d'écoute du serveur.
        """
        # Exemple: uvicorn.run(app, host="0.0.0.0", port=port)
        pass

    def create_model_endpoint(self, name, role, model_name, system_prompt, rag_file=None):
        """
        Endpoint pour créer un nouveau modèle.
        Args:
            name (str): Nom du modèle.
            role (str): Rôle du modèle (assistant, etc.).
            model_name (str): Nom du modèle LLM (ex: qwen3:latest).
            system_prompt (str): Prompt système.
            rag_file (str, optional): Chemin du fichier RAG.
        Returns:
            dict: Résultat de la création.
        """
        self.model_manager.create_model(name, role, model_name, system_prompt, rag_file)
        return {"status": "success", "message": f"Model '{name}' created."}

    def chat_endpoint(self, model_name, user_message, rag_content=None):
        """
        Endpoint pour chatter avec un modèle.
        Args:
            model_name (str): Nom du modèle à utiliser.
            user_message (str): Message utilisateur.
            rag_content (str, optional): Contexte RAG additionnel.
        Returns:
            dict: Réponse du modèle.
        """
        if model_name not in self.model_interfaces:
            config = self.model_manager.get_model(model_name)
            self.model_interfaces[model_name] = ModelInterface(config)
        interface = self.model_interfaces[model_name]
        response = interface.send_message(user_message, rag_content)
        return {"response": response}