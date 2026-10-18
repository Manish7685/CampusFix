# CampusFix Frontend

## Overview

CampusFix currently uses the Neuro-SAN Studio interface as its user-facing interface. This submission does not include a separate custom frontend application.

Users interact with the CampusFix agent through an authorized Neuro-SAN Studio runtime.

## User Interaction Flow

1. The user submits a campus maintenance complaint or a campus-location question through the interface.
2. The Neuro-SAN agent workflow coordinates the relevant CampusFix coded tools.
3. The tools perform supported operations, such as location resolution, maintenance issue classification, priority assessment, duplicate checking against synthetic demo records, and routing recommendations.
4. The resulting assessment and recommended next step are returned through the agent interface for human review.

Not every request requires every operation; the workflow depends on the user's request and the configured agent behavior.

## Scope and Limitations

- No separate custom frontend application is included in this repository.
- The interface depends on an authorized Neuro-SAN Studio runtime compatible with the CampusFix configuration.
- Routing results are recommendations, not confirmed assignments.
- The prototype does not dispatch maintenance staff, send operational notifications, or persist complaints as live work orders.

## Related Documentation

- [Project overview](../README.md)
- [System architecture](../architecture.md)
- [Project summary](../summary.md)
- [Backend documentation](../backend/README.md)