#!/usr/bin/env python3
"""
Realms of Power -- v0.3 DSL Converter (Markdown sources)

Parses the four Realms of Power sourcebooks and emits v0.3 .ttrpg and
.lore files into titterpig-dsl-arm5e/0.3/{subdir}/.

Sources:
  - Faerie      -> 0.3/rop-faerie/
  - Magic       -> 0.3/rop-magic/
  - The Divine   -> 0.3/rop-divine/
  - The Infernal -> 0.3/rop-infernal/
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
SOURCE_BASE = SCRIPT_DIR.parent / "sources" / "arm5e" / "Ars-Magica-Open-License-main"

BOOKS = {
    "faerie": {
        "source": SOURCE_BASE / "wip" / "Ars Magica 5e - Realms of Power - Faerie.md",
        "output_dir": SCRIPT_DIR / "0.3" / "rop-faerie",
        "prefix": "arm5e-rop-faerie-0.3",
        "title": "Realms of Power: Faerie",
        "file_id_prefix": "ARM5e_RoP_Fae",
    },
    "magic": {
        "source": SOURCE_BASE / "wip" / "Ars Magica 5e - Realms of Power - Magic.md",
        "output_dir": SCRIPT_DIR / "0.3" / "rop-magic",
        "prefix": "arm5e-rop-magic-0.3",
        "title": "Realms of Power: Magic",
        "file_id_prefix": "ARM5e_RoP_Mag",
    },
    "infernal": {
        "source": SOURCE_BASE / "wip" / "Ars Magica 5e - Realms of Power - The Infernal.md",
        "output_dir": SCRIPT_DIR / "0.3" / "rop-infernal",
        "prefix": "arm5e-rop-infernal-0.3",
        "title": "Realms of Power: The Infernal",
        "file_id_prefix": "ARM5e_RoP_Inf",
    },
    "divine": {
        "source": SOURCE_BASE / "reviewed" / "Ars Magica 5e - Realms of Power - The Divine (Revised).md",
        "output_dir": SCRIPT_DIR / "0.3" / "rop-divine",
        "prefix": "arm5e-rop-divine-0.3",
        "title": "Realms of Power: The Divine",
        "file_id_prefix": "ARM5e_RoP_Div",
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
    "Road": "Road", "Prs": "Presence", "Presence": "Presence",
    "Sympathy": "Sympathy", "Prop": "Proprietary",
    "Water-way": "Water-way",
}

DURATION_MAP = {
    "Mom": "Momentary", "Momentary": "Momentary",
    "Conc": "Concentration", "Concentration": "Concentration",
    "Diam": "Diameter", "Diameter": "Diameter",
    "Sun": "Sun", "Ring": "Ring", "Moon": "Moon",
    "Year": "Year", "Fire": "Fire", "Bargain": "Bargain",
    "Until": "Until", "While": "While", "Mid": "Midday",
    "Focus": "Focus", "Forsaken": "Forsaken", "Aura": "Aura",
    "Perm": "Permanent", "Permanent": "Permanent",
    "Special": "Special", "Held": "Held",
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
    "Medium": "Medium", "Symbol": "Symbol",
    "Passion": "Passion", "Body-of-water": "Body-of-water",
    "Faith": "Faith", "Community": "Community",
    "Special": "Special",
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


@dataclass
class AbilityEntry:
    name: str
    ability_type: str
    specialties: list = field(default_factory=list)
    description: str = ""


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
    return re.sub(r'\*\*(.+?)\*\*', r'\1', s)


def to_title_case(name: str) -> str:
    """Convert ALL-CAPS names to Title Case."""
    minor = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'from',
             'in', 'into', 'nor', 'of', 'on', 'or', 'so', 'the', 'to',
             'up', 'yet', 'with'}
    words = name.split()
    result = []
    for i, w in enumerate(words):
        if "'" in w:
            parts = w.split("'")
            parts[0] = parts[0].capitalize()
            if len(parts) > 1:
                parts[1] = parts[1].lower()
            result.append("'".join(parts))
        elif i == 0:
            result.append(w.capitalize())
        elif w.lower() in minor:
            result.append(w.lower())
        else:
            result.append(w.capitalize())
    return ' '.join(result)


def fix_name_casing(name: str) -> str:
    """Fix ALL-CAPS names, return title case names unchanged."""
    words = name.split()
    alpha = [w.replace("'", "").replace("-", "").replace("(", "").replace(")", "")
             for w in words if len(w) >= 2]
    if not alpha:
        return name
    upper_count = sum(1 for w in alpha if w == w.upper() and w.isalpha())
    total_alpha = sum(1 for w in alpha if w.isalpha() and len(w) >= 2)
    if total_alpha > 0 and upper_count == total_alpha:
        return to_title_case(name)
    return name


# ============================================================
# SPELL PARSER (reused from HoH with adaptations)
# ============================================================

def parse_spells(lines: list) -> list:
    """Parse Hermetic spells from a Realms of Power sourcebook."""
    spells = []

    rdt_pat = re.compile(
        r'^R:\s*([^,;.]+?)\s*[,;.\s]\s*D:\s*([^,;.]+?)\s*[,;.\s]\s*T:\s*(.+?)\s*$'
    )
    tefo_pat = re.compile(
        r'^(Cr|In|Mu|Pe|Re)\(?(\w{2})?\)?(An|Aq|Au|Co|He|Ig|Im|Me|Te|Vi)'
        r'\(?(\w{2})?\)?\s+(\d+|Gen)\s*$'
    )
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

        sm = section_pat.match(line)
        if sm:
            cur_tech = sm.group(1).capitalize()
            cur_form = sm.group(2).capitalize()
            i += 1
            continue

        stripped = strip_bold(line)
        rdt_match = rdt_pat.match(stripped)

        if not rdt_match:
            i += 1
            continue

        r_val = rdt_match.group(1).strip()
        d_val = rdt_match.group(2).strip()
        t_rest = rdt_match.group(3).strip()

        level = None
        ritual = False
        requisite = ""

        level_m = re.search(r',?\s*\*?\*?Level\s+(\d+|Gen)\*?\*?', t_rest, re.IGNORECASE)
        if level_m:
            level = level_m.group(1)
            t_rest = t_rest[:level_m.start()].strip().rstrip(',. ')

        if re.search(r'\bRitual\b', t_rest, re.IGNORECASE):
            ritual = True
            t_rest = re.sub(r',?\s*Ritual\s*', '', t_rest, flags=re.IGNORECASE).strip()

        req_m = re.search(r',?\s*Req(?:uisite)?s?:\s*(.+)', t_rest, re.IGNORECASE)
        if req_m:
            requisite = req_m.group(1).strip()
            t_rest = t_rest[:req_m.start()].strip()

        t_val = t_rest.rstrip(',. ')

        technique = cur_tech
        form = cur_form
        name = None

        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1

        if i + 1 < len(lines):
            next_line = strip_bold(lines[i + 1].strip())
            req_m2 = req_pat.match(next_line)
            if req_m2 and not requisite:
                requisite = req_m2.group(1).strip()

        if j >= 0:
            candidate = lines[j].strip()
            candidate_clean = strip_bold(candidate)

            tefo_m = tefo_pat.match(candidate_clean)
            if tefo_m:
                technique = TE_ABBR.get(tefo_m.group(1), technique)
                form = FO_ABBR.get(tefo_m.group(3), form)
                if level is None:
                    level = tefo_m.group(5)
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
                k = j - 1
                while k >= 0 and not lines[k].strip():
                    k -= 1
                if k >= 0:
                    name = strip_bold(lines[k].strip())
            else:
                name = candidate_clean

        if not name or len(name) > 120:
            i += 1
            continue

        if section_pat.match(name) or design_pat.match(name):
            i += 1
            continue
        if name.startswith('R:') or name.startswith('(Base'):
            i += 1
            continue

        if level is None:
            level = "0"

        if "Ritual" in line and not ritual:
            ritual = True

        # Fix ALL-CAPS names
        name = fix_name_casing(name)

        # Collect description
        desc_start = i + 1
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
            if tefo_pat.match(dl_clean):
                break
            if section_pat.match(dl_clean):
                break
            if rdt_pat.match(dl_clean):
                break
            if dl.startswith('####') or dl.startswith('###'):
                break
            if re.match(r'^\*\*[A-Z][A-Z\s\']+\*\*$', dl):
                break
            if re.match(r'^[A-Z][A-Z\s\']{5,}$', dl_clean) and len(dl_clean) < 80:
                break
            if design_pat.match(dl_clean):
                design = dl_clean.strip("()")
                continue
            if dl_clean and len(dl_clean) < 100 and not dl.startswith('-') and not dl.startswith('('):
                nj = di + 1
                while nj < len(lines) and not lines[nj].strip():
                    nj += 1
                if nj < len(lines):
                    nxt_clean = strip_bold(lines[nj].strip())
                    if rdt_pat.match(nxt_clean) or tefo_pat.match(nxt_clean):
                        break
            desc_lines.append(dl_clean)

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
# VIRTUE/FLAW PARSER (extended for RoP categories)
# ============================================================

def parse_virtues_flaws(lines: list) -> tuple:
    """Parse virtues and flaws from a Realms of Power sourcebook."""
    virtues = []
    flaws = []

    # Extended category pattern for RoP books
    cat_pat = re.compile(
        r'^\*?(Major|Minor|Free|Major or Minor|Major/Minor)\s*[,.]?\s*'
        r'(General|Hermetic|Supernatural|Social Status|Social|Story|Personality|Tainted'
        r'|Heroic|Status'
        r'|Supernatural Ability|Supernatural Method|Supernatural Power'
        r'|Goetic Art|Unholy Method|Unholy Power'
        r'|Holy Method|Holy Power'
        r'|Hermetic and Supernatural|Supernatural and Hermetic'
        r'|Story, Supernatural|Hermetic, Story|General, Supernatural'
        r'|Hermetic \(House \w+ only\)|Social Status \(House \w+ only\)'
        r'|House \w+ only'
        r')'
        r'(?:\s*\(.*?\))?'
        r'(?:\s*Virtue|\s*Flaw)?'
        r'\*?\s*$'
    )

    section_vf_pat = re.compile(
        r'^(MINOR|MAJOR|FREE)\s+(HERMETIC|SUPERNATURAL|GENERAL|SOCIAL STATUS|STORY|PERSONALITY'
        r'|TAINTED|GOETIC|UNHOLY|HOLY)\s+'
        r'(VIRTUES?|FLAWS?)\s*$', re.IGNORECASE
    )

    section_type = None
    section_size = None
    section_category = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        stripped = strip_bold(line)

        sec_m = section_vf_pat.match(stripped)
        if sec_m:
            section_size = sec_m.group(1).capitalize()
            section_category = sec_m.group(2).strip().title()
            if section_category == "Social Status":
                pass
            vf_word = sec_m.group(3).upper()
            section_type = "Virtue" if "VIRTUE" in vf_word else "Flaw"
            i += 1
            continue

        # Track section context
        stripped_lower = stripped.lower()
        if stripped in ("New Virtues", "Virtues", "New Virtues and Flaws",
                        "Virtues & Flaws", "Virtues and Flaws"):
            section_type = "Virtue"
            i += 1
            continue
        if stripped in ("New Flaws", "Flaws"):
            section_type = "Flaw"
            i += 1
            continue

        cat_m = cat_pat.match(line)
        if cat_m:
            size = cat_m.group(1)
            category = cat_m.group(2)

            if size in ("Major or Minor", "Major/Minor"):
                size = "Major"
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
            # Normalize realm-specific categories to broader ones
            if category in ("Supernatural Ability", "Supernatural Method", "Supernatural Power"):
                category = "Supernatural"
            if category in ("Goetic Art", "Unholy Method", "Unholy Power"):
                category = "Supernatural"
            if category in ("Holy Method", "Holy Power"):
                category = "Supernatural"

            name_idx = i - 1
            while name_idx >= 0 and not lines[name_idx].strip():
                name_idx -= 1

            if name_idx < 0:
                i += 1
                continue

            name = strip_bold(lines[name_idx].strip())
            name = re.sub(r'^#+\s*', '', name)
            name = name.strip('*').strip()

            if not name or len(name) > 120:
                i += 1
                continue

            name = fix_name_casing(name)

            entry_type = section_type or "Virtue"

            # Determine type from keywords in context
            # Look for "Flaw" indicator
            if "Flaw" in line:
                entry_type = "Flaw"
            elif "Virtue" in line:
                entry_type = "Virtue"

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
                if cat_pat.match(dl):
                    break
                if dl_clean in ("Virtues", "Flaws", "New Virtues", "New Flaws",
                                "Virtues and Flaws", "New Virtues and Flaws",
                                "Virtues & Flaws", "Appendix"):
                    break
                if re.match(r'^\*\*[A-Z]+\s*,\s*[A-Z]+\*\*\s*$', dl):
                    break
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

        # Reset section context at chapter headings
        elif section_type and (
            stripped.startswith("Chapter ") or
            stripped == "Appendix" or
            stripped == "Abilities" or
            re.match(r'^(Creo|Intellego|Muto|Perdo|Rego)\s+', stripped, re.IGNORECASE)
        ):
            section_type = None
            section_size = None
            section_category = None

        # Handle entries under section headings with no individual category lines
        elif section_type and section_size and section_category:
            if (re.match(r'^\*\*[A-Z]', line) and not cat_pat.match(line)
                    and '**R:**' not in line and 'R:' not in strip_bold(line)
                    and 'D:' not in strip_bold(line)):
                bold_m = re.match(r'^\*\*(.+?)\*\*[:\s.]*\s*(.*)', line)
                if bold_m:
                    name = bold_m.group(1).strip().rstrip(':').rstrip('.').rstrip('*')
                    inline_desc = bold_m.group(2).strip()
                else:
                    name = strip_bold(line).strip().rstrip(':').rstrip('.')
                    inline_desc = ""
                if (name and len(name) < 80 and not section_pat_match(stripped)
                        and not re.match(r'^Level \d', name)
                        and not re.match(r'^\d+', name)
                        and ':' not in name):
                    name = fix_name_casing(name)
                    ni = i + 1
                    while ni < len(lines) and not lines[ni].strip():
                        ni += 1
                    if ni < len(lines) and not cat_pat.match(lines[ni].strip()):
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
                            if section_vf_pat.match(dl_clean):
                                break
                            if dl_clean in ("Virtues", "Flaws", "New Virtues", "New Flaws",
                                            "Virtues and Flaws", "Appendix"):
                                break
                            if re.match(r'^\*\*[A-Z]', dl) and di > i:
                                bold_check = re.match(r'^\*\*(.+?)\*\*', dl)
                                if bold_check and len(bold_check.group(1)) < 80:
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


def section_pat_match(s):
    return bool(re.match(
        r'^(Creo|Intellego|Muto|Perdo|Rego)\s+'
        r'(Animal|Aquam|Auram|Corpus|Herbam|Ignem|Imaginem|Mentem|Terram|Vim)',
        s, re.IGNORECASE
    ))


# ============================================================
# ABILITY PARSER
# ============================================================

def parse_abilities(lines: list) -> list:
    """Parse new abilities from a Realms of Power sourcebook."""
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
            name = fix_name_casing(m.group(1).strip())
            desc_lines = []
            ability_type = "Supernatural"
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
# LORE EXTRACTOR (by chapter for RoP books)
# ============================================================

def extract_lore(lines: list, book_title: str) -> dict:
    """Extract lore sections from a Realms of Power sourcebook.

    Extracts the first few hundred lines from each major chapter.
    """
    lore = {}

    chapter_starts = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^Chapter\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten'
                    r'|Eleven|Twelve|Thirteen|1|2|3|4|5|6|7|8|9|10|11|12|13)\b',
                    stripped, re.IGNORECASE):
            # Get chapter title from same or next line
            title = stripped
            if i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].strip().startswith('Chapter'):
                title = stripped + ": " + lines[i + 1].strip()
            chapter_starts.append((i, title))

    for idx, (start, title) in enumerate(chapter_starts):
        end = chapter_starts[idx + 1][0] if idx + 1 < len(chapter_starts) else len(lines)
        section = lines[start:min(start + 400, end)]
        content = "\n".join(l for l in section if l.strip())
        content = clean_text(content)
        if len(content) > 10000:
            content = content[:10000] + "\n\n[Content truncated]"

        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60]
        key = f"ch{idx + 1}-{slug}"
        lore[key] = (title, content)

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
# MAIN -- PROCESS ONE BOOK
# ============================================================

def process_book(book_key: str, config: dict):
    source_file = config["source"]
    output_dir = config["output_dir"]
    prefix = config["prefix"]
    title = config["title"]
    fid_prefix = config["file_id_prefix"]

    print(f"\n{'=' * 60}")
    print(f"Processing: {title}")
    print(f"{'=' * 60}")

    output_dir.mkdir(parents=True, exist_ok=True)

    if not source_file.exists():
        print(f"  ERROR: Source file not found: {source_file}")
        return None

    print(f"  Source: {source_file.name}")
    all_lines = read_markdown(source_file)
    print(f"  Read {len(all_lines)} lines")

    total_defs = 0
    total_files = 0

    # ---- SPELLS ----
    print(f"\n  --- Parsing Spells ---")
    spells = parse_spells(all_lines)
    print(f"  Found {len(spells)} spells")

    if spells:
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
    virtues, flaws = parse_virtues_flaws(all_lines)
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
    abilities = parse_abilities(all_lines)
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
    lore = extract_lore(all_lines, title)
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
    print("Realms of Power -- v0.3 DSL Converter (Markdown)")
    print("=" * 60)

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
