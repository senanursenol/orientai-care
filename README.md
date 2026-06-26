<div align="center">

# 🧭 OrientAI

### Multimodal Orientation and Memory Support Assistant for Dementia Care

**OrientAI** is an AI-powered cognitive support assistant designed to help individuals with mild to moderate dementia maintain orientation, recall personal memories, follow daily routines, and receive multimodal support through voice, vision, and personalized memory retrieval.

</div>

---

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?style=for-the-badge&logo=streamlit)
![ChromaDB](https://img.shields.io/badge/ChromaDB-RAG-purple?style=for-the-badge)
![Whisper](https://img.shields.io/badge/Whisper-STT-black?style=for-the-badge)
![Jira](https://img.shields.io/badge/Jira-Scrum-0052CC?style=for-the-badge&logo=jira)

</div>

---

## 📌 Project Overview

**OrientAI** is a multimodal AI assistant developed to support individuals with mild to moderate dementia and their caregivers.

Dementia and Alzheimer’s disease may cause difficulties in short-term memory, orientation, daily routine management, and recognition of familiar people, objects, or situations. OrientAI aims to reduce these challenges by combining:

- Voice-based interaction
- Visual understanding
- Personalized memory retrieval
- Daily routine and medication support
- Sentiment analysis
- Caregiver monitoring dashboard

The system is designed as a **non-clinical cognitive support prototype** and does not provide medical diagnosis, treatment, or emergency decision-making.

---

## 🎯 Problem

Individuals with dementia may experience:

- Repeated questions due to memory loss
- Forgetting medication or daily routines
- Difficulty recognizing familiar people, objects, or environments
- Confusion about time, place, or current situation
- Increased dependency on caregivers

At the same time, caregivers often face emotional and physical burden due to continuous monitoring responsibilities.

---

## 💡 Our Solution

OrientAI provides an AI-powered support layer that helps patients stay oriented and helps caregivers track the patient’s daily status.

The assistant can:

- Understand voice input
- Respond with generated speech
- Retrieve personalized memories using RAG
- Analyze images and connect them with patient memories
- Track conversations, routines, and emotional state
- Provide caregivers with a dashboard for monitoring

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🎙️ Voice Interaction | Patients can ask questions using speech. |
| 🔊 Text-to-Speech | The assistant can respond with generated voice output. |
| 🧠 Personalized Memory Support | RAG-based retrieval from synthetic patient memories. |
| 🖼️ Visual Understanding | Image analysis for objects, people, and context. |
| 🗓️ Routine Tracking | Daily routines and medication reminders. |
| 📊 Caregiver Dashboard | Visual monitoring of logs, routines, and emotional state. |
| 😊 Sentiment Analysis | Detection of anxious, negative, neutral, or positive interactions. |
| 🤖 Dual-Agent Simulation | AI-based patient simulator and assistant evaluation flow. |
| 🛡️ Safety-Oriented Prompting | Hallucination reduction and safe response design. |

---

## 👥 Target Audience

- Individuals with mild to moderate dementia
- Alzheimer’s patients
- Family caregivers
- Elderly care centers
- Non-clinical cognitive support systems

---

## 🧱 System Architecture

```text
Patient Voice / Text / Image Input
              |
              v
        FastAPI Backend
              |
   --------------------------------
   |              |               |
 STT Service   Vision Service   RAG Service
 Whisper       LLaVA / API      ChromaDB
   |              |               |
   --------------------------------
              |
              v
          LLM Response
              |
        ---------------
        |             |
      TTS       Interaction Logs
        |             |
        v             v
 Patient Output  Caregiver Dashboard
```

> A detailed architecture diagram will be added as the project evolves.

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Frontend | Streamlit |
| Speech-to-Text | Whisper |
| Text-to-Speech | TTS Services |
| Multimodal AI | LLaVA / Vision API |
| RAG | ChromaDB |
| Database | PostgreSQL / SQL Server |
| Project Management | Jira |
| Version Control | Git, GitHub |

---

## 🧪 Synthetic Data Approach

Due to privacy and ethical concerns, OrientAI does not use real patient data during development.

Instead, the system uses fully synthetic personas that include:

- Patient metadata
- Daily routines
- Medication reminders
- Core memories
- Family-related information
- Simulated conversation patterns

Example persona structure:

```json
{
  "patient_id": "P-10942",
  "metadata": {
    "name": "Ahmet Yılmaz",
    "age": 74,
    "diagnosis": "Early Stage Alzheimer",
    "former_profession": "History Teacher"
  },
  "daily_routines": [
    {
      "time": "08:30",
      "action": "Take morning medication"
    }
  ],
  "core_memories": [
    {
      "category": "family",
      "content": "His oldest granddaughter's name is Ayşe.",
      "keywords": ["granddaughter", "Ayşe", "family"]
    }
  ]
}
```

---

## 👨‍👩‍👧 Team

### Team Name

**Team OrientAI**

| Name | Role |
|---|---|
| Team Member 1 | Product Owner & Data Designer |
| Team Member 2 | AI & Model Integration Developer |
| Team Member 3 | Backend Developer |
| Team Member 4 | Database & RAG Developer |
| Team Member 5 | Frontend & UI Developer |

> Team member names will be added later.

---

## 📋 Product Backlog

[Jira Product Backlog](https://senanursenol4.atlassian.net/jira/software/projects/ORI/boards/67/backlog)

---

# 🚀 Sprint Planning

The project is planned as a **6-week Agile/Scrum development process** consisting of **3 sprints**.

| Sprint | Focus Area | Estimated Points |
|---|---|---:|
| Sprint 1 | Infrastructure and Data Architecture | 100 SP |
| Sprint 2 | LLM, RAG and Voice Interaction | 100 SP |
| Sprint 3 | Vision, Dashboard and Final Testing | 100 SP |

---

# Sprint 1 — Infrastructure and Data Architecture

## Sprint Goal

The goal of Sprint 1 is to establish the core project structure, FastAPI backend skeleton, database schema, synthetic patient persona structure, and initial ChromaDB-based RAG infrastructure.

## Sprint Backlog

| Task | Status |
|---|---|
| Project folder structure setup | To Do |
| FastAPI backend skeleton setup | To Do |
| Health check endpoint implementation | To Do |
| Database schema design | To Do |
| User, patient, routine and log tables | To Do |
| Synthetic patient persona JSON schema | To Do |
| Sample synthetic patient profiles | To Do |
| ChromaDB vector database setup | To Do |
| Persona indexing into vector database | To Do |
| Initial README documentation | To Do |
| Requirements and .gitignore setup | To Do |
| Backend environment configuration | To Do |
| Sprint 1 board screenshots | To Do |
| Sprint 1 review and retrospective notes | To Do |

## Sprint Board

![Sprint 1 Backlog](assets/sprint_boards/sprint_1_backlog.png)

## Sprint Review

To be completed at the end of Sprint 1.

## Sprint Retrospective

To be completed at the end of Sprint 1.

---

# Sprint 2 — LLM, RAG and Voice Interaction

## Sprint Goal

The goal of Sprint 2 is to develop the voice interaction layer, RAG-supported memory retrieval, LLM prompting structure, speech-to-text, text-to-speech, and sentiment analysis modules.

## Sprint Backlog

| Task | Status |
|---|---|
| Whisper STT service integration | To Do |
| TTS service integration | To Do |
| Voice question-answering flow | To Do |
| RAG retriever service development | To Do |
| LLM prompt design for RAG context | To Do |
| Memory-supported chat endpoint | To Do |
| Voice chat endpoint | To Do |
| Conversation history logging | To Do |
| Sentiment analysis module | To Do |
| Flagging anxious or negative conversations | To Do |
| Sprint 2 demo screenshots | To Do |
| Sprint 2 review and retrospective notes | To Do |

## Sprint Board

![Sprint 2 Backlog](assets/sprint_boards/sprint_2_backlog.png)

## Sprint Review

To be completed at the end of Sprint 2.

## Sprint Retrospective

To be completed at the end of Sprint 2.

---

# Sprint 3 — Vision, Dashboard and Final Testing

## Sprint Goal

The goal of Sprint 3 is to complete visual understanding, image-based memory therapy, caregiver dashboard, dual-agent simulation, hallucination testing, and final demo preparation.

## Sprint Backlog

| Task | Status |
|---|---|
| LLaVA or Vision API integration | To Do |
| Photo description module | To Do |
| Image-based memory therapy flow | To Do |
| Connecting visual analysis with RAG memory | To Do |
| Streamlit caregiver dashboard | To Do |
| Patient interaction screen simulation | To Do |
| Reminder management screen | To Do |
| Sentiment charts on dashboard | To Do |
| Conversation and routine logs on dashboard | To Do |
| Dual-agent patient simulator | To Do |
| Assistant agent evaluation flow | To Do |
| Hallucination and safety testing | To Do |
| Final demo scenario | To Do |
| Sprint 3 product screenshots | To Do |
| Sprint 3 review and retrospective notes | To Do |

## Sprint Board

![Sprint 3 Backlog](assets/sprint_boards/sprint_3_backlog.png)

## Sprint Review

To be completed at the end of Sprint 3.

## Sprint Retrospective

To be completed at the end of Sprint 3.

---

## 📸 Screenshots

```text
assets/
└── sprint_boards/
    ├── sprint_1_backlog.png
    ├── sprint_2_backlog.png
    └── sprint_3_backlog.png
```

---

## 🔒 Ethics and Privacy

OrientAI does not use real patient data during development or testing.

All patient profiles, memories, routines, and conversations are synthetically generated. The project is designed only as a cognitive support and caregiver-assistance prototype. It is not intended for clinical diagnosis, treatment, or emergency medical decision-making.

---

## 📍 Project Status

```text
Current Stage: Sprint Planning and Repository Setup
```

---

<div align="center">

### OrientAI  
#### Supporting orientation, memory, and daily life through multimodal AI.

</div>
