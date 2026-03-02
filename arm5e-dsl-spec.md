# Ars Magica 5th Edition Definitive - Titterpig DSL Specification v0.3

## Overview

This document defines the ARM5e-specific DSL conventions built on top of the [Titterpig DSL Base Specification v0.3](../titterpig-dsl/titterpig-dsl-spec.md). The base spec defines the system-agnostic grammar (DEF, PROPERTIES, EXTENDS, RULES, etc.); this document defines the **ARM5e vocabulary** — the system-defined keywords, property shapes, and structural patterns used across all ARM5e `.ttrpg` files.

**Design Philosophy:** Ars Magica is a troupe-play game set in Mythic Europe (1220 AD), centered on Hermetic wizards and their covenants. The DSL captures three character tiers (Magus, Companion, Grog) plus Covenants as first-class ACTORs, and models the Hermetic magic system (15 Arts, spell parameters, laboratory activities) as a distinct mechanical subsystem. The DSL showcases what game designers had in mind using actual game terminology. It provides clear traceability for modifications, overrides, and extensions. It is not a game engine implementation but rather a specification for rule relationships and interactions.

## System Architecture

### Base System with Extensions

ARM5e uses a multi-file BASE architecture where the core rulebook is split across five thematic files, with sourcebooks and supplements defined as EXTENSION files that layer additional content on top.

```ttrpg
BASE "ARM5e_Core_Base" {
    NAME "Ars Magica 5th Edition Definitive - Foundation"
    VERSION "0.3"
    RELEASE_DATE "2026-03-02"

    # ACTOR types (Entity, Magus, Companion, Grog, Mythic Companion, Creature, Covenant)
    # Characteristics (8 attributes)
    # Metatype anchors (Virtue, Flaw, Ability, Spell, House, etc.)
    # Dice system (Simple Die, Stress Die, Botch)
    # Core resolution (Ability Roll, Ease Factor)
    # Size, Confidence, Personality Traits, Reputations
    # Scene and time structure (Story, Season, Year)
    # Troupe-style play framework
}

BASE "ARM5e_Core_Character" {
    NAME "Ars Magica 5th Edition Definitive - Character Creation and Advancement"
    VERSION "0.3"
    RELEASE_DATE "2026-03-02"

    # Character creation rules (buying characteristics, virtue/flaw balance)
    # 12 Houses of Hermes with properties and culture
    # Virtue and Flaw metatypes with validation rules
    # Experience and advancement (pyramid XP formula)
    # Aging and Decrepitude
    # Warping system
}

BASE "ARM5e_Core_Magic" {
    NAME "Ars Magica 5th Edition Definitive - Hermetic Magic"
    VERSION "0.3"
    RELEASE_DATE "2026-03-02"

    # 15 Hermetic Arts (5 Techniques + 10 Forms) with descriptions
    # Spell parameter hierarchy (Range/Duration/Target with level costs)
    # Spell guidelines per Technique/Form pair
    # Casting mechanics (Formulaic, Spontaneous, Ritual)
    # Penetration, Magic Resistance, Parma Magica
    # Laboratory activities (invention, enchantment, longevity, familiars)
    # Certamen (wizards' duel)
    # Twilight
}

BASE "ARM5e_Core_Systems" {
    NAME "Ars Magica 5th Edition Definitive - Game Systems"
    VERSION "0.3"
    RELEASE_DATE "2026-03-02"

    # Combat system (initiative, attack/defense totals, damage, wound tables)
    # Fatigue system (short-term and long-term)
    # Wounds and recovery
    # Encumbrance
    # Seasonal activities framework
}

BASE "ARM5e_Core_Covenant" {
    NAME "Ars Magica 5th Edition Definitive - Covenant"
    VERSION "0.3"
    RELEASE_DATE "2026-03-02"

    # Covenant seasons (Spring/Summer/Autumn/Winter lifecycle)
    # Build points
    # Library (Summae, Tractatus, Lab Texts)
    # Vis sources and stockpile
    # Aura mechanics
    # Covenfolk and specialists
}
```

### Extension Architecture

Content files (virtues, flaws, spells, abilities, creatures) extend a specific base file using the `EXTENSION ... EXTENDS` syntax or `DEPENDS_ON` form:

