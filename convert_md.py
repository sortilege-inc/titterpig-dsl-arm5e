#!/usr/bin/env python3
"""
Ars Magica Definitive Edition — v0.3 DSL Converter (Markdown source)

Parses the "Ars Magica Definitive High Contrast.md" markdown file and emits
v0.3 .ttrpg and .lore files into titterpig-dsl-arm5e/0.3/.

Source: /titterpig/sources/arm5e/Ars-Magica-Open-License-main/wip/
        Ars Magica Definitive High Contrast.md
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
SOURCE_FILE = (
    SCRIPT_DIR.parent / "sources" / "arm5e"
    / "Ars-Magica-Open-License-main" / "wip"
    / "Ars Magica Definitive High Contrast.md"
)
OUTPUT_DIR = SCRIPT_DIR / "0.3" / "core-definitive"

TECHNIQUES = ["Creo", "Intellego", "Muto", "Perdo", "Rego"]
FORMS = ["Animal", "Aquam", "Auram", "Corpus", "Herbam",
         "Ignem", "Imaginem", "Mentem", "Terram", "Vim"]

RANGE_MAP = {
    "Per": "Personal", "Personal": "Personal",
    "Touch": "Touch", "Eye": "Eye",
    "Voice": "Voice", "Sight": "Sight",
    "Arc": "Arcane Connection", "Arcane Connection": "Arcane Connection",
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
    "Circle": "Circle",
    "Bloodline": "Bloodline",
    "Taste": "Taste", "Hearing": "Hearing",
    "Smell": "Smell", "Touch": "Touch", "Vision": "Vision",
}

VIRTUE_CATEGORIES = ["General", "Hermetic", "Supernatural", "Social Status",
                     "Story", "Personality", "Tainted"]
VIRTUE_SIZES = ["Major", "Minor", "Free", "Major or Minor"]

ABILITY_TYPES = {
    "General": "General", "Academic": "Academic", "Arcane": "Arcane",
    "Martial": "Martial", "Supernatural": "Supernatural",
}


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class SpellEntry:
    name: str
    technique: str
    form: str
    level: str  # integer or "Gen"
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


@dataclass
class CreatureEntry:
    name: str
    might: int = 0
    might_type: str = ""
    form: str = ""
    size: int = 0
    characteristics: dict = field(default_factory=dict)
    virtues_flaws: str = ""
    qualities: str = ""
    personality_traits: str = ""
    reputations: str = ""
    combat: str = ""
    soak: str = ""
    fatigue_levels: str = ""
    wound_penalties: str = ""
    abilities: str = ""
    powers: str = ""
    natural_weapons: str = ""
    vis: str = ""
    appearance: str = ""
    confidence: str = ""
    is_mundane: bool = False


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

_hash_counters = defaultdict(int)


def make_hash(prefix: str) -> str:
    """Generate a sequential hash ID with the given prefix."""
    _hash_counters[prefix] += 1
    seq = f"{_hash_counters[prefix]:03d}"
    pad_chars = "aB2cD4eF6gH8iJ0kL"
    needed = 24 - len(prefix) - len(seq) - 1
    pad = (pad_chars * 3)[:needed]
    return f"#{prefix}{seq}{pad}"


def dsl_string(s: str) -> str:
    """Quote a string for DSL output. Use triple-quotes for multiline."""
    if not s:
        return '""'
    s = s.strip()
    if "\n" in s:
        return f'"""{s}"""'
    s = s.replace('"', '\\"')
    return f'"{s}"'


def dsl_name(name: str) -> str:
    """Format a caret-quoted name reference."""
    return f'^"{name}"'


def indent(text: str, level: int = 1) -> str:
    """Indent text by level * 4 spaces."""
    prefix = "    " * level
    lines = text.split("\n")
    return "\n".join(prefix + line if line.strip() else "" for line in lines)


def clean_text(text: str) -> str:
    """Clean up text: normalize smart quotes, whitespace, markdown artifacts."""
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2013', '-').replace('\u2014', ' -- ')
    # Remove markdown bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # Remove escaped asterisks
    text = text.replace('\\*', '*')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def strip_md_heading(line: str) -> str:
    """Strip markdown heading prefix (####, ###, ##, #)."""
    return re.sub(r'^#{1,6}\s+', '', line)


# ============================================================
# MARKDOWN READER
# ============================================================

def strip_latex(s: str) -> str:
    """Remove LaTeX math wrappers, extracting inner text."""
    if '$' not in s:
        return s
    latex_cmd = re.compile(r'\\(?:mathsf|textbf|mbox|hbox|text|scriptsize|tiny)\{([^}]+)\}')
    result = latex_cmd.sub(r'\1', s)
    result = re.sub(r'\$', '', result)
    result = re.sub(r'\\begin\{array\}\{[^}]*\}', '', result)
    result = re.sub(r'\\end\{array\}', '', result)
    result = re.sub(r'\\\\', ' ', result)
    result = re.sub(r'\\,', '', result)
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def read_markdown(filepath: Path) -> list:
    """Read the markdown file and return list of text lines.

    Strips markdown heading prefixes and LaTeX artifacts to produce plain text
    lines comparable to .docx paragraph output.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    lines = []
    for raw in raw_lines:
        line = raw.rstrip('\n')
        # Strip heading markers but preserve the text
        if line.startswith('#'):
            line = strip_md_heading(line)
        # Remove escaped asterisks (markdown artifact)
        line = line.replace('\\*', '*')
        # Strip LaTeX math formatting
        if '$' in line:
            line = strip_latex(line)
        lines.append(line)

    return lines


def extract_section(lines: list, start_heading: str, end_headings: list = None,
                    start_line: int = 0) -> list:
    """Extract lines from a section starting at start_heading.

    Returns lines from the heading match to the next h2 (##) heading
    or any heading in end_headings.
    """
    section_start = None
    for i in range(start_line, len(lines)):
        # Check original line for heading match
        stripped = lines[i].strip()
        if stripped == start_heading:
            section_start = i
            break

    if section_start is None:
        return []

    section_end = len(lines)
    for i in range(section_start + 1, len(lines)):
        stripped = lines[i].strip()
        if end_headings and stripped in end_headings:
            section_end = i
            break

    return lines[section_start:section_end]


# ============================================================
# SPELL PARSER (MARKDOWN)
# ============================================================

def parse_spells_markdown(lines: list) -> list:
    """Parse spells from the Spells section of the markdown.

    Two-pass approach:
      Pass 1: Build context maps (section headers, level markers, technique/form).
      Pass 2: Anchor on every R:D:T line, look back for name/level, forward for desc.
    """
    spells = []

    # --- Patterns ---
    section_pat = re.compile(
        r'^(Creo|Intellego|Muto|Perdo|Rego)\s*(Animal|Aquam|Auram|Corpus|Herbam|'
        r'Ignem|Imaginem|Mentem|Terram|Vim)\s+(Spells|Guidelines)$'
    )
    form_only_pat = re.compile(
        r'^(Animal|Aquam|Auram|Corpus|Herbam|Ignem|Imaginem|Mentem|Terram|Vim)\s+Spells$'
    )
    level_pat = re.compile(r'^(?:LEVEL\s+)?(\d+)\s*$', re.IGNORECASE)
    level_heading_pat = re.compile(r'^LEVEL\s+(\d+)\s*$', re.IGNORECASE)
    general_pat = re.compile(r'^General\s*$')
    # R:D:T can be standalone or inline with name; separators can be , ; . or space
    rdt_pat = re.compile(
        r'^R:\s*([^,;.]+?)\s*[,;.\s]\s*D:\s*([^,;.]+?)\s*[,;.\s]\s*T:\s*(.+?)\s*$'
    )
    # Inline: "SPELL NAME R: Touch, D: Sun, T: Ind"
    inline_rdt_pat = re.compile(
        r'^(.+?)\s+R:\s*([^,;.]+?)\s*[,;.\s]\s*D:\s*([^,;.]+?)\s*[,;.\s]\s*T:\s*(.+?)\s*$'
    )
    design_pat = re.compile(r'^\(Base\s+.+\)\s*$')
    req_line_pat = re.compile(r'^Req(?:uisite)?:\s*(.+)$', re.IGNORECASE)

    # --- Pre-process: split inline name+R:D:T lines ---
    # (LaTeX already stripped globally by read_markdown)
    expanded_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('R:') and not stripped.startswith('('):
            m = inline_rdt_pat.match(stripped)
            if m:
                name_part = m.group(1).strip()
                rdt_part = f"R: {m.group(2).strip()}, D: {m.group(3).strip()}, T: {m.group(4).strip()}"
                # Only split if name_part looks like a spell name (not a sentence)
                if len(name_part) < 80 and not name_part.startswith('Level'):
                    expanded_lines.append(name_part)
                    expanded_lines.append(rdt_part)
                    continue
        expanded_lines.append(line)

    lines = expanded_lines

    # --- Pass 1: Build context ---
    tech_at = [None] * len(lines)
    form_at = [None] * len(lines)
    level_at = [None] * len(lines)
    in_spells_at = [False] * len(lines)

    cur_tech = None
    cur_form = None
    cur_level = None
    cur_in_spells = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        m = section_pat.match(stripped)
        if m:
            cur_tech = m.group(1)
            cur_form = m.group(2)
            # Both "Spells" and "Guidelines" headings set cur_in_spells=True
            # because spells appear after Guidelines headings for many combos
            cur_in_spells = True
            cur_level = None
        else:
            m = form_only_pat.match(stripped)
            if m:
                cur_form = m.group(1)
                cur_tech = None
                cur_in_spells = True
                cur_level = None
            elif stripped in ("Ritual Spells", "Spell Format", "Magical Senses",
                              "Magical Wards", "Magical Craft"):
                cur_in_spells = False
            elif "Spells and Enchanted Devices" in stripped and cur_in_spells:
                cur_in_spells = False
            elif level_heading_pat.match(stripped):
                cur_level = level_heading_pat.match(stripped).group(1)
            elif general_pat.match(stripped):
                cur_level = "Gen"

        tech_at[i] = cur_tech
        form_at[i] = cur_form
        level_at[i] = cur_level
        in_spells_at[i] = cur_in_spells

    # --- Pass 2: Find all R:D:T lines and build spells ---
    rdt_indices = []
    for i, line in enumerate(lines):
        if in_spells_at[i] and rdt_pat.match(line.strip()):
            rdt_indices.append(i)

    for ri, rdt_idx in enumerate(rdt_indices):
        stripped_rdt = lines[rdt_idx].strip()
        m = rdt_pat.match(stripped_rdt)
        if not m:
            continue

        r, d, t = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()

        # Parse Ritual flag
        ritual = False
        if "Ritual" in t:
            ritual = True
            t = re.sub(r',?\s*Ritual\s*', '', t).strip()

        # Parse inline Requisite
        requisite = ""
        req_m = re.search(r'Req(?:uisite)?:\s*(.+)', t)
        if req_m:
            requisite = req_m.group(1).strip()
            t = re.sub(r',?\s*Req(?:uisite)?:.*$', '', t).strip()
        t = t.rstrip(", .")

        # Look back for spell name
        name = None
        name_idx = rdt_idx - 1
        while name_idx >= 0 and not lines[name_idx].strip():
            name_idx -= 1
        if name_idx >= 0:
            candidate = lines[name_idx].strip()
            if (candidate and len(candidate) < 100
                    and not level_pat.match(candidate)
                    and not general_pat.match(candidate)
                    and not section_pat.match(candidate)
                    and not form_only_pat.match(candidate)
                    and not candidate.startswith('R:')
                    and not design_pat.match(candidate)):
                name = candidate

        if not name:
            continue

        # Get technique/form/level from context
        technique = tech_at[rdt_idx]
        form = form_at[rdt_idx]
        level = level_at[rdt_idx]

        if not technique:
            for j in range(rdt_idx, -1, -1):
                if tech_at[j]:
                    technique = tech_at[j]
                    break

        # Check for Requisite on its own line after R:D:T
        if not requisite and rdt_idx + 1 < len(lines):
            req_m2 = req_line_pat.match(lines[rdt_idx + 1].strip())
            if req_m2:
                requisite = req_m2.group(1).strip()

        # Collect description
        desc_start = rdt_idx + 1
        if requisite and desc_start < len(lines) and req_line_pat.match(lines[desc_start].strip()):
            desc_start += 1

        if ri + 1 < len(rdt_indices):
            next_rdt = rdt_indices[ri + 1]
            desc_end = next_rdt - 1
            while desc_end > desc_start and not lines[desc_end].strip():
                desc_end -= 1
        else:
            desc_end = len(lines) - 1

        desc_lines = []
        design = ""
        for j in range(desc_start, desc_end + 1):
            s = lines[j].strip()
            if not s:
                continue
            if section_pat.match(s) or form_only_pat.match(s):
                break
            if level_heading_pat.match(s) or general_pat.match(s):
                break
            if design_pat.match(s):
                design = s.strip("()")
                continue
            desc_lines.append(s)

        desc = clean_text("\n".join(desc_lines))
        if len(desc) > 2000:
            desc = desc[:2000] + "..."

        spells.append(SpellEntry(
            name=name,
            technique=technique or "Rego",
            form=form or "Vim",
            level=str(level) if level else "0",
            range=RANGE_MAP.get(r, r),
            duration=DURATION_MAP.get(d, d),
            target=TARGET_MAP.get(t, t),
            ritual=ritual,
            requisite=requisite,
            design=design,
            description=desc,
        ))

    return spells


# ============================================================
# VIRTUE/FLAW PARSER (MARKDOWN)
# ============================================================

def parse_virtues_flaws_markdown(lines: list) -> tuple:
    """Parse virtues and flaws from the markdown.

    In the markdown, individual entries are:
        #### Name
        Size, Category
        Description paragraph(s)...

    Returns (virtues, flaws).
    """
    # Category line pattern
    cat_pattern = re.compile(
        r'^(Major|Minor|Free|Major or Minor|Minor or Major)\s*[.,]\s*'
        r'(General|Hermetic|Supernatural|Social Status|Story|Personality|Tainted'
        r'|Mythic Companion|Special'
        r'|General and Hermetic|Hermetic and General|Story and Hermetic'
        r'|Hermetic, Tainted|Story, Tainted|General, Tainted|Supernatural, Tainted'
        r'|Hermetic, Story|Story, Supernatural|General or Supernatural|Hermetic or General'
        r'|Social Status, Supernatural|Social Status, animals only|General, animals only'
        r')'
        r'(?:\s*,\s*.+)?$'  # allow trailing qualifiers
    )

    # Find "Virtues" and "Flaws" major sections
    # In the markdown, these are "## Virtues" and "## Flaws" headings
    # (stripped to just "Virtues" and "Flaws" by read_markdown)
    virtues_start = None
    flaws_start = None

    # First, find all "Flaws" lines (there may be multiple: list and detailed)
    flaws_candidates = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "Virtues" and virtues_start is None:
            virtues_start = i
        if stripped == "Flaws":
            flaws_candidates.append(i)

    # If we didn't find explicit virtues section, scan for the pattern
    if virtues_start is None:
        for i, line in enumerate(lines):
            if cat_pattern.match(line.strip()):
                virtues_start = max(0, i - 2)
                break

    # The flaws divider is the "Flaws" heading that comes AFTER individual
    # virtue descriptions have started (i.e., after we've seen cat_pattern matches).
    # It separates the virtue descriptions from the flaw descriptions.
    first_cat_match = None
    for i in range(virtues_start or 0, len(lines)):
        if cat_pattern.match(lines[i].strip()):
            first_cat_match = i
            break

    if first_cat_match is not None:
        for idx in flaws_candidates:
            if idx > first_cat_match + 100:  # Well past the first few entries
                flaws_start = idx
                break

    if flaws_start is None:
        flaws_start = len(lines)

    # Find all entries: look for category-pattern lines preceded by a name
    headers = []  # (line_idx_of_name, name, size, category, is_flaw)
    scan_start = virtues_start or 0

    for i in range(scan_start, len(lines) - 1):
        stripped = lines[i].strip()
        m = cat_pattern.match(stripped)
        if not m:
            continue

        # Name is on the previous non-blank line
        name_idx = i - 1
        while name_idx >= scan_start and not lines[name_idx].strip():
            name_idx -= 1

        if name_idx < scan_start:
            continue

        name = lines[name_idx].strip()
        # Validate: not too long, starts with letter or special char
        if not name or len(name) > 100:
            continue
        if not (name[0].isalpha() or name[0] in ('(', "'", '\u2018', '"')):
            continue

        size = m.group(1)
        category = m.group(2)

        # Normalize size
        if "or" in size:
            size = "Major"

        # Normalize category
        if "Tainted" in category:
            category = "Tainted"
        elif category in ("Mythic Companion", "Special"):
            category = "General"
        elif "and" in category or "or" in category:
            parts = re.split(r'\s+and\s+|\s+or\s+', category)
            category = parts[0].strip()
        elif ", " in category:
            parts = category.split(", ")
            category = parts[0].strip()

        name = clean_text(name)
        is_flaw = (flaws_start is not None and i > flaws_start)
        headers.append((name_idx, name, size, category, is_flaw))

    # Build entries with descriptions
    virtues = []
    flaws = []

    for idx, (line_num, name, size, category, is_flaw) in enumerate(headers):
        desc_begin = line_num + 2  # Skip name and category lines
        if idx + 1 < len(headers):
            desc_end = headers[idx + 1][0]
        else:
            desc_end = len(lines)

        desc_lines = [lines[j].strip() for j in range(desc_begin, desc_end)
                       if lines[j].strip()]
        desc = clean_text("\n".join(desc_lines))
        if len(desc) > 1500:
            desc = desc[:1500] + "..."

        entry_type = "Flaw" if is_flaw else "Virtue"

        entry = VirtueFlawEntry(
            name=name,
            type=entry_type,
            size=size,
            category=category,
            description=desc,
        )

        if entry_type == "Virtue":
            virtues.append(entry)
        else:
            flaws.append(entry)

    return virtues, flaws


# ============================================================
# ABILITY PARSER (MARKDOWN)
# ============================================================

def parse_abilities_markdown(lines: list) -> list:
    """Parse abilities from the Ability List section of the markdown."""
    entries = []

    # Find "Ability List" header
    list_start = None
    for i, line in enumerate(lines):
        if line.strip() == "Ability List":
            list_start = i + 1
            break

    if list_start is None:
        return entries

    # Skip the intro line
    if list_start < len(lines) and "This list contains" in lines[list_start]:
        list_start += 1

    # Ability name pattern: Name[*]: description
    # Handles optional **bold** markdown wrapping
    name_pat = re.compile(
        r'^\*{0,2}(\(?[A-Z][A-Za-z\s\(\)\'\-&:]+?\*?)\*{0,2}\s*:\s+'
    )

    NON_ABILITY_NAMES = {
        "Specialties", "Specialty", "Specialities", "Note", "Notes",
        "Example", "Examples", "Warning", "Important",
        "Ease Factor", "Ease Factors",
        "Memorization Ease Factors", "Example of Curse-Throwing",
        "Hex Effects", "Hex Delay Modifiers", "Roll Modifiers",
        "Entrancement and Induction", "Complex Memorization Roll",
        "Stress Die", "Simple Die", "HEX",
        "The artes liberales are divided into two groups",
    }

    # Find the end of the ability list section.
    # The section ends at the next chapter heading (e.g., "VI. Covenants")
    # NOT at "Example of Curse-Throwing" which is an inline sidebar.
    list_end = len(lines)
    for i in range(list_start, len(lines)):
        stripped = lines[i].strip()
        # Chapter heading pattern: "VI. Covenants", "VII. ...", etc.
        if re.match(r'^[IVXL]+\.\s+', stripped):
            list_end = i
            break

    # First pass: find ability start lines (within the ability list section only)
    ability_starts = []
    for i in range(list_start, list_end):
        line = lines[i].strip()
        m = name_pat.match(line)
        if m:
            raw_name = m.group(1).strip()
            clean_raw = raw_name.rstrip('*').strip()
            if clean_raw in NON_ABILITY_NAMES or raw_name in NON_ABILITY_NAMES:
                continue
            if len(raw_name) > 60:
                continue
            rest = line[m.end():].strip()
            ability_starts.append((i, raw_name, rest))

    # Second pass: collect each ability's full text
    for idx, (start_line, raw_name, first_line_rest) in enumerate(ability_starts):
        if idx + 1 < len(ability_starts):
            end_line = ability_starts[idx + 1][0]
        else:
            end_line = len(lines)

        text_parts = [first_line_rest]
        for j in range(start_line + 1, end_line):
            line = lines[j].strip()
            if line:
                text_parts.append(line)

        full_text = "\n".join(text_parts)

        requires_gift = False
        name = raw_name
        if name.endswith('*'):
            name = name[:-1].strip()
            requires_gift = True

        # Extract (Type) from the full text
        ability_type = "General"
        type_pat = re.compile(r'\((' + '|'.join(ABILITY_TYPES.keys()) + r')\)')
        for part in reversed(text_parts):
            tm = type_pat.search(part)
            if tm:
                ability_type = tm.group(1)
                break

        # Extract Specialties
        specialties = []
        spec_m = re.search(
            r'[Ss]pecialt(?:ies|y):\s*([^.]+?)\.?\s*\((?:General|Academic|Arcane|Martial|Supernatural)\)',
            full_text
        )
        if not spec_m:
            spec_m = re.search(r'[Ss]pecialt(?:ies|y):\s*([^.]+?)\.', full_text)
        if spec_m:
            spec_text = spec_m.group(1)
            specialties = [s.strip() for s in spec_text.split(",") if s.strip()]

        # Clean description
        desc = full_text
        spec_idx = desc.find("Specialties:")
        if spec_idx == -1:
            spec_idx = desc.find("Specialities:")
        if spec_idx == -1:
            spec_idx = desc.find("specialties:")
        if spec_idx > 0:
            desc = desc[:spec_idx]
        desc = clean_text(desc)
        if len(desc) > 1000:
            desc = desc[:1000] + "..."

        entries.append(AbilityEntry(
            name=name,
            ability_type=ability_type,
            specialties=specialties,
            description=desc,
            requires_gift=requires_gift,
        ))

    return entries


# ============================================================
# CREATURE PARSER (MARKDOWN)
# ============================================================

CREATURE_FIELDS = [
    "Characteristics", "Size", "Confidence Score", "Confidence",
    "Virtues and Flaws", "Qualities", "Personality Traits",
    "Reputations", "Combat", "Soak", "Fatigue Levels",
    "Wound Penalties", "Abilities", "Powers", "Equipment",
    "Natural Weapons", "Vis", "Appearance",
]


def parse_creatures_markdown(lines: list) -> dict:
    """Parse creatures from the Bestiary section of the markdown.

    Returns dict of realm -> list[CreatureEntry].
    """
    creatures = {}

    realm_patterns = {
        "mundane": "Mundane Beasts",
        "magical": "Creatures of Magic",
        "faerie": "Creatures of Faerie",
        "infernal": "Infernal Creatures",
        "divine": "Angelic Powers",
    }

    realm_starts = {}
    for realm, header in realm_patterns.items():
        for i, line in enumerate(lines):
            if line.strip() == header:
                realm_starts[realm] = i
                break

    skip_sections = {
        "Creating Mundane Beasts", "Creating Creatures", "Beasts in Combat",
        "Creature Might", "Creature Powers", "Creature Format",
        "Demonic Powers", "Demonic Weaknesses", "Demons and Magic",
        "Demons and Free Will", "Character Conversion",
    }

    # Find Bestiary chapter end (next chapter heading like "XIV. Mythic Europe")
    bestiary_end = len(lines)
    for i in range(max(realm_starts.values()) if realm_starts else 0, len(lines)):
        stripped = lines[i].strip()
        if re.match(r'^[IVXL]+\.\s+Mythic\s+Europe', stripped):
            bestiary_end = i
            break

    sorted_realms = sorted(realm_starts.items(), key=lambda x: x[1])

    for idx, (realm, start) in enumerate(sorted_realms):
        if idx + 1 < len(sorted_realms):
            end = sorted_realms[idx + 1][1]
        else:
            end = bestiary_end
        realm_lines = lines[start:end]
        creatures[realm] = extract_creatures_from_realm(realm_lines, realm, skip_sections)

    return creatures


def extract_creatures_from_realm(realm_lines: list, realm: str, skip_sections: set) -> list:
    """Extract creature entries from a realm section."""
    entries = []

    char_indices = []
    for i, line in enumerate(realm_lines):
        stripped = line.strip()
        if stripped.startswith("Characteristics:") or stripped == "Characteristics":
            char_indices.append(i)
        elif "Characteristics:" in stripped and (
            "Might:" in stripped or "textbf{Characteristics" in stripped
        ):
            # Handle merged "Magic Might: X (Form) Characteristics: ..." lines
            # and LaTeX-wrapped Characteristics lines
            char_indices.append(i)

    for ci_idx, char_line in enumerate(char_indices):
        # If Characteristics is merged with Might on same line, find the name before Might
        char_stripped = realm_lines[char_line].strip()
        if "Might:" in char_stripped and "Characteristics:" in char_stripped:
            # Merged line — look further back for name
            name_idx = char_line - 1
        else:
            name_idx = char_line - 1

        while name_idx >= 0:
            stripped = realm_lines[name_idx].strip()
            if not stripped:
                name_idx -= 1
                continue
            if re.match(r'^(?:Magic|Faerie|Infernal|Divine)\s+Might:', stripped):
                name_idx -= 1
                continue
            # Skip Might continuation lines like "6 (Corpus)" or "10 (Animal)"
            if re.match(r'^\d+\s*\([^)]+\)\s*$', stripped):
                name_idx -= 1
                continue
            if re.match(r'^Size:', stripped) or re.match(r'^Age:', stripped):
                name_idx -= 1
                continue
            if stripped.startswith('\u2014') or stripped.startswith('--') or stripped.startswith('-'):
                name_idx -= 1
                continue
            if re.match(r'^\d+\s+\w+\s+\d+:\d+', stripped):
                name_idx -= 1
                continue
            if len(stripped) > 100:
                name_idx -= 1
                continue
            # Skip markdown blockquotes
            if stripped.startswith('>'):
                name_idx -= 1
                continue
            break

        if name_idx < 0:
            continue

        name = realm_lines[name_idx].strip()
        clean_name = re.sub(r'\s*\([^)]+\)\s*$', '', name).strip()
        # Remove bold markdown
        clean_name = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_name)

        if clean_name in skip_sections or not clean_name:
            continue
        if len(clean_name) > 80:
            continue

        block_start = name_idx
        if ci_idx + 1 < len(char_indices):
            next_char = char_indices[ci_idx + 1]
            block_end = next_char
            ni = next_char - 1
            while ni > char_line:
                s = realm_lines[ni].strip()
                if not s:
                    ni -= 1
                    continue
                if re.match(r'^(?:Magic|Faerie|Infernal|Divine)\s+Might:', s):
                    ni -= 1
                    continue
                block_end = ni
                break
        else:
            block_end = len(realm_lines)

        block = realm_lines[block_start:block_end]
        entry = parse_single_creature(clean_name, block, realm)
        if entry:
            entries.append(entry)

    return entries


def parse_single_creature(name: str, block_lines: list, realm: str) -> CreatureEntry:
    """Parse a single creature stat block."""
    entry = CreatureEntry(name=name)
    entry.is_mundane = (realm == "mundane")

    text = "\n".join(block_lines)

    # Might
    m = re.search(r'(?:Magic|Faerie|Infernal|Divine)\s+Might:\s*(\d+)\s*(?:\(([^)]+)\))?', text)
    if m:
        entry.might = int(m.group(1))
        entry.form = m.group(2) or ""
        for mt in ["Magic", "Faerie", "Infernal", "Divine"]:
            if text[:m.start()].rfind(mt) >= 0 or m.group(0).startswith(mt):
                entry.might_type = mt
                break
        if not entry.might_type:
            entry.might_type = realm.capitalize() if realm != "mundane" else "Magic"

    # Parse fields
    field_data = {}
    current_field = None
    current_lines = []

    field_pat = re.compile(
        r'^(' + '|'.join(re.escape(f) for f in CREATURE_FIELDS) + r'):\s*(.*)'
    )

    for line in block_lines:
        stripped = line.strip()
        if not stripped:
            if current_field:
                current_lines.append("")
            continue

        m = field_pat.match(stripped)
        if m:
            if current_field:
                field_data[current_field] = "\n".join(current_lines).strip()
            current_field = m.group(1)
            current_lines = [m.group(2)]
        elif current_field:
            current_lines.append(stripped)

    if current_field:
        field_data[current_field] = "\n".join(current_lines).strip()

    # Characteristics
    chars_text = field_data.get("Characteristics", "")
    if chars_text:
        for char_name, abbr in [("Intelligence", "Int"), ("Cunning", "Cun"),
                                 ("Perception", "Per"), ("Presence", "Pre"),
                                 ("Communication", "Com"), ("Strength", "Str"),
                                 ("Stamina", "Sta"), ("Dexterity", "Dex"),
                                 ("Quickness", "Qik")]:
            cm = re.search(rf'{abbr}\s+([+\-]?\d+)', chars_text)
            if cm:
                entry.characteristics[char_name] = int(cm.group(1).replace("+", ""))

    # Size
    size_text = field_data.get("Size", "")
    if size_text:
        size_m = re.match(r'([+\-]?\d+)', size_text.strip())
        if size_m:
            entry.size = int(size_m.group(1).replace("+", ""))

    # Confidence
    entry.confidence = field_data.get("Confidence Score", field_data.get("Confidence", ""))

    # Simple string fields
    entry.virtues_flaws = clean_text(field_data.get("Virtues and Flaws", ""))
    entry.qualities = clean_text(field_data.get("Qualities", ""))
    entry.personality_traits = clean_text(field_data.get("Personality Traits", ""))
    entry.reputations = clean_text(field_data.get("Reputations", ""))
    entry.combat = clean_text(field_data.get("Combat", ""))
    entry.soak = field_data.get("Soak", "").strip()
    entry.fatigue_levels = clean_text(field_data.get("Fatigue Levels", ""))
    entry.wound_penalties = clean_text(field_data.get("Wound Penalties", ""))
    entry.abilities = clean_text(field_data.get("Abilities", ""))
    entry.powers = clean_text(field_data.get("Powers", ""))
    entry.natural_weapons = clean_text(field_data.get("Natural Weapons", ""))
    entry.vis = clean_text(field_data.get("Vis", ""))

    appearance = clean_text(field_data.get("Appearance", ""))
    if len(appearance) > 1500:
        appearance = appearance[:1500] + "..."
    entry.appearance = appearance

    return entry


# ============================================================
# LORE EXTRACTOR (MARKDOWN)
# ============================================================

# Map of lore key -> (section_heading, title, end_heading_or_none)
LORE_SECTIONS = {
    "introduction": {
        "title": "Ars Magica -- Introduction",
        "start_heading": "Preface",
        "end_before": "Die Rolls and Difficulty",
    },
    "order-of-hermes": {
        "title": "The Order of Hermes",
        "start_heading": "The History of the Order",
        "end_before": "The Peripheral Code",
    },
    "covenant-life": {
        "title": "Covenant Life",
        "start_heading": "Through the Aegis",
        "end_before": "The Gift",
    },
    "realms": {
        "title": "The Four Realms -- Magic and the Supernatural",
        "start_heading": "Realm Auras",
        "end_before": "Vis Sources",
    },
    "bestiary": {
        "title": "Bestiary -- Introduction",
        "start_heading": "Vis Sources",
        "end_before": "Mundane Beasts",
    },
    "mythic-europe": {
        "title": "Mythic Europe -- Setting",
        "start_heading": "Making it Historical",
        "end_before": "Player Character Centrality",
    },
    "stories": {
        "title": "Stories -- Running the Game",
        "start_heading": "Player Character Centrality",
        "end_before": "Troupe-Style Roleplaying",
    },
    "sagas": {
        "title": "Stories and Sagas",
        "start_heading": "Troupe-Style Roleplaying",
        "end_before": "That is the Open License?",
    },
}


def extract_lore_markdown(lines: list) -> dict:
    """Extract lore content from narrative sections of the markdown.

    Returns dict of key -> (title, content_text).
    """
    lore = {}

    # Build a heading index for quick lookup
    heading_index = {}  # heading_text -> line_number
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            heading_index.setdefault(stripped, i)

    for key, config in LORE_SECTIONS.items():
        title = config["title"]
        start_heading = config["start_heading"]
        end_before = config.get("end_before")

        start_idx = heading_index.get(start_heading)
        if start_idx is None:
            print(f"  WARNING: Lore section not found: {start_heading}")
            continue

        end_idx = len(lines)
        if end_before:
            end_candidate = heading_index.get(end_before)
            if end_candidate and end_candidate > start_idx:
                end_idx = end_candidate

        section_lines = lines[start_idx:end_idx]
        content = "\n".join(l for l in section_lines if l.strip())

        # Limit lore size
        paras = content.split("\n\n")
        if len(paras) > 500:
            content = "\n\n".join(paras[:500])

        content = clean_text(content)
        lore[key] = (title, content)

    return lore


# ============================================================
# DSL EMITTERS (same as original convert.py)
# ============================================================

def emit_spell_def(spell: SpellEntry) -> str:
    """Emit a single spell DEF block."""
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
    """Emit a single virtue or flaw DEF block."""
    prefix = "ARM5VG" if entry.type == "Virtue" else "ARM5FG"
    if entry.category == "Hermetic":
        prefix = "ARM5VH" if entry.type == "Virtue" else "ARM5FH"
    elif entry.category == "Supernatural" or entry.category == "Tainted":
        prefix = "ARM5VS" if entry.type == "Virtue" else "ARM5FS"

    h = make_hash(prefix)
    lines = []
    lines.append(f'    {h} {dsl_name(entry.name)} DEF {{')
    lines.append(f'        APPLIES TO [{dsl_name("Entity")}]')
    lines.append(f'        PROPERTIES {{')
    lines.append(f'            {dsl_name("Type")} ENUM ["{entry.type}"]')
    lines.append(f'            {dsl_name("Size")} ENUM ["{entry.size}"]')
    lines.append(f'            {dsl_name("Category")} ENUM ["{entry.category}"]')
    if entry.repeatable:
        lines.append(f'            {dsl_name("Repeatable")} BOOLEAN true')
    lines.append(f'        }}')
    if entry.description:
        lines.append(f'        DESCRIPTION {dsl_string(entry.description)}')
    lines.append(f'    }}')
    return "\n".join(lines)


def emit_ability_def(entry: AbilityEntry) -> str:
    """Emit a single ability DEF block."""
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


def emit_creature_def(entry: CreatureEntry) -> str:
    """Emit a single creature DEF block."""
    h = make_hash("ARM5CR")
    lines = []
    lines.append(f'    {h} {dsl_name(entry.name)} DEF {{')
    lines.append(f'        EXTENDS {dsl_name("Creature")}')
    lines.append(f'        PROPERTIES {{')

    if not entry.is_mundane and entry.might:
        lines.append(f'            {dsl_name("Might")} INTEGER {entry.might}')
        if entry.might_type:
            lines.append(f'            {dsl_name("Might Type")} ENUM ["{entry.might_type}"]')
        if entry.form:
            lines.append(f'            {dsl_name("Form")} STRING "{entry.form}"')

    lines.append(f'            {dsl_name("Size")} INTEGER {entry.size}')

    if entry.characteristics:
        lines.append(f'            {dsl_name("Characteristics")} DEF {{')
        for char_name, val in entry.characteristics.items():
            lines.append(f'                {dsl_name(char_name)} INTEGER {val}')
        lines.append(f'            }}')

    if entry.virtues_flaws:
        lines.append(f'            {dsl_name("Virtues and Flaws")} STRING {dsl_string(entry.virtues_flaws)}')
    if entry.personality_traits:
        lines.append(f'            {dsl_name("Personality Traits")} STRING {dsl_string(entry.personality_traits)}')
    if entry.combat:
        lines.append(f'            {dsl_name("Combat")} STRING {dsl_string(entry.combat)}')
    if entry.soak:
        lines.append(f'            {dsl_name("Soak")} STRING "{entry.soak}"')
    if entry.fatigue_levels:
        lines.append(f'            {dsl_name("Fatigue Levels")} STRING {dsl_string(entry.fatigue_levels)}')
    if entry.wound_penalties:
        lines.append(f'            {dsl_name("Wound Penalties")} STRING {dsl_string(entry.wound_penalties)}')
    if entry.abilities:
        lines.append(f'            {dsl_name("Abilities")} STRING {dsl_string(entry.abilities)}')
    if entry.powers:
        lines.append(f'            {dsl_name("Powers")} STRING {dsl_string(entry.powers)}')
    if entry.vis:
        lines.append(f'            {dsl_name("Vis")} STRING {dsl_string(entry.vis)}')
    if entry.appearance:
        lines.append(f'            {dsl_name("Appearance")} STRING {dsl_string(entry.appearance)}')

    lines.append(f'        }}')
    lines.append(f'    }}')
    return "\n".join(lines)


# ============================================================
# FILE WRITERS
# ============================================================

def write_ttrpg_extension(filename: str, file_id: str, name: str,
                          depends_on: str, defs: list):
    """Write a .ttrpg extension file."""
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f'EXTENSION "{file_id}" {{\n')
        f.write(f'    NAME "{name}"\n')
        f.write(f'    VERSION "0.3"\n')
        f.write(f'    RELEASE_DATE "2026-03-05"\n')
        f.write(f'    DEPENDS_ON "{depends_on}"\n')
        f.write(f'\n')
        for d in defs:
            f.write(d)
            f.write('\n\n')
        f.write('}\n')
    return filepath


def write_lore_file(filename: str, title: str, content: str):
    """Write a .lore file."""
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"**Version:** 0.3\n")
        f.write(f"**Source:** Ars Magica Definitive Edition (Atlas Games, 2025)\n")
        f.write(f"**Release Date:** 2026-03-05\n\n")
        f.write("---\n\n")
        f.write(content)
        f.write("\n")
    return filepath


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def main():
    print("=" * 60)
    print("Ars Magica Definitive Edition — v0.3 DSL Converter (Markdown)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not SOURCE_FILE.exists():
        print(f"ERROR: Source file not found: {SOURCE_FILE}")
        sys.exit(1)
    print(f"\nSource: {SOURCE_FILE}")

    # Read the full markdown file
    print("Reading markdown file...")
    all_lines = read_markdown(SOURCE_FILE)
    print(f"  Read {len(all_lines)} lines")

    # ---- SPELLS ----
    print("\n--- Parsing Spells ---")
    # Extract the spells section (from "Spell Format" to end of Vim spells)
    spell_start = None
    spell_end = None
    for i, line in enumerate(all_lines):
        stripped = line.strip()
        if stripped == "Spell Format" and spell_start is None:
            spell_start = i
        # End at "Experience and Advancement" or similar post-spell section
        if stripped in ("Experience and Advancement", "Advancement") and spell_start and spell_end is None:
            spell_end = i
            break
    if spell_start is None:
        # Fallback: search for first Creo Animal Guidelines
        for i, line in enumerate(all_lines):
            if "Creo Animal Guidelines" in line.strip():
                spell_start = i
                break
    if spell_end is None:
        spell_end = len(all_lines)

    spell_lines = all_lines[spell_start:spell_end] if spell_start else []
    print(f"  Spell section: lines {spell_start}-{spell_end} ({len(spell_lines)} lines)")
    spells = parse_spells_markdown(spell_lines)
    print(f"  Found {len(spells)} spells")

    # Group spells by Form
    spells_by_form = defaultdict(list)
    for s in spells:
        spells_by_form[s.form].append(s)

    spell_files = 0
    spell_total = 0
    for form in FORMS:
        form_spells = spells_by_form.get(form, [])
        if form_spells:
            defs = [emit_spell_def(s) for s in form_spells]
            fname = f"arm5e-core-definitive-0.3-spells-{form.lower()}.ttrpg"
            fid = f"ARM5e_Spells_{form}"
            write_ttrpg_extension(
                fname, fid,
                f"Ars Magica Definitive Edition - {form} Spells",
                "ARM5e_Core_Magic", defs
            )
            print(f"  Wrote {fname}: {len(defs)} spells")
            spell_files += 1
            spell_total += len(defs)

    # ---- VIRTUES & FLAWS ----
    print("\n--- Parsing Virtues & Flaws ---")
    # The virtues/flaws section spans from "## Virtues" to the Abilities section
    vf_start = None
    vf_end = None
    for i, line in enumerate(all_lines):
        stripped = line.strip()
        if stripped == "Virtues" and i > 3000 and vf_start is None:
            vf_start = i
        if stripped == "Abilities With No Score" and vf_start and vf_end is None:
            vf_end = i
            break
    if vf_end is None:
        vf_end = len(all_lines)

    vf_lines = all_lines[vf_start:vf_end] if vf_start else all_lines
    print(f"  V&F section: lines {vf_start}-{vf_end} ({len(vf_lines)} lines)")
    virtues, flaws = parse_virtues_flaws_markdown(vf_lines)
    print(f"  Found {len(virtues)} virtues, {len(flaws)} flaws")

    def group_by_cat(entries):
        groups = {"general": [], "hermetic": [], "supernatural": []}
        for e in entries:
            cat = e.category.lower()
            if cat in ("hermetic",):
                groups["hermetic"].append(e)
            elif cat in ("supernatural", "tainted"):
                groups["supernatural"].append(e)
            else:
                groups["general"].append(e)
        return groups

    virtue_groups = group_by_cat(virtues)
    flaw_groups = group_by_cat(flaws)

    vf_files = 0
    vf_total = 0

    for cat_key, cat_name in [("general", "General"), ("hermetic", "Hermetic"),
                               ("supernatural", "Supernatural")]:
        v_entries = virtue_groups[cat_key]
        if v_entries:
            defs = [emit_virtue_flaw_def(v) for v in v_entries]
            fname = f"arm5e-core-definitive-0.3-virtues-{cat_key}.ttrpg"
            fid = f"ARM5e_Virtues_{cat_name}"
            write_ttrpg_extension(
                fname, fid,
                f"Ars Magica Definitive Edition - {cat_name} Virtues",
                "ARM5e_Core_Character", defs
            )
            print(f"  Wrote {fname}: {len(defs)} virtues")
            vf_files += 1
            vf_total += len(defs)

        f_entries = flaw_groups[cat_key]
        if f_entries:
            defs = [emit_virtue_flaw_def(f) for f in f_entries]
            fname = f"arm5e-core-definitive-0.3-flaws-{cat_key}.ttrpg"
            fid = f"ARM5e_Flaws_{cat_name}"
            write_ttrpg_extension(
                fname, fid,
                f"Ars Magica Definitive Edition - {cat_name} Flaws",
                "ARM5e_Core_Character", defs
            )
            print(f"  Wrote {fname}: {len(defs)} flaws")
            vf_files += 1
            vf_total += len(defs)

    # ---- ABILITIES ----
    print("\n--- Parsing Abilities ---")
    # Abilities section starts at "Ability List"
    abilities = parse_abilities_markdown(all_lines)
    print(f"  Found {len(abilities)} abilities")

    if abilities:
        seen_names = {}
        deduped = []
        for a in abilities:
            if a.name in seen_names:
                first = seen_names[a.name]
                if a.description:
                    first.description = first.description.rstrip() + "\n\n" + a.description
            else:
                seen_names[a.name] = a
                deduped.append(a)
        abilities = deduped
        defs = [emit_ability_def(a) for a in abilities]
        fname = "arm5e-core-definitive-0.3-abilities.ttrpg"
        write_ttrpg_extension(
            fname, "ARM5e_Abilities",
            "Ars Magica Definitive Edition - Abilities",
            "ARM5e_Core_Base", defs
        )
        print(f"  Wrote {fname}: {len(defs)} abilities")

    # ---- CREATURES ----
    print("\n--- Parsing Creatures ---")
    creatures = parse_creatures_markdown(all_lines)
    creature_files = 0
    creature_total = 0

    realm_names = {
        "mundane": ("Mundane", "ARM5e_Bestiary_Mundane"),
        "magical": ("Magical", "ARM5e_Bestiary_Magical"),
        "faerie": ("Faerie", "ARM5e_Bestiary_Faerie"),
        "infernal": ("Infernal", "ARM5e_Bestiary_Infernal"),
        "divine": ("Divine", "ARM5e_Bestiary_Divine"),
    }

    for realm, entries in creatures.items():
        if entries:
            defs = [emit_creature_def(c) for c in entries]
            display_name, fid = realm_names.get(
                realm, (realm.capitalize(), f"ARM5e_Bestiary_{realm.capitalize()}")
            )
            fname = f"arm5e-core-definitive-0.3-bestiary-{realm}.ttrpg"
            write_ttrpg_extension(
                fname, fid,
                f"Ars Magica Definitive Edition - {display_name} Creatures",
                "ARM5e_Core_Base", defs
            )
            print(f"  Wrote {fname}: {len(defs)} creatures")
            creature_files += 1
            creature_total += len(defs)

    # ---- LORE FILES ----
    print("\n--- Extracting Lore ---")
    lore = extract_lore_markdown(all_lines)

    lore_files = 0
    for key, (title, content) in lore.items():
        fname = f"arm5e-core-definitive-0.3-{key}.lore"
        write_lore_file(fname, title, content)
        print(f"  Wrote {fname}")
        lore_files += 1

    # ---- SUMMARY ----
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    print(f"  Source:           {SOURCE_FILE.name}")
    print(f"  Spells:           {spell_total} entries in {spell_files} files")
    print(f"  Virtues & Flaws:  {vf_total} entries in {vf_files} files")
    print(f"  Abilities:        {len(abilities)} entries in 1 file")
    print(f"  Creatures:        {creature_total} entries in {creature_files} files")
    print(f"  Lore files:       {lore_files}")
    print(f"  Base files:       5 (hand-crafted, copy from 0.2)")
    total_files = spell_files + vf_files + 1 + creature_files + lore_files + 5
    total_defs = spell_total + vf_total + len(abilities) + creature_total
    print(f"  ---")
    print(f"  TOTAL FILES:      {total_files}")
    print(f"  TOTAL DEFs:       {total_defs}")
    print(f"\n  Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
