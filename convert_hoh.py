#!/usr/bin/env python3
"""
Houses of Hermes — v0.3 DSL Converter (Markdown sources)

Parses the three Houses of Hermes sourcebooks and emits v0.3 .ttrpg and
.lore files into titterpig-dsl-arm5e/0.3/{subdir}/.

Sources:
  - Mystery Cults   → 0.3/hoh-mystery-cults/
  - Societates       → 0.3/hoh-societates/
  - True Lineages    → 0.3/hoh-true-lineages/
"""

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

# ============================================================
# CONFIGURATION
# ============================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
SOURCE_DIR = (
    SCRIPT_DIR.parent / "sources" / "arm5e"
    / "Ars-Magica-Open-License-main" / "wip"
)

BOOKS = {
    "mystery-cults": {
        "source": "Ars Magica 5e - Houses of Hermes - Mystery Cults.md",
        "output_dir": SCRIPT_DIR / "0.3" / "hoh-mystery-cults",
        "prefix": "arm5e-hoh-mystery-cults-0.3",
        "title": "Houses of Hermes: Mystery Cults",
        "houses": ["Bjornaer", "Criamon", "Merinita", "Verditius"],
        "file_id_prefix": "ARM5e_HoH_MC",
    },
    "societates": {
        "source": "Ars Magica 5e - Houses of Hermes - Societates.md",
        "output_dir": SCRIPT_DIR / "0.3" / "hoh-societates",
        "prefix": "arm5e-hoh-societates-0.3",
        "title": "Houses of Hermes: Societates",
        "houses": ["Flambeau", "Jerbiton", "Tytalus", "Ex Miscellanea"],
        "file_id_prefix": "ARM5e_HoH_Soc",
    },
    "true-lineages": {
        "source": "Ars Magica 5e - Houses of Hermes - True Lineages.md",
        "output_dir": SCRIPT_DIR / "0.3" / "hoh-true-lineages",
        "prefix": "arm5e-hoh-true-lineages-0.3",
        "title": "Houses of Hermes: True Lineages",
        "houses": ["Bonisagus", "Guernicus", "Mercere", "Tremere"],
        "file_id_prefix": "ARM5e_HoH_TL",
    },
}

TECHNIQUES = ["Creo", "Intellego", "Muto", "Perdo", "Rego"]
FORMS = ["Animal", "Aquam", "Auram", "Corpus", "Herbam",
         "Ignem", "Imaginem", "Mentem", "Terram", "Vim"]

TE_ABBR = {"Cr": "Creo", "In": "Intellego", "Mu": "Muto",
            "Pe": "Perdo", "Re": "Rego"}
FO_ABBR = {"An": "Animal", "Aq": "Aquam", "Au": "Auram",
            "Co": "Corpus", "He": "Herbam", "Ig": "Ignem",
            "Im": "Imaginem", "Me": "Mentem", "Te": "Terram",
            "Vi": "Vim"}

RANGE_MAP = {
    "Per": "Personal", "Personal": "Personal",
    "Touch": "Touch", "Eye": "Eye",
    "Voice": "Voice", "Sight": "Sight",
    "Arc": "Arcane Connection", "Arcane": "Arcane Connection",
    "Arcane Connection": "Arcane Connection",
    "Road": "Road",
}

DURATION_MAP = {
    "Mom": "Momentary", "Momentary": "Momentary",
    "Conc": "Concentration", "Concentration": "Concentration",
    "Diam": "Diameter", "Diameter": "Diameter",
    "Sun": "Sun", "Ring": "Ring", "Moon": "Moon",
    "Year": "Year", "Fire": "Fire", "Bargain": "Bargain",
    "Until": "Until",
}

TARGET_MAP = {
    "Ind": "Individual", "Individual": "Individual",
    "Part": "Part", "Group": "Group",
    "Room": "Room", "Structure": "Structure",
    "Bound": "Boundary", "Boundary": "Boundary",
    "Circle": "Circle", "Bloodline": "Bloodline",
    "Taste": "Taste", "Hearing": "Hearing",
    "Smell": "Smell", "Touch": "Touch", "Vision": "Vision",
    "Flavor": "Taste", "Texture": "Touch", "Scent": "Smell",
    "Sound": "Hearing", "Spectacle": "Vision",
}


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class SpellEntry:
    name: str
    technique: str
    form: str
    level: str
    range: str
    duration: str
    target: str
    ritual: bool = False
    requisite: str = ""
    design: str = ""
    description: str = ""


@dataclass
class VirtueFlawEntry:
    name: str
    type: str  # "Virtue" or "Flaw"
    size: str  # "Major", "Minor", "Free"
    category: str
    description: str = ""
    repeatable: bool = False


@dataclass
class AbilityEntry:
    name: str
    ability_type: str
    specialties: list = field(default_factory=list)
    description: str = ""
    requires_gift: bool = False


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

_hash_counters = defaultdict(int)


def make_hash(prefix: str) -> str:
    _hash_counters[prefix] += 1
    seq = f"{_hash_counters[prefix]:03d}"
    pad_chars = "aB2cD4eF6gH8iJ0kL"
    needed = 24 - len(prefix) - len(seq) - 1
    pad = (pad_chars * 3)[:needed]
    return f"#{prefix}{seq}{pad}"


