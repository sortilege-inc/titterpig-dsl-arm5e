#!/usr/bin/env python3
"""
Ars Magica 5th Edition Definitive — v0.3 DSL Converter

Parses the manuscript .docx files and emits v0.3 .ttrpg and .lore files
into titterpig-dsl-arm5e/0.3/.

Source: /titterpig/sources/arm5e/ArMDef Manuscript Docs/
"""

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
from docx import Document

# ============================================================
# CONFIGURATION
# ============================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
SOURCE_DIR = SCRIPT_DIR.parent / "sources" / "arm5e"
DOCS_DIR = SOURCE_DIR / "ArMDef Manuscript Docs"
OUTPUT_DIR = SCRIPT_DIR / "0.3"

TECHNIQUES = ["Creo", "Intellego", "Muto", "Perdo", "Rego"]
FORMS = ["Animal", "Aquam", "Auram", "Corpus", "Herbam",
         "Ignem", "Imaginem", "Mentem", "Terram", "Vim"]

RANGE_MAP = {
    "Per": "Personal", "Personal": "Personal",
    "Touch": "Touch", "Eye": "Eye",
    "Voice": "Voice", "Sight": "Sight",
    "Arc": "Arcane Connection", "Arcane Connection": "Arcane Connection",
}

DURATION_MAP = {
    "Mom": "Momentary", "Momentary": "Momentary",
    "Conc": "Concentration", "Concentration": "Concentration",
    "Diam": "Diameter", "Diameter": "Diameter",
    "Sun": "Sun", "Ring": "Ring", "Moon": "Moon",
    "Year": "Year",
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
    # Pad with alternating alpha/digits to fill 24 chars total
    pad_chars = "aB2cD4eF6gH8iJ0kL"
    needed = 24 - len(prefix) - len(seq) - 1  # -1 for #
    pad = (pad_chars * 3)[:needed]
    return f"#{prefix}{seq}{pad}"


def dsl_string(s: str) -> str:
    """Quote a string for DSL output. Use triple-quotes for multiline."""
    if not s:
        return '""'
    s = s.strip()
    if "\n" in s:
        return f'"""{s}"""'
    # Escape internal quotes
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


def clean_manuscript_text(text: str) -> str:
    """Clean up manuscript text: normalize smart quotes, whitespace."""
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2013', '-').replace('\u2014', ' -- ')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ============================================================
# MANUSCRIPT READER
# ============================================================

def read_manuscript_doc(filepath: Path) -> list:
    """Read a .docx manuscript and return list of paragraph text lines."""
    doc = Document(str(filepath))
    return [p.text for p in doc.paragraphs]


# ============================================================
# SPELL PARSER (MANUSCRIPT)
# ============================================================

def parse_spells_manuscript(lines: list) -> list:
    """Parse spells from manuscript 09-Spells.docx paragraph lines.

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
    level_pat = re.compile(r'^Level\s+(\d+)\s*$')
    general_pat = re.compile(r'^General\s*$')
    rdt_pat = re.compile(
        r'^R:\s*([^,]+?)\s*[,;]?\s*D:\s*([^,;]+?)\s*[,;]?\s*T:\s*(.+?)\s*$'
    )
    design_pat = re.compile(r'^\(Base\s+.+\)\s*$')
    req_line_pat = re.compile(r'^Req(?:uisite)?:\s*(.+)$', re.IGNORECASE)

    # --- Pass 1: Build context at each line index ---
    # Track technique, form, level, and whether we're in a Spells section
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
            cur_in_spells = (m.group(3) == "Spells")
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
            elif level_pat.match(stripped):
                cur_level = level_pat.match(stripped).group(1)
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

        # Look back for spell name: previous non-empty line
        name = None
        name_idx = rdt_idx - 1
        while name_idx >= 0 and not lines[name_idx].strip():
            name_idx -= 1
        if name_idx >= 0:
            candidate = lines[name_idx].strip()
            # Validate: not a level marker, section header, or too long
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

        # Get technique/form/level from context at the R:D:T line
        technique = tech_at[rdt_idx]
        form = form_at[rdt_idx]
        level = level_at[rdt_idx]

        # If technique is None (form-only section), try to infer from nearby
        # section headers by scanning back
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

        # Collect description: lines after R:D:T (and optional Req line) until
        # the next R:D:T's name line, or a section/level header
        desc_start = rdt_idx + 1
        if requisite and desc_start < len(lines) and req_line_pat.match(lines[desc_start].strip()):
            desc_start += 1

        # Find end of description
        if ri + 1 < len(rdt_indices):
            # End before the name line of the next spell (one line before next R:D:T)
            next_rdt = rdt_indices[ri + 1]
            # Walk back from next R:D:T to find its name line
            desc_end = next_rdt - 1
            while desc_end > desc_start and not lines[desc_end].strip():
                desc_end -= 1
            # desc_end is the name line of the next spell, so stop before it
        else:
            desc_end = len(lines) - 1

        desc_lines = []
        design = ""
        for j in range(desc_start, desc_end + 1):
            s = lines[j].strip()
            if not s:
                continue
            # Stop at section/level headers
            if section_pat.match(s) or form_only_pat.match(s):
                break
            if level_pat.match(s) or general_pat.match(s):
                break
            if design_pat.match(s):
                design = s.strip("()")
                continue
            desc_lines.append(s)

        desc = clean_manuscript_text("\n".join(desc_lines))
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
# VIRTUE/FLAW PARSER (MANUSCRIPT)
# ============================================================

def parse_virtues_flaws_manuscript(lines: list) -> tuple:
    """Parse virtues and flaws from manuscript 04-Virtues.docx paragraph lines.

    Returns (virtues, flaws) as lists of VirtueFlawEntry.
    """
    # Category pattern on a line by itself.
    # Handles standard ("Minor, General") and non-standard forms:
    #   "Minor or Major, General", "Free, Mythic Companion",
    #   "Minor, General, animals only", "Minor, Hermetic, Tainted", etc.
    cat_pattern = re.compile(
        r'^(Major|Minor|Free|Major or Minor|Minor or Major)\s*,\s*'
        r'(General|Hermetic|Supernatural|Social Status|Story|Personality|Tainted'
        r'|Mythic Companion|Special'
        r'|General and Hermetic|Hermetic and General|Story and Hermetic'
        r'|Hermetic, Tainted|Story, Tainted|General, Tainted|Supernatural, Tainted'
        r'|Hermetic, Story|Story, Supernatural|General or Supernatural|Hermetic or General'
        r'|Social Status, Supernatural|Social Status, animals only|General, animals only'
        r')'
    )

    # Find the "Flaws" dividing line in the detailed descriptions section.
    # There are two "Flaws" lines: one in the quick-reference (~line 588) and
    # one in the detailed descriptions (~line 2214). We want the second one.
    flaws_line_indices = [i for i, l in enumerate(lines) if l.strip() == 'Flaws']

    # Find where detailed descriptions begin (first cat_pattern match after ~line 800)
    desc_start = 0
    for i in range(800, len(lines)):
        if cat_pattern.match(lines[i].strip()):
            desc_start = i - 1
            break

    # The detailed flaws divider is the "Flaws" line that comes after desc_start
    flaws_divider = None
    for idx in flaws_line_indices:
        if idx > desc_start:
            flaws_divider = idx
            break

    # Find all entry headers in the detailed section
    headers = []  # (line_idx, name, size, category)
    for i in range(desc_start, len(lines) - 1):
        m = cat_pattern.match(lines[i].strip())
        if m:
            name_line = i - 1
            if name_line >= 0:
                name = lines[name_line].strip()
                # Validate name
                if name and len(name) < 100 and (name[0].isupper() or name[0] in ('(', '\u2018', "'")):
                    size = m.group(1)
                    category = m.group(2)
                    # Normalize size
                    if "or" in size:
                        size = "Major"
                    # Normalize category to canonical form
                    if "Tainted" in category:
                        category = "Tainted"
                    elif category in ("Mythic Companion", "Special"):
                        category = "General"
                    elif "and" in category or "or" in category:
                        # "General and Hermetic" -> take primary
                        parts = re.split(r'\s+and\s+|\s+or\s+', category)
                        category = parts[0].strip()
                    elif ", " in category:
                        # "Social Status, Supernatural" / "Social Status, animals only"
                        parts = category.split(", ")
                        category = parts[0].strip()
                    # Normalize smart quotes in name
                    name = clean_manuscript_text(name)
                    headers.append((name_line, name, size, category))

    # Build entries with descriptions
    virtues = []
    flaws = []

    for idx, (line_num, name, size, category) in enumerate(headers):
        desc_begin = line_num + 2  # Skip name and category lines
        if idx + 1 < len(headers):
            desc_end = headers[idx + 1][0]
        else:
            desc_end = len(lines)

        desc_lines = [lines[j].strip() for j in range(desc_begin, desc_end) if lines[j].strip()]
        desc = clean_manuscript_text("\n".join(desc_lines))
        if len(desc) > 1500:
            desc = desc[:1500] + "..."

        entry_type = "Flaw" if (flaws_divider and line_num > flaws_divider) else "Virtue"

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
# ABILITY PARSER (MANUSCRIPT)
# ============================================================

def parse_abilities_manuscript(lines: list) -> list:
    """Parse abilities from manuscript 05-Abilities.docx paragraph lines."""
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
    if list_start < len(lines) and lines[list_start].startswith("This list contains"):
        list_start += 1

    # Ability name pattern: starts with a capitalized word (possibly parenthetical)
    # followed by optional asterisk and colon
    name_pat = re.compile(
        r'^(\(?[A-Z][A-Za-z\s\(\)\'\-&:]+?\*?)\s*:\s+'
    )

    # Words that are NOT ability names
    NON_ABILITY_NAMES = {
        "Specialties", "Specialty", "Note", "Notes", "Example", "Examples",
        "Warning", "Important", "Ease Factor", "Ease Factors",
        "Memorization Ease Factors", "Example of Curse-Throwing",
        "Hex Effects", "Hex Delay Modifiers", "Roll Modifiers",
        "Entrancement and Induction",
    }

    # First pass: find ability start lines
    ability_starts = []  # (line_index, name, rest_of_first_line)
    for i in range(list_start, len(lines)):
        m = name_pat.match(lines[i])
        if m:
            raw_name = m.group(1).strip()
            # Skip non-ability header lines
            if raw_name in NON_ABILITY_NAMES or raw_name.rstrip('*') in NON_ABILITY_NAMES:
                continue
            # Skip very long names (sentence fragments)
            if len(raw_name) > 60:
                continue
            rest = lines[i][m.end():].strip()
            ability_starts.append((i, raw_name, rest))

    # Second pass: collect each ability's full text
    for idx, (start_line, raw_name, first_line_rest) in enumerate(ability_starts):
        # Find end: next ability start, or end of file
        if idx + 1 < len(ability_starts):
            end_line = ability_starts[idx + 1][0]
        else:
            end_line = len(lines)

        # Collect all text for this ability
        text_parts = [first_line_rest]
        for j in range(start_line + 1, end_line):
            # Skip lines that look like table headers/data (tab-separated)
            line = lines[j].strip()
            if line:
                text_parts.append(line)

        full_text = "\n".join(text_parts)

        # Check for asterisk (supernatural/special marker)
        requires_gift = False
        name = raw_name
        if name.endswith('*'):
            name = name[:-1].strip()
            requires_gift = True

        # Extract (Type) from the full text
        ability_type = "General"
        type_pat = re.compile(r'\((' + '|'.join(ABILITY_TYPES.keys()) + r')\)')
        # Search backwards through text parts for the type marker
        for part in reversed(text_parts):
            tm = type_pat.search(part)
            if tm:
                ability_type = tm.group(1)
                break

        # Extract Specialties
        specialties = []
        spec_m = re.search(r'Specialties?:\s*([^.]+?)\.?\s*\((?:General|Academic|Arcane|Martial|Supernatural)\)', full_text)
        if not spec_m:
            # Try without the type anchor
            spec_m = re.search(r'Specialties?:\s*([^.]+?)\.', full_text)
        if spec_m:
            spec_text = spec_m.group(1)
            specialties = [s.strip() for s in spec_text.split(",") if s.strip()]

        # Clean description: take text up to Specialties line
        desc = full_text
        # Remove everything from "Specialties:" onward for clean description
        spec_idx = desc.find("Specialties:")
        if spec_idx == -1:
            spec_idx = desc.find("Specialities:")  # handle typo
        if spec_idx > 0:
            desc = desc[:spec_idx]
        desc = clean_manuscript_text(desc)
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
# CREATURE PARSER (MANUSCRIPT)
# ============================================================

# Stat block fields in order of appearance
CREATURE_FIELDS = [
    "Characteristics", "Size", "Confidence Score", "Virtues and Flaws",
    "Qualities", "Personality Traits", "Reputations", "Combat",
    "Soak", "Fatigue Levels", "Wound Penalties", "Abilities",
    "Powers", "Equipment", "Natural Weapons", "Vis", "Appearance",
]


def parse_creatures_manuscript(lines: list) -> dict:
    """Parse creatures from manuscript 13-Bestiary.docx paragraph lines.

    Returns dict of realm -> list[CreatureEntry].
    """
    creatures = {}

    # Find realm section boundaries
    realm_patterns = {
        "mundane": "Mundane Beasts",
        "magical": "Creatures of Magic",
        "faerie": "Creatures of Faerie",
        "infernal": "Infernal Creatures",
        "divine": "Creatures of the Divine",
    }

    realm_starts = {}
    for realm, header in realm_patterns.items():
        for i, line in enumerate(lines):
            if line.strip() == header:
                realm_starts[realm] = i
                break

    # Non-creature sections to skip
    skip_sections = {"Creating Mundane Beasts", "Creating Creatures", "Beasts in Combat"}

    # Sort realm starts by line number
    sorted_realms = sorted(realm_starts.items(), key=lambda x: x[1])

    for idx, (realm, start) in enumerate(sorted_realms):
        end = sorted_realms[idx + 1][1] if idx + 1 < len(sorted_realms) else len(lines)
        realm_lines = lines[start:end]
        creatures[realm] = extract_creatures_from_realm(realm_lines, realm, skip_sections)

    return creatures


def extract_creatures_from_realm(realm_lines: list, realm: str, skip_sections: set) -> list:
    """Extract creature entries from a realm section."""
    entries = []

    # Find all "Characteristics:" lines — each marks a creature
    char_indices = []
    for i, line in enumerate(realm_lines):
        if line.strip().startswith("Characteristics:"):
            char_indices.append(i)

    for ci_idx, char_line in enumerate(char_indices):
        # Walk back from Characteristics to find the creature name
        # Skip Might, Size, Age, blank lines, and citation/quote lines
        name_idx = char_line - 1
        while name_idx >= 0:
            stripped = realm_lines[name_idx].strip()
            if not stripped:
                name_idx -= 1
                continue
            if re.match(r'^(?:Magic|Faerie|Infernal|Divine)\s+Might:', stripped):
                name_idx -= 1
                continue
            if re.match(r'^Size:', stripped) or re.match(r'^Age:', stripped):
                name_idx -= 1
                continue
            # Skip citation lines (start with em-dash, or are short quote attributions)
            if stripped.startswith('\u2014') or stripped.startswith('—') or stripped.startswith('–'):
                name_idx -= 1
                continue
            # Skip scripture/quote citations (e.g., "4 Maccabees 7:11", "—Qur'an 2:97")
            if re.match(r'^\d+\s+\w+\s+\d+:\d+', stripped):
                name_idx -= 1
                continue
            # Skip book citations (e.g., "Author (d. YYYY), Book Title")
            if re.search(r'\(d\.\s*\d{3,4}\)', stripped):
                name_idx -= 1
                continue
            # Skip long quote paragraphs (>100 chars)
            if len(stripped) > 100:
                name_idx -= 1
                continue
            break

        if name_idx < 0:
            continue

        name = realm_lines[name_idx].strip()
        # Clean name: remove parenthetical Latin name
        clean_name = re.sub(r'\s*\([^)]+\)\s*$', '', name).strip()

        # Skip non-creature headings
        if clean_name in skip_sections or not clean_name:
            continue
        # Skip if name looks like a rule paragraph (too long)
        if len(clean_name) > 80:
            continue

        # Determine block boundaries
        block_start = name_idx
        if ci_idx + 1 < len(char_indices):
            # End before next creature's name line (walk back from next Characteristics)
            next_char = char_indices[ci_idx + 1]
            # Walk back to find next creature's name
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
        entry = parse_single_creature_manuscript(clean_name, block, realm)
        if entry:
            entries.append(entry)

    return entries


def parse_single_creature_manuscript(name: str, block_lines: list, realm: str) -> CreatureEntry:
    """Parse a single creature stat block from manuscript lines."""
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

    # Parse fields using line-by-line approach
    field_data = {}
    current_field = None
    current_lines = []

    field_pat = re.compile(r'^(' + '|'.join(re.escape(f) for f in CREATURE_FIELDS) + r'):\s*(.*)')

    for line in block_lines:
        stripped = line.strip()
        if not stripped:
            if current_field:
                current_lines.append("")
            continue

        m = field_pat.match(stripped)
        if m:
            # Save previous field
            if current_field:
                field_data[current_field] = "\n".join(current_lines).strip()
            current_field = m.group(1)
            current_lines = [m.group(2)]
        elif current_field:
            current_lines.append(stripped)

    # Save last field
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
    entry.confidence = field_data.get("Confidence Score", "")

    # Simple string fields
    entry.virtues_flaws = clean_manuscript_text(field_data.get("Virtues and Flaws", ""))
    entry.qualities = clean_manuscript_text(field_data.get("Qualities", ""))
    entry.personality_traits = clean_manuscript_text(field_data.get("Personality Traits", ""))
    entry.reputations = clean_manuscript_text(field_data.get("Reputations", ""))
    entry.combat = clean_manuscript_text(field_data.get("Combat", ""))
    entry.soak = field_data.get("Soak", "").strip()
    entry.fatigue_levels = clean_manuscript_text(field_data.get("Fatigue Levels", ""))
    entry.wound_penalties = clean_manuscript_text(field_data.get("Wound Penalties", ""))
    entry.abilities = clean_manuscript_text(field_data.get("Abilities", ""))
    entry.powers = clean_manuscript_text(field_data.get("Powers", ""))
    entry.natural_weapons = clean_manuscript_text(field_data.get("Natural Weapons", ""))
    entry.vis = clean_manuscript_text(field_data.get("Vis", ""))

    appearance = clean_manuscript_text(field_data.get("Appearance", ""))
    if len(appearance) > 1500:
        appearance = appearance[:1500] + "..."
    entry.appearance = appearance

    return entry


# ============================================================
# LORE EXTRACTOR (MANUSCRIPT)
# ============================================================

LORE_SOURCES = {
    "introduction": ("01-Introduction.docx", "Ars Magica -- Introduction", None),
    "order-of-hermes": ("02-Order of Hermes.docx", "The Order of Hermes", None),
    "covenant-life": ("06-Covenants.docx", "Covenant Life", None),
    "realms": ("12-Realms.docx", "The Four Realms -- Magic and the Supernatural", None),
    "bestiary": ("13-Bestiary.docx", "Bestiary -- Introduction", "before_mundane"),
    "mythic-europe": ("14-Mythic Europe.docx", "Mythic Europe -- Setting", None),
    "stories": ("15-Stories.docx", "Stories -- Running the Game", None),
    "sagas": ("16-Sagas.docx", "Stories and Sagas", None),
}


def extract_lore_manuscript(docs_dir: Path) -> dict:
    """Extract lore content from narrative manuscript .docx files.

    Returns dict of key -> (title, content_text).
    """
    lore = {}

    for key, (filename, title, mode) in LORE_SOURCES.items():
        filepath = docs_dir / filename
        if not filepath.exists():
            print(f"  WARNING: Lore source not found: {filepath}")
            continue

        lines = read_manuscript_doc(filepath)

        if mode == "before_mundane":
            # Extract only intro section before "Mundane Beasts"
            end = len(lines)
            for i, line in enumerate(lines):
                if line.strip() == "Mundane Beasts":
                    end = i
                    break
            content = "\n\n".join(l for l in lines[:end] if l.strip())
        else:
            content = "\n\n".join(l for l in lines if l.strip())

        # Limit lore to ~500 paragraphs
        paras = content.split("\n\n")
        if len(paras) > 500:
            content = "\n\n".join(paras[:500])

        content = clean_manuscript_text(content)
        lore[key] = (title, content)

    return lore


# ============================================================
# DSL EMITTERS
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

    # Characteristics
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
        f.write(f'    RELEASE_DATE "2026-03-02"\n')
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
        f.write(f"**Source:** Ars Magica 5th Edition Definitive (Atlas Games, 2024)\n")
        f.write(f"**Release Date:** 2026-03-02\n\n")
        f.write("---\n\n")
        f.write(content)
        f.write("\n")
    return filepath


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def main():
    print("=" * 60)
    print("Ars Magica 5e Definitive — v0.3 DSL Converter (Manuscript)")
    print("=" * 60)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Verify manuscript docs directory
    if not DOCS_DIR.exists():
        print(f"ERROR: Manuscript docs directory not found: {DOCS_DIR}")
        sys.exit(1)
    print(f"\nSource: {DOCS_DIR}")

    # ---- SPELLS ----
    print("\n--- Parsing Spells ---")
    spell_lines = read_manuscript_doc(DOCS_DIR / "09-Spells.docx")
    print(f"  Read {len(spell_lines)} paragraphs from 09-Spells.docx")
    spells = parse_spells_manuscript(spell_lines)
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
            fname = f"arm5e-0.3-spells-{form.lower()}.ttrpg"
            fid = f"ARM5e_Spells_{form}"
            write_ttrpg_extension(
                fname, fid,
                f"Ars Magica 5th Edition Definitive - {form} Spells",
                "ARM5e_Core_Magic", defs
            )
            print(f"  Wrote {fname}: {len(defs)} spells")
            spell_files += 1
            spell_total += len(defs)

    # ---- VIRTUES & FLAWS ----
    print("\n--- Parsing Virtues & Flaws ---")
    vf_lines = read_manuscript_doc(DOCS_DIR / "04-Virtues.docx")
    print(f"  Read {len(vf_lines)} paragraphs from 04-Virtues.docx")
    virtues, flaws = parse_virtues_flaws_manuscript(vf_lines)
    print(f"  Found {len(virtues)} virtues, {len(flaws)} flaws")

    # Group by category
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
        # Virtues
        v_entries = virtue_groups[cat_key]
        if v_entries:
            defs = [emit_virtue_flaw_def(v) for v in v_entries]
            fname = f"arm5e-0.3-virtues-{cat_key}.ttrpg"
            fid = f"ARM5e_Virtues_{cat_name}"
            write_ttrpg_extension(
                fname, fid,
                f"Ars Magica 5th Edition Definitive - {cat_name} Virtues",
                "ARM5e_Core_Character", defs
            )
            print(f"  Wrote {fname}: {len(defs)} virtues")
            vf_files += 1
            vf_total += len(defs)

        # Flaws
        f_entries = flaw_groups[cat_key]
        if f_entries:
            defs = [emit_virtue_flaw_def(f) for f in f_entries]
            fname = f"arm5e-0.3-flaws-{cat_key}.ttrpg"
            fid = f"ARM5e_Flaws_{cat_name}"
            write_ttrpg_extension(
                fname, fid,
                f"Ars Magica 5th Edition Definitive - {cat_name} Flaws",
                "ARM5e_Core_Character", defs
            )
            print(f"  Wrote {fname}: {len(defs)} flaws")
            vf_files += 1
            vf_total += len(defs)

    # ---- ABILITIES ----
    print("\n--- Parsing Abilities ---")
    ab_lines = read_manuscript_doc(DOCS_DIR / "05-Abilities.docx")
    print(f"  Read {len(ab_lines)} paragraphs from 05-Abilities.docx")
    abilities = parse_abilities_manuscript(ab_lines)
    print(f"  Found {len(abilities)} abilities")

    if abilities:
        # Deduplicate: merge entries with the same name
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
        fname = "arm5e-0.3-abilities.ttrpg"
        write_ttrpg_extension(
            fname, "ARM5e_Abilities",
            "Ars Magica 5th Edition Definitive - Abilities",
            "ARM5e_Core_Base", defs
        )
        print(f"  Wrote {fname}: {len(defs)} abilities")

    # ---- CREATURES ----
    print("\n--- Parsing Creatures ---")
    cr_lines = read_manuscript_doc(DOCS_DIR / "13-Bestiary.docx")
    print(f"  Read {len(cr_lines)} paragraphs from 13-Bestiary.docx")
    creatures = parse_creatures_manuscript(cr_lines)
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
            display_name, fid = realm_names.get(realm, (realm.capitalize(), f"ARM5e_Bestiary_{realm.capitalize()}"))
            fname = f"arm5e-0.3-bestiary-{realm}.ttrpg"
            write_ttrpg_extension(
                fname, fid,
                f"Ars Magica 5th Edition Definitive - {display_name} Creatures",
                "ARM5e_Core_Base", defs
            )
            print(f"  Wrote {fname}: {len(defs)} creatures")
            creature_files += 1
            creature_total += len(defs)

    # ---- LORE FILES ----
    print("\n--- Extracting Lore ---")
    lore = extract_lore_manuscript(DOCS_DIR)

    lore_files = 0
    for key, (title, content) in lore.items():
        fname = f"arm5e-0.3-{key}.lore"
        write_lore_file(fname, title, content)
        print(f"  Wrote {fname}")
        lore_files += 1

    # ---- SUMMARY ----
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    print(f"  Source:           {DOCS_DIR}")
    print(f"  Spells:           {spell_total} entries in {spell_files} files")
    print(f"  Virtues & Flaws:  {vf_total} entries in {vf_files} files")
    print(f"  Abilities:        {len(abilities)} entries in 1 file")
    print(f"  Creatures:        {creature_total} entries in {creature_files} files")
    print(f"  Lore files:       {lore_files}")
    print(f"  Base files:       5 (hand-crafted)")
    total_files = spell_files + vf_files + 1 + creature_files + lore_files + 5
    total_defs = spell_total + vf_total + len(abilities) + creature_total
    print(f"  ---")
    print(f"  TOTAL FILES:      {total_files}")
    print(f"  TOTAL DEFs:       {total_defs}")
    print(f"\n  Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
