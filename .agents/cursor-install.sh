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
    
    cat > "$mdc_path" << EOF
---
description: $rule_name rule from .agents/rules/
alwaysApply: false
---

$(cat "$rule_file")
EOF
    echo "  Rule: $rule_name.mdc"
done

# === Subagents: generate thin wrappers for workflow skills ===
rm -rf .cursor/agents
mkdir -p .cursor/agents

for skill_dir in .agents/skills/workflow/*/; do
    [ -d "$skill_dir" ] || continue
    skill_path="${skill_dir}SKILL.md"
    [ -f "$skill_path" ] || continue
    
    skill_name=$(basename "$skill_dir")
    description=$(grep -m1 '^description:' "$skill_path" 2>/dev/null | sed 's/^description:\s*//' || echo "$skill_name workflow skill")
    [ -z "$description" ] && description="$skill_name workflow skill"
    
    agent_path=".cursor/agents/$skill_name.md"
    cat > "$agent_path" << EOF
---
name: $skill_name
description: $description
---

Read and follow the skill at \`.agents/skills/workflow/$skill_name/SKILL.md\`
EOF
    echo "  Subagent: $skill_name"
done

echo "Setup complete. Cursor will discover skills, rules, and subagents from .agents/"