def dsl_string(s: str) -> str:
    if not s:
        return '""'
    s = s.strip()
    if "\n" in s:
        return f'"""{s}"""'
    s = s.replace('"', '\\"')
    return f'"{s}"'


def dsl_name(name: str) -> str:
    return f'^"{name}"'


def clean_text(text: str) -> str:
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2013', '-').replace('\u2014', ' -- ')
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = text.replace('\\*', '*')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def strip_md_heading(line: str) -> str:
    return re.sub(r'^#{1,6}\s+', '', line)


def strip_latex(s: str) -> str:
    if '$' not in s:
        return s
    latex_cmd = re.compile(
        r'\\(?:mathsf|textbf|mbox|hbox|text|scriptsize|tiny)\{([^}]+)\}')
    result = latex_cmd.sub(r'\1', s)
    result = re.sub(r'\$', '', result)
    result = re.sub(r'\\begin\{array\}\{[^}]*\}', '', result)
    result = re.sub(r'\\end\{array\}', '', result)
    result = re.sub(r'\\\\', ' ', result)
    result = re.sub(r'\\,', '', result)
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def read_markdown(filepath: Path) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()
    lines = []
    for raw in raw_lines:
        line = raw.rstrip('\n')
        if line.startswith('#'):
            line = strip_md_heading(line)
        line = line.replace('\\*', '*')
        if '$' in line:
            line = strip_latex(line)
        lines.append(line)
    return lines


def strip_bold(s: str) -> str:
    """Remove markdown bold markers from a string."""
    return re.sub(r'\*\*(.+?)\*\*', r'\1', s)


# ============================================================
# SPELL PARSER (HoH — handles both formatting patterns)
# ============================================================

