#!/bin/bash
set -eo pipefail

TOOL="${QUALBENCH_TOOL:-prollama}"
MODE="${QUALBENCH_MODE:-quality}"
ISSUE="${QUALBENCH_ISSUE:-LOCAL}"
FAIL_ON="${QUALBENCH_FAIL_ON_SCORE:-}"

echo "🧠 QualBench — CI for AI-generated code"
echo "   Tool: $TOOL | Mode: $MODE | Issue: $ISSUE"
echo ""

RESULT=$(qualbench run --tool "$TOOL" --mode "$MODE" --issue "$ISSUE" --json)
SCORE=$(echo "$RESULT" | jq -r '.quality_score' | cut -d. -f1)
VERDICT=$(echo "$RESULT" | jq -r '.verdict')

echo "$RESULT" | jq '.'

echo "quality_score=$SCORE" >> "$GITHUB_OUTPUT"
echo "verdict=$VERDICT" >> "$GITHUB_OUTPUT"

# Multiline JSON output using heredoc syntax
{
  echo "result_json<<QBJSON"
  echo "$RESULT"
  echo "QBJSON"
} >> "$GITHUB_OUTPUT"

if [ -n "$GITHUB_STEP_SUMMARY" ]; then
  CORRECTNESS=$(echo "$RESULT" | jq -r '.dimensions.correctness')
  SECURITY=$(echo "$RESULT" | jq -r '.dimensions.security')
  QUALITY=$(echo "$RESULT" | jq -r '.dimensions.quality')
  ISSUES=$(echo "$RESULT" | jq -r '.top_issues | join(", ")')

  cat >> "$GITHUB_STEP_SUMMARY" << EOF
## 🧠 QualBench Review

**Quality Score: ${SCORE}/100**

| Dimension | Score |
|-----------|-------|
| Correctness | ${CORRECTNESS} |
| Security | ${SECURITY} |
| Quality | ${QUALITY} |

**Verdict:** ${VERDICT}

${ISSUES:+**Issues:** $ISSUES}
EOF
fi

if [ -n "$FAIL_ON" ] && [ "$SCORE" -lt "$FAIL_ON" ]; then
  echo ""
  echo "❌ Quality score $SCORE < threshold $FAIL_ON"
  exit 1
fi
