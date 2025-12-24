#!/usr/bin/env python3
"""
Generate verification report for a story.

Usage: python generate_report.py <story_id> [--json] [--ci]

Output: Human-readable report or JSON (with --json flag)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# Import sibling modules
sys.path.insert(0, os.path.dirname(__file__))
from parse_criteria import get_story_criteria
from find_evidence import find_evidence


def run_tests(test_files: list[str]) -> dict:
    """Run pytest on specified test files and return results."""
    if not test_files:
        return {"ran": False, "reason": "No test files specified"}

    results = {
        "ran": True,
        "passed": [],
        "failed": [],
        "errors": []
    }

    for test_file in test_files[:5]:  # Limit to 5 test files
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', test_file, '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                results["passed"].append(test_file)
            else:
                results["failed"].append({
                    "file": test_file,
                    "output": result.stdout[-500:] if result.stdout else result.stderr[-500:]
                })
        except subprocess.TimeoutExpired:
            results["errors"].append({"file": test_file, "error": "Test timeout"})
        except Exception as e:
            results["errors"].append({"file": test_file, "error": str(e)})

    return results


def classify_criterion(criterion: dict, test_evidence: dict, code_evidence: dict, test_results: dict) -> dict:
    """Classify a single criterion based on evidence."""
    # Already checked in description
    if criterion.get('checked'):
        return {
            "status": "SKIP",
            "reason": "Already marked as complete in description"
        }

    # No code evidence at all
    code_files = code_evidence.get('source_files', [])
    code_funcs = code_evidence.get('functions', [])
    if not code_files and not code_funcs:
        return {
            "status": "FAIL",
            "reason": "No implementation code found"
        }

    # Has code but no tests
    test_files = test_evidence.get('test_files', [])
    test_funcs = test_evidence.get('test_functions', [])
    if not test_files and not test_funcs:
        return {
            "status": "UNTESTABLE",
            "reason": "Implementation exists but no automated tests found",
            "code_locations": [f.get('path') for f in code_files[:3]]
        }

    # Has tests - check results
    if test_results.get('ran'):
        passed = test_results.get('passed', [])
        failed = test_results.get('failed', [])

        if passed and not failed:
            return {
                "status": "PASS",
                "reason": "Tests pass",
                "test_files": passed,
                "code_locations": [f.get('path') for f in code_files[:3]]
            }
        elif passed and failed:
            return {
                "status": "PARTIAL",
                "reason": f"{len(passed)} tests pass, {len(failed)} fail",
                "passed": passed,
                "failed": [f.get('file') for f in failed]
            }
        elif failed:
            return {
                "status": "FAIL",
                "reason": "Tests fail",
                "failed": [f.get('file') for f in failed]
            }

    # Tests exist but weren't run
    return {
        "status": "UNTESTABLE",
        "reason": "Tests exist but results not available",
        "test_files": [f.get('path') for f in test_files[:3]]
    }


def generate_report(story_id: str, run_tests_flag: bool = True, ci_mode: bool = False) -> dict:
    """Generate full verification report for a story."""
    # Get story and criteria
    story_data = get_story_criteria(story_id)
    if 'error' in story_data:
        return story_data

    criteria = story_data.get('criteria', [])
    if not criteria:
        return {
            "story_id": story_id,
            "title": story_data.get('title'),
            "error": "No acceptance criteria found in story description"
        }

    project_path = story_data.get('project_path')

    # Process each criterion
    results = []
    all_test_files = set()

    for criterion in criteria:
        criterion_text = criterion['text']

        # Find evidence
        evidence = find_evidence('all', criterion_text, project_path)
        test_evidence = evidence.get('test_evidence', {})
        code_evidence = evidence.get('code_evidence', {})

        # Collect test files
        for tf in test_evidence.get('test_files', []):
            all_test_files.add(tf.get('path'))

        # Run tests if requested
        test_results = {}
        if run_tests_flag and test_evidence.get('test_files'):
            test_paths = [tf.get('path') for tf in test_evidence.get('test_files', [])]
            test_results = run_tests(test_paths)

        # Classify
        classification = classify_criterion(criterion, test_evidence, code_evidence, test_results)

        results.append({
            "index": criterion['index'],
            "text": criterion_text,
            "checked": criterion['checked'],
            "classification": classification,
            "keywords": evidence.get('keywords', []),
            "evidence_score": evidence.get('evidence_score', 0)
        })

    # Calculate summary
    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r['classification']['status'] == 'PASS'),
        "failed": sum(1 for r in results if r['classification']['status'] == 'FAIL'),
        "partial": sum(1 for r in results if r['classification']['status'] == 'PARTIAL'),
        "untestable": sum(1 for r in results if r['classification']['status'] == 'UNTESTABLE'),
        "skipped": sum(1 for r in results if r['classification']['status'] == 'SKIP')
    }

    # Determine recommendation
    if summary['failed'] > 0:
        recommendation = "NEEDS_WORK"
    elif summary['passed'] + summary['skipped'] == summary['total']:
        recommendation = "READY"
    elif summary['untestable'] > 0:
        recommendation = "MANUAL_REVIEW"
    else:
        recommendation = "REVIEW"

    # Suggested stage transition
    if recommendation == "READY":
        suggested_stage = "ready"
    elif recommendation == "MANUAL_REVIEW":
        suggested_stage = "reviewing"
    else:
        suggested_stage = story_data.get('display_state')  # Keep current

    report = {
        "story_id": story_id,
        "title": story_data.get('title'),
        "current_stage": story_data.get('display_state'),
        "criteria_results": results,
        "summary": summary,
        "recommendation": recommendation,
        "suggested_stage": suggested_stage,
        "failures": [
            f"Criterion {r['index']}: {r['text'][:60]}..."
            for r in results
            if r['classification']['status'] == 'FAIL'
        ]
    }

    return report


def format_text_report(report: dict) -> str:
    """Format report as human-readable text."""
    lines = [
        "STORY VERIFICATION REPORT",
        "=" * 50,
        "",
        f"Story: {report['story_id']} - {report['title']}",
        f"Current Stage: {report['current_stage']}",
        "",
        "ACCEPTANCE CRITERIA RESULTS:",
        ""
    ]

    status_icons = {
        "PASS": "[PASS]",
        "FAIL": "[FAIL]",
        "PARTIAL": "[PART]",
        "UNTESTABLE": "[????]",
        "SKIP": "[SKIP]"
    }

    for result in report.get('criteria_results', []):
        status = result['classification']['status']
        icon = status_icons.get(status, "[????]")
        reason = result['classification'].get('reason', '')

        lines.append(f"{result['index']}. {icon} {result['text'][:60]}")
        if reason:
            lines.append(f"   Reason: {reason}")

        # Show evidence locations for PASS
        if status == 'PASS':
            locs = result['classification'].get('code_locations', [])
            if locs:
                lines.append(f"   Code: {', '.join(locs[:2])}")
            tests = result['classification'].get('test_files', [])
            if tests:
                lines.append(f"   Tests: {', '.join(tests[:2])}")

        lines.append("")

    # Summary
    summary = report.get('summary', {})
    lines.extend([
        "SUMMARY:",
        f"  Passed:     {summary.get('passed', 0)}/{summary.get('total', 0)}",
        f"  Failed:     {summary.get('failed', 0)}/{summary.get('total', 0)}",
        f"  Partial:    {summary.get('partial', 0)}/{summary.get('total', 0)}",
        f"  Untestable: {summary.get('untestable', 0)}/{summary.get('total', 0)}",
        f"  Skipped:    {summary.get('skipped', 0)}/{summary.get('total', 0)}",
        "",
        f"RECOMMENDATION: {report.get('recommendation', 'UNKNOWN')}",
        f"Suggested Stage: {report.get('suggested_stage', 'unchanged')}"
    ])

    if report.get('failures'):
        lines.extend(["", "FAILURES:"])
        for failure in report['failures']:
            lines.append(f"  - {failure}")

    return "\n".join(lines)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <story_id> [--json] [--ci] [--no-tests]")
        sys.exit(1)

    story_id = sys.argv[1]
    json_output = '--json' in sys.argv
    ci_mode = '--ci' in sys.argv
    run_tests_flag = '--no-tests' not in sys.argv

    report = generate_report(story_id, run_tests_flag=run_tests_flag, ci_mode=ci_mode)

    if json_output or ci_mode:
        print(json.dumps(report, indent=2))
    else:
        print(format_text_report(report))