def parse_hoh_spells(lines: list) -> list:
    """Parse spells from a Houses of Hermes sourcebook.

    Handles two R:D:T formats:
      1. Plain:  R: Touch, D: Mom, T: Ind
      2. Bold:   **R:** Touch, **D:** Sun, **T:** Ind, **Level 40**
    Also handles TeFo Level lines like "ReAn 20" or "Cr(Re)An 25"
    """
    spells = []

    # Patterns for R:D:T lines (after bold stripping)
    rdt_pat = re.compile(
        r'^R:\s*([^,;.]+?)\s*[,;.\s]\s*D:\s*([^,;.]+?)\s*[,;.\s]\s*T:\s*(.+?)\s*$'
    )
    # Bold R:D:T with optional Level (True Lineages style)
    bold_rdt_pat = re.compile(
        r'^\*\*R:\*\*\s*(.+?)\s*[,;.]\s*\*\*D:\*\*\s*(.+?)\s*[,;.]\s*\*\*T:\*\*\s*(.+?)$'
    )
    # TeFo Level line: "CrAn 25" or "Cr(Re)An 25" or "MuMe(Te) 40"
    tefo_pat = re.compile(
        r'^(Cr|In|Mu|Pe|Re)\(?(\w{2})?\)?(An|Aq|Au|Co|He|Ig|Im|Me|Te|Vi)'
        r'\(?(\w{2})?\)?\s+(\d+|Gen)\s*$'
    )
    # Section heading: "Creo Animal Spells" or "CREO ANIMAL SPELLS" or
    # "REGO MENTEM SPELLS" etc.
    section_pat = re.compile(
        r'^(Creo|Intellego|Muto|Perdo|Rego|CREO|INTELLEGO|MUTO|PERDO|REGO)\s+'
        r'(Animal|Aquam|Auram|Corpus|Herbam|Ignem|Imaginem|Mentem|Terram|Vim|'
        r'ANIMAL|AQUAM|AURAM|CORPUS|HERBAM|IGNEM|IMAGINEM|MENTEM|TERRAM|VIM)'
        r'(?:\s+(?:Spells|SPELLS|spell))?\s*$',
        re.IGNORECASE
    )
    design_pat = re.compile(r'^\(Base\s+.+\)\s*$')
    req_pat = re.compile(r'^\*?\*?Req(?:uisite)?s?\*?\*?:?\s*(.+)$', re.IGNORECASE)

    cur_tech = None
    cur_form = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Track technique/form from section headings
        sm = section_pat.match(line)
        if sm:
            cur_tech = sm.group(1).capitalize()
            cur_form = sm.group(2).capitalize()
            i += 1
            continue

        # Try to match an R:D:T line (either plain or bold-stripped)
        stripped = strip_bold(line)
        rdt_match = rdt_pat.match(stripped)

        if not rdt_match:
            i += 1
            continue

        r_val = rdt_match.group(1).strip()
        d_val = rdt_match.group(2).strip()
        t_rest = rdt_match.group(3).strip()

        # Parse Level from inline (e.g., "T: Ind, Level 40")
        level = None
        ritual = False
        requisite = ""

        # Extract Level if inline
        level_m = re.search(r',?\s*\*?\*?Level\s+(\d+|Gen)\*?\*?', t_rest, re.IGNORECASE)
        if level_m:
            level = level_m.group(1)
            t_rest = t_rest[:level_m.start()].strip().rstrip(',. ')

        # Extract Ritual flag
        if re.search(r'\bRitual\b', t_rest, re.IGNORECASE):
            ritual = True
            t_rest = re.sub(r',?\s*Ritual\s*', '', t_rest, flags=re.IGNORECASE).strip()

        # Extract inline Requisite
        req_m = re.search(r',?\s*Req(?:uisite)?s?:\s*(.+)', t_rest, re.IGNORECASE)
        if req_m:
            requisite = req_m.group(1).strip()
            t_rest = t_rest[:req_m.start()].strip()

        t_val = t_rest.rstrip(',. ')

        # Look backwards for spell name and optional TeFo/Level line
        technique = cur_tech
        form = cur_form
        name = None

        # Search backwards from R:D:T line
        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1

        # Check for Requisite line right after R:D:T
        if i + 1 < len(lines):
            next_line = strip_bold(lines[i + 1].strip())
            req_m2 = req_pat.match(next_line)
            if req_m2 and not requisite:
                requisite = req_m2.group(1).strip()

        if j >= 0:
            candidate = lines[j].strip()
            candidate_clean = strip_bold(candidate)

            # Check if this line is a TeFo line
            tefo_m = tefo_pat.match(candidate_clean)
            if tefo_m:
                technique = TE_ABBR.get(tefo_m.group(1), technique)
                form = FO_ABBR.get(tefo_m.group(3), form)
                if level is None:
                    level = tefo_m.group(5)
                # Requisite from parenthetical
                if tefo_m.group(2):
                    req_te = TE_ABBR.get(tefo_m.group(2))
                    req_fo = FO_ABBR.get(tefo_m.group(2))
                    if req_te and not requisite:
                        requisite = req_te
                    elif req_fo and not requisite:
                        requisite = req_fo
                if tefo_m.group(4):
                    req_te = TE_ABBR.get(tefo_m.group(4))
                    req_fo = FO_ABBR.get(tefo_m.group(4))
                    if req_te and not requisite:
                        requisite = req_te
                    elif req_fo and not requisite:
                        requisite = req_fo
                # Name is above the TeFo line
                k = j - 1
                while k >= 0 and not lines[k].strip():
                    k -= 1
                if k >= 0:
                    name = strip_bold(lines[k].strip())
            else:
                # No TeFo line — candidate is the name
                name = candidate_clean

        if not name or len(name) > 120:
            i += 1
            continue

        # Skip non-spell names
        if section_pat.match(name) or design_pat.match(name):
            i += 1
            continue
        if name.startswith('R:') or name.startswith('(Base'):
            i += 1
            continue

        # Default level if not found
        if level is None:
            level = "0"

        # Check for "Ritual" in the line or in the level context
        if "Ritual" in line and not ritual:
            ritual = True

        # Collect description (lines after R:D:T until next spell/heading)
        desc_start = i + 1
        # Skip Requisite line if present
        if desc_start < len(lines) and req_pat.match(strip_bold(lines[desc_start].strip())):
            desc_start += 1

        desc_lines = []
        design = ""
        for di in range(desc_start, len(lines)):
            dl = lines[di].strip()
            dl_clean = strip_bold(dl)
            if not dl:
                if desc_lines:
                    desc_lines.append("")
                continue
            # Stop at next spell name (bold heading or TeFo line or section heading)
            if tefo_pat.match(dl_clean):
                break
            if section_pat.match(dl_clean):
                break
            if rdt_pat.match(dl_clean):
                break
            # Stop at next #### heading (spell name)
            if dl.startswith('####') or dl.startswith('###'):
                break
            # Stop at bold-only line that looks like a spell name
            if re.match(r'^\*\*[A-Z][A-Z\s\']+\*\*$', dl):
                break
            if re.match(r'^[A-Z][A-Z\s\']{5,}$', dl_clean) and len(dl_clean) < 80:
                break
            if design_pat.match(dl_clean):
                design = dl_clean.strip("()")
                continue
            # Stop at any line followed by R:D:T or TeFo (next spell entry)
            if dl_clean and len(dl_clean) < 100 and not dl.startswith('-') and not dl.startswith('('):
                nj = di + 1
                while nj < len(lines) and not lines[nj].strip():
                    nj += 1
                if nj < len(lines):
                    nxt_clean = strip_bold(lines[nj].strip())
                    if rdt_pat.match(nxt_clean) or tefo_pat.match(nxt_clean):
                        break
            desc_lines.append(dl_clean)

        # Trim trailing blanks
        while desc_lines and not desc_lines[-1]:
            desc_lines.pop()

        desc = clean_text("\n".join(desc_lines))
        if len(desc) > 2000:
            desc = desc[:2000] + "..."

        spells.append(SpellEntry(
            name=name,
            technique=technique or "Rego",
            form=form or "Vim",
            level=str(level),
            range=RANGE_MAP.get(r_val, r_val),
            duration=DURATION_MAP.get(d_val, d_val),
            target=TARGET_MAP.get(t_val, t_val),
            ritual=ritual,
            requisite=requisite,
            design=design,
            description=desc,
        ))

        i += 1

    return spells


