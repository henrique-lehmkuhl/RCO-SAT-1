# Educational CubeSat Project

Systems engineering documentation for an educational CubeSat portfolio
project, structured around the classic Systems Engineering process
(need → requirements → architecture → subsystem design → verification
and validation → schedule), following the conventions used in real
CubeSat missions (CubeSat Design Specification, NASA CSLI/GSFC handbooks,
and ECSS guidelines adapted to small-scale projects).

Each document is a skeleton: it holds the section structure the systems
engineering process requires, but the content is filled in incrementally,
with dated revisions, as the project develops.

## Revision convention

Every document starts with a **Revision history** section:

| Date | Version | Description | Author |
|---|---|---|---|
| _(TBD)_ | v0.1 | Skeleton created | |

Each meaningful content change becomes a new row, with a date and an
incremented version (v0.1, v0.2, ...). The **Status** field at the top of
the document shows the current state: `Skeleton`, `Draft`, `In review`, or
`Approved`.

## Document structure

| File | SE Phase | Content | Status |
|---|---|---|---|
| `01_Mission_Need_and_Objectives.md` | Phase 0 — Need analysis | Motivation, mission objectives, CONOPS, constraints | Skeleton |
| `02_System_Requirements.md` | Phase A — Requirements | Mission, functional and performance requirements, traceable | Skeleton |
| `03_Architecture_and_Budgets.md` | Phase A/B — Architecture | Block architecture, mass/power/data/link budgets | Skeleton |
| `04_Subsystem_Structure.md` | Phase B — Preliminary design | Mechanical structure, layout, integration | Skeleton |
| `05_Subsystem_EPS.md` | Phase B | Electrical power | Skeleton |
| `06_Subsystem_OBDH.md` | Phase B | On-board computer and software | Skeleton |
| `07_Subsystem_ADCS.md` | Phase B | Attitude determination/control | Skeleton |
| `08_Subsystem_TTC.md` | Phase B | Telemetry, tracking and command | Skeleton |
| `09_Payload.md` | Phase B | Payload | Skeleton |
| `10_Verification_and_Validation_Plan.md` | Phase C/D — V&V | Test plan, traceability matrix | Skeleton |
| `11_Schedule_and_Milestones.md` | Management | WBS, project reviews, risks | Skeleton |

## Development order

The order follows the actual dependency chain of the engineering process:
01 → 02 → 03 → subsystems (04–09) → 10 → 11. Project reviews (MDR, SRR,
PDR, CDR, TRR, ORR, FRR), detailed in file 11, mark the transition points
between phases.

## Using this with Git/GitHub

- `CHANGELOG.md` at the root tracks the history of the project as a
  whole; the revision history at the top of each document tracks that
  document's own history.
- Each content revision is meant to become a commit — suggested commit
  message format: `docs(NN): <summary of the change> — vX.Y`.
- `.gitignore` covers common editor/OS artifacts — this repository is
  Markdown documentation only.
