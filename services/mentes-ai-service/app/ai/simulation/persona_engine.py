import json
import random

class PersonaEngine:
    """
    Loads and manages synthetic patient persona data.
    Responsible only for accessing persona information.
    """

    REQUIRED_FIELDS = [
        "metadata",
        "family_members",
        "core_memories",
        "daily_routines"
    ]

    def __init__(self, persona_path):

        with open(persona_path, "r", encoding="utf-8") as file:
            self.persona = json.load(file)

        self.validate()

    # Validation
    def validate(self):

        for field in self.REQUIRED_FIELDS:

            if field not in self.persona:

                raise ValueError(
                    f"Missing required persona field: {field}"
                )

    # Basic getters
    @property
    def metadata(self):
        return self.persona.get("metadata", {})

    @property
    def patient_id(self):
        return self.persona.get("patient_id")

    @property
    def orientation(self):
        return self.persona.get("orientation_support", {})

    @property
    def communication(self):
        return self.persona.get(
            "communication_preferences",
            {}
        )

    # Random generators
    def random_family_member(self):

        members = self.persona.get("family_members", [])

        if not members:
            return "Selin"

        return random.choice(members)["name"]

    def random_memory(self):

        memories = self.persona.get("core_memories", [])

        if not memories:
            return None

        return random.choice(memories)

    def random_routine(self):

        routines = self.persona.get("daily_routines", [])

        if not routines:
            return None

        return random.choice(routines)

    def random_sample_question(self):

        questions = self.persona.get("sample_questions", [])

        if not questions:
            return None

        return random.choice(questions)["question"]

    # Memory helpers
    def random_memory_keyword(self):

        memory = self.random_memory()

        if not memory:
            return None

        keywords = memory.get("keywords", [])

        if not keywords:
            return memory.get("content", "")

        return random.choice(keywords)

    def reassurance_message(self):

        return self.orientation.get(
            "reassurance_message",
            "Güvendesiniz."
        )

    def home_location(self):

        return self.orientation.get(
            "current_home",
            "Ev"
        )
    

    def build_context(self) -> str:
        """
        Converts the persona into a structured text context
        that can be provided directly to the LLM.
        """

        metadata = self.metadata

        lines = []

        lines.append(
            f"Patient Name: {metadata.get('full_name','Unknown')}"
        )

        lines.append(
            f"Age: {metadata.get('age','Unknown')}"
        )

        lines.append(
            f"Diagnosis: {metadata.get('diagnosis','Unknown')}"
        )

        lines.append(
            f"Disease Stage: {metadata.get('disease_stage','Unknown')}"
        )

        lines.append(
            f"Former Profession: {metadata.get('former_profession','Unknown')}"
        )

        lines.append("")

        if self.persona.get("family_members"):

            lines.append("Family Members:")

            for member in self.persona["family_members"]:

                lines.append(
                    f"- {member['name']} ({member['relation']})"
                )

            lines.append("")

        if self.persona.get("daily_routines"):

            lines.append("Daily Routines:")

            for routine in self.persona["daily_routines"]:

                lines.append(
                    f"- {routine['time']} : {routine['activity']}"
                )

            lines.append("")

        if self.persona.get("core_memories"):

            lines.append("Core Memories:")

            for memory in self.persona["core_memories"]:

                lines.append(
                    f"- {memory['content']}"
                )

        return "\n".join(lines)