# ============================================================
# VIRTUE/FLAW PARSER (HoH)
# ============================================================

def parse_hoh_virtues_flaws(lines: list) -> tuple:
    """Parse virtues and flaws from a Houses of Hermes sourcebook.

    Format: Heading line (#### or **bold**) followed by
            *Size, Category* on next non-blank line.
    """
    virtues = []
    flaws = []

    # Category line in italics: *Minor, Hermetic* or *Major, Supernatural*
    cat_pat = re.compile(
        r'^\*?(Major|Minor|Free|Major or Minor)\s*[,.]?\s*'
        r'(General|Hermetic|Supernatural|Social Status|Social|Story|Personality|Tainted'
        r'|Heroic|Status'
        r'|Hermetic and Supernatural|Supernatural and Hermetic'
        r'|Story, Supernatural|Hermetic, Story|General, Supernatural'
        r'|Hermetic \(House \w+ only\)|Social Status \(House \w+ only\)'
        r'|House \w+ only'
        r')'
        r'(?:\s*\(.*?\))?'  # optional parenthetical qualifier
        r'\*?\s*$'
    )

    # Also match heading-based V&F sections like "### MINOR HERMETIC VIRTUES"
    section_vf_pat = re.compile(
        r'^(MINOR|MAJOR|FREE)\s+(HERMETIC|SUPERNATURAL|GENERAL|SOCIAL STATUS|STORY|PERSONALITY)\s+'
        r'(VIRTUES?|FLAWS?)\s*$', re.IGNORECASE
    )

    # Track current context from section headings
    section_type = None  # "Virtue" or "Flaw"
    section_size = None  # "Major", "Minor", "Free"
    section_category = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        stripped = strip_bold(line)

        # Check for section heading that sets V/F context
        sec_m = section_vf_pat.match(stripped)
        if sec_m:
            section_size = sec_m.group(1).capitalize()
            section_category = sec_m.group(2).strip()
            # Normalize category capitalization
            section_category = section_category.title()
            if section_category == "Social Status":
                pass
            vf_word = sec_m.group(3).upper()
            section_type = "Virtue" if "VIRTUE" in vf_word else "Flaw"
            i += 1
            continue

        # Check for explicit "New Virtues" / "New Flaws" / "Virtues & Flaws" headings
        if stripped in ("New Virtues", "Virtues", "New Virtues and Flaws", "Virtues & Flaws"):
            section_type = "Virtue"
            i += 1
            continue
        if stripped in ("New Flaws", "Flaws"):
            section_type = "Flaw"
            i += 1
            continue

        # Look for category line pattern
        cat_m = cat_pat.match(line)
        if cat_m:
            size = cat_m.group(1)
            category = cat_m.group(2)

            # Normalize
            if size == "Major or Minor":
                size = "Major"
            # Clean category
            category = re.sub(r'\s*\(House \w+ only\)', '', category).strip()
            if category == "Social":
                category = "Social Status"
            if category == "Status":
                category = "Social Status"
            if category == "Heroic":
                category = "Supernatural"
            if "," in category:
                category = category.split(",")[0].strip()
            if " and " in category:
                category = category.split(" and ")[0].strip()

            # Look backwards for name
            name_idx = i - 1
            while name_idx >= 0 and not lines[name_idx].strip():
                name_idx -= 1

            if name_idx < 0:
                i += 1
                continue

            name = strip_bold(lines[name_idx].strip())
            # Remove heading markers
            name = re.sub(r'^#+\s*', '', name)
            name = name.strip('*').strip()

            if not name or len(name) > 120:
                i += 1
                continue

            # Determine if virtue or flaw
            entry_type = section_type or "Virtue"  # Default to section context

            # Collect description
            desc_lines = []
            di = i + 1
            while di < len(lines):
                dl = lines[di].strip()
                if not dl:
                    if desc_lines:
                        desc_lines.append("")
                    di += 1
                    continue
                dl_clean = strip_bold(dl)
                # Stop at next category line
                if cat_pat.match(dl):
                    break
                # Stop at known section headings (heading markers stripped by read_markdown)
                if dl_clean in ("Virtues", "Flaws", "New Virtues", "New Flaws",
                                "Virtues and Flaws", "New Virtues and Flaws",
                                "Virtues & Flaws", "Appendix"):
                    break
                # Stop at bold category headers from ToC blocks (**HERMETIC, MAJOR** etc.)
                if re.match(r'^\*\*[A-Z]+\s*,\s*[A-Z]+\*\*\s*$', dl):
                    break
                # Stop at any non-blank line followed by a cat_pat or ToC header
                if dl_clean and len(dl_clean) < 120 and not dl.startswith('-') and not dl.startswith('>'):
                    next_j = di + 1
                    while next_j < len(lines) and not lines[next_j].strip():
                        next_j += 1
                    if next_j < len(lines):
                        nxt = lines[next_j].strip()
                        if cat_pat.match(nxt) or re.match(r'^\*\*[A-Z]+\s*,\s*[A-Z]+\*\*\s*$', nxt):
                            break
                desc_lines.append(dl_clean)
                di += 1

            while desc_lines and not desc_lines[-1]:
                desc_lines.pop()

            desc = clean_text("\n".join(desc_lines))
            if len(desc) > 1500:
                desc = desc[:1500] + "..."

            entry = VirtueFlawEntry(
                name=name,
                type=entry_type,
                size=size,
                category=category,
                description=desc,
            )

            if entry_type == "Flaw":
                flaws.append(entry)
            else:
                virtues.append(entry)

        # Reset section context at chapter/major headings that aren't V&F sections
        elif section_type and (
            stripped.startswith("Chapter ") or
            stripped == "History" or
            stripped == "Customs" or
            stripped.startswith("New Spells") or
            stripped.startswith("Designing ") or
            stripped.startswith("Certamen") or
            stripped.startswith("Dueling") or
            stripped == "Appendix" or
            stripped == "Original Research" or
            stripped == "Abilities" or
            stripped.startswith("Specialist") or
            stripped.startswith("Magical Items") or
            stripped.startswith("Parma Magica") or
            stripped.startswith("Parmulae") or
            stripped.startswith("Mythic Companions") or
            stripped.startswith("Heroic Characters") or
            re.match(r'^(Creo|Intellego|Muto|Perdo|Rego)\s+', stripped, re.IGNORECASE) or
            # Generic: ALL CAPS lines > 10 chars that aren't V&F names or section headings
            (re.match(r'^[A-Z][A-Z\s]{10,}$', stripped) and not section_vf_pat.match(stripped)
             and not _is_followed_by_cat_pat(lines, i, cat_pat))
        ):
            section_type = None
            section_size = None
            section_category = None

        # Also handle entries under section headings (e.g., "### MINOR HERMETIC VIRTUES")
        # where individual entries have bold names but NO category line
        elif section_type and section_size and section_category:
            # Check if this line is a bold name followed by description (no cat line)
            # Must look like a proper name: starts with bold letter, reasonable length,
            # not an R:D:T line, not a spell/section reference
            if (re.match(r'^\*\*[A-Z]', line) and not cat_pat.match(line)
                    and '**R:**' not in line and 'R:' not in strip_bold(line)
                    and 'D:' not in strip_bold(line)):
                # Extract just the bold portion as the name
                bold_m = re.match(r'^\*\*(.+?)\*\*[:\s.]*\s*(.*)', line)
                if bold_m:
                    name = bold_m.group(1).strip().rstrip(':').rstrip('.').rstrip('*')
                    inline_desc = bold_m.group(2).strip()
                else:
                    name = strip_bold(line).strip().rstrip(':').rstrip('.')
                    inline_desc = ""
                # Skip things that don't look like V&F names
                if (name and len(name) < 80 and not section_pat_match(stripped)
                        and not re.match(r'^Level \d', name)
                        and not re.match(r'^\d+', name)
                        and ':' not in name):
                    # Check next non-blank line — if it's NOT a cat_pat, use section context
                    ni = i + 1
                    while ni < len(lines) and not lines[ni].strip():
                        ni += 1
                    if ni < len(lines) and not cat_pat.match(lines[ni].strip()):
                        # Collect description
                        desc_lines = []
                        if inline_desc:
                            desc_lines.append(strip_bold(inline_desc))
                        di = ni
                        while di < len(lines):
                            dl = lines[di].strip()
                            if not dl:
                                if desc_lines:
                                    desc_lines.append("")
                                di += 1
                                continue
                            dl_clean = strip_bold(dl)
                            if cat_pat.match(dl):
                                break
                            # Stop at section V&F headings (e.g., MINOR HERMETIC VIRTUES)
                            if section_vf_pat.match(dl_clean):
                                break
                            # Stop at known section headings
                            if dl_clean in ("Virtues", "Flaws", "New Virtues", "New Flaws",
                                            "Virtues and Flaws", "New Virtues and Flaws",
                                            "Virtues & Flaws", "Appendix",
                                            "Original Research", "Abilities"):
                                break
                            # Stop at next bold-name entry (check bold portion length, not whole line)
                            if re.match(r'^\*\*[A-Z]', dl) and di > i:
                                bold_check = re.match(r'^\*\*(.+?)\*\*', dl)
                                if bold_check and len(bold_check.group(1)) < 80:
                                    break
                            # Stop at any line followed by a cat_pat or ToC header
                            if dl_clean and len(dl_clean) < 120 and not dl.startswith('-') and not dl.startswith('>'):
                                nj = di + 1
                                while nj < len(lines) and not lines[nj].strip():
                                    nj += 1
                                if nj < len(lines):
                                    nxt = lines[nj].strip()
                                    if cat_pat.match(nxt) or re.match(r'^\*\*[A-Z]+\s*,\s*[A-Z]+\*\*\s*$', nxt):
                                        break
                            desc_lines.append(dl_clean)
                            di += 1

                        while desc_lines and not desc_lines[-1]:
                            desc_lines.pop()
                        desc = clean_text("\n".join(desc_lines))
                        if len(desc) > 1500:
                            desc = desc[:1500] + "..."

                        entry = VirtueFlawEntry(
                            name=name,
                            type=section_type,
                            size=section_size,
                            category=section_category,
                            description=desc,
                        )
                        if section_type == "Flaw":
                            flaws.append(entry)
                        else:
                            virtues.append(entry)

        i += 1

    return virtues, flaws