```ttrpg
EXTENSION "ARM5e_Virtues_General" EXTENDS "ARM5e_Core_Character" {
    NAME "Ars Magica 5th Edition Definitive - General Virtues"
    VERSION "0.3"
    RELEASE_DATE "2026-03-02"

    # General, Social Status, Story, and Personality virtues
}

EXTENSION "ARM5e_Spells_Ignem" EXTENDS "ARM5e_Core_Magic" {
    NAME "Ars Magica 5th Edition Definitive - Ignem Spells"
    VERSION "0.3"
    RELEASE_DATE "2026-03-02"

    # All Ignem Form spells (Creo Ignem, Intellego Ignem, etc.)
}

EXTENSION "ARM5e_Bestiary_Mundane" EXTENDS "ARM5e_Core_Base" {
    NAME "Ars Magica 5th Edition Definitive - Mundane Beasts"
    VERSION "0.3"
    RELEASE_DATE "2026-03-02"

    # Mundane animals (no Might score)
}
```

## Core ARM5e ACTORs

### Entity Hierarchy

ARM5e defines a root `Entity` ACTOR from which all other actor types inherit. The `EXTENDS` keyword establishes inheritance, referencing the parent by hash ID and name.

```ttrpg
Entity (root — Name, Description)
├── Magus (EXTENDS Entity — House, The Gift, Hermetic Arts, Parma Magica, Sigil)
├── Companion (EXTENDS Entity — no Gift, broader social freedom)
├── Grog (EXTENDS Entity — simplified, restricted Virtues/Flaws)
├── Mythic Companion (EXTENDS Entity — supernatural but non-Hermetic)
├── Creature (EXTENDS Entity — Might Score, Might Type, Powers, Vis)
└── Covenant (EXTENDS Entity — Season, Aura, Members, Library, Vis Sources)
```

### Entity (Root)

All ACTORs inherit from Entity. Provides Name and Description.

```ttrpg
#ARM5B001aB2cD4eF6gH8iJ0k ACTOR "Entity" DEF {
    PROPERTIES {
        ^"Name" STRING REQUIRED
        ^"Description" STRING
    }
}
```

### Magus

Hermetic wizards — members of the Order of Hermes. The most complex character type with full access to Hermetic magic.

```ttrpg
#ARM5B003xY4zA6bC8dE0fG2hI ACTOR "Magus" DEF {
    EXTENDS #ARM5B001aB2cD4eF6gH8iJ0k ^"Entity"

    PROPERTIES {
        ^"House" STRING REQUIRED
        ^"Characteristics" DEF {
            ^"Intelligence" INTEGER MIN -5 MAX 5 DEFAULT 0
            ^"Perception" INTEGER MIN -5 MAX 5 DEFAULT 0
            ^"Strength" INTEGER MIN -5 MAX 5 DEFAULT 0
            ^"Stamina" INTEGER MIN -5 MAX 5 DEFAULT 0
            ^"Presence" INTEGER MIN -5 MAX 5 DEFAULT 0
            ^"Communication" INTEGER MIN -5 MAX 5 DEFAULT 0
            ^"Dexterity" INTEGER MIN -5 MAX 5 DEFAULT 0
            ^"Quickness" INTEGER MIN -5 MAX 5 DEFAULT 0
        }
        ^"Hermetic Arts" DEF {
            # Techniques
            ^"Creo" INTEGER MIN 0 DEFAULT 0
            ^"Intellego" INTEGER MIN 0 DEFAULT 0
            ^"Muto" INTEGER MIN 0 DEFAULT 0
            ^"Perdo" INTEGER MIN 0 DEFAULT 0
            ^"Rego" INTEGER MIN 0 DEFAULT 0
            # Forms
            ^"Animal" INTEGER MIN 0 DEFAULT 0
            ^"Aquam" INTEGER MIN 0 DEFAULT 0
            ^"Auram" INTEGER MIN 0 DEFAULT 0
            ^"Corpus" INTEGER MIN 0 DEFAULT 0
            ^"Herbam" INTEGER MIN 0 DEFAULT 0
            ^"Ignem" INTEGER MIN 0 DEFAULT 0
            ^"Imaginem" INTEGER MIN 0 DEFAULT 0
            ^"Mentem" INTEGER MIN 0 DEFAULT 0
            ^"Terram" INTEGER MIN 0 DEFAULT 0
            ^"Vim" INTEGER MIN 0 DEFAULT 0
        }
        ^"Size" INTEGER DEFAULT 0
        ^"Age" INTEGER MIN 0
        ^"Apparent Age" INTEGER MIN 0
        ^"Decrepitude" INTEGER MIN 0 DEFAULT 0
        ^"Warping Score" INTEGER MIN 0 DEFAULT 0
        ^"Confidence Score" INTEGER MIN 0 DEFAULT 1
        ^"Confidence Points" INTEGER MIN 0 DEFAULT 3
        ^"Parma Magica Score" INTEGER MIN 0 DEFAULT 0
        ^"Sigil" STRING
        ^"Voting Sigil" STRING
        ^"Abilities" LIST OF ^"Ability"
        ^"Virtues" LIST OF ^"Virtue"
        ^"Flaws" LIST OF ^"Flaw"
        ^"Spells" LIST OF ^"Spell"
        ^"Personality Traits" LIST OF ^"Personality Trait"
        ^"Reputations" LIST OF ^"Reputation"
        ^"Equipment" LIST OF STRING
    }
}
```

