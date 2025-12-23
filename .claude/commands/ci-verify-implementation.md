# Verify Implementation Exists

Verify whether a plan has actually been implemented in the codebase.

**Arguments:**
- `$ARGUMENTS` - Path to the plan file (e.g., `.claude/data/plans/024_feature.md`)

---

## CONTEXT

The database indicates this story is at an advanced stage (reviewing/verifying/implemented),
but the plan document still exists in the plans folder. This could mean:

1. The implementation was completed but the plan wasn't archived (verification should PASS)
2. The database was updated prematurely and implementation doesn't exist (verification should FAIL)

## YOUR TASK

1. Read the plan document at `$ARGUMENTS` completely
2. Identify the TOP 3-5 KEY deliverables (focus on new files and critical functions)
3. Use parallel Glob/Grep calls to quickly verify if they exist
4. Check only the MOST IMPORTANT deliverables - don't exhaustively check everything
5. Write the result file IMMEDIATELY once you have enough evidence

## EFFICIENCY GUIDELINES

- Use Glob to check for file existence in parallel (multiple calls at once)
- Use Grep to quickly verify key functions/classes exist
- Stop searching once you have clear evidence (3-5 checks is usually enough)
- Prioritize: new files > new functions > config changes > minor modifications
- If core files exist with key functions, that's sufficient for PASS

## VERIFICATION CRITERIA

- **PASS**: Core deliverables exist (main files + key functions)
- **PARTIAL**: Some core files exist but key parts are missing
- **FAIL**: Core deliverables are completely missing

## CRITICAL: WRITE OUTPUT EARLY

Write the JSON file AS SOON AS you have enough evidence. Don't wait until you've
checked everything - prioritize writing the result.

## OUTPUT REQUIRED

Write to `.claude/skills/story-execution/ci-verify-result.json`:

```json
{
  "verification_passed": true,
  "status": "pass",
  "deliverables_checked": [
    {"item": "src/syncopaid/feature.py", "found": true, "location": "src/syncopaid/feature.py"},
    {"item": "FeatureClass implementation", "found": true, "location": "src/syncopaid/feature.py:45"},
    {"item": "tests/test_feature.py", "found": true, "location": "tests/test_feature.py"}
  ],
  "summary": "All core deliverables found - implementation complete",
  "recommendation": "archive"
}
```

Where recommendation is:
- **"archive"**: Implementation exists, safe to archive the plan
- **"execute"**: Implementation missing, plan should be executed
- **"manual_review"**: Partial implementation, needs human review

## IMPORTANT

After writing the JSON, print a human-readable summary:

```
## Verification Result: [PASS/PARTIAL/FAIL]

**Plan:** [filename]
**Recommendation:** [archive/execute/manual_review]

### Deliverables Checked
| Item | Found | Location |
|------|-------|----------|
| ... | ✓/✗ | ... |

### Summary
[Brief explanation of findings]
```
