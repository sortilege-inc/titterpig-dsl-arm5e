# titterpig-dsl-arm5e — TODO

## 2026-10-04 — sidebar TEXT is now a gate (`gates.sh`: "sidebar text")

`Temp/arm5e-sourcebook-conversions/scripts/sidebars_text_gate.py` checks every paragraph and row of every sidebar div
(letters AND digits) against each arm5e manifest's corpus. A unit passes if it is in the corpus, or held as fields (every
4-word shingle in the corpus's strings), or listed in `sidebars_text_allow.json`. That list has 27 reviewed entries, each
with a reason: wrapped table headers, spell `(Base …)` lines, Virtue/item lead-ins, the futhark rows. An entry that stops
matching FAILS, so the list cannot rot. Proven by planting each defect in a scratch copy: a deleted sidebar, a sidebar
truncated after its first sub-heading, one dropped stat line, one changed table number, and a stale allow entry all FAIL;
the unmodified copy PASSES.

- **Digits found one more gap:** Grogs p48 "Weight of Common Materials" prints a second grid (Size → Weight, 9 rows).
  It was absent; it is now `^"Weight of Common Materials: Size"` (systems.ttrpg 0.5.3). Letters-only could not see it:
  every row is numbers, and every stat line reads alike without them.
- **OPEN — owner call: the corebook is held out of the gate.** 39 of its 137 sidebars fail, 29 with whole sentences.
  The core was built by the Stage-B LLM pipeline, so its sidebars are paraphrased ("Pick three words … assign a number
  between +3 and –3" → "Choose three words … attach a value between –3 and +3"), or absent ("A Virtue or Flaw may be
  taken more than once only if the description explicitly allows it" is nowhere). The fix is a verbatim sidebar pass
  over the core, like the sourcebooks' 2026-07-27 backfill. Once that is done, drop the corebook exclusion in `gates.sh`.

## 2026-10-04 — sidebar TEXT completed across the sourcebooks (pushed 363c509)

The coverage gate credits a Text Box by name. A per-sidebar-div text audit of every sourcebook
(`Temp/arm5e-sourcebook-conversions/scripts/sidebars_text_audit.py`) found 20 sidebars whose text was absent although
the gate passed: Covenants 14, RoP:Faerie 3, City & Guild 2, RoP:Magic 1. All 20 converted (owner, 2026-10-04) by
`scripts/sidebars_complete.py` into 4 arm5e files, then a full `retarget_armdef.py` run, which changed exactly the 4
mirrors. Covenants' 19 unexcluded blank worksheet boxes and A&A's list of inserts are now page-keyed exclusions in
their manifests. `gates.sh` → ALL GATES PASS. Full write-up + decision log:
`Temp/arm5e-sourcebook-conversions/SIDEBARS-AUDIT-2026-10-04.md`.

## 2026-10-04 — Art & Academe converted, both editions (uncommitted)

`arm5e/0.5/art-and-academe/` (49 files, source of truth) + `armdef/0.5/art-and-academe/` (retarget mirror). One
command rebuilds and gates it: `Temp/arm5e-sourcebook-conversions/scripts/build_art_and_academe.sh`. Last run: verbatim gate
PASS on all 12 generators; pagecheck 0 missing on every page range; validator 245 files 0 errors both editions;
references 0 errors; verify_armdef PASS; coverage 660 units, 0 uncovered, 3 excluded with reasons (both editions);
synthesist 0 missing parents; rebuild byte-identical. Records (counted from the files by EXTENDS): 27 diseases, 33
formulae (11 inceptions, 12 reagents, 10 theriacs), 30 Virtues/Flaws, 23 spells, 7 spell guidelines + 3 formula
guidelines, 21 tables, 40 rules formulas, 27 glossary terms, 5 characters, 1 Ability, 6 figures (read by eye), 102
GUIDANCE.
Full state + decision log: `Temp/arm5e-sourcebook-conversions/art-and-academe/PROGRESS.md`. Adds 19 armdef
implicit overrides of the tabled edition-seam kind (below) — not patched per book. (Hedge Magic's coverage failure,
pre-existing since 2026-09-22, was fixed separately in 937739e.)

## 2026-09-21 — `check_references.py` now passes on both editions

Both gate parts, both editions, from `titterpig-dsl/check_references.py`:

| | §5c REFERENCES | §5d reference sites | validator |
|---|---|---|---|
| `arm5e/0.5` | 1,773 refs, **0 errors** (was 30) | 4,169 sites, **0 errors** (was 91) | 204 files 0/0 |
| `armdef/0.5` | 2,540 refs, 0 errors | 4,936 sites, **0 errors** (was 492) | 204 files 0/0 |

`verify_armdef.py`: **PASS — only the five structural forms differ.**

### The 29 §5c surface forms (owner ruling, 2026-09-21)

A `REFERENCES` entry is a stand-off annotation of printed prose (§5c): the surface form has to be
in the text it marks. Twenty-nine were not — they had been minted by matching entity NAMES into
text rather than read off the page, and the gate never caught it because its drift check had been
vacuous for all 4,626 entries corpus-wide until 2026-09-20.

- **Twelve on the Houses are dropped.** The 2026-07-27 restructure moved each House's narrative to
  `arm5e-0.5-houses.lore`; the annotations stayed on the mechanical DEF, pointing at text that is
  no longer in the file. All seven surfaces (`Hermetic magic`, `The Gift`, `House Tremere`, …) are
  in that `.lore`, which is Markdown and has nowhere to carry a stand-off annotation.
- **Seventeen on TABLE records are re-typed** as `^"See Also" #hash ^"Target"` — a §5d reference
  site, which the gate does check, rather than a §5c annotation of prose that was never printed
  there. `^"Aging Table"` is a table of living conditions and modifiers; the words `Aging Rolls`
  are nowhere in it. The property is `^"See Also"` and not `^"Tabulates"` because only eight of
  the seventeen tabulate their target — `^"Aging Rolls" → ^"Aging Table"` and
  `^"Crisis Table" → ^"Aging Table"` are one table pointing at another, and the six covenant
  situations ARE situations rather than tables of them.
- **One was case drift**: `"Aging"` where the page prints `aging rolls`.

### The 583 ambiguous §5d sites

A hashless reference whose caret name resolves to more than one entity is an ERROR under §5d
(DECISION-13). Resolution rule, applied throughout: **the nearest declaring scope — the same file,
else the same book, else the edition core.** It is not a guess: Covenants and ArMDef core each
declare `^"Laboratory Virtue"` and `^"Laboratory Flaw"`, and all 183 records that extend them say
which they mean in their own shape (Covenants' carry `^"Group"`, core's carry `^"Category"`). The
rule agrees with every one.

**arm5e (91):** `^"Magus"` ×31 → core-base's `ACTOR "Magus"`, not character-creation's prose record
of the character kind — `APPLIES TO` names an actor type, and the 13 `EXTENDS` are all character
TEMPLATEs, which *are* a Magus with a stat block. `^"Hermetic Practice"` ×58 → the societates type;
every site is in that book. `^"Animal Ken"` → the Virtue: the Grogs book's two other references to
the name use the Virtue's hash. `^"Failed Apprentice"` → the core Virtue: the ten other Failed
Apprentice story-seed records in the same file all use it.

**armdef (492)** was almost entirely the retarget's doing, and is fixed in
`arm5e-sourcebook-conversions/scripts/retarget_armdef.py` so it does not come back:

- **`ACTOR "Name" DEF` was invisible to the anchor index** (it matched `^"Name" DEF` and
  `TEMPLATE "Name" DEF`, not `ACTOR`), so ArMDef's `^"Character"`, `^"Entity"`, `^"Covenant"`,
  `^"Magus"`, `^"Grog"` and `^"Companion"` could not be found, and **340 references to them were
  left addressing arm5e's anchors**. A later hand pass had repaired those in `armdef/`, where the
  next retarget would have undone the repair — the clobber trap, in a new place.
- **An ambiguous name used to have its hash DROPPED**, on the reasoning that by-name is safer than
  a guess. §5d post-dates that reasoning and makes by-name an error. The script now resolves such a
  hash to **the ArMDef counterpart of the arm5e FILE that declared it** (132 sites: `#t42wf…
  ^"Faerie Blood"` is declared in `arm5e-0.5-virtues.ttrpg`, so it means
  `armdef-0.5-virtues.ttrpg`'s, not RoP:Faerie's two, which sit nearer), then by nearest scope (43).
- **`^"Grog"` / `^"Companion"` exist twice in ArMDef core** — as core-base ACTORs and as the plain
  types `armdef-0.5-sourcebook-compat.ttrpg` declares expressly so the re-targeted books' records
  can extend them "exactly as converted". A book means the shim; ArMDef's own files mean the ACTOR.
- **`^"Enchantment"` and `^"Virtues and Flaws"` are a real ArMDef core gap** — arm5e declares both
  (Laboratory chapter, Character Creation) and ArMDef declares neither, so Societates' Verditius
  Enchantment and the Grogs sidebar on Social Status were pointing at a RoP:Faerie record and a
  House chapter's section heading. Declared in the compat file on its own stated terms: the schema
  the books need, and not one sentence of either edition's prose.
- The retarget's `ROOT` still pointed at `~/Working`, dissolved 2026-09-13. It reads
  `ARM5E_DSL_ROOT` now and defaults to `~/Sortilege`.

### A gate script, and what it found  *(2026-09-21)*

There was no `gates.sh` in this repo, which is how the above accumulated unseen. There is one now —
validator, references and constructs for both editions, `verify_armdef.py`, and all 22 coverage
manifests — and it reports honestly:

**`arm5e-hedge-magic` and `armdef-hedge-magic` FAIL the coverage gate.** Two source units, the same
entity twice: `[Text Box] Elisavet ("Psychorrhax")` and `[Heading] Elisavet ("Psychorrhax")`. The
name appears **nowhere in either corpus** — this is a genuine content omission, not a key mismatch,
and it needs the Hedge Magic PDF and a conversion pass. Everything else passes: 872/921 covered,
47 excluded-with-reason, 0 deferred. **Owner's call.**

(The first version of that script piped each audit through `tail -1`, so a failing gate reported the
PIPE's status and read as passing — the trap the `titterpig-dsl` skill warns about. Fixed before
this was written; the FAIL above is what it says once the audit's own exit code survives.)

One site was settled by reading rather than by rule: `^"Sin-Eating" APPLIES TO ^"Curse-Throwing"`
in `armdef-0.5-mythic-companions.ttrpg` → the Supernatural **Ability**, not the Virtue that grants
it — "the supernatural power of Curse-Throwing is called Sin-Eating. A sin-eater uses this power."


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
