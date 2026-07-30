import json
import random
from pathlib import Path

from patient_state import EmotionState
from behaviors import BehaviorEngine

class PatientSimulator:

    def __init__(self, persona_path):

        self.persona = self.load_persona(persona_path)

        self.behavior = BehaviorEngine()

        self.state = EmotionState.CALM

        self.history = []

        self.last_question = None

    def load_persona(self, persona_path):

        with open(persona_path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    def receive_message(self, assistant_message):

        self.history.append(
            {
                "role": "assistant",
                "message": assistant_message
            }
        )    

    def generate_response(self):

        return "Bugün günlerden neydi?"    