# titterpig-dsl-arm5e — TODO

Status as of 2026-07-26 (evening). Corpus validates **arm5e 100 files 0/0, armdef 40 files
0/0**; MENTIONS arm5e 2167 / armdef 1431 (both 0 unresolved / 0 surface-mismatch);
MODIFY/no-armdef-type gates clean; sources.json fully synced (146/146).

**COMMITTED** (not pushed): corpus `a1466f8` (coverage + record gaps) → `a84d4fd` (Things-of-
Virtue verbatim write-ups); titterpig-mastra `7868d97` (builders/manifests); titterpig-dsl
`82bb5c5` (MENTIONS tooling + spec). RoP:Magic Ch8 Things-of-Virtue write-ups now recovered
verbatim via a column-aware PDF re-extraction (the HTML slice was displaced) — the flagged
extraction defect is RESOLVED.

## 2026-07-27 — supplements → 0.5.0 COMPLETE; core 0.5.1 (Houses + duplicate tables)
Both cores + all 5 supplements now fully 0.5-compliant: validator arm5e 104/0/0 + armdef 41/0/0,
references 0 hashless both, constructs 0 err, **all 6 arm5e coverage gates + armdef PASS**. The
five supplements' previously-deferred "sidebars-only" gap (217 Text Boxes) was **backfilled**
(owner call): verbatim GUIDANCE + structured TABLE DEFs in new `*-0.5-sidebars.ttrpg`. Grogs
editorial records → GUIDANCE. Full hashless disambiguation done (owner-reviewed per cluster).
Core 0.5.1: consolidated duplicate `^"Damage Table"` / `^"Advancement Table"` DEFs; Houses
restructured (mechanical DEF + verbatim `arm5e-0.5-houses.lore`, OoH dup DEFs dropped).
Committed/pushed: arm5e `8051006`, mastra `234bb21`, dsl `df12989`. **Live state-of-record now
lives in `titterpig-mastra/worklogs/DSL-0.5-worklog.md`** — the sections below are pre-2026-07-27 history.

### FUTURE PASS — apply the Houses-restructure pattern to other long-DESCRIPTION core records
The Houses restructure split each `^"House X"` into a **mechanical DEF** (`EXTENDS "Hermetic
House"` + PROPERTIES) plus **verbatim narrative in `.lore`** (`arm5e-0.5-houses.lore`, pointing
back to the DEF). Other core records that carry long narrative prose inside a DEF `DESCRIPTION`
are candidates for the same treatment (mechanics stay structured; story → `.lore`, mirror not
duplicate). Not yet surveyed — a future pass could `grep` for oversized `DESCRIPTION` bodies on
mechanical DEFs and reconcile each verbatim against source, as was done for the 12 Houses.

## Current effort — five supplements: coverage + record-gap remediation **DONE**

The coverage pass revealed the "record buckets done" milestone measured built buckets, not the
source's enumerable sets — ~260 genuine mechanical records had been skipped. Those are now
**built, verbatim, gated**. All five books are at **sidebars-only** (every record gap closed,
every narrative section captured verbatim to `.lore`, all structural excluded-with-reason):
grogs 0 uncovered (coverage PASS); covenants 39 / faerie 37 / rop-magic 76 / hedge 65 uncovered
— **all content sidebars**, the owner's deferred audit.

Record gaps built (deterministic-from-source, all validating): **RoP:Faerie** 12 Ars-Fabulosa
spells + 21 R/D/T params; **RoP:Magic** ~123 (15 spells, 77 creature-powers→addressable Power
DEFs, 15 vis, 10 modifier tables, item, Jinn, beast-virtues, gap-types); **Covenants** ~100
(craft/scribal/librarian/ward/lab spells, 17 devices, tables, guidelines, **21 sample covenfolk
→ Companion-type DEFs**, **9 example laboratories → Laboratory DEFs**, Virtuous Hound + Familiar
Cat); **Hedge** 6 Magic Defenses. `.lore` for all narrative chapters. MENTIONS re-run over both
editions (`apply_mentions.py` made idempotent — strips existing blocks before re-adding).

