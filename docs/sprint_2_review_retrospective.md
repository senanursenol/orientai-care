# Sprint 2 Review and Retrospective

## Project

OrientAI — Multimodal Cognitive Support Assistant for Dementia and Alzheimer Patients

## Sprint

Sprint 2 - AI Services & Frontend Integration

## Sprint Status

Completed

## Sprint Duration

6 July 2026 - 19 July 2026

## Sprint Goal

Develop the core AI interaction capabilities of OrientAI by integrating Speech-to-Text (STT), Text-to-Speech (TTS), Turkish sentiment analysis, safety detection, RAG prompt development, frontend interaction flows and AI service testing infrastructure.

The main objective of Sprint 2 was to transform the initial infrastructure created in Sprint 1 into a functional AI interaction pipeline where users can provide text and voice inputs and receive analyzed results.

---

## Sprint Board

![Sprint 2 Backlog](../assets/sprint_boards/sprint_2_backlog.png)

---

# Sprint 2 Review

Sprint 2 focused on developing the artificial intelligence service layer and connecting these services with the frontend interface.

During this sprint, the team implemented the first functional AI interaction components of OrientAI, including speech processing, sentiment analysis, safety detection, RAG prompt development and frontend result visualization.

The sprint created the foundation for future LLM-based response generation and multimodal patient interaction features.

---

# Completed Work

## AI Service Development

### Speech-to-Text (STT) Service

A Whisper-based speech recognition pipeline was developed to convert user voice inputs into text.

Completed tasks:

- Audio input processing.
- Whisper model integration.
- Speech transcription.
- Language detection.
- Transcription confidence calculation.
- Audio validation and error handling.

Service structure:
services/
└── mentes-ai-service/
└── app/
└── services/
└── stt/
├── audio_processing.py
├── voice_input.py
└── whisper.py


---

## Text-to-Speech (TTS) Service

A TTS module was integrated to provide voice output capabilities for OrientAI responses.

Completed tasks:

- Text-to-audio conversion.
- TTS service structure preparation.
- Audio response generation flow.

Service structure:
services/
└── mentes-ai-service/
└── app/
└── services/
└── tts/
└── tts.py


---

## Turkish Sentiment Analysis and Safety Detection

A Turkish sentiment analysis service was developed to analyze user emotional states.

Supported categories:

- Positive
- Negative
- Neutral
- Anxious


A separate safety analysis layer was implemented to detect potentially critical situations.

The system evaluates:

- Threat-related expressions.
- Risk signals.
- Anxiety indicators.
- Attention-required situations.


Service structure:
services/
└── mentes-ai-service/
└── app/
└── services/
└── sentiment/
└── sentiment.py


The analysis output contains:

- Sentiment label.
- Confidence score.
- Probability scores.
- Safety status.
- Detected signals.

---

# RAG Prompt Development

Sprint 2 continued the RAG foundation created during Sprint 1.

Completed tasks:

- Patient memory context integration.
- Prompt template development.
- Context usage rules.
- Hallucination prevention rules.
- Prompt validation.


The developed prompt structure ensures that the model only uses retrieved patient information and avoids generating unsupported details.

---

# Prompt Testing Results

## RAG Context Test

The system was tested to verify that retrieved patient information is correctly transferred into the prompt context.

![RAG Context Test](../assets/tests/rag_prompt_context_test.png)


---

## Hallucination Prevention Test

The system was tested to ensure that responses are generated only from available context information.

![Hallucination Prevention Test](../assets/tests/rag_hallucination_prevention_test.png)


---

## Prompt Validation Test

Prompt generation and validation process were successfully completed.

![Prompt Test Success](../assets/tests/prompt_test_success.png)


---

# Frontend Integration

The frontend interface was connected with AI service outputs.

Completed features:

- Text input analysis.
- Voice input analysis.
- Sentiment result visualization.
- Confidence score display.
- Safety warning visualization.


The frontend allows users to observe AI analysis results through a simple and understandable interface.

---

# Frontend Analysis Results

## Positive Sentiment Example

The system successfully detected positive emotional expressions and displayed the confidence score.

![Positive Sentiment](../assets/screenshots/frontend_text_positive_sentiment.png)


---

## Negative Sentiment Example

The system successfully detected negative emotional expressions and provided analysis feedback.

![Negative Sentiment](../assets/screenshots/frontend_text_negative_sentiment.png)


---

## Voice Analysis Example

The complete voice pipeline was tested:

1. Voice input received.
2. Speech converted into text.
3. Sentiment analysis performed.
4. Result displayed on frontend.

![Voice Analysis](../assets/screenshots/frontend_voice_analysis_result.png)

---

# Testing

Sprint 2 included test development for validating AI service behavior.

Tested components:

- STT processing.
- Audio processing.
- Sentiment analysis.
- Safety detection.
- RAG prompt validation.
- Hallucination prevention.


Test structure:
test/

├── asset/
├── evaluation/
├── fixtures/
└── services/
└── mentes-ai-service/
├── integration/
└── unit/


---

# Completed Jira Tasks

| Jira ID | Task | Status |
|---|---|---|
| ORI-20 | RAG prompt validation tests | Done |
| ORI-21 | Patient interaction flow improvements | Done |
| ORI-22 | Voice interaction development | Done |
| ORI-52 | AI service development improvements | Done |
| ORI-59 | Patient chat interface development | Done |
| ORI-60 | STT service integration | Done |
| ORI-61 | TTS service integration | Done |
| ORI-62 | Sentiment analysis module | Done |
| ORI-63 | Safety detection mechanism | Done |

---

# Sprint 2 Retrospective

## What Went Well

- AI service modules were developed with a more organized structure.
- STT, TTS and sentiment services were separated into independent components.
- Frontend and AI service communication was successfully established.
- RAG prompt rules improved context-aware response preparation.
- Test scenarios helped validate system behavior.
- Team collaboration and GitHub workflow improved compared to Sprint 1.

---

## What Could Be Improved

- Service folder structures should be finalized earlier before implementation.
- Branch synchronization should be performed more frequently.
- Dependency management for AI services should be documented earlier.
- Frontend and backend API contracts should be defined before integration.
- Testing should start earlier instead of being completed near the sprint deadline.

---

## Challenges

- Integrating independently developed services required additional adjustments.
- Merge conflicts occurred while combining different development branches.
- Python dependency management required extra configuration.
- Maintaining consistency between GitHub, Jira and documentation required additional coordination.

---

## Action Items for Sprint 3

- Complete LLM response generation pipeline.
- Improve RAG retrieval and memory management.
- Add multimodal vision capabilities.
- Improve caregiver interaction features.
- Expand end-to-end testing.
- Optimize AI service deployment structure.
- Continue updating documentation after each sprint output.

---

# Conclusion

Sprint 2 successfully transformed OrientAI from an infrastructure-focused project into a functional AI interaction system.

The team completed STT, TTS, sentiment analysis, safety detection, RAG prompt development and frontend integration.

These improvements created the foundation required for Sprint 3, where advanced multimodal AI capabilities and final system improvements will be implemented.