import os
import re
import sys
import yaml
import requests
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import namedtuple

Post = namedtuple('Post', ['metadata', 'content'])

ROOT = Path(".")
SKILLS_DIR = ROOT / "skills"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PR_NUMBER = os.getenv("PR_NUMBER")
REPO_NAME = os.getenv("REPO_NAME")

VALID_CATEGORIES = {
    "frontend",
    "backend",
    "architecture",
    "dev-tools",
    "ui-ux",
    "code-quality"
}

VALID_SKILL_TYPES = {
    "workflow",
    "architecture",
    "security",
    "debugging",
    "review",
    "generation",
    "migration"
}

VALID_SECURITY_LEVELS = {
    "safe",
    "review-required",
    "dangerous"
}

VALID_AGENTS = {
    "claude-code",
    "cursor",
    "copilot",
    "codex",
    "gemini"
}

REQUIRED_FIELDS = [
    "name",
    "description",
    "version",
    "category",
    "tags",
    "skill_type",
    "author",
    "license",
    "compatible_agents",
    "estimated_context_tokens",
    "dangerous",
    "requires_review",
    "security_level",
    "dependencies",
    "triggers",
    "permissions",
    "input_requirements",
    "output_contract",
    "failure_conditions",
    "last_updated"
]

REQUIRED_SECTIONS = [
    "## Purpose",
    "## When to use",
    "## When NOT to use",
    "## Inputs required",
    "## Workflow",
    "## Rules",
    "## Anti-patterns",
    "## Failure conditions",
    "## Validation checklist",
    "## Output format",
    "## Security considerations",
    "## Agent execution notes",
    "## Example"
]

API_KEY_PATTERNS = [
    r"ghp_[A-Za-z0-9]{36}",
    r"AIza[0-9A-Za-z\-_]{35}",
    r"sk-[A-Za-z0-9]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
    r"xox[baprs]-[A-Za-z0-9-]+",
]

# Robust security pattern tracking
SUSPICIOUS_PATTERNS = [
    r"curl.+\|.+bash",
    r"wget.+\|.+sh",
    r"curl\s+.*http.*\.sh",       # Catches standalone curl downloads targeting scripts
    r"wget\s+.*http.*\.sh",       # Catches standalone wget downloads targeting scripts
    r"curl\s+.*http.*\.exe",      # Catches downloads targeting executable bin scripts
    r"powershell.+iex",
    r"Invoke-Expression",
    r"base64\s+-d",
    r"sh\s+-c\s+.*http",          # Remote shell command executions
]

OBFUSCATION_PATTERNS = [
    r"[A-Za-z0-9+/]{200,}={0,2}",
    r"marshal\.loads",
    r"zlib\.decompress",
]

REQUIRED_PR_CHECKBOXES = [
    "I have read and accepted the DISCLAIMER and CONTRIBUTING GUIDELINES",
    "I am making chages that are actually useful and that they do not violate the SECURITY GUIDELINES"
]

errors = []
warnings = []


def fail(message):
    errors.append(message)


def warn(message):
    warnings.append(message)


def get_pr_changed_files():
    if not all([GITHUB_TOKEN, PR_NUMBER, REPO_NAME]):
        return []

    url = f"https://api.github.com/repos/{REPO_NAME}/pulls/{PR_NUMBER}/files"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
        
    return [file_item.get("filename") for file_item in response.json()]


def validate_pr_template():
    if not all([GITHUB_TOKEN, PR_NUMBER, REPO_NAME]):
        fail("Missing GitHub environment variables")
        return

    url = f"https://api.github.com/repos/{REPO_NAME}/pulls/{PR_NUMBER}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        fail(f"Failed to fetch PR data: {response.status_code}")
        return

    data = response.json()
    body = data.get("body", "") or ""

    # Fix: Strip all HTML comment blocks before evaluating user input length
    clean_body = re.sub(r"", "", body, flags=re.DOTALL).strip()

    if len(clean_body) < 50:
        fail("PR description content is completely empty or too short. Please fill out the template.")
        return

    # Enforce strict checkbox completion
    for checkbox in REQUIRED_PR_CHECKBOXES:
        cleaned_checkbox = re.escape(checkbox).replace(r"\ ", r"\s+")
        pattern = rf"- \[[xX]\]\s+{cleaned_checkbox}"

        if not re.search(pattern, body, re.IGNORECASE):
            fail(f"Required PR checkbox missing or unchecked: {checkbox}")

    # Section-specific empty verification rules
    pr_sections = {
        "## Summary": r"## Summary\s*(?:\n\s*)?\s*(.*?)(?=\n##|$)",
        "## Type of Change": r"## Type of Change\s*(?:\n\s*)?\s*(.*?)(?=\n##|$)",
        "## What Changed": r"## What Changed\s*(?:\n\s*)?\s*(.*?)(?=\n##|$)"
    }

    for section_name, regex_pattern in pr_sections.items():
        if section_name not in body:
            fail(f"Missing required PR section: {section_name}")
            continue

        match = re.search(regex_pattern, body, re.DOTALL)
        if match:
            section_content = match.group(1).strip()
            # Filter comments out of this section's content
            section_content = re.sub(r"", "", section_content, flags=re.DOTALL).strip()
            
            # Check if user left default unchecked items or completely ignored text blocks
            if not section_content or section_content == "- [ ]" or len(section_content) < 5:
                fail(f"The PR section '{section_name}' has been left blank. Please provide actual details.")