### Companion

Important non-magus characters. Each player has one companion in addition to their magus. Companions can be knights, friars, nobles, hedge wizards, or other significant individuals. Companions generally do not have The Gift.

### Grog

Minor characters: warriors, servants, specialists. Shared between players. Simplified creation: no Major Virtues or Flaws, no more than 3 Minor Flaws, no Story Flaws, cannot have The Gift.

### Mythic Companion

Extra-powerful non-magus characters comparable to magi in power level. Includes non-Hermetic wizards, holy hermits, supernaturally strong warriors. Played as an alternative to a magus character, not in addition to one.

### Creature

Supernatural beings with Might scores: magical beasts, faeries, demons, angels. Realm alignment determines which realm powers the creature. Creatures use Cunning instead of Intelligence when they lack human-level reasoning.

```ttrpg
#ARM5B018iJ9kL1mN3oP5qR7sT ACTOR "Creature" DEF {
    EXTENDS #ARM5B001aB2cD4eF6gH8iJ0k ^"Entity"

    PROPERTIES {
        ^"Might" INTEGER MIN 0
        ^"Might Type" ENUM ["Magic", "Faerie", "Infernal", "Divine"]
        ^"Characteristics" DEF {
            ^"Intelligence" INTEGER MIN -10 MAX 10 DEFAULT 0
            ^"Perception" INTEGER MIN -10 MAX 10 DEFAULT 0
            ^"Strength" INTEGER MIN -10 MAX 10 DEFAULT 0
            ^"Stamina" INTEGER MIN -10 MAX 10 DEFAULT 0
            ^"Presence" INTEGER MIN -10 MAX 10 DEFAULT 0
            ^"Communication" INTEGER MIN -10 MAX 10 DEFAULT 0
            ^"Dexterity" INTEGER MIN -10 MAX 10 DEFAULT 0
            ^"Quickness" INTEGER MIN -10 MAX 10 DEFAULT 0
        }
        ^"Size" INTEGER
        ^"Abilities" LIST OF ^"Ability"
        ^"Powers" LIST OF ^"Power"
        ^"Vis" STRING
        ^"Virtues" LIST OF ^"Virtue"
        ^"Flaws" LIST OF ^"Flaw"
        ^"Personality Traits" LIST OF ^"Personality Trait"
        ^"Combat" DEF {
            ^"Weapons" LIST OF ^"Weapon Attack"
        }
    }
}
```

### Covenant

The shared home of a group of magi. Covenants are quasi-characters with their own resources, seasons, and development.

```ttrpg
#ARM5B022eF3gH5iJ7kL9mN1oP ACTOR "Covenant" DEF {
    EXTENDS #ARM5B001aB2cD4eF6gH8iJ0k ^"Entity"

    PROPERTIES {
        ^"Season" ENUM ["Spring", "Summer", "Autumn", "Winter"]
        ^"Aura" INTEGER MIN 0 MAX 10
        ^"Aura Type" ENUM ["Magic", "Faerie", "Infernal", "Divine"]
        ^"Members" LIST OF ^"Magus" REQUIRED
        ^"Companions" LIST OF ^"Companion"
        ^"Grogs" LIST OF ^"Grog"
        ^"Library" LIST OF ^"Book"
        ^"Laboratories" LIST OF ^"Laboratory"
        ^"Vis Sources" LIST OF ^"Vis Source"
        ^"Income" INTEGER
        ^"Build Points" INTEGER MIN 0
    }
}
```

