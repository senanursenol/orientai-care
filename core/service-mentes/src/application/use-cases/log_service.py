from services.postgres_config import conn

def save_interaction(
    patient_id,
    user_input,
    response,
    input_type="text",
    transcription=None
):
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO interaction_logs
        (patient_id, input_type, user_input, response, transcription)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        patient_id,
        input_type,
        user_input,
        response,
        transcription
    ))

    conn.commit()
    cursor.close()
    print("Konuşma başarıyla kaydedildi.")
    if __name__ == "__main__":
        save_interaction(
            patient_id=1,
            user_input="What is my daughter's name?",
            response="His daughter is Zeynep.",
            input_type="text"
        )