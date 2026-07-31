import os


PROMPT_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../prompts"
    )
)


def load_prompt(filename):
    """
    Prompt dosyasını yükler.
    """

    file_path = os.path.join(
        PROMPT_DIR,
        filename
    )

    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def build_rag_prompt(context, question):
    """
    RAG context ve kullanıcı sorusundan
    LLM için hazır prompt oluşturur.
    """

    template = load_prompt("rag_prompt.txt")

    return template.format(
        context=context,
        question=question
    )


def build_patient_prompt(context, question, history=""):
    """
    Hasta iletişimi için prompt oluşturur.
    """

    template = load_prompt(
        "patient_assistant_prompt.txt"
    )

    return template.format(
        context=context,
        question=question,
        history=history
    )


def build_image_memory_prompt(context, image_description, question):
    """
    Görsel analiz (vision) çıktısı ile hasta hafızasını (RAG context)
    birleştirip LLM için hazır prompt oluşturur.
    """

    template = load_prompt("image_memory_prompt.txt")

    return template.format(
        context=context,
        image_description=image_description,
        question=question
    )