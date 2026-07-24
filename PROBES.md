# PROBES — Test 2: Recall vs Manipulation (photograph vs usable knowledge)

**Question (Nikhil's Test 2):** when a trained arm fails the bench, is that because the book's
content was never STORED, or stored as an inert photograph that can't be USED? Two probe sets
split the diagnosis, and their verdict decides "how the divergence we have to do" (whether
run 4b multi-angle rendering is the indicated fix).

## Design (FROZEN 2026-07-24, before any inference)

- **Source:** 24 principles stratified-sampled across `lane_pages_train.jsonl` page_idx range
  (the same Clausewitz principles the run-4 scenes were rendered from — so the probes test
  exactly what laneF was supposed to internalize and what book_C06 read raw).
- **Two probes per principle** (drafted by Sonnet 5 native, code-validated, human readback):
  - `recall_q` — direct doctrine question; answering = stating the principle. No scene
    surfaces, no principle 5-grams embedded in the question.
  - `manip_q` — novel non-military two-path scenario; correct resolution requires the
    principle's MECHANISM; principle never stated; wrong path superficially attractive;
    ends "Which path, and what happens if you choose wrong?" + hidden `manip_key` grading key.
- **Validation gates (code, not judgment):** JSON schema; length bounds; 5-gram leakage check
  (no principle 5-gram may appear in either probe); scene-name ban list (injection-pool
  names); Path 1/Path 2 required in manip_q. Plus full human readback of all pairs.
- **Arms probed (pod A card, greedy, wrk seat only):** `base`, `keep100` (wrk_keep1.0 —
  the no-book control), `book_C06` (raw Clausewitz), `laneF` (transformed), `fedH`
  (fresh-book arm; Clausewitz probes are a NEGATIVE control for it — it should NOT move).
- **Grading:** Sonnet 5, blind to arm labels, one call per (probe, answer), 0–2 scale:
  - recall: 0 = principle absent/contradicted; 1 = partial/adjacent; 2 = correctly stated.
  - manip: 0 = wrong path or no mechanism; 1 = right path, weak/generic why; 2 = right path
    AND the consequence matches the principle's mechanism (per manip_key).

## Frozen reads (mean over 24, 0–2 scale; Δ = arm − keep100)

1. **STORAGE:** Δrecall ≥ +0.30 → the book's content IS stored in that arm.
2. **USABILITY:** Δmanip ≥ +0.30 → the content is manipulable knowledge in that arm.
3. **PHOTOGRAPH VERDICT (the 4b decision rule, applied to laneF):**
   - STORAGE holds, USABILITY fails → single-angle transformation stored photographs →
     **multi-angle re-render (run 4b) is the indicated divergence.**
   - Both fail → content not even stored → arrangement/exposure issue — read the RUN-6 sweep
     before touching rendering.
   - Both hold → storage AND usability fine at probe level → the bench shortfall is
     TRANSFER, not storage → capacity story strengthens, 4b unlikely to pay.
4. **RAW-VS-TRANSFORMED STORAGE:** same reads on book_C06 vs laneF — does transformation
   change what gets stored at equal step budgets?
5. **NEGATIVE CONTROL:** fedH on Clausewitz probes should sit within ±0.20 of keep100 on
   both sets; a big move means the probes measure something generic, and all probe reads
   are demoted to exploratory.
6. Base is reported (Clausewitz prior exists in pretraining) but reads use keep100 as the
   reference, since every arm shares base's prior plus v5 SFT.

## Fingerprint

- `data/probes/probes.jsonl` md5: `201d71746bb9beb54b24883fc1e15ae8` — 24 pairs, generated
  2026-07-24, validation gates fired 3x during generation (2 principle-leak redrafts, 1
  scene-name redraft), full human readback passed (incl. P05-vs-P07 decisive-vs-protracted
  consistency check and P15 barrier-scale key check). FROZEN — no edits after this point.

## RESULTS (2026-07-24, blind Sonnet 5 grading, 24/24 coverage every arm)

Main batch (pod-A answers; Δ vs keep100; regrade replicated every read within ±0.1):

| arm | Δrecall | Δmanip | read |
|---|---|---|---|
| base | −0.08..−0.17 | −0.21 | (v5 SFT slightly helps both) |
| book_C06 (raw book) | +0.04..+0.13 | −0.17..−0.13 | no storage, no usability |
| laneF (transformed) | +0.08..+0.17 | +0.04..+0.13 | no storage, no usability |
| fedH (negative ctrl) | −0.04..+0.08 | −0.04..0.00 | control behaves — instrument valid |

Exposure extension (pod-B sweep arms): Δrecall at 1.25×/5×/10×/20× = +0.04/−0.08/−0.17/+0.04
— no storage at any exposure.

**VERDICT (frozen rule): NOT STORED.** Neither raw reading nor single-angle transformation
puts retrievable Clausewitz content into the 3.4B, at any exposure from 1.25 to 20 per page.
This is NOT the photograph failure mode (which would be recall-high/manip-flat) — recall
itself never moves. Per the frozen branch: with the sweep also flat, the surviving suspects
are presentation-diversity (multi-angle 4b, per Allen-Zhu diverse-presentations-create-
extractable-storage) and capacity/modality (LoRA continuation at 3.4B cannot write
extractable knowledge). 4b's motivation SHIFTS: it would now be testing
diversity-for-STORAGE, not diversity-for-usability.

## Isolation

Probe files live in `data/probes/` (never mixed into training data or bench_data). Answers:
`out/probe_answers_<arm>.jsonl` on pod A; grades: `out/probe_grades.json` local. No probe
content is ever used as training input for any adapter.
