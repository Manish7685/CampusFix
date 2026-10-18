# CampusFix — AI-Assisted Campus Maintenance Intake

## Project Summary

CampusFix is a campus maintenance intake prototype built using the Neuro-SAN agent framework. It turns free-text maintenance complaints into structured assessments and proposes appropriate Student Council routing paths for human review.

The project demonstrates how agent orchestration, coded tools, deterministic Python rules, and structured data can work together to support a practical campus operations workflow.

## The Problem

Campus maintenance reports may arrive as informal messages with incomplete or ambiguous information about location, issue type, urgency, and ownership. Assessing these reports consistently can be difficult, and similar reports may go unnoticed.

A structured intake process can help organize the information, identify possible duplicates, and recommend a suitable next step while keeping people responsible for final decisions.

## Our Solution

CampusFix processes supported requests through a Neuro-SAN agent workflow connected to custom Python coded tools. Its capabilities include:

- **Location resolution:** Matches reported locations against configured campus knowledge.
- **Issue triage:** Classifies maintenance issues using documented keyword-based rules.
- **Priority and safety assessment:** Estimates priority and flags potential hazards for human review.
- **Duplicate assessment:** Checks synthetic demo work orders for possible matches.
- **Routing recommendations:** Uses configured Student Council routing rules to propose eligible recipients.
- **Structured reporting:** Returns findings and a recommended next step.

The prototype supports both maintenance intake and direct campus-location questions where applicable.

## How the Agentic Workflow Works

The user submits a request through the Neuro-SAN Studio interface. A Neuro-SAN agent workflow coordinates the relevant CampusFix tools, which apply structured rules and consult the configured JSON data.

The HOCON registry defines the agent and tool configuration. Python coded tools provide the application-specific operations, while separate JSON files supply campus knowledge, synthetic work-order examples, and routing policy.

This separation keeps orchestration, assessment logic, and data configuration distinct, making the prototype easier to inspect and extend.

## Technology Stack

| Component | Technology |
|---|---|
| Agent orchestration | Neuro-SAN |
| Assessment logic | Python |
| Agent and tool configuration | HOCON |
| Knowledge and demo records | JSON |
| Model-provider configuration | OpenRouter, subject to configuration verification |
| User interface | Neuro-SAN Studio interface |

## What Makes CampusFix Useful

- **Practical application:** Addresses the everyday challenge of organizing campus maintenance reports.
- **Agent-tool coordination:** Uses Neuro-SAN to coordinate application-specific operations.
- **Structured decision support:** Combines configured knowledge and deterministic rules to produce consistent assessment outputs.
- **Modular design:** Separates the agent registry, Python tools, and data files.
- **Human oversight:** Presents routing and assessment results as recommendations rather than automatically taking operational action.

## Current Scope and Limitations

CampusFix is a prototype, not a live campus maintenance management system.

- Duplicate checking uses only the supplied synthetic local records.
- Routing recommendations require human review.
- Complaints are not persisted as live work orders.
- The system does not notify staff, dispatch maintenance teams, or perform repairs.
- Keyword-based classification cannot verify actual on-site conditions.
- Runtime execution must be verified in the authorized Neuro-SAN environment.

Immediate hazards should be reported directly to the appropriate campus authority rather than waiting for automated assessment.

## Project Structure

The submission includes the CampusFix coded tools, HOCON registry, JSON data, backend documentation, architecture description, and project summary. The current prototype uses the Neuro-SAN Studio interface and does not include a separate custom frontend application.

See [README.md](README.md) for the project overview and [architecture.md](architecture.md) for the technical design.

## Conclusion

CampusFix demonstrates a modular approach to agent-assisted campus maintenance intake using Neuro-SAN. It combines tool-based assessment, configured knowledge, and routing recommendations into a workflow intended to help organize maintenance reports while preserving human responsibility for decisions and actions.