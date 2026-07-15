import sys
import os


# Repo kök dizinini bul
REPO_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../../.."
    )
)

# AI service app klasörünü Python path'e ekle
AI_APP_PATH = os.path.join(
    REPO_ROOT,
    "services",
    "mentes-ai-service",
    "app"
)

sys.path.insert(0, AI_APP_PATH)


from services.rag.prompt_builder import (
    build_rag_prompt,
    build_patient_prompt,
    load_prompt
)


def test_rag_prompt_generation():
    """
    RAG context ile prompt oluşturma testi.
    """

    context = """
    Patient: Fatma Kaya

    Memory:
    Fatma enjoys gardening and growing roses in her garden.
    """

    question = "Fatma ne yapmayı sever?"

    prompt = build_rag_prompt(
        context=context,
        question=question
    )

    print("\n--- RAG PROMPT ---")
    print(prompt)

    # Context ve soru prompt içine doğru yerleşmiş mi?
    assert "Fatma enjoys gardening" in prompt
    assert "Fatma ne yapmayı sever?" in prompt


def test_patient_prompt_generation():
    """
    Hasta asistan prompt oluşturma testi.
    """

    context = """
    Patient: Ahmet Yılmaz

    Routine:
    Takes medication at 08:00.
    """

    question = "İlacımı ne zaman almalıyım?"

    prompt = build_patient_prompt(
        context=context,
        question=question,
        history=""
    )

    print("\n--- PATIENT PROMPT ---")
    print(prompt)

    # Hasta bilgisi ve soru doğru aktarılıyor mu?
    assert "Ahmet Yılmaz" in prompt
    assert "İlacımı ne zaman almalıyım?" in prompt


def test_prompt_prevents_hallucination():
    """
    Prompt'un olmayan bilgileri uydurmayı
    engelleyen kuralları içerdiğini test eder.
    """

    context = """
    Patient: Mehmet Demir

    Memory:
    Mehmet enjoys listening to classical music.
    """

    question = "Mehmet hangi şehirde doğdu?"

    prompt = build_rag_prompt(
        context=context,
        question=question
    )

    print("\n--- HALLUCINATION TEST ---")
    print(prompt)

    assert "Do not create new memories" in prompt
    assert "Do not assume information" in prompt
    assert "Mehmet hangi şehirde doğdu?" in prompt


def test_system_prompt_exists():
    """
    System prompt dosyasının doğru yüklendiğini test eder.
    """

    prompt = load_prompt(
        "system_prompt.txt"
    )

    print("\n--- SYSTEM PROMPT ---")
    print(prompt)

    assert "OrientAI" in prompt
    assert "Never invent patient memories" in prompt


if __name__ == "__main__":

    test_rag_prompt_generation()
    test_patient_prompt_generation()
    test_prompt_prevents_hallucination()
    test_system_prompt_exists()

    print("\nPrompt tests completed successfully.")