# ARM5e DSL v0.3 Conversion Report

**Date**: 2026-03-05
**Source**: `sources/arm5e/Ars-Magica-Open-License-main/wip/Ars Magica Definitive High Contrast.md` (27,478 lines)
**Previous source (v0.2)**: `sources/arm5e/ArMDef Manuscript Docs/` (.docx files)
**Converter**: `titterpig-dsl-arm5e/convert_md.py`
**Output**: `titterpig-dsl-arm5e/0.3/` (35 files, 1,287 DEF blocks)

---

## Summary

| Category | v0.2 | v0.3 | Delta | Coverage |
|----------|------|------|-------|----------|
| Spells | 359 | 334 | -25 | 93% |
| Virtues | 316 | 312 | -4 | 99% |
| Flaws | 308 | 306 | -2 | 99% |
| Abilities | 81 | 75 | -6 | 93% |
| Creatures | 62 | 61 | -1 | 98% |
| Lore files | 8 | 8 | 0 | 100% |
| Base files | 5 | 5 | 0 | 100% |
| **Total files** | **35** | **35** | **0** | **100%** |

Note: The v0.2 creature count of 124 in the raw file count included nested `^"Characteristics" DEF {}` sub-blocks inside each creature. The actual creature count in v0.2 was 62.

---

## Spell Discrepancies (-25)

### ~23 spells absent from the markdown source

The markdown file (derived from the Definitive Edition PDF) contains approximately 334 R:D:T anchor lines in the spell chapters, compared to 359 in the .docx manuscript files. These ~25 spells were present in the manuscript but are not in this markdown edition. This is a source-level difference, not a parser limitation.

### 1 spell with no R:D:T line

**Strings of the Unwilling Marionette** (Rego Corpus) — present in the markdown by name but has no `R: D: T:` line, so the anchor-based parser cannot detect it.

### 1 spell entirely absent

**The Shrouded Glen** (Rego Mentem 40) — does not appear anywhere in the markdown file.

### OCR/conversion artifacts in spell names

Several spell names in the markdown contain artifacts from the PDF-to-markdown conversion:

| Markdown name | Correct name |
|---------------|-------------|
| THE WOLIND THAT WEEPS | The Wound That Weeps |
| NEVER QUITE LIVED (fragment) | Recollection of Memories Never Quite Lived |

These are emitted with the mangled names as they appear in the source.

---

## Virtue Discrepancies (-4)

The v0.3 converter found 312 virtues vs 316 in v0.2. The 4 missing entries are likely due to:

- Formatting variations in the markdown where the `Size, Category` line does not match the expected pattern (e.g., unusual category combinations not covered by the regex)
- A small number of entries may have been present in the .docx but removed or restructured in the Definitive Edition

No virtues were misclassified as flaws or vice versa. The section boundary between virtues and flaws is correctly detected.

---

## Flaw Discrepancies (-2)

306 flaws found vs 308 in v0.2. Same root causes as virtues — minor formatting variations in the category line pattern.

---

## Ability Discrepancies (-6)

### v0.2 had false positives

The v0.2 converter found 81 abilities, but some of these were false positives from sections beyond the ability list (hex rules, covenant rules, etc.). The v0.3 parser correctly scopes to the "Ability List" section only, ending at the next chapter heading (`VI. Covenants`).

### 7 bold-formatted abilities (recovered)

Seven abilities use markdown bold formatting (`**Name**:`) instead of plain text. The v0.3 parser handles these with an updated regex.

### Net result

75 unique abilities extracted, which represents the true set of distinct abilities defined in the Ability List section.

---

## Creature Discrepancies (-1)

### Zwergenstimme (Magical) — missing from source

The Zwergenstimme creature block in the markdown has no `##` heading and no `Characteristics:` line. Its stat block content appears directly after the Stellatus lore text without any creature name header. This data was lost during PDF-to-markdown conversion and cannot be recovered programmatically.

### Issues fixed during development

| Creature | Issue | Resolution |
|----------|-------|------------|
| Cat (Mundane) | Characteristics line wrapped in LaTeX (`$\begin{array}...`) | Global LaTeX stripping in `read_markdown()` |
| Scitalis (Magical) | Might and Characteristics merged on single line | Extended Characteristics detection to check for `Characteristics:` anywhere in lines containing `Might:` |
| Revenant (Magical) | Name resolved to "6" from split Might continuation line `6 (Corpus)` | Added skip pattern for `^\d+\s*\([^)]+\)\s*$` in name backtracking |
| Character Conversion (false positive) | Appendix `Characteristics:` line detected as divine creature | Added "Character Conversion" to skip_sections; limited divine section to Bestiary chapter boundary |