## Key Properties & Patterns

### Characteristics

All character ACTORs share the same 8 Characteristics, defined as a nested DEF. Human characters range -5 to +5; creatures may exceed these bounds.

| Characteristic | Abbreviation | Covers |
|---|---|---|
| Intelligence | Int | Reasoning, memory, learning |
| Perception | Per | Noticing, sensing, awareness |
| Strength | Str | Physical power, lifting, damage |
| Stamina | Sta | Endurance, resistance, soak |
| Presence | Pre | Force of personality, leadership |
| Communication | Com | Expression, persuasion, teaching |
| Dexterity | Dex | Manual agility, crafting, aiming |
| Quickness | Qik | Reaction speed, initiative |

Creatures with animal-level intelligence use **Cunning** (Cun) instead of Intelligence.

### Hermetic Arts

Defined as a nested DEF on Magus. 5 Techniques (verbs) + 10 Forms (nouns), each `INTEGER MIN 0 DEFAULT 0`. Every spell combines one Technique with one Form.

**Techniques:** Creo (Cr), Intellego (In), Muto (Mu), Perdo (Pe), Rego (Re)
**Forms:** Animal (An), Aquam (Aq), Auram (Au), Corpus (Co), Herbam (He), Ignem (Ig), Imaginem (Im), Mentem (Me), Terram (Te), Vim (Vi)

### Virtue DEF Pattern

```ttrpg
#ARM5VGnnn ^"Virtue Name" DEF {
    APPLIES TO [^"Entity"]
    PROPERTIES {
        ^"Type" ENUM ["Virtue"]
        ^"Size" ENUM ["Major", "Minor", "Free"]
        ^"Category" ENUM ["General", "Hermetic", "Supernatural", "Social Status", "Story", "Personality", "Tainted"]
        ^"Repeatable" BOOLEAN false
    }
    DESCRIPTION """..."""
    RULES {
        #HASHnnn: mechanical_effect_description
    }
}
```

### Flaw DEF Pattern

```ttrpg
#ARM5FGnnn ^"Flaw Name" DEF {
    APPLIES TO [^"Entity"]
    PROPERTIES {
        ^"Type" ENUM ["Flaw"]
        ^"Size" ENUM ["Major", "Minor", "Free"]
        ^"Category" ENUM ["General", "Hermetic", "Supernatural", "Social Status", "Story", "Personality", "Tainted"]
        ^"Repeatable" BOOLEAN false
    }
    DESCRIPTION """..."""
    RULES {
        #HASHnnn: mechanical_effect_description
    }
}
```

### Spell DEF Pattern

```ttrpg
#ARM5SPnnn ^"Spell Name" DEF {
    APPLIES TO [^"Magus"]
    PROPERTIES {
        ^"Technique" ENUM ["Creo", "Intellego", "Muto", "Perdo", "Rego"]
        ^"Form" ENUM ["Animal", "Aquam", "Auram", "Corpus", "Herbam", "Ignem", "Imaginem", "Mentem", "Terram", "Vim"]
        ^"Level" INTEGER
        ^"Range" ENUM ["Personal", "Touch", "Eye", "Voice", "Sight", "Arcane Connection"]
        ^"Duration" ENUM ["Momentary", "Concentration", "Diameter", "Sun", "Ring", "Moon", "Year"]
        ^"Target" ENUM ["Individual", "Part", "Group", "Room", "Structure", "Boundary", "Circle", "Bloodline", "Taste", "Hearing", "Smell", "Touch", "Vision"]
        ^"Ritual" BOOLEAN false
        ^"Requisite" STRING ""
        ^"Design" STRING ""
    }
    DESCRIPTION """..."""
}
```

### Ability DEF Pattern

```ttrpg
#ARM5ABnnn ^"Ability Name" DEF {
    APPLIES TO [^"Entity"]
    PROPERTIES {
        ^"Ability Type" ENUM ["General", "Academic", "Arcane", "Martial", "Supernatural"]
        ^"Requires Gift" BOOLEAN false
        ^"Specialties" LIST OF STRING [...]
    }
    DESCRIPTION """..."""
}
```

