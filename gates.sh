#!/usr/bin/env bash
# Every gate this corpus is measured by, in one run. Exits non-zero if any fails.
#
#   bash gates.sh
#
# There was no such script until 2026-09-21, which is how 583 §5d ambiguity
# errors and 30 vacuous §5c surface forms accumulated unseen. A gate nothing
# runs is a gate that rots.
set -uo pipefail

DSL="${DSL:-$HOME/Sortilege/Titterpig/DSL/titterpig-dsl}"
MASTRA="${MASTRA:-$HOME/Sortilege/Titterpig/Utilities/titterpig-mastra}"
RETARGET="${RETARGET:-$HOME/Sortilege/Titterpig/Temp/arm5e-sourcebook-conversions}"
cd "$(dirname "${BASH_SOURCE[0]}")"

fail=0
run() { echo; echo "--- $1 ---"; shift; "$@" || fail=1; }

for ed in arm5e armdef; do
    run "validator ($ed)"  python3 "$DSL/ttrpg_validator.py" "$ed/0.5/"
    run "references ($ed)" python3 "$DSL/check_references.py" "$ed/0.5/"
    run "constructs ($ed)" python3 "$DSL/check_constructs.py" "$ed/0.5/"
done

# armdef's sourcebooks are regenerated from arm5e; this proves the re-target
# changed only the five structural forms and not one word of either book.
if [ -f "$RETARGET/scripts/verify_armdef.py" ]; then
    run "armdef re-target is byte-faithful" python3 "$RETARGET/scripts/verify_armdef.py"
fi

# Sidebar TEXT, not just titles. The coverage gate below credits a Text Box by its
# NAME, so 81 sidebars whose text never reached the corpus passed it at 100%
# (2026-10-04). This checks every paragraph of every sidebar div, letters and digits,
# each book against its own corpus. arm5e only: armdef is proven a faithful re-target above.
if [ -f "$RETARGET/scripts/sidebars_text_gate.py" ]; then
    run "sidebar text (arm5e core + sourcebooks + Sub Rosa)" python3 "$RETARGET/scripts/sidebars_text_gate.py" "$MASTRA"/coverage/arm5e-*.manifest.json
fi

for m in "$MASTRA"/coverage/arm5e-*.manifest.json "$MASTRA"/coverage/armdef-*.manifest.json; do
    [ -f "$m" ] || continue
    # NOT `... | tail -1`: a pipe reports the PIPE's exit status, so the audit's
    # own non-zero is lost and a failing gate reads as a passing one.
    run "source coverage ($(basename "$m" .manifest.json))" \
        bash -c "cd '$MASTRA' && set -o pipefail && npx tsx scripts/coverageAudit.ts '$m' | tail -1"
done

echo
[ $fail -eq 0 ] && echo "ALL GATES PASS" || echo "GATES FAILED"
exit $fail
