# titterpig-dsl-arm5e — TODO

Status as of 2026-07-26. Corpus validates **arm5e 80 files 0/0, armdef 40 files 0/0**;
MENTIONS/MODIFY/no-armdef-type gates all clean. The five supplements' record buckets +
the MENTIONS pass + the cross-book MODIFY pass are **committed** (`f3224d1`).

## Current effort — five supplements (Covenants, Grogs, RoP: Faerie, RoP: Magic, Hedge Magic)

Record buckets: **DONE + committed.** Remaining coordinated work to call the effort complete:

1. **Core mechanical DEFs + MENTIONS re-run — NEEDS OWNER (new core content).**
   `Light Wound` / `Medium Wound` / `Ease Factor` / `Recovery Roll` / the wound levels
   are not DEFs in the arm5e core, so DECISION-7's own worked example ("close the flesh")
   has nothing to link to. Adding them is new core content (a core wounds / die-rolls /
   recovery file), then re-run the linker so they resolve automatically. Owner call on
   whether/how to add.

2. **Per-book coverage / `.lore` pass (all five books).** Apply the SETTLED coverage
   policy (structural → exclude-with-reason; mechanics → `.ttrpg`; story-seeds +
   setting/rules-prose/GM-guidance/examples → `.lore` verbatim; double-capture kept).
   Get `coverageAudit.ts <manifest>` to exit 0 per book with owner-signed deferrals.
   Bring the owner **only the sidebar lists** to audit (`.lore` vs `.ttrpg` per sidebar).
   - RoP:Faerie has no manifest yet — create `coverage/arm5e-rop-faerie.manifest.json`.
   - Grogs manifest owes a note: `Master of (Form) Creatures` is **covered-by-cross-
     reference** (canonical in rop-magic; Grogs' Minor/General erratum dropped), not
     uncovered — its Grogs DEF was removed in the dedup.

3. **`sources.json` sync + final gates.** Covenants' and Grogs' subdir files aren't all
   tracked in `sources.json` yet; sync all five books, then re-run the full-corpus
   validator + coverage gates on both editions.

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