### Remaining — BOTH deferred by the owner (2026-07-26)
1. **The 234 content sidebars** — `.lore` vs `.ttrpg` per sidebar is the owner's audit. All
   pre-classified with recommendations in the per-book reports (scratchpad `report-<book>.md`);
   coverage gates FAIL by design until these are dispositioned. Owner said defer.
2. **Core wound/recovery DEFs** (`Light/Medium/Heavy/Incapacitating Wound`, `Recovery Roll`) so
   ~300 supplement description terms MENTIONS-link. Owner has "a different idea" — revisit.
   Apply-ready package + pre-minted anchors at scratchpad `OWNER-DECISION-core-wound-defs.md`.

### Known extraction defect (flagged, owner-aware)
RoP:Magic Ch8 Things-of-Virtue write-up prose is DISPLACED in the HTML extraction (paragraphs
misattributed under wrong headings). NOT built from the bad extraction; the 25 Things stay
covered by their verbatim Shape&Material records. Needs a targeted re-extraction of p.55-130.

### Flagged (deferred, owner-aware) — see DECISIONS-FOR-MORNING.md
- **Page-cite strip is incomplete** (~40 residual ArM5/RoP cites in arm5e; armdef clean).
  `apply_mentions.py`'s `PAGE_RE` is case-sensitive and DESCRIPTION-only, so it missed
  capital-S `(See ArM5, page N)`, the prose form `(See the Virtue on page N of ArM5.)`,
  and cites inside note-properties / `LIST` tables. **Not a regex sweep:** many residuals
  are entity references (`(see the Lightning Reflexes Virtue, ArM5 page 45)`,
  `(ReMe as Enslave the Mortal Mind, ArM5 page 152)`) where only the page-locator should
  go, not the whole clause. Needs a considered pass.
- **MENTIONS hash-qualification unsupported.** Load-bearing refs (EXTENDS, MODIFY) are
  hash-fixed; MENTIONS to ambiguous names stay by-name because `MENTIONS` isn't in the
  grammar and `check_mentions.py` can't parse a hash target. Recommend leaving MENTIONS
  by-name (non-load-bearing see-also links) unless the construct is formally extended
  (grammar + `apply_mentions` emit + `check_mentions` parse).
- **MENTIONS LLM refinement (optional).** Single-word / inflected links the deterministic
  pass skips on purpose (Wealth, Road, Vim) could be added by a high-confidence LLM pass.

### Rebuild caveat
The corpus is source-of-truth (post-MENTIONS). The `Magical (Being) Companion` spelling
and the removed Grogs `Master of (Form) Creatures` DEF diverge from the deterministic
builders' ground truth — sync the GT / check_rosters pins first if anyone re-runs
`buildRopMagic` / `buildGrogs`.

## Next queue — sourcebooks to convert after the current five

All in `/home/hewhocutsdown/Working/Arm5e Sourcebooks/`. Each is an EXTENSION on the
`arm5e` edition (or a new dependency where it originates content the current five
reference — e.g. Lords of Men, City & Guild, The Cradle & The Crescent are already named
as blocked-on-dependency origins in Grogs templates and Master of Kennels).

- `Apprentices.pdf`
- `City & Guild.pdf`
- `Art & Academe.pdf`
- `Houses of Hermes - Mystery Cults.pdf`
- `Houses of Hermes - Societates.pdf`
- `Houses of Hermes - True Lineages.pdf`
- `Realms of Power - The Infernal.pdf`
- `Realms of Power - The Divine [Revised].pdf`

## 2026-09-15 — TABLED: the arm5e↔armdef edition seam (owner)

**All arm5e/armdef sourcebook reference work is tabled** pending a decision on how
the Definitive Edition should express absorbing a Fifth Edition sourcebook's
types. The §5d reference migration (DECISION-13) was applied to both trees and
filled everything unambiguous; **583 references are held** — arm5e 91, armdef 492
— and are NOT to be resolved piecemeal. They are one architectural question.