def _is_followed_by_cat_pat(lines, i, cat_pat):
    """Check if line i is followed (after blanks) by a cat_pat match."""
    j = i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    return j < len(lines) and cat_pat.match(lines[j].strip())


def section_pat_match(s):
    """Helper to check if a line is a section heading."""
    return bool(re.match(
        r'^(Creo|Intellego|Muto|Perdo|Rego)\s+'
        r'(Animal|Aquam|Auram|Corpus|Herbam|Ignem|Imaginem|Mentem|Terram|Vim)',
        s, re.IGNORECASE
    ))


# ============================================================
# ABILITY PARSER (HoH)
# ============================================================

def parse_hoh_abilities(lines: list) -> list:
    """Parse new abilities from a Houses of Hermes sourcebook.

    Abilities typically appear as:
      ### New Ability: Name
      or
      #### New Supernatural Ability: Name
      or
      **Name:** Description (Type)
    """
    entries = []

    ability_heading_pat = re.compile(
        r'^New\s+(?:Supernatural\s+)?Ability:\s*(.+?)\\?\s*$', re.IGNORECASE
    )
    type_pat = re.compile(r'\((General|Academic|Arcane|Martial|Supernatural)\)')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        stripped = strip_bold(line)

        m = ability_heading_pat.match(stripped)
        if m:
            name = m.group(1).strip()
            # Collect description
            desc_lines = []
            ability_type = "Supernatural"  # Default for HoH books
            di = i + 1
            while di < len(lines):
                dl = lines[di].strip()
                if not dl:
                    if desc_lines:
                        desc_lines.append("")
                    di += 1
                    continue
                dl_clean = strip_bold(dl)
                if dl.startswith('###') or dl.startswith('####'):
                    break
                if ability_heading_pat.match(dl_clean):
                    break
                tm = type_pat.search(dl_clean)
                if tm:
                    ability_type = tm.group(1)
                desc_lines.append(dl_clean)
                di += 1

            while desc_lines and not desc_lines[-1]:
                desc_lines.pop()
            desc = clean_text("\n".join(desc_lines))
            if len(desc) > 1000:
                desc = desc[:1000] + "..."

            entries.append(AbilityEntry(
                name=name,
                ability_type=ability_type,
                description=desc,
            ))

        i += 1

    return entries


