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

        self.update_state()

        if self.state == EmotionState.ANXIOUS:
            return self.anxious_response()

        if self.state == EmotionState.CONFUSED:
            return self.confused_response()

        if self.state == EmotionState.FORGETFUL:
            return self.forgetful_response()

        return self.normal_response()
    

    def update_state(self):

        states = [
            EmotionState.CALM,
            EmotionState.ANXIOUS,
            EmotionState.CONFUSED,
            EmotionState.FORGETFUL
        ]

        self.state = random.choice(states)


    def anxious_response(self):
        return "Kızım gelecek mi bugün?" 
    
    def confused_response(self):
        return "Bugün hangi gündeyiz?"

    def forgetful_response(self):
        return "Az önce ne konuşuyorduk?"
    
    def normal_response(self):
        return "Bugün kendimi biraz daha iyi hissediyorum."