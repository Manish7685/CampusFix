# CampusFix Backend

The CampusFix backend implements the tool layer for an AI-assisted campus maintenance intake and routing prototype built with Neuro-SAN.

It combines a Neuro-SAN coded-tool adapter, deterministic Python assessment rules, and JSON configuration data to produce structured findings and routing recommendations for human review.

## 1. Components

| File or directory | Responsibility |
|---|---|
| `coded_tools/campusfix/campusfix_tools.py` | Exposes CampusFix operations through the Neuro-SAN coded-tool interface. |
| `coded_tools/campusfix/campusfix_rules.py` | Implements location resolution, complaint classification, priority assessment, duplicate checking, and routing proposal logic. |
| `registries/campusfix.hocon` | Defines the agent, tool, and language-model configuration. |
| `data/campus_knowledge.json` | Provides configured campus location knowledge. |
| `data/demo_work_orders.json` | Supplies synthetic example work orders for duplicate assessment. |
| `data/student_council_routing.json` | Defines the routing rules used to propose eligible Student Council recipients. |
| `requirements.txt` | Lists the backend Python dependency requirements. |

## 2. Processing Workflow

The backend supports the following logical workflow:

1. Receive a campus-location question or maintenance complaint.
2. Resolve the reported location against the configured campus knowledge, where applicable.
3. For maintenance complaints, classify the issue and assess priority using deterministic keyword-based rules.
4. Compare the report with the available synthetic demo records to identify possible duplicates.
5. Propose eligible Student Council recipients according to the configured routing rules.
6. Return the available assessment results for human review.

Not every request requires every operation. Direct campus-location questions are handled as information requests rather than maintenance complaints.

## 3. Requirements

The backend requires:

- A Python environment compatible with the authorized Neuro-SAN runtime.
- The `neuro-san` package version specified in `requirements.txt`.
- An authorized Neuro-SAN Studio/runtime installation capable of loading the supplied registry and exposing the agent interface.
- Any model-provider credentials required by the registry configuration.

### Install Dependencies

From the `backend/` directory, run:

```bash
python -m pip install -r requirements.txt
```

Use an appropriately configured virtual environment and follow the installation requirements of the authorized Neuro-SAN distribution.

**Runtime note:** The exact server launch and registry-loading commands depend on the authorized runtime installation. These commands must be verified in that environment before the project can be described as fully runnable.

## 4. Configuration

The agent registry is located at:

`registries/campusfix.hocon`

It defines the agent/tool configuration and model-provider settings used by the workflow. The current configuration specifies an OpenRouter model configuration; confirm the exact model and credential requirements in the registry before running the application.

Configure credentials through the environment mechanism supported by the authorized runtime. Do not commit real API keys, passwords, or other secrets.

### Optional Data-Path Environment Variables

CampusFix supports the following optional environment variables for data-file locations:

| Variable | Purpose |
|---|---|
| `CAMPUSFIX_KNOWLEDGE_PATH` | Path to the campus knowledge JSON file. |
| `CAMPUSFIX_RECORDS_PATH` | Path to the synthetic demo work-orders JSON file. |
| `CAMPUSFIX_ROUTING_PATH` | Path to the Student Council routing JSON file. |

If configured, each variable must point to a readable JSON file with the structure expected by the implementation. If these variables are not set, the code's default data-path behavior applies.

## 5. Data Sources

The backend uses local JSON files rather than a live campus maintenance database.

- **Campus knowledge:** Supports location resolution and related campus information requests.
- **Synthetic work orders:** Supports local duplicate assessment against example records.
- **Routing policy:** Supports recommendations based on configured Student Council roles and rules.

These data sources should be reviewed before public distribution to ensure that they contain no personal information, confidential records, or other restricted campus details.

## 6. Safety and Limitations

CampusFix is a decision-support prototype, not a production maintenance management system.

- **Keyword-based assessment:** Classification and priority results are preliminary rule-based assessments, not verified diagnoses of on-site conditions.
- **Location resolution:** A matching location candidate does not automatically mean the reporter has confirmed that location.
- **Limited duplicate checking:** The duplicate assessment examines only configured local records and does not query a live database.
- **Proposed routing:** Council routing is a recommendation, not a saved assignment or dispatch.
- **No live work-order persistence:** Complaints are not stored as live work orders by the current implementation.
- **No operational actions:** The backend does not notify technicians, dispatch maintenance teams, or perform repairs.
- **Human review:** High-priority or critical results require appropriate human attention.

**Safety note:** Immediate hazards should be reported directly to the appropriate campus authority without waiting for automated intake or assessment.

## 7. Related Documentation

- [Project overview](../README.md)
- [System architecture](../architecture.md)
- [Project summary](../summary.md)
- [Frontend documentation](../frontend/README.md)
- [Third-party notices](../THIRD-PARTY-NOTICES.md)