# ============================================================
# LORE EXTRACTOR (HoH)
# ============================================================

def extract_hoh_lore(lines: list, houses: list) -> dict:
    """Extract lore sections for each House from a HoH sourcebook.

    Each house chapter starts with "Chapter One/Two/Three/Four" or
    house-name headings. We extract History and Culture sections.
    """
    lore = {}

    # Find chapter boundaries
    chapter_starts = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Look for "Key Facts" which starts each house chapter
        if stripped == "Key Facts":
            chapter_starts.append(i)
        # Also look for "## History" as chapter marker
        if stripped == "History" and i > 100:
            # Check if this is near a Key Facts
            if not chapter_starts or abs(chapter_starts[-1] - i) > 50:
                chapter_starts.append(i)

    # For each house, try to find and extract its history/culture section
    for house in houses:
        # Find house name in lines
        house_start = None
        house_end = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if house.lower() in stripped.lower() and (
                "the Founder" in stripped or "History" in stripped or
                stripped.startswith("House") or
                stripped == house or
                f"Key Facts" in lines[min(i+10, len(lines)-1):min(i+30, len(lines)-1)].__repr__()
            ):
                house_start = i
                break

        if house_start is None:
            # Fallback: search for "Chapter" followed by house reference
            for i, line in enumerate(lines):
                if line.strip().startswith("Chapter") and i + 30 < len(lines):
                    chunk = "\n".join(lines[i:i+30])
                    if house in chunk:
                        house_start = i
                        break

        if house_start is None:
            continue

        # Find end: next "Chapter" heading or end of file
        for i in range(house_start + 50, len(lines)):
            stripped = lines[i].strip()
            if stripped.startswith("Chapter ") and stripped != lines[house_start].strip():
                house_end = i
                break
        if house_end is None:
            house_end = len(lines)

        # Extract the section
        section = lines[house_start:min(house_start + 500, house_end)]
        content = "\n".join(l for l in section if l.strip())
        content = clean_text(content)

        # Limit size
        if len(content) > 10000:
            content = content[:10000] + "\n\n[Content truncated]"

        key = house.lower().replace(" ", "-")
        lore[key] = (f"House {house}", content)

    return lore


# ============================================================
# DSL EMITTERS
# ============================================================

