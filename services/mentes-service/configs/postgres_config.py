import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="patient_care_db",
    user="postgres",
    password="741gam1542"
)