### Creature DEF Pattern

```ttrpg
#ARM5CRnnn ^"Creature Name" DEF {
    EXTENDS ^"Creature"
    PROPERTIES {
        ^"Might" INTEGER
        ^"Might Type" ENUM ["Magic", "Faerie", "Infernal", "Divine"]
        ^"Form" STRING ""
        ^"Size" INTEGER 0
        ^"Characteristics" DEF {
            ^"Cunning" INTEGER DEFAULT 0
            ^"Perception" INTEGER DEFAULT 0
            ^"Strength" INTEGER DEFAULT 0
            ^"Stamina" INTEGER DEFAULT 0
            ^"Presence" INTEGER DEFAULT 0
            ^"Communication" INTEGER DEFAULT 0
            ^"Dexterity" INTEGER DEFAULT 0
            ^"Quickness" INTEGER DEFAULT 0
        }
        ^"Virtues" LIST OF STRING [...]
        ^"Flaws" LIST OF STRING [...]
        ^"Personality Traits" LIST OF STRING [...]
        ^"Abilities" LIST OF STRING [...]
        ^"Powers" LIST OF STRING [...]
        ^"Combat" DEF {
            ^"Weapons" LIST OF STRING [...]
            ^"Soak" INTEGER
        }
        ^"Fatigue Levels" STRING ""
        ^"Wound Penalties" STRING ""
        ^"Vis" STRING ""
        ^"Appearance" STRING ""
    }
    DESCRIPTION """..."""
}
```

### House DEF Pattern

```ttrpg
#ARM5Cnnn ^"House Name" DEF {
    APPLIES TO [^"Magus"]
    PROPERTIES {
        ^"Founder" STRING
        ^"Domus Magna" STRING
        ^"Primus" STRING
        ^"Focus" STRING
        ^"Free House Virtue" STRING ""
    }
    DESCRIPTION """..."""
}
```

## System-Defined Keywords (ARM5e Vocabulary)

These keywords are **not** reserved by the base DSL spec. They are system-specific vocabulary defined by the ARM5e conversion for use in RULES blocks and specialized sub-blocks.

| Keyword | Domain | Purpose |
|---|---|---|
| `HERMETIC_ARTS` | Magic | Sub-block defining Technique + Form scores on Magus |
| `CASTING_TOTAL` | Magic | Formula: Technique + Form + Stamina + Aura + die |
| `PENETRATION` | Magic | Formula: Casting Total − Spell Level + Penetration Bonus |
| `SPELL_PARAMETERS` | Magic | Range, Duration, Target hierarchy with level modifiers |
| `SPELL_GUIDELINES` | Magic | Base effect levels per Technique/Form pair |
| `ADVANCEMENT_COSTS` | Character | Pyramid XP formula: (New Score × (New Score + 1)) / 2 |
| `LABORATORY` | Magic | Sub-block for lab activities (invent, enchant, longevity, familiar) |
| `FORMULA` | Core | Mathematical resolution expression |
| `DIFFICULTY_SCALE` | Core | Maps Ease Factors to difficulty descriptions |
| `FORM_BONUS` | Magic | Defense formula: Form Score / 5 rounded up |
| `MASTERY_OPTIONS` | Magic | Spell mastery special abilities |
| `WARPING` | Character | Long-term supernatural exposure mechanic |
| `CONFIDENCE` | Core | Spend-to-boost system (+3 per point to a roll) |
| `COVENANT_RESOURCES` | Covenant | Library, vis, specialists sub-blocks |
| `BOTCH_SEVERITY` | Core | Escalating severity scale for botched stress dice |
| `REPUTATION_EASE_FACTORS` | Core | Recognition roll difficulty by scope |
| `DESCRIPTION` | All | Multi-line narrative text block |

## Hash ID Convention

Hash IDs use a system-specific prefix to indicate file scope, followed by a 3-digit sequence number and alphanumeric padding to fill 24 characters total (including the `#` prefix).

