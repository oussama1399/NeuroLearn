# utils/model_manager.py

import json
import os





class ModelManager:
    def __init__(self, model_file="models.json"):
        self.model_file = model_file
        self.models = self._load_models()

    def _load_models(self):
    # Load models from JSON file, or return empty dict if not found or invalid
        if os.path.exists(self.model_file):
            try:
                with open(self.model_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, ValueError):
                return {}
        return {}

    def _save_models(self):
        # Save current models back to JSON file
        if self.models:
            with open(self.model_file, 'w') as f:
                json.dump(self.models, f, indent=2)

    def create_model(self, name, role, model_name, system_prompt, rag_file=None):
        if name in self.models:  # Only check for duplicate config name
            raise ValueError(f"Model config '{name}' already exists.")
        # Remove the Ollama model check for now
        self.models[name] = {
            "role": role,       
            "model": model_name,  # This should be validated separately
            "system_prompt": system_prompt,
            "rag_file": rag_file
        }
        self._save_models()
        
        

    def list_models(self):
        # Return list of model names
        data = self._load_models()
        model_names = list(data.keys())
        return model_names

    def get_model(self, name):
        # Return full config of a model by name
        if name in self.list_models():
            return self.models[name]
        raise ValueError(f"Model config '{name}' not found.")

    def edit_model(self, name, **updates):
        if name not in self.models:
            raise ValueError(f"Model config '{name}' not found.")
        for key, value in updates.items():
            self.models[name][key] = value
        self._save_models()

    def delete_model(self, name):
        # Remove a model
        if name in self.models:
            del self.models[name]
            self._save_models()
        else:
            raise ValueError(f"Model config '{name}' not found.")
        
        
    
    
    

"""
ModelManager - Classe pour la gestion des configurations de modèles AI.

Permet de créer, éditer, lister, supprimer et charger des configurations de modèles depuis un fichier JSON.
Compatible avec APIUtils pour l'orchestration via endpoints API.
"""

# ...existing code...