def emit_spell_def(spell: SpellEntry) -> str:
    h = make_hash("ARM5SP")
    lines = []
    lines.append(f'    {h} {dsl_name(spell.name)} DEF {{')
    lines.append(f'        APPLIES TO [{dsl_name("Magus")}]')
    lines.append(f'        PROPERTIES {{')
    lines.append(f'            {dsl_name("Technique")} ENUM ["{spell.technique}"]')
    lines.append(f'            {dsl_name("Form")} ENUM ["{spell.form}"]')
    level_str = spell.level
    if level_str.lower() == "gen":
        lines.append(f'            {dsl_name("Level")} INTEGER 0')
        lines.append(f'            {dsl_name("General")} BOOLEAN true')
    else:
        lines.append(f'            {dsl_name("Level")} INTEGER {level_str}')
    lines.append(f'            {dsl_name("Range")} ENUM ["{spell.range}"]')
    lines.append(f'            {dsl_name("Duration")} ENUM ["{spell.duration}"]')
    lines.append(f'            {dsl_name("Target")} ENUM ["{spell.target}"]')
    if spell.ritual:
        lines.append(f'            {dsl_name("Ritual")} BOOLEAN true')
    if spell.requisite:
        lines.append(f'            {dsl_name("Requisite")} STRING "{spell.requisite}"')
    if spell.design:
        lines.append(f'            {dsl_name("Design")} STRING {dsl_string(spell.design)}')
    lines.append(f'        }}')
    if spell.description:
        lines.append(f'        DESCRIPTION {dsl_string(spell.description)}')
    lines.append(f'    }}')
    return "\n".join(lines)


def emit_virtue_flaw_def(entry: VirtueFlawEntry) -> str:
    prefix = "ARM5VG" if entry.type == "Virtue" else "ARM5FG"
    if entry.category == "Hermetic":
        prefix = "ARM5VH" if entry.type == "Virtue" else "ARM5FH"
    elif entry.category in ("Supernatural", "Tainted"):
        prefix = "ARM5VS" if entry.type == "Virtue" else "ARM5FS"

    h = make_hash(prefix)
    lines = []
    lines.append(f'    {h} {dsl_name(entry.name)} DEF {{')
    lines.append(f'        APPLIES TO [{dsl_name("Entity")}]')
    lines.append(f'        PROPERTIES {{')
    lines.append(f'            {dsl_name("Type")} ENUM ["{entry.type}"]')
    lines.append(f'            {dsl_name("Size")} ENUM ["{entry.size}"]')
    lines.append(f'            {dsl_name("Category")} ENUM ["{entry.category}"]')
    lines.append(f'        }}')
    if entry.description:
        lines.append(f'        DESCRIPTION {dsl_string(entry.description)}')
    lines.append(f'    }}')
    return "\n".join(lines)


def emit_ability_def(entry: AbilityEntry) -> str:
    h = make_hash("ARM5AB")
    lines = []
    lines.append(f'    {h} {dsl_name(entry.name)} DEF {{')
    lines.append(f'        APPLIES TO [{dsl_name("Entity")}]')
    lines.append(f'        PROPERTIES {{')
    lines.append(f'            {dsl_name("Ability Type")} ENUM ["{entry.ability_type}"]')
    if entry.requires_gift:
        lines.append(f'            {dsl_name("Requires Gift")} BOOLEAN true')
    if entry.specialties:
        spec_list = ", ".join(f'"{s}"' for s in entry.specialties)
        lines.append(f'            {dsl_name("Specialties")} LIST OF STRING [{spec_list}]')
    lines.append(f'        }}')
    if entry.description:
        lines.append(f'        DESCRIPTION {dsl_string(entry.description)}')
    lines.append(f'    }}')
    return "\n".join(lines)


# ============================================================
# FILE WRITERS
# ============================================================

def write_ttrpg_extension(output_dir: Path, filename: str, file_id: str,
                          name: str, depends_on: str, defs: list, source_title: str):
    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f'EXTENSION "{file_id}" {{\n')
        f.write(f'    NAME "{name}"\n')
        f.write(f'    VERSION "0.3"\n')
        f.write(f'    RELEASE_DATE "2026-03-05"\n')
        f.write(f'    DEPENDS_ON "{depends_on}"\n')
        f.write(f'    # Source: {source_title}\n')
        f.write(f'\n')
        for d in defs:
            f.write(d)
            f.write('\n\n')
        f.write('}\n')
    return filepath


def write_lore_file(output_dir: Path, filename: str, title: str,
                    content: str, source_title: str):
    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"**Version:** 0.3\n")
        f.write(f"**Source:** {source_title} (Atlas Games)\n")
        f.write(f"**Release Date:** 2026-03-05\n\n")
        f.write("---\n\n")
        f.write(content)
        f.write("\n")
    return filepath


# ============================================================
# MAIN — PROCESS ONE BOOK
# ============================================================

