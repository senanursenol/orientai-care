CREATE TABLE caregivers (
    caregiver_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20)
);

CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    caregiver_id INT REFERENCES caregivers(caregiver_id),
    name VARCHAR(100) NOT NULL,
    birth_date DATE,
    disease VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE routines (
    routine_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(patient_id),
    title VARCHAR(100),
    description TEXT,
    frequency VARCHAR(50)
);

CREATE TABLE reminders (
    reminder_id SERIAL PRIMARY KEY,
    routine_id INT REFERENCES routines(routine_id),
    reminder_time TIME,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE logs (
    log_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(patient_id),
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    note TEXT,
    status VARCHAR(50)
);
CREATE TABLE interaction_logs (
    log_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(patient_id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    input_type VARCHAR(20) NOT NULL,
    user_input TEXT NOT NULL,
    response TEXT NOT NULL,
    transcription TEXT
);