### What the seam is

ArM5 core has no `^"Laboratory"` entity; **Covenants** introduced it. ArMDef
**consolidated** it into its own core. So:

```
arm5e/0.5/arm5e-0.5-core-laboratory.ttrpg     3 DEFs, no ^"Laboratory"
arm5e/0.5/covenants/…-core-ext.ttrpg          #taKk3J80C97U9JM8e8grpEvf ^"Laboratory"   ← the only one
armdef/0.5/armdef-0.5-core-laboratory.ttrpg   #tkAcHrN5TUjI8v5f2bOaLGQj ^"Laboratory"   ← armdef's own
armdef/0.5/covenants/…-core-ext.ttrpg         #taKk3J80C97U9JM8e8grpEvf ^"Laboratory"   ← mirrored, arm5e's hash
```

Inside armdef the name now has two anchors, so every by-name reference to it is
ambiguous. Six names carry 351 of the 492: Laboratory, Laboratory Virtue,
Laboratory Flaw, Income Source, Expenditure Category, Covenfolk Category — plus
Grog/Companion (68) against `armdef-0.5-sourcebook-compat.ttrpg`.

### Why it happens — and it is not a conversion defect

`retarget_armdef.py`'s Rule 6 already handles stale cross-edition hashes: it
**remaps** `#arm5e_hash ^"Name"` to ArMDef's own anchor for that name, and where
**ArMDef has two anchors for one name it drops the hash instead**, on the stated
reasoning that "guessing which one was meant is worse than a by-name reference."

That was correct under the old rule. **DECISION-13 withdrew it**: a hashless
reference whose name resolves to more than one distinct entity is now an ERROR.
The retarget's deliberate fallback and the new spec rule are in direct conflict,
and the conflict is exactly these 583 sites.

### The larger finding

§19 says hash identity is **stable within** an edition and carries **no identity
across** it — "the same" entity in a newer edition is a *new* definition with a
*new* hash. Measured across the eleven mirrored sourcebooks:

| | anchors |
|---|---:|
| declared in arm5e sourcebooks | 3,144 |
| declared in armdef sourcebooks | 3,149 |
| **byte-identical across the edition boundary** | **2,788** |

`spells` is the sole exception (356 / 360, **0 shared**) — worth checking whether
that was deliberate, because it is the one book already doing what §19 describes.
`grogs` has the single allow-listed armdef-only `^"Grog Aging"`.

Separately: **266 armdef core type names are also defined in a mirrored
sourcebook with no shared anchor** — the Laboratory pattern, 266 times, not 6.

### The options (owner has not chosen)

1. **Follow §19 as written.** Retarget mints armdef-namespace anchors for
   mirrored DEFs and records each correspondence in a new
   `arm5e-to-armdef.bridge` (§21 `MAP`, which already covers rename /
   revision-in-place / merge / substitution with no new vocabulary). Fixes the
   collision at its cause; no new spec construct. Touches the retarget and every
   mirrored anchor.
2. **A conditional / system-gated construct** (owner's sketch, 2026-09-15):
   `CONDITION: system=arm5e { … } CONDITION: system=armdef { … }` in one source.
   A genuine spec extension (would be DECISION-14). Attractive because the
   sourcebooks really are meant to be compatible with both targets — but it
   reverses §19's settled choice of *separate namespaces + a derived artifact*
   over *automatic overlay*, and adopts the silent-divergence failure §19 names.
3. **Bind per book.** A reference takes the type declared in its own book. All
   583 resolve; changes nothing architecturally; leaves the seam undescribed.

No `arm5e-to-armdef` bridge exists today — only `arm4-to-arm5e` and
`dnd5e-to-dnd5.5e`.

### State while tabled

Both trees validate 0/0 and compose unchanged (`arm5e-0.5-full`: 3974 entities,
2918 flattened, 0 missing parents, 0 cycles — before and after the migration).
Only the new §5d references gate fails, by design. Held sites are listed with
their candidates in `titterpig-mastra/worklogs/DECISION-13-holds.md`.
