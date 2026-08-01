import json
from datetime import datetime


class SimulationLogger:
    """
    Stores and exports simulation conversations.
    """

    def __init__(self):

        self.history = []

    # Logging
    def log(self, role, message, state=None):

        entry = {

            "timestamp": datetime.now().isoformat(),

            "role": role,

            "message": message

        }

        if state is not None:

            entry["state"] = state

        self.history.append(entry)

    # Access
    def conversation(self):

        return self.history

    def build_history(self, last_n=10):
        """
        Build a compact conversation history for the LLM prompt.
        """

        history = []

        for entry in self.history[-last_n:]:

            role = entry["role"].capitalize()

            history.append(
                f"{role}: {entry['message']}"
            )

        return "\n".join(history)

    # Export JSON
    def export_json(self, output_path):

        with open(output_path, "w", encoding="utf-8") as file:

            json.dump(

                self.history,

                file,

                indent=4,

                ensure_ascii=False

            )

    # Export Markdown
    def export_markdown(self, output_path):

        with open(output_path, "w", encoding="utf-8") as file:

            file.write("# Simulation Conversation\n\n")

            for entry in self.history:

                role = entry["role"].capitalize()

                if role == "Patient":

                    state = entry.get("state", "").upper()

                    file.write(

                        f"**Patient ({state})**: {entry['message']}\n\n"

                    )

                else:

                    file.write(

                        f"**Assistant**: {entry['message']}\n\n"

                    )


    def export_evaluation_json(
        self,
        evaluation,
        output_path,
    ):

        with open(output_path, "w", encoding="utf-8") as file:

            json.dump(

                evaluation.to_dict(),

                file,

                indent=4,

                ensure_ascii=False,

            )

    def export_evaluation_markdown(
        self,
        evaluation,
        output_path,
    ):

        with open(output_path, "w", encoding="utf-8") as file:

            file.write("# Assistant Evaluation Report\n\n")

            file.write(
                f"**Overall Score:** {evaluation.overall_score}/10\n\n"
            )

            file.write("## Scores\n\n")

            file.write(
                f"- RAG Groundedness: {evaluation.rag_grounded}/2\n"
            )

            file.write(
                f"- Hallucination: {evaluation.hallucination}/2\n"
            )

            file.write(
                f"- Empathy: {evaluation.empathy}/2\n"
            )

            file.write(
                f"- Guidance: {evaluation.guidance}/2\n"
            )

            file.write(
                f"- Safety: {evaluation.safety}/2\n\n"
            )

            file.write("## Strengths\n\n")

            for item in evaluation.strengths:

                file.write(f"- {item}\n")

            file.write("\n## Improvements\n\n")

            for item in evaluation.improvements:

                file.write(f"- {item}\n")

            file.write("\n## Summary\n\n")

            file.write(evaluation.summary)

    # Reset
    def reset(self):

        self.history = []