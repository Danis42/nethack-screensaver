# Decisions (ADR intel)

No ADR-classified documents are in the ingest set (11 docs: 9 SPEC, 2 DOC), so there are no
locked decisions and no `status: locked` entries. Nothing was fabricated to fill this file.

Where decisions live instead (do not treat any of these as locked):
- SPEC "Decisions" tables and bullet lists (status in the sources: "Approved design, pending
  spec review", or undated brainstorm decisions) are carried verbatim in `constraints.md`
  under each spec's entries.
- Dated, user-stated project directives from the two DOCs (ROADMAP "Decided 2026-10-20",
  STATUS "Ascension is the only priority (user, 2026-10-21)", "Never push; merge finished,
  tested branches to main locally") are recorded in `context.md` under "Project direction
  and priority". They are the current direction of the project and supersede earlier SPEC
  text where they differ; see the INFO entries in `.planning/INGEST-CONFLICTS.md`.