def process_book(book_key: str, config: dict):
    source_file = SOURCE_DIR / config["source"]
    output_dir = config["output_dir"]
    prefix = config["prefix"]
    title = config["title"]
    houses = config["houses"]
    fid_prefix = config["file_id_prefix"]

    print(f"\n{'=' * 60}")
    print(f"Processing: {title}")
    print(f"{'=' * 60}")

    output_dir.mkdir(parents=True, exist_ok=True)

    if not source_file.exists():
        print(f"  ERROR: Source file not found: {source_file}")
        return

    print(f"  Source: {source_file.name}")
    all_lines = read_markdown(source_file)
    print(f"  Read {len(all_lines)} lines")

    total_defs = 0
    total_files = 0

    # ---- SPELLS ----
    print(f"\n  --- Parsing Spells ---")
    spells = parse_hoh_spells(all_lines)
    print(f"  Found {len(spells)} spells")

    if spells:
        # Group by form
        spells_by_form = defaultdict(list)
        for s in spells:
            spells_by_form[s.form].append(s)

        for form in FORMS:
            form_spells = spells_by_form.get(form, [])
            if form_spells:
                defs = [emit_spell_def(s) for s in form_spells]
                fname = f"{prefix}-spells-{form.lower()}.ttrpg"
                write_ttrpg_extension(
                    output_dir, fname, f"{fid_prefix}_Spells_{form}",
                    f"{title} - {form} Spells",
                    "ARM5e_Core_Magic", defs, title
                )
                print(f"    Wrote {fname}: {len(defs)} spells")
                total_defs += len(defs)
                total_files += 1

    # ---- VIRTUES & FLAWS ----
    print(f"\n  --- Parsing Virtues & Flaws ---")
    virtues, flaws = parse_hoh_virtues_flaws(all_lines)
    print(f"  Found {len(virtues)} virtues, {len(flaws)} flaws")

    if virtues:
        defs = [emit_virtue_flaw_def(v) for v in virtues]
        fname = f"{prefix}-virtues.ttrpg"
        write_ttrpg_extension(
            output_dir, fname, f"{fid_prefix}_Virtues",
            f"{title} - Virtues",
            "ARM5e_Core_Character", defs, title
        )
        print(f"    Wrote {fname}: {len(defs)} virtues")
        total_defs += len(defs)
        total_files += 1

    if flaws:
        defs = [emit_virtue_flaw_def(f) for f in flaws]
        fname = f"{prefix}-flaws.ttrpg"
        write_ttrpg_extension(
            output_dir, fname, f"{fid_prefix}_Flaws",
            f"{title} - Flaws",
            "ARM5e_Core_Character", defs, title
        )
        print(f"    Wrote {fname}: {len(defs)} flaws")
        total_defs += len(defs)
        total_files += 1

    # ---- ABILITIES ----
    print(f"\n  --- Parsing Abilities ---")
    abilities = parse_hoh_abilities(all_lines)
    print(f"  Found {len(abilities)} abilities")

    if abilities:
        defs = [emit_ability_def(a) for a in abilities]
        fname = f"{prefix}-abilities.ttrpg"
        write_ttrpg_extension(
            output_dir, fname, f"{fid_prefix}_Abilities",
            f"{title} - Abilities",
            "ARM5e_Core_Base", defs, title
        )
        print(f"    Wrote {fname}: {len(defs)} abilities")
        total_defs += len(defs)
        total_files += 1

    # ---- LORE ----
    print(f"\n  --- Extracting Lore ---")
    lore = extract_hoh_lore(all_lines, houses)
    for key, (lore_title, content) in lore.items():
        fname = f"{prefix}-{key}.lore"
        write_lore_file(output_dir, fname, lore_title, content, title)
        print(f"    Wrote {fname}")
        total_files += 1

    print(f"\n  --- Summary for {title} ---")
    print(f"  Spells:      {len(spells)}")
    print(f"  Virtues:     {len(virtues)}")
    print(f"  Flaws:       {len(flaws)}")
    print(f"  Abilities:   {len(abilities)}")
    print(f"  Lore files:  {len(lore)}")
    print(f"  Total DEFs:  {total_defs}")
    print(f"  Total files: {total_files}")
    print(f"  Output: {output_dir}")

    return {
        "spells": len(spells),
        "virtues": len(virtues),
        "flaws": len(flaws),
        "abilities": len(abilities),
        "lore": len(lore),
        "total_defs": total_defs,
        "total_files": total_files,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("Houses of Hermes — v0.3 DSL Converter (Markdown)")
    print("=" * 60)

    # Allow specifying which books to process
    if len(sys.argv) > 1:
        book_keys = sys.argv[1:]
    else:
        book_keys = list(BOOKS.keys())

    grand_totals = defaultdict(int)

    for key in book_keys:
        if key not in BOOKS:
            print(f"Unknown book: {key}")
            print(f"Available: {', '.join(BOOKS.keys())}")
            continue

        # Reset hash counters per book to avoid collision
        _hash_counters.clear()

        result = process_book(key, BOOKS[key])
        if result:
            for k, v in result.items():
                grand_totals[k] += v

    print(f"\n{'=' * 60}")
    print("GRAND TOTAL")
    print(f"{'=' * 60}")
    print(f"  Spells:      {grand_totals['spells']}")
    print(f"  Virtues:     {grand_totals['virtues']}")
    print(f"  Flaws:       {grand_totals['flaws']}")
    print(f"  Abilities:   {grand_totals['abilities']}")
    print(f"  Lore files:  {grand_totals['lore']}")
    print(f"  Total DEFs:  {grand_totals['total_defs']}")
    print(f"  Total files: {grand_totals['total_files']}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
