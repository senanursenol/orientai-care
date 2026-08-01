# ORIENTAI - Final Demo Scenario

## Demo Objective

The objective of this demonstration is to present the core capabilities of OrientAI within a maximum duration of **3 minutes**.

The demo focuses on showing how the system supports dementia and Alzheimer's patients through:

- Personalized patient personas
- Memory-supported conversations
- Voice interaction
- Image understanding and reminiscence support
- Caregiver dashboard
- Synthetic patient simulation
- Automatic conversation evaluation

---

# Demo Duration

Target duration: **3 minutes**

---

# Demo Flow

---

## Step 1 – Project Introduction (00:00 – 00:20)

### Screen

OrientAI Home Page

### Presenter

> Hello everyone.
>
> Today we present **OrientAI**, an AI-powered multimodal cognitive support assistant designed for people living with dementia and Alzheimer's disease.
>
> The system combines conversational AI, memory support, image understanding and caregiver assistance into a single platform.

---

## Step 2 – Patient Persona (00:20 – 00:40)

### Screen

Patient Profile

Display:

- Ayşe Arslan
- 76 years old
- Early Stage Alzheimer's Disease
- Former Primary School Teacher
- Lives in Beşiktaş
- Relative: Selin

### Presenter

> Every patient has a personalized synthetic persona.
>
> This persona contains long-term memories, routines, family relationships and personal preferences.
>
> The assistant uses this information to generate personalized and context-aware responses.

---

## Step 3 – Memory-Supported Conversation (00:40 – 01:20)

### Screen

Chat Interface

### Example Questions

Assistant:

> Merhaba Ayşe Hanım.

Patient:

> Merhaba evladım.

---

Assistant:

> Bugün nasılsınız?

---

Assistant:

> Sabah ilacınızı aldınız mı?

---

Assistant:

> Selin bugün saat 16.00'da sizi ziyaret edecek.

### Presenter

> During the conversation the assistant retrieves information from the patient's memory database using Retrieval-Augmented Generation (RAG).
>
> Responses remain consistent with the patient's history and emotional state.

---

## Step 4 – Voice Interaction (01:20 – 01:40)

### Screen

Voice Assistant

### Demonstration

Example voice question:

> Bugün ilacımı aldım mı?

Show:

- Speech-to-Text
- AI Response
- Text-to-Speech

### Presenter

> OrientAI also supports natural voice interaction, allowing elderly users to communicate without typing.

---

## Step 5 – Image Understanding & Reminiscence Therapy (01:40 – 02:00)

### Screen

Vision Module

Upload an old family photograph or classroom photograph.

Example prompt:

> Bu fotoğrafta ne görüyorsun?

or

> Bu bana neyi hatırlatıyor?

### Presenter

> The vision module analyzes uploaded images and can support reminiscence therapy by encouraging conversations around meaningful memories.

---

## Step 6 – Caregiver Dashboard (02:00 – 02:20)

### Screen

Caregiver Dashboard

Show:

- Patient Profile
- Conversation History
- Medication Reminders
- Emotional State
- Safety Alerts

### Presenter

> Caregivers can monitor conversations, reminders and patient wellbeing through the dashboard.

---

## Step 7 – Synthetic Patient Simulation & Evaluation (02:20 – 02:50)

### Screen

Terminal

Run

```bash
python -m app.ai.simulation.run_simulation
```

Show only the final part of the output.

Display:

- Conversation Summary
- Assistant Evaluation

Especially:

```
Overall Score

RAG

Safety

Empathy

Guidance
```

### Presenter

> The project also includes a synthetic patient simulator.
>
> The assistant communicates with a virtual dementia patient generated from a structured persona.
>
> At the end of each conversation, a second AI agent automatically evaluates the assistant according to:
>
> - RAG groundedness
> - Hallucination
> - Empathy
> - Guidance
> - Safety

This allows automatic quality assessment of assistant responses.

---

## Step 8 – Closing (02:50 – 03:00)

### Presenter

> OrientAI combines multimodal AI, personalized memory support, patient simulation and automated safety evaluation into a single platform to support both patients and caregivers.
>
> Thank you for watching.

---

# Demo Assets

## Patient Persona

- Ayşe Arslan JSON

---

## Conversation

Use the prepared simulation conversation.

---

## Voice Example

Question:

> Bugün ilacımı aldım mı?

---

## Vision Example

Image:

- Family photo
or
- Classroom photo

Question:

> Bu fotoğrafta ne görüyorsun?

---

## Dashboard

Show:

- Conversation history
- Reminder cards
- Patient information

---

## Simulation

Run:

```bash
python -m app.ai.simulation.run_simulation
```

---

# Demo Checklist

Before recording the demo, verify the following:

- [ ] OrientAI homepage is ready
- [ ] Patient persona is available
- [ ] Chat interface is working
- [ ] Voice interaction is functional
- [ ] Vision module is ready
- [ ] Caregiver dashboard is accessible
- [ ] Patient simulation runs successfully
- [ ] Assistant evaluation is displayed
- [ ] Terminal output is readable
- [ ] Required images are prepared
- [ ] Recording duration is under 3 minutes

---

# Expected Demo Outcome

By the end of the demonstration, evaluators should clearly understand that OrientAI provides:

- Personalized dementia support
- Memory-aware conversations
- Voice interaction
- Image understanding
- Reminiscence therapy support
- Caregiver monitoring
- Synthetic patient simulation
- Automatic conversation quality evaluation
- Safe and context-aware AI responses

The complete demonstration should remain within **3 minutes** while showcasing the project's main capabilities in a clear and structured manner.