| Prefix | Scope | Used In |
|---|---|---|
| `#ARM5B` | Core Base | ACTOR types, metatypes, dice, resolution |
| `#ARM5C` | Core Character | Character creation, houses, advancement, aging |
| `#ARM5M` | Core Magic | Hermetic Arts, spell parameters, casting, lab |
| `#ARM5S` | Core Systems | Combat, fatigue, wounds, recovery |
| `#ARM5V` | Core Covenant | Covenant mechanics, library, vis |
| `#ARM5VG` | Virtues — General | General, Social Status, Story, Personality virtues |
| `#ARM5VH` | Virtues — Hermetic | Hermetic-only virtues |
| `#ARM5VS` | Virtues — Supernatural | Supernatural virtues |
| `#ARM5FG` | Flaws — General | General, Social Status, Story, Personality flaws |
| `#ARM5FH` | Flaws — Hermetic | Hermetic-only flaws |
| `#ARM5FS` | Flaws — Supernatural | Supernatural flaws |
| `#ARM5SP` | Spells | Per-Form spell files |
| `#ARM5CR` | Creatures | Per-realm bestiary files |
| `#ARM5AB` | Abilities | All ability definitions |

### Hash ID Format

```
#ARM5B001aB2cD4eF6gH8iJ0k
 ╰──╯╰─╯╰───────────────╯
  │    │         │
  │    │         └── Alphanumeric padding (fills to 24 chars)
  │    └── 3-digit sequence (001, 002, ...)
  └── Prefix (scope indicator)
```

## Extension Patterns

### File Organization

Extension files group related content and extend the appropriate base file:

| Extension File | Extends | Content |
|---|---|---|
| `arm5e-0.3-virtues-general.ttrpg` | ARM5e_Core_Character | General, Social Status, Story, Personality virtues |
| `arm5e-0.3-virtues-hermetic.ttrpg` | ARM5e_Core_Character | Hermetic virtues |
| `arm5e-0.3-virtues-supernatural.ttrpg` | ARM5e_Core_Character | Supernatural virtues |
| `arm5e-0.3-flaws-general.ttrpg` | ARM5e_Core_Character | General, Social Status, Story, Personality flaws |
| `arm5e-0.3-flaws-hermetic.ttrpg` | ARM5e_Core_Character | Hermetic flaws |
| `arm5e-0.3-flaws-supernatural.ttrpg` | ARM5e_Core_Character | Supernatural flaws |
| `arm5e-0.3-abilities.ttrpg` | ARM5e_Core_Base | All abilities |
| `arm5e-0.3-spells-[form].ttrpg` | ARM5e_Core_Magic | Spells organized by Form (10 files) |
| `arm5e-0.3-bestiary-mundane.ttrpg` | ARM5e_Core_Base | Mundane animals |
| `arm5e-0.3-bestiary-magical.ttrpg` | ARM5e_Core_Base | Magic realm creatures |
| `arm5e-0.3-bestiary-faerie.ttrpg` | ARM5e_Core_Base | Faerie realm creatures |
| `arm5e-0.3-bestiary-divine.ttrpg` | ARM5e_Core_Base | Divine realm creatures |
| `arm5e-0.3-bestiary-infernal.ttrpg` | ARM5e_Core_Base | Infernal realm creatures |

### Section Separators

Within extension files, content is organized using section separator comments:

```ttrpg
    # ===========================
    # SECTION HEADING
    # ===========================
```

### Lore Files

Lore files (`.lore`) contain narrative content in markdown format with a simple header:

```
# Title

**Version:** 0.3
**Source:** Ars Magica 5th Edition Definitive (Atlas Games, 2024)
**Release Date:** 2026-03-02

---

## Section Heading

Narrative content here...
```

Lore files cover setting material, house histories, realm descriptions, and other non-mechanical content.

## Differences from v0.1

The v0.3 conversion improves on v0.1 in several key areas:

1. **DESCRIPTION blocks** replace v0.1's RULES-as-narrative-text pattern — v0.3 uses DESCRIPTION for prose and RULES only for mechanical constraints
2. **Proper hash ID prefixes** per file type (see Hash ID Convention above)
3. **Typed spell parameters** with ENUM constraints (not free-text strings)
4. **Creature properties** fully typed (nested Characteristics DEF, typed Powers, etc.)
5. **Multi-BASE architecture** with proper DEPENDS_ON chains across 5 base files
6. **Consistent APPLIES TO** scoping on all content DEFs
7. **Five base files** instead of two, providing cleaner separation of concerns