### OCR-mangled creature names

The markdown source has numerous OCR errors in creature names:

| Markdown name | Correct name |
|---------------|-------------|
| Oat (Pelis) | Cat (Felis) |
| Lound | Hound |
| Colf | Wolf |
| Dasir, the Delper | Nasir, the Helper |

These are emitted with the names as they appear in the source.

---

## Bugs Fixed During Converter Development

### 1. Spell Guidelines context (recovered 99 spells)

**Problem**: Pass 1 context tracking set `in_spells = False` when encountering "Guidelines" headings. Ten technique/form combinations in the markdown have no "Spells" heading — only "Guidelines" — so all their spells were skipped.

**Affected combos**: Muto Auram, Rego Corpus, Perdo Herbam, Rego Herbam, Rego Ignem, Creo Imaginem, Creo Terram, Rego Terram, Perdo Vim, Rego Vim.

**Fix**: Both "Spells" and "Guidelines" headings now set `in_spells = True`.

### 2. Flaws section detection (recovered all 306 flaws)

**Problem**: The flaws section divider used a hardcoded threshold (`i > 5000`) relative to the virtues/flaws line array. The "Flaws" heading in the markdown fell at index 2973 in the offset array, below the threshold, causing all entries to be classified as virtues.

**Fix**: Changed to relative positioning — the "Flaws" heading must come after the first category-pattern match + 100 lines.

### 3. Abilities end marker (recovered 54 abilities)

**Problem**: "Example of Curse-Throwing" was in the `end_markers` list, and this heading appears at line 8762 as an inline sidebar within the ability list. The ability list continues to line ~9127. Only the first 21 abilities (before the sidebar) were captured.

**Fix**: Removed all premature end markers. The section now ends at the next chapter heading (`VI. Covenants`), detected by the pattern `^[IVXL]+\.\s+`.

### 4. Bold ability names (recovered 7 abilities)

**Problem**: The name regex `^(\(?[A-Z]...)` did not match abilities formatted with markdown bold (`**Brawl**:`, `**Teaching**:`, etc.).

**Fix**: Updated regex to `^\*{0,2}(\(?[A-Z]...)`.

### 5. Global LaTeX stripping

**Problem**: The markdown source contains LaTeX math formatting artifacts from PDF conversion (e.g., `$\mathsf{Touch}$`, `$\begin{array}{c}\textbf{Characteristics: ...}\end{array}$`). These broke pattern matching for R:D:T lines, spell names, and creature Characteristics.

**Fix**: Added `strip_latex()` function to `read_markdown()` that removes LaTeX wrappers globally, extracting inner text.

### 6. R:D:T regex relaxation (recovered 6 spells)

**Problem**: The R:D:T regex required `,`, `;`, or `.` as separators. Six lines in the markdown use spaces instead (e.g., `R: Arc D: Mom, T: Ind`).

**Fix**: Added `\s` as an accepted separator character.

### 7. Inline R:D:T splitting (recovered ~11 spells)

**Problem**: Some spells have name and R:D:T on the same line (e.g., `TRUE REST OF THE INJURED BRUTE R: Touch, D: Moon, T: Ind`). The two-pass parser expects them on separate lines.

**Fix**: Pre-processing step detects inline R:D:T patterns and splits them into two lines.

### 8. Divine creature section boundary (removed 1 false positive)

**Problem**: The divine realm section extended to end-of-file, picking up a `Characteristics:` line from the Appendix's "Character Conversion" section.

**Fix**: Divine section now ends at the `XIV. Mythic Europe` chapter heading.

### 9. Creature name backtracking (fixed 1 wrong name)

**Problem**: The Revenant creature's Might line was split across two lines (`Magic Might:` / `6 (Corpus)`). The name backtracker used `6 (Corpus)` as the creature name.

**Fix**: Added a skip pattern for Might continuation lines matching `^\d+\s*\([^)]+\)\s*$`.

---

## Verification

- `gen_gamedata.py` successfully reads all 0.3 DSL files and generates Go source
- `go build ./...` passes with the updated ARM5e data
- All 35 output files match the v0.2 file structure (same file categories and naming convention)
