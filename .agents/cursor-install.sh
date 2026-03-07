#!/bin/bash
# Setup script for Linux/macOS - creates symlinks/files for Cursor auto-discovery
# Run from workspace root (where .agents/ lives)
set -e

cd "$(dirname "$0")/.."

mkdir -p .cursor

# === Skills: flat per-skill symlinks in .cursor/skills/ ===
rm -rf .cursor/skills
mkdir -p .cursor/skills

find .agents/skills -name "SKILL.md" -exec dirname {} \; | while read -r skill_dir; do
    skill_name=$(basename "$skill_dir")
    target=".cursor/skills/$skill_name"
    ln -s "../../$skill_dir" "$target"
    echo "  Skill: $skill_name -> $skill_dir"
done

# === Rules: generate .mdc files from .agents/rules/*.md ===
rm -rf .cursor/rules
mkdir -p .cursor/rules

for rule_file in .agents/rules/*.md; do
    [ -f "$rule_file" ] || continue
    rule_name=$(basename "$rule_file" .md)
    mdc_path=".cursor/rules/$rule_name.mdc"

    always_apply="false"
    [ "$rule_name" = "get-docs" ] && always_apply="true"

    cat > "$mdc_path" << EOF
---
description: $rule_name rule from .agents/rules/
alwaysApply: $always_apply
---

$(cat "$rule_file")
EOF
    echo "  Rule: $rule_name.mdc (alwaysApply=$always_apply)"
done

echo "Setup complete. Cursor will discover skills and rules from .agents/"
