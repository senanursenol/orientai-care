import time
import asyncio

from pathlib import Path

from app.ai.simulation.patient_simulator import PatientSimulator

from app.ai.evaluation.evaluation_service import (
    evaluation_service,
)

async def main():

    # Persona Path
    project_root = Path(__file__).resolve().parents[5]

    persona_path = (
        project_root
        / "data"
        / "synthetic_personas"
        / "ayse_arslan.json"
    )

    simulator = PatientSimulator(persona_path)

    # Assistant Messages
    assistant_messages = [
        "Merhaba Ayşe Hanım.",
        "Bugün nasılsınız?",
        "Bugün günlerden Salı.",
        "Kahvaltınızı yaptınız mı?",
        "Sabah ilacınızı aldınız mı?",
        "Selin bugün saat 16.00'da sizi ziyaret edecek.",
        "Çiçeklerinizi sulamayı unutmayın.",
        "Eskiden öğretmenlik yaptığınızı hatırlıyor musunuz?",
        "Şu anda kendi evinizdesiniz.",
        "İyi geceler Ayşe Hanım."
    ]

    print("""
    ===========================================
    ORIENTAI
    Synthetic Dementia Patient Simulator
    ===========================================
    """)

    for message in assistant_messages:

        print(f"\nAssistant : {message}")

        response = await simulator.generate_response(message)

        print(
            f"Patient ({simulator.state.value.upper()}) : {response}"
        )

        time.sleep(1)

    print("\n")

    # Assistant Evaluation
    conversation = simulator.logger.build_history()

    evaluation = await evaluation_service.evaluate(
        conversation=conversation,
        patient_context=simulator.persona.build_context(),
    )

    print("\n")

    print("=" * 50)

    print("ASSISTANT EVALUATION")

    print("=" * 50)

    print(f"Overall Score : {evaluation.overall_score}/10")

    print(f"RAG           : {evaluation.rag_grounded}/2")

    print(f"Hallucination : {evaluation.hallucination}/2")

    print(f"Empathy       : {evaluation.empathy}/2")

    print(f"Guidance      : {evaluation.guidance}/2")

    print(f"Safety        : {evaluation.safety}/2")

    print()

    print("Strengths")

    for item in evaluation.strengths:

        print(f" + {item}")

    print()

    print("Improvements")

    for item in evaluation.improvements:

        print(f" - {item}")

    print()

    print(evaluation.summary)

    print("\nPersona Information")

    print("-"*40)

    metadata = simulator.persona.metadata

    print(f"Patient : {metadata['full_name']}")

    print(f"Age : {metadata['age']}")

    print(f"Diagnosis : {metadata['diagnosis']}")

    print(f"Former Profession : {metadata['former_profession']}")

    simulator.print_summary()

    # Export
    conversation_folder = (
        project_root
        / "simulation"
        / "conversations"
    )

    conversation_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    simulator.export_history(

        conversation_folder
        / "sample_conversation.json"

    )

    simulator.export_markdown(

        conversation_folder
        / "sample_conversation.md"

    )

    simulator.logger.export_evaluation_json(

        evaluation,

        conversation_folder / "evaluation.json",

    )

    simulator.logger.export_evaluation_markdown(

        evaluation,

        conversation_folder / "evaluation.md",

    )

    print("\nConversation exported successfully.")

if __name__ == "__main__":

    asyncio.run(main())