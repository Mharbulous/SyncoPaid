#!/usr/bin/env python3
"""
Find test and code evidence for acceptance criteria.

Usage:
  python find_evidence.py test "<criterion_text>" [project_path]
  python find_evidence.py code "<criterion_text>" [project_path]
  python find_evidence.py all "<criterion_text>" [project_path]

Output: JSON with found evidence locations
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def extract_keywords(criterion: str) -> list[str]:
    """Extract searchable keywords from criterion text."""
    # Remove common filler words
    stopwords = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
        'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'under', 'again', 'further', 'then', 'once',
        'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
        'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
        'too', 'very', 'just', 'and', 'but', 'or', 'if', 'when', 'where',
        'how', 'what', 'which', 'who', 'whom', 'this', 'that', 'these',
        'those', 'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'she',
        'it', 'its', 'they', 'them', 'their', 'user', 'users', 'able'
    }

    # Extract words
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', criterion.lower())

    # Filter stopwords and short words
    keywords = [w for w in words if w not in stopwords and len(w) > 2]

    # Also extract potential function/variable names (camelCase, snake_case)
    camel_pattern = re.findall(r'\b[a-z]+(?:[A-Z][a-z]+)+\b', criterion)
    snake_pattern = re.findall(r'\b[a-z]+(?:_[a-z]+)+\b', criterion)

    keywords.extend([w.lower() for w in camel_pattern])
    keywords.extend(snake_pattern)

    return list(set(keywords))


def search_tests(keywords: list[str], project_path: str = None) -> dict:
    """Search for test files containing keywords."""
    search_dirs = ['tests', 'test']
    if project_path:
        search_dirs = [os.path.join(project_path, d) for d in search_dirs]

    results = {
        "test_files": [],
        "test_functions": [],
        "assertions": []
    }

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue

        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            content_lower = content.lower()

                            # Check if any keyword matches
                            matching_keywords = [k for k in keywords if k in content_lower]
                            if matching_keywords:
                                results["test_files"].append({
                                    "path": filepath,
                                    "keywords_found": matching_keywords
                                })

                                # Find test function names
                                test_funcs = re.findall(r'def (test_\w+)', content)
                                for func in test_funcs:
                                    if any(k in func.lower() for k in keywords):
                                        results["test_functions"].append({
                                            "file": filepath,
                                            "function": func
                                        })

                                # Find assertions related to keywords
                                for line_num, line in enumerate(content.split('\n'), 1):
                                    if 'assert' in line.lower() and any(k in line.lower() for k in keywords):
                                        results["assertions"].append({
                                            "file": filepath,
                                            "line": line_num,
                                            "content": line.strip()
                                        })
                    except Exception:
                        pass

    return results


def search_code(keywords: list[str], project_path: str = None) -> dict:
    """Search for implementation code containing keywords."""
    search_dirs = ['src', 'lib', '.']
    if project_path:
        search_dirs = [os.path.join(project_path, d) for d in search_dirs]

    results = {
        "source_files": [],
        "functions": [],
        "classes": [],
        "config_refs": []
    }

    exclude_dirs = {'__pycache__', '.git', 'venv', 'node_modules', 'tests', 'test', '.claude'}

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue

        for root, dirs, files in os.walk(search_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if not file.endswith('.py'):
                    continue
                if file.startswith('test_'):
                    continue

                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        content_lower = content.lower()

                        matching_keywords = [k for k in keywords if k in content_lower]
                        if matching_keywords:
                            results["source_files"].append({
                                "path": filepath,
                                "keywords_found": matching_keywords
                            })

                            # Find function definitions
                            func_pattern = r'def (\w+)\s*\([^)]*\):'
                            for match in re.finditer(func_pattern, content):
                                func_name = match.group(1)
                                if any(k in func_name.lower() for k in keywords):
                                    line_num = content[:match.start()].count('\n') + 1
                                    results["functions"].append({
                                        "file": filepath,
                                        "function": func_name,
                                        "line": line_num
                                    })

                            # Find class definitions
                            class_pattern = r'class (\w+)'
                            for match in re.finditer(class_pattern, content):
                                class_name = match.group(1)
                                if any(k in class_name.lower() for k in keywords):
                                    line_num = content[:match.start()].count('\n') + 1
                                    results["classes"].append({
                                        "file": filepath,
                                        "class": class_name,
                                        "line": line_num
                                    })

                            # Find config references
                            if 'config' in filepath.lower() or 'settings' in filepath.lower():
                                results["config_refs"].append({
                                    "path": filepath,
                                    "keywords_found": matching_keywords
                                })

                except Exception:
                    pass

    return results


def find_evidence(evidence_type: str, criterion: str, project_path: str = None) -> dict:
    """Find evidence for a criterion."""
    keywords = extract_keywords(criterion)

    result = {
        "criterion": criterion,
        "keywords": keywords
    }

    if evidence_type in ('test', 'all'):
        result["test_evidence"] = search_tests(keywords, project_path)

    if evidence_type in ('code', 'all'):
        result["code_evidence"] = search_code(keywords, project_path)

    # Calculate evidence score
    score = 0
    if 'test_evidence' in result:
        te = result['test_evidence']
        score += len(te.get('test_files', [])) * 2
        score += len(te.get('test_functions', [])) * 3
        score += len(te.get('assertions', [])) * 1

    if 'code_evidence' in result:
        ce = result['code_evidence']
        score += len(ce.get('source_files', [])) * 1
        score += len(ce.get('functions', [])) * 2
        score += len(ce.get('classes', [])) * 2

    result["evidence_score"] = score
    result["has_evidence"] = score > 0

    return result


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python find_evidence.py <test|code|all> \"<criterion_text>\" [project_path]")
        sys.exit(1)

    evidence_type = sys.argv[1]
    criterion = sys.argv[2]
    project_path = sys.argv[3] if len(sys.argv) > 3 else None

    result = find_evidence(evidence_type, criterion, project_path)
    print(json.dumps(result, indent=2))
