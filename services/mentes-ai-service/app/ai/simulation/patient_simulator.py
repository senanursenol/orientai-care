import random

from app.ai.simulation.persona_engine import PersonaEngine
from app.ai.simulation.patient_state import EmotionState
from app.ai.simulation.behaviors import BehaviorEngine
from app.ai.simulation.simulation_logger import SimulationLogger
from app.ai.simulation.simulation_stats import SimulationStats

from app.ai.conversation.orchestrator import conversation_service


class PatientSimulator:

    def __init__(self, persona_path):

        self.persona = PersonaEngine(persona_path)

        self.behavior = BehaviorEngine()

        self.logger = SimulationLogger()

        self.stats = SimulationStats()

        self.state = EmotionState.CALM

        self.last_patient_question = None

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
            ],
        }

        # Legacy templates
        # (Kept temporarily as fallback during migration)

        self.response_templates = {

            EmotionState.CALM: [

                "Bugün kendimi iyi hissediyorum.",

                "Biraz yürüyüş yapmak istiyorum.",

                "Bugün hava güzel görünüyor.",

                "Çiçeklerimi sulamayı unutmayayım."
            ],

            EmotionState.FORGETFUL: [

                "Az önce ne söylemiştin?",

                "Tekrar eder misin?",

                "İlacımı içtim mi?",

                "Bir şeyi unuttuğumu hissediyorum."
            ],

            EmotionState.CONFUSED: [

                "Bugün hangi gündeyiz?",

                "Ben evde miyim?",

                "Şu an neredeyim?",

                "Bir yere mi gidecektim?"
            ],

            EmotionState.ANXIOUS: [

                "Kimse bana ulaşamıyor gibi hissediyorum.",

                "Yanlış bir şey mi yaptım?",

                "Beni almaya gelecekler mi?"
            ]
        }

    # --------------------------------------------------

    def receive_message(self, message):

        self.stats.record_turn()

        self.logger.log(
            "assistant",
            message
        )

    # --------------------------------------------------

    def update_state(self):

        turns = self.stats.turns

        if turns > 12 and self.state == EmotionState.CALM:

            self.state = EmotionState.FORGETFUL

            return

        if turns > 18 and self.state == EmotionState.FORGETFUL:

            self.state = EmotionState.CONFUSED

            return

        if self.state == EmotionState.CALM:

            self.state = random.choices(

                [

                    EmotionState.CALM,

                    EmotionState.FORGETFUL

                ],

                weights=[70, 30],

                k=1

            )[0]

        elif self.state == EmotionState.FORGETFUL:

            self.state = random.choices(

                [

                    EmotionState.FORGETFUL,

                    EmotionState.CONFUSED,

                    EmotionState.CALM

                ],

                weights=[50, 30, 20],

                k=1

            )[0]

        elif self.state == EmotionState.CONFUSED:

            self.state = random.choices(

                [

                    EmotionState.CONFUSED,

                    EmotionState.ANXIOUS,

                    EmotionState.FORGETFUL

                ],

                weights=[50, 30, 20],

                k=1

            )[0]

        elif self.state == EmotionState.ANXIOUS:

            self.state = random.choices(

                [

                    EmotionState.ANXIOUS,

                    EmotionState.CONFUSED,

                    EmotionState.FORGETFUL

                ],

                weights=[50, 30, 20],

                k=1

            )[0]

    # --------------------------------------------------

    async def maybe_repeat_question(self, assistant_message):

        if not (
            self.last_patient_question
            and self.behavior.should_repeat()
        ):
            return None

        self.stats.record_repeated()

        patient_context = self.persona.build_context()
        history = self.logger.build_history()

        result = await conversation_service.simulate_patient(
            assistant_message=assistant_message,
            emotion_state=self.state.value,
            patient_context=patient_context,
            patient_id=self.persona.patient_id,
            history=history,
        )

        return result.assistant_response
    # --------------------------------------------------

    async def generate_response(

        self,

        assistant_message: str,

    ):

        self.receive_message(assistant_message)

        self.update_state()

        repeated = await self.maybe_repeat_question(
            assistant_message
        )

        if repeated:

            self.logger.log(
                "patient",
                repeated,
                self.state.value,
            )

            return repeated

        patient_context = self.persona.build_context()

        result = await conversation_service.simulate_patient(

            assistant_message=assistant_message,

            emotion_state=self.state.value,

            patient_context=patient_context,

            patient_id=self.persona.patient_id,

        )

        response = result.assistant_response

        if self.state == EmotionState.CALM:
            self.stats.record_normal()

        elif self.state == EmotionState.FORGETFUL:
            self.stats.record_forgetful()

        elif self.state == EmotionState.CONFUSED:
            self.stats.record_confused()

        elif self.state == EmotionState.ANXIOUS:
            self.stats.record_anxious()

        self.last_patient_question = response

        self.logger.log(

            "patient",

            response,

            self.state.value,

        )

        return response

    # --------------------------------------------------
    # Legacy fallback methods
    # These are kept temporarily until the LLM-based
    # simulator is fully validated.
    # --------------------------------------------------

    def anxious_response(self):

        family = self.persona.random_family_member()

        return random.choice(

            [

                f"{family} bugün gelecek mi?",

                f"{family} beni aradı mı?",

                f"{family} beni unuttu mu?",

                "Kimse bana ulaşamıyor gibi geliyor.",

            ]

        )

    def confused_response(self):

        return (
            self.persona.random_sample_question()
            or random.choice(
                self.response_templates[
                    EmotionState.CONFUSED
                ]
            )
        )

    def forgetful_response(self):

        routine = self.persona.random_routine()

        if routine:

            activity = routine["activity"]

            return random.choice(

                [

                    f"{activity} yaptım mı acaba?",

                    f"{activity} zamanı geldi mi?",

                    f"{activity} aklımdan çıktı.",

                    f"{activity} unuttum galiba.",

                    f"{activity} yapmayı hatırlatır mısın?",

                ]

            )

        return random.choice(

            self.response_templates[
                EmotionState.FORGETFUL
            ]

        )

    def normal_response(self):

        responses = self.response_templates[
            EmotionState.CALM
        ].copy()

        memory = self.persona.random_memory()

        if memory:

            responses.append(

                memory.get("content", "")

            )

        keyword = self.persona.random_memory_keyword()

        if keyword:

            responses.append(

                f"{keyword} aklıma geldi."

            )

        return random.choice(responses)

    # --------------------------------------------------

    def export_history(self, path):

        self.logger.export_json(path)

    def export_markdown(self, path):

        self.logger.export_markdown(path)

    def print_summary(self):

        self.stats.print_summary(

            self.persona.metadata.get(

                "full_name",

                "Unknown",

            )

        )

    def reset(self):

        self.state = EmotionState.CALM

        self.last_patient_question = None

        self.logger.reset()

        self.stats.reset()