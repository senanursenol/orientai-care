# Sprint 1 Review and Retrospective

## Project

OrientAI — Multimodal Cognitive Support Assistant for Dementia and Alzheimer Patients

## Sprint

Sprint 1 - Altyapı ve Veri Mimarisi

## Sprint Status

Completed

## Sprint Duration

29 June 2026 - 9 July 2026

## Sprint Goal

Establish the initial infrastructure of OrientAI by setting up the Node.js backend, Python AI services, React frontend, database schema, ChromaDB/RAG foundation, synthetic patient persona structure, environment configuration and initial project documentation.

---

## Sprint Board

![Sprint 1 Backlog](../assets/sprint_boards/sprint_1_backlog.png)

---

## Sprint 1 Review

Sprint 1 focused on preparing the initial infrastructure and data architecture of OrientAI. The team created the foundation required for the following development phases, including backend, frontend, AI services, database, RAG infrastructure, synthetic patient data and documentation.

During this sprint, the Jira Scrum board was organized, epics were created, Sprint 1 tasks were assigned, responsibilities were clarified and the first development outputs were added to the GitHub repository.

The sprint established the base structure for a multimodal cognitive support assistant designed for dementia and Alzheimer patients.

## Completed Work

### Project and Scrum Setup

- Jira Scrum project was created and configured.
- Sprint 1, Sprint 2 and Sprint 3 backlogs were organized.
- Project epics were created and linked to related work items.
- Sprint 1 goal was defined.
- Team roles and responsibilities were clarified.
- Story points and task assignments were completed.
- Sprint 1 board screenshot was added to the documentation.

### Repository and Folder Structure

The initial repository structure was prepared for modular development.

Main project structure:

- `backend/`
- `frontend/`
- `ai-services/`
- `database/`
- `rag/`
- `data/`
- `simulation/`
- `docs/`
- `assets/`

This structure allows backend, frontend, AI services, database, RAG, simulation and documentation parts to be developed separately by the responsible team members.

### Backend Infrastructure

- Node.js backend skeleton was prepared.
- Basic backend project structure was created.
- Health check endpoint was implemented.
- Backend environment configuration was prepared for the next sprint.

### Python AI Services Infrastructure

- Python AI service skeleton was prepared.
- Initial AI service folder structure was created.
- The structure was prepared for future STT, TTS, LLM, RAG and vision service integrations.

### React Frontend Infrastructure

- React frontend skeleton was prepared.
- Initial frontend folder structure was created.
- The structure was prepared for future patient chat screen, caregiver dashboard, reminder management and API connection features.

### Database and RAG Foundation

- Database schema design was prepared.
- User, patient, routine and log table structures were planned.
- Initial ChromaDB vector database structure was prepared.
- Persona indexing structure was prepared for the RAG pipeline.

### Synthetic Patient Persona Data

A reusable JSON schema and five diverse synthetic dementia/Alzheimer patient profiles were created.

Added files:

- `data/synthetic_personas/persona_schema.json`
- `data/synthetic_personas/ahmet_yilmaz.json`
- `data/synthetic_personas/fatma_kaya.json`
- `data/synthetic_personas/mehmet_demir.json`
- `data/synthetic_personas/ayse_arslan.json`
- `data/synthetic_personas/hasan_karaca.json`

The JSON files were validated using:

```bash
python -m json.tool
```

The synthetic personas include different patient backgrounds, disease stages, daily routines, family relationships, personal memories, medication reminders, communication preferences and safety considerations.

## Completed Jira Tasks

| Jira ID | Task | Status |
|---|---|---|
| ORI-2 | Project folder structure setup | Done |
| ORI-3 | Node.js backend skeleton setup | Done |
| ORI-4 | Health check endpoint implementation | Done |
| ORI-5 | Database schema design | Done |
| ORI-6 | User, patient, routine and log tables | Done |
| ORI-7 | Synthetic patient persona JSON schema | Done |
| ORI-8 | Sample synthetic patient profiles | Done |
| ORI-9 | Persona indexing into vector database | Done |
| ORI-10 | Initial README documentation | Done |
| ORI-11 | Package, requirements and .gitignore setup | Done |
| ORI-12 | Node.js backend and Python AI services environment configuration | Done |
| ORI-13 | Sprint 1 board screenshots | Done |
| ORI-14 | Sprint 1 review and retrospective notes | Done |
| ORI-15 | ChromaDB vector database setup | Done |
| ORI-52 | Python AI service skeleton setup | Done |
| ORI-58 | React frontend skeleton setup | Done |

## Persona Diversity

| Persona | Disease Stage | Main Focus |
|---|---|---|
| Ahmet Yılmaz | Mild Alzheimer | Family recall, teacher background, orientation support |
| Fatma Kaya | Moderate Dementia | Visual memory, sewing memories, family photo support |
| Mehmet Demir | Moderate Alzheimer | Medication routine, blood pressure routine, caregiver support |
| Ayşe Arslan | Mild Alzheimer | Independent living, plant care, caregiver visit tracking |
| Hasan Karaca | Moderate Dementia | Visual memory, seaside memories, emotional safety |

---

## Sprint 1 Retrospective

### What Went Well

- The project scope became clearer after defining the OrientAI product name.
- Jira epics, tasks, story points and sprint structure were organized successfully.
- Team responsibilities became more understandable.
- The initial repository structure was organized according to the selected technology stack.
- Backend, frontend, AI services, database and RAG responsibilities were separated clearly.
- Synthetic patient persona data was created in a detailed and reusable format.
- Five patient personas were designed with different backgrounds, routines and memory contexts.
- The first GitHub workflow was completed successfully with branch, commit, push, pull request and merge steps.

### What Could Be Improved

- Some Jira task descriptions were missing at the beginning and had to be updated later.
- The difference between Sprint 1, Sprint 2 and Sprint 3 responsibilities needed clarification.
- Some tasks were initially too broad and required better separation by technology area.
- GitHub branches and Jira statuses should be synchronized more consistently.
- Future commits should reference related Jira tasks more clearly.

### Challenges

- Aligning the Jira backlog with the updated technology stack required extra edits.
- Sprint 1 infrastructure tasks had to be separated from later prompt, RAG, simulation and testing tasks.
- Since multiple technologies are used in the project, the initial folder structure and task ownership needed careful planning.
- The team needed to keep README documentation, Jira status and GitHub outputs consistent.

### Action Items for Sprint 2

- Keep Jira task descriptions consistent using User Story and Acceptance Criteria format.
- Ensure every completed task has a matching GitHub commit or documentation output.
- Start Sprint 2 with a clear focus on LLM, RAG and voice interaction features.
- Define prompt structure and RAG response rules in Sprint 2.
- Connect frontend, backend, AI services and database outputs more consistently.
- Update README after each major sprint output.
- Keep Jira statuses synchronized with GitHub pull requests.

---

## Conclusion

Sprint 1 established the initial planning, documentation, infrastructure and synthetic data foundation of OrientAI. This sprint created a strong base for the next phase, where RAG, LLM prompting, STT/TTS integration and patient interaction flows will be implemented.