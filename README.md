# CampusFix — AI-Assisted Campus Maintenance Intake

**CampusFix** is a campus maintenance intake prototype built with the Neuro-SAN agent framework. It transforms free-text maintenance complaints into structured assessments and proposes an appropriate Student Council routing path for human review.

> **Prototype status:** CampusFix supports assessment and routing recommendations. It does not create live work orders, dispatch staff, or initiate repairs.

## The Problem

Campus maintenance complaints often arrive as unstructured messages with unclear locations, issue types, urgency, and ownership. This can make consistent assessment difficult and increase the chance that duplicate reports go unnoticed.

## Our Solution

CampusFix combines a Neuro-SAN agent workflow with deterministic Python tools to structure complaint intake and recommend next steps.

### Key Features

- **Location resolution** — matches reported locations against a configured campus knowledge base.
- **Campus information queries** — recognizes direct questions about campus locations.
- **Issue classification** — categorizes maintenance reports using documented keyword rules.
- **Priority and safety assessment** — estimates priority and flags possible hazards for human review.
- **Duplicate assessment** — checks synthetic demo work orders for potentially similar reports.
- **Routing recommendations** — proposes eligible Student Council recipients using configured routing rules.
- **Readable reports** — presents the assessment and recommended next step in a structured format.

## How It Works

1. A user provides a maintenance complaint or campus-location question.
2. The Neuro-SAN agent workflow coordinates the relevant CampusFix tools.
3. Python rules perform structured assessment using the configured knowledge and policy data.
4. The system returns findings and, where applicable, a proposed routing path for human review.

See [architecture.md](architecture.md) for the system design and [backend/README.md](backend/README.md) for implementation details.

## Technology Stack

| Component | Technology |
|---|---|
| Agent orchestration | Neuro-SAN |
| Assessment logic | Python |
| Agent and tool configuration | HOCON |
| Knowledge and demo data | JSON |
| Model-provider configuration | OpenRouter |

## Repository Structure

```text
CampusFix-Submission/
├── backend/
│   ├── coded_tools/
│   │   └── campusfix/
│   ├── data/
│   ├── registries/
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   └── README.md
├── architecture.md
├── summary.md
├── THIRD-PARTY-NOTICES.md
├── .env.example
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python environment compatible with the authorized Neuro-SAN runtime.
- Access to an authorized Neuro-SAN installation compatible with the supplied HOCON registry.
- Valid model-provider credentials if required by the configured runtime.

### Setup and Execution

1. Review [backend/README.md](backend/README.md) for backend details.
2. Review `backend/requirements.txt` and the configuration in `backend/registries/campusfix.hocon`.
3. Configure any required provider credentials locally. Use `.env.example` as a reference, and never commit real API keys.
4. Follow the launch instructions for the authorized Neuro-SAN runtime.

**Important:** The exact installation and launch procedure must be verified in the target runtime environment. Configuration validation alone does not confirm that the complete application runs successfully.

## Frontend

The current prototype uses the Neuro-SAN Studio interface. This repository does not include a separate custom frontend application.

See [frontend/README.md](frontend/README.md) for details.

## Prototype Scope and Limitations

- Duplicate checking uses only the supplied synthetic local demo records.
- Routing results are recommendations and require human review.
- Complaints are not persisted as live work orders.
- The prototype does not notify staff, dispatch maintenance teams, or perform repairs.
- Keyword-based classification cannot establish actual on-site conditions.
- Campus knowledge and routing policies depend on the supplied configuration and may require review before real-world use.

**Safety note:** Report immediate hazards directly to the appropriate campus authority. Do not wait for automated intake or assessment.

## Project Documentation and Demo

- [Architecture description](architecture.md)
- [Project summary](summary.md)
- [Backend documentation](backend/README.md)
- [Frontend documentation](frontend/README.md)

## Responsible Use and Distribution

- Use synthetic data for demonstrations.
- Do not commit personal information, sensitive complaints, confidential campus data, or API credentials.
- Review the applicable third-party licenses and notices before distributing dependencies.
- Follow the hackathon rules governing access to and distribution of Neuro-SAN components.

CampusFix is intended as a hackathon prototype demonstrating agent-assisted maintenance intake and routing recommendations.