def validate_frontmatter(metadata, path):
    for field in REQUIRED_FIELDS:
        if field not in metadata:
            fail(f"{path}: Missing metadata field '{field}'")

    name = metadata.get("name", "")
    if not re.fullmatch(r"[a-z0-9-]{1,40}", str(name)):
        fail(f"{path}: Invalid kebab-case name")

    version = metadata.get("version", "")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(version)):
        fail(f"{path}: Invalid semver version")

    description = metadata.get("description", "")
    if len(str(description)) > 140:
        fail(f"{path}: Description exceeds 140 characters")

    category = metadata.get("category")
    if category not in VALID_CATEGORIES:
        fail(f"{path}: Invalid category '{category}'")

    skill_type = metadata.get("skill_type")
    if skill_type not in VALID_SKILL_TYPES:
        fail(f"{path}: Invalid skill_type")

    security_level = metadata.get("security_level")
    if security_level not in VALID_SECURITY_LEVELS:
        fail(f"{path}: Invalid security_level")

    compatible_agents = metadata.get("compatible_agents", [])
    for agent in compatible_agents:
        if agent not in VALID_AGENTS:
            fail(f"{path}: Invalid compatible agent '{agent}'")


def validate_sections(content, path):
    last_index = -1
    for section in REQUIRED_SECTIONS:
        index = content.find(section)
        if index == -1:
            fail(f"{path}: Missing required section '{section}'")
            continue
        if index < last_index:
            fail(f"{path}: Section order invalid near '{section}'")
        last_index = index


def scan_api_keys(content, path):
    for pattern in API_KEY_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            fail(f"{path}: Potential API key or secret detected")


def scan_suspicious_commands(content, path):
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            fail(f"{path}: Suspicious connection command string detected")


def scan_obfuscation(content, path):
    for pattern in OBFUSCATION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            fail(f"{path}: Possible obfuscated payload detected")


def detect_duplicates(skill_texts):
    if len(skill_texts) < 2:
        return

    names = list(skill_texts.keys())
    texts = list(skill_texts.values())

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(texts)
    similarity = cosine_similarity(matrix)

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            score = similarity[i][j]
            if score > 0.95:
                fail(f"Duplicate skill detected between '{names[i]}' and '{names[j]}' (similarity {score:.2f})")


def parse_frontmatter(content):
    if not content.startswith('---'):
        raise ValueError("Content does not start with ---")
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError("Invalid frontmatter format")
    
    metadata_str = parts[1]
    content_str = parts[2]
    
    try:
        metadata = yaml.safe_load(metadata_str)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")
    
    if metadata is None:
        metadata = {}
    
    return Post(metadata=metadata, content=content_str)


def validate_skill_file(path):
    raw = path.read_text(encoding="utf-8")

    try:
        post = parse_frontmatter(raw)
    except Exception as e:
        fail(f"{path}: Invalid frontmatter: {e}")
        return None

    validate_frontmatter(post.metadata, path)
    validate_sections(post.content, path)
    scan_api_keys(raw, path)
    scan_suspicious_commands(raw, path)
    scan_obfuscation(raw, path)

    has_anti = "**❌ Anti-pattern:**" in raw or "Anti-pattern" in raw or "### Anti-pattern" in raw
    has_correct = "**✅ Correct pattern:**" in raw or "Correct pattern" in raw or "### Correct pattern" in raw

    if not has_anti:
        fail(f"{path}: Missing anti-pattern example")

    if not has_correct:
        fail(f"{path}: Missing correct-pattern example")

    return post.content


def main():
    validate_pr_template()

    changed_files = get_pr_changed_files()
    skill_texts = {}

    for skill_file in SKILLS_DIR.rglob("SKILL.md"):
        relative_path = str(skill_file)
        is_changed_in_pr = any(relative_path.endswith(f) or f.endswith(relative_path) for f in changed_files)
        
        if is_changed_in_pr or not changed_files:
            content = validate_skill_file(skill_file)
            if content:
                skill_texts[relative_path] = content
        else:
            try:
                raw = skill_file.read_text(encoding="utf-8")
                post = parse_frontmatter(raw)
                skill_texts[relative_path] = post.content
            except Exception:
                pass

    detect_duplicates(skill_texts)

    print("\n================ VALIDATION REPORT ================\n")

    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print("\nValidation failed.")
        sys.exit(1)

    print("All automated checks passed.")
    print("Human review is still REQUIRED before merge.")
    sys.exit(0)


if __name__ == "__main__":
    main()
