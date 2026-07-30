import json
import random
from pathlib import Path
from datetime import datetime

from patient_state import EmotionState
from behaviors import BehaviorEngine


class PatientSimulator:

    def __init__(self, persona_path):

        # ---------------------------------------------------
        # Persona
        # ---------------------------------------------------

        self.persona = self.load_persona(persona_path)

        self.metadata = self.persona.get("metadata", {})
        self.family_members = self.persona.get("family_members", [])
        self.core_memories = self.persona.get("core_memories", [])
        self.daily_routines = self.persona.get("daily_routines", [])
        self.orientation = self.persona.get("orientation_support", {})
        self.communication = self.persona.get(
            "communication_preferences", {}
        )
        self.sample_questions = self.persona.get(
            "sample_questions", []
        )

        # ---------------------------------------------------
        # Behaviour
        # ---------------------------------------------------

        self.behavior = BehaviorEngine()

        self.state = EmotionState.CALM

        self.transition_map = {

            EmotionState.CALM: [
                EmotionState.CALM,
                EmotionState.FORGETFUL
            ],

            EmotionState.FORGETFUL: [
                EmotionState.FORGETFUL,
                EmotionState.CONFUSED
            ],

            EmotionState.CONFUSED: [
                EmotionState.CONFUSED,
                EmotionState.ANXIOUS
            ],

            EmotionState.ANXIOUS: [
                EmotionState.ANXIOUS,
                EmotionState.CONFUSED
            ]
        }

        # ---------------------------------------------------
        # Conversation
        # ---------------------------------------------------

        self.history = []

        self.last_patient_question = None

        self.turn_count = 0

        # ---------------------------------------------------
        # Statistics
        # ---------------------------------------------------

        self.statistics = {

            "normal": 0,

            "forgetful": 0,

            "confused": 0,

            "anxious": 0,

            "repeated": 0

        }

        # ---------------------------------------------------
        # Templates
        # ---------------------------------------------------

        self.response_templates = {

            EmotionState.CALM: [

                "Bugün kendimi iyi hissediyorum.",

                "Biraz yürüyüş yapmak istiyorum.",

                "Bugün hava güzel görünüyor.",

                "Çiçeklerime su vermeyi unutmamalıyım."

            ],

            EmotionState.FORGETFUL: [

                "Az önce ne söylemiştin?",

                "Tekrar eder misin?",

                "İlacımı içtim mi?",

                "Bir şeyi unuttuğumu hissediyorum."

            ],

            EmotionState.CONFUSED: [

                "Bugün hangi gündeyiz?",

                "Ben şu anda neredeyim?",

                "Ben evde miyim?",

                "Bir yere mi gidecektim?"

            ],

            EmotionState.ANXIOUS: [

                "Kendimi biraz endişeli hissediyorum.",

                "Kimse bana ulaşamıyor gibi geliyor.",

                "Beni almaya gelecekler mi?",

                "Yanlış bir şey mi yaptım?"

            ]

        }

    # ======================================================
    # PERSONA
    # ======================================================

    def load_persona(self, persona_path):

        with open(persona_path, "r", encoding="utf-8") as file:

            persona = json.load(file)

        required = [

            "metadata",

            "family_members",

            "core_memories",

            "daily_routines"

        ]

        for field in required:

            if field not in persona:

                raise ValueError(
                    f"Missing required field: {field}"
                )

        return persona

    # ======================================================
    # CONVERSATION
    # ======================================================

    def receive_message(self, assistant_message):

        self.turn_count += 1

        self.history.append(

            {

                "timestamp": datetime.now().isoformat(),

                "role": "assistant",

                "message": assistant_message

            }

        )

    # ======================================================
    # STATE MACHINE
    # ======================================================

    def update_state(self):

        possible = self.transition_map[self.state]

        self.state = random.choice(possible)


        # ======================================================
    # PERSONA HELPERS
    # ======================================================

    def get_random_family_member(self):

        if not self.family_members:
            return "Selin"

        return random.choice(self.family_members)["name"]


    def get_random_memory(self):

        if not self.core_memories:
            return None

        return random.choice(self.core_memories)


    def get_random_routine(self):

        if not self.daily_routines:
            return None

        return random.choice(self.daily_routines)


    def get_random_sample_question(self):

        if not self.sample_questions:
            return None

        return random.choice(self.sample_questions)["question"]


    # ======================================================
    # RESPONSE GENERATION
    # ======================================================

    def generate_response(self):

        self.update_state()

        repeated = self.maybe_repeat_question()

        if repeated:

            self.statistics["repeated"] += 1

            self.save_patient_message(repeated)

            return repeated

        if self.state == EmotionState.ANXIOUS:

            response = self.anxious_response()

            self.statistics["anxious"] += 1

        elif self.state == EmotionState.CONFUSED:

            response = self.confused_response()

            self.statistics["confused"] += 1

        elif self.state == EmotionState.FORGETFUL:

            response = self.forgetful_response()

            self.statistics["forgetful"] += 1

        else:

            response = self.normal_response()

            self.statistics["normal"] += 1

        self.last_patient_question = response

        self.save_patient_message(response)

        return response


    # ======================================================
    # RESPONSE TYPES
    # ======================================================

    def anxious_response(self):

        family = self.get_random_family_member()

        responses = [

            f"{family} bugün gelecek mi?",

            f"{family} beni aradı mı?",

            f"{family} beni unuttu mu?",

            "Kimse bana ulaşamıyor gibi hissediyorum.",

            "Yanlış bir şey mi yaptım?"

        ]

        return random.choice(responses)


    def confused_response(self):

        sample_question = self.get_random_sample_question()

        if sample_question:

            return sample_question

        orientation_questions = [

            "Ben evde miyim?",

            "Bugün hangi gündeyiz?",

            "Şu an neredeyim?",

            "Saat kaç oldu?"

        ]

        return random.choice(orientation_questions)


    def forgetful_response(self):

        routine = self.get_random_routine()

        if routine:

            activity = routine["activity"]

            responses = [

                f"{activity} yaptım mı acaba?",

                f"{activity} zamanı geldi mi?"

            ]

        else:

            responses = [

                "Az önce ne söylemiştin?",

                "Tekrar eder misin?",

                "İlacımı içtim mi?"

            ]

        return random.choice(responses)


    def normal_response(self):

        memory = self.get_random_memory()

        responses = self.response_templates[EmotionState.CALM].copy()

        if memory:

            responses.append(memory["content"])

        return random.choice(responses)


    # ======================================================
    # REPEAT ENGINE
    # ======================================================

    def maybe_repeat_question(self):

        if (

            self.last_patient_question

            and self.behavior.should_repeat()

        ):

            variants = [

                self.last_patient_question,

                self.last_patient_question,

                self.last_patient_question + " Söyler misin?",

                self.last_patient_question + " Hatırlayamadım."

            ]

            return random.choice(variants)

        return None


    # ======================================================
    # HISTORY
    # ======================================================

    def save_patient_message(self, message):

        self.history.append(

            {

                "timestamp": datetime.now().isoformat(),

                "role": "patient",

                "state": self.state.value,

                "message": message

            }

        )

         # ======================================================
    # SIMULATION SUMMARY
    # ======================================================

    def get_statistics(self):

        return {

            "patient": self.metadata.get("full_name", "Unknown"),

            "turns": self.turn_count,

            "normal": self.statistics["normal"],

            "forgetful": self.statistics["forgetful"],

            "confused": self.statistics["confused"],

            "anxious": self.statistics["anxious"],

            "repeated": self.statistics["repeated"]

        }


    def print_summary(self):

        stats = self.get_statistics()

        print("\n" + "=" * 50)
        print("SIMULATION SUMMARY")
        print("=" * 50)

        print(f"Patient              : {stats['patient']}")
        print(f"Conversation Turns   : {stats['turns']}")
        print(f"Normal Responses     : {stats['normal']}")
        print(f"Forgetful Responses  : {stats['forgetful']}")
        print(f"Confused Responses   : {stats['confused']}")
        print(f"Anxious Responses    : {stats['anxious']}")
        print(f"Repeated Questions   : {stats['repeated']}")

        print("=" * 50)


    # ======================================================
    # EXPORT CONVERSATION
    # ======================================================

    def export_history(self, output_path):

        with open(output_path, "w", encoding="utf-8") as file:

            json.dump(
                self.history,
                file,
                ensure_ascii=False,
                indent=4
            )


    def export_markdown(self, output_path):

        with open(output_path, "w", encoding="utf-8") as file:

            file.write("# Simulation Conversation\n\n")

            for message in self.history:

                role = message["role"].capitalize()

                if role == "Patient":

                    state = message.get("state", "").upper()

                    file.write(
                        f"**Patient ({state})**: {message['message']}\n\n"
                    )

                else:

                    file.write(
                        f"**Assistant**: {message['message']}\n\n"
                    )


    # ======================================================
    # RESET
    # ======================================================

    def reset(self):

        self.state = EmotionState.CALM

        self.history = []

        self.turn_count = 0

        self.last_patient_question = None

        self.statistics = {

            "normal": 0,

            "forgetful": 0,

            "confused": 0,

            "anxious": 0,

            "repeated": 0

        }       