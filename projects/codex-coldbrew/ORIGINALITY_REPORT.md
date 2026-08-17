# Originality Audit — v6.0.0

This v6 audit compares the current product candidate tree directly with the
current reference tree. It does not depend on a historical ZIP extraction.
Generated archives, backups, Git metadata, licenses, provenance records and
source-map ledgers are excluded as non-product comparison noise; implementation,
tests, Skills, Pages, workflows and product documentation remain in scope.

## Reproducible Evidence

- Candidate tree: `C:\Users\Administrator\Documents\Codex\2026-08-07\new-chat-2\work\codex5.6-coldbrew`
- Candidate text/code files: `67`
- Candidate manifest SHA-256: `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`
- Reference tree: `C:\Users\Administrator\Documents\Codex\2026-08-07\new-chat-2\work\references`
- Reference text/code files: `916`
- Reference manifest SHA-256: `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`
- Machine-readable evidence: [`docs/originality-evidence-v6.json`](docs/originality-evidence-v6.json)

## Results

- Byte-identical candidate files: `0` / threshold `<= 0`
- Normalized candidate-line overlap: `0.5106%` / threshold `<= 12%`
- Longest normalized common block: `4` contiguous lines / threshold `<= 12`
- Foreign copyright headers: `0` / threshold `<= 0`
- Result: `PASS`

The audit intentionally removes the exact `冷咖啡` / `cold coffee` interface
identifiers before normalized text comparison. This narrowly prevents a shared
public activation label from creating a false match; no product code, tests,
page content, workflow, or prompt body is blanket-excluded.

Reference repositories are research inputs only. Their source, prompts, Skills,
tests, visual assets, schemas and release artifacts are not shipped in this
repository or its source archive.
