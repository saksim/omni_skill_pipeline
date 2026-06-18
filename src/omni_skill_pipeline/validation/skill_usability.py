from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from omni_skill_pipeline.redaction import is_sensitive_key

REQUIRED_SECTIONS = (
    'Workflow',
    'Decision Rules',
    'Validation',
    'Failure Modes',
)
DEFAULT_MAX_SKILL_LINES = 500
DEFAULT_MIN_DESCRIPTION_WORDS = 8
DEFAULT_MAX_DESCRIPTION_WORDS = 80
TOKEN_LIKE_SECRET_PATTERN = re.compile(r'(?i)\b(?:sk|rk|pk|ghp|glpat|xoxb|xoxp|pat)-[A-Za-z0-9_\-]{8,}\b')
LONG_TOKEN_PATTERN = re.compile(r'\b[A-Za-z0-9_\-]{24,}\b')
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r'(?i)\b[A-Z]:\\[^\s"\']+')
POSIX_ABSOLUTE_PATH_PATTERN = re.compile(r'(?<!\w)/(?:Users|home|root|etc|var|opt|srv|tmp|private|mnt)/[^\s"\']+')

FAILURE_CODE_MISSING_FRONTMATTER = 'MISSING_FRONTMATTER'
FAILURE_CODE_INVALID_FRONTMATTER = 'INVALID_FRONTMATTER'
FAILURE_CODE_MISSING_FRONTMATTER_NAME = 'MISSING_FRONTMATTER_NAME'
FAILURE_CODE_MISSING_FRONTMATTER_DESCRIPTION = 'MISSING_FRONTMATTER_DESCRIPTION'
FAILURE_CODE_WEAK_DESCRIPTION = 'WEAK_DESCRIPTION'
FAILURE_CODE_DESCRIPTION_TOO_LONG = 'DESCRIPTION_TOO_LONG'
FAILURE_CODE_MISSING_SECTION = 'MISSING_SECTION'
FAILURE_CODE_MAX_LENGTH_EXCEEDED = 'MAX_LENGTH_EXCEEDED'
FAILURE_CODE_MISSING_REFERENCES_DIR = 'MISSING_REFERENCES_DIR'
FAILURE_CODE_EMPTY_REFERENCES_DIR = 'EMPTY_REFERENCES_DIR'
FAILURE_CODE_ABSOLUTE_PATH_LEAK = 'ABSOLUTE_PATH_LEAK'
FAILURE_CODE_SECRET_TOKEN_LEAK = 'SECRET_TOKEN_LEAK'
FAILURE_CODE_DANGEROUS_COMMAND_MARKER = 'DANGEROUS_COMMAND_MARKER'
FAILURE_CODE_REVIEW_APPROVAL_MISSING = 'REVIEW_APPROVAL_MISSING'
FAILURE_CODE_PACKAGE_METADATA_MISSING = 'PACKAGE_METADATA_MISSING'

_DANGEROUS_COMMAND_MARKERS = (
    'rm -rf /',
    'sudo rm -rf',
    'terraform destroy',
    'kubectl delete namespace',
    'drop database',
    'drop table',
    'truncate table',
    'shutdown -h',
    'reboot',
    'mkfs.',
    'dd if=',
)
_DESCRIPTION_TRIGGER_HINTS = (
    'use when',
    'when the user asks',
    'trigger',
    'only for',
)


@dataclass(frozen=True, slots=True)
class SkillUsabilityIssue:
    code: str
    message: str
    severity: str = 'error'

    def to_dict(self) -> dict[str, str]:
        return {
            'code': self.code,
            'message': self.message,
            'severity': self.severity,
        }


@dataclass(frozen=True, slots=True)
class SkillUsabilityReport:
    status: str
    package_path: str
    skill_path: str
    references_path: str
    max_lines: int
    actual_line_count: int
    issues: list[SkillUsabilityIssue] = field(default_factory=list)

    @property
    def failure_codes(self) -> list[str]:
        return [item.code for item in self.issues]

    def to_dict(self) -> dict[str, Any]:
        return {
            'status': self.status,
            'package_path': self.package_path,
            'skill_path': self.skill_path,
            'references_path': self.references_path,
            'max_lines': self.max_lines,
            'actual_line_count': self.actual_line_count,
            'failure_code_count': len(self.failure_codes),
            'failure_codes': self.failure_codes,
            'issues': [item.to_dict() for item in self.issues],
        }


def validate_skill_package(
    *,
    package_path: Path,
    max_lines: int = DEFAULT_MAX_SKILL_LINES,
    min_description_words: int = DEFAULT_MIN_DESCRIPTION_WORDS,
    max_description_words: int = DEFAULT_MAX_DESCRIPTION_WORDS,
) -> SkillUsabilityReport:
    package_root = Path(package_path).resolve()
    skill_path = package_root / 'SKILL.md'
    references_path = package_root / 'references'
    package_metadata_path = package_root / 'agent_skill_package.json'

    issues: list[SkillUsabilityIssue] = []
    markdown = ''
    if not package_metadata_path.is_file():
        issues.append(
            SkillUsabilityIssue(
                code=FAILURE_CODE_PACKAGE_METADATA_MISSING,
                message='Missing agent_skill_package.json in package root.',
            )
        )
    if not skill_path.is_file():
        issues.append(
            SkillUsabilityIssue(
                code=FAILURE_CODE_MISSING_FRONTMATTER,
                message='Missing SKILL.md in package root.',
            )
        )
        return SkillUsabilityReport(
            status='fail',
            package_path=str(package_root),
            skill_path=str(skill_path),
            references_path=str(references_path),
            max_lines=int(max_lines),
            actual_line_count=0,
            issues=issues,
        )

    markdown = skill_path.read_text(encoding='utf-8')
    line_count = len(markdown.splitlines())
    if line_count > int(max_lines):
        issues.append(
            SkillUsabilityIssue(
                code=FAILURE_CODE_MAX_LENGTH_EXCEEDED,
                message='SKILL.md line count %s exceeds max_lines=%s.' % (line_count, int(max_lines)),
            )
        )

    frontmatter, frontmatter_error = _parse_frontmatter(markdown)
    if frontmatter_error:
        issues.append(frontmatter_error)
    else:
        name = str(frontmatter.get('name', '')).strip()
        if not name:
            issues.append(
                SkillUsabilityIssue(
                    code=FAILURE_CODE_MISSING_FRONTMATTER_NAME,
                    message='Frontmatter must include non-empty "name".',
                )
            )
        description = str(frontmatter.get('description', '')).strip()
        if not description:
            issues.append(
                SkillUsabilityIssue(
                    code=FAILURE_CODE_MISSING_FRONTMATTER_DESCRIPTION,
                    message='Frontmatter must include non-empty "description".',
                )
            )
        else:
            issues.extend(
                _validate_description(
                    description=description,
                    min_description_words=int(min_description_words),
                    max_description_words=int(max_description_words),
                )
            )

    for section in REQUIRED_SECTIONS:
        if ('## %s' % section) not in markdown:
            issues.append(
                SkillUsabilityIssue(
                    code=FAILURE_CODE_MISSING_SECTION,
                    message='Missing required section: %s.' % section,
                )
            )

    if not references_path.is_dir():
        issues.append(
            SkillUsabilityIssue(
                code=FAILURE_CODE_MISSING_REFERENCES_DIR,
                message='Missing references/ directory.',
            )
        )
    elif not any(path.is_file() for path in references_path.rglob('*')):
        issues.append(
            SkillUsabilityIssue(
                code=FAILURE_CODE_EMPTY_REFERENCES_DIR,
                message='references/ directory is empty.',
            )
        )

    issues.extend(_detect_absolute_path_leak(markdown))
    issues.extend(_detect_secret_leak(markdown))
    issues.extend(_detect_dangerous_command_markers(markdown))
    issues.extend(_validate_review_approval(markdown=markdown, package_metadata_path=package_metadata_path))

    status = 'pass' if not issues else 'fail'
    return SkillUsabilityReport(
        status=status,
        package_path=str(package_root),
        skill_path=str(skill_path),
        references_path=str(references_path),
        max_lines=int(max_lines),
        actual_line_count=line_count,
        issues=issues,
    )


def _parse_frontmatter(markdown: str) -> tuple[dict[str, str], SkillUsabilityIssue | None]:
    lines = markdown.splitlines()
    if len(lines) < 3 or lines[0].strip() != '---':
        return {}, SkillUsabilityIssue(
            code=FAILURE_CODE_MISSING_FRONTMATTER,
            message='SKILL.md must start with YAML frontmatter delimited by "---".',
        )

    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == '---':
            closing_index = index
            break
    if closing_index is None:
        return {}, SkillUsabilityIssue(
            code=FAILURE_CODE_INVALID_FRONTMATTER,
            message='SKILL.md frontmatter is missing closing "---".',
        )

    payload: dict[str, str] = {}
    for raw_line in lines[1:closing_index]:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if ':' not in stripped:
            return {}, SkillUsabilityIssue(
                code=FAILURE_CODE_INVALID_FRONTMATTER,
                message='Invalid frontmatter line: %s.' % raw_line.strip(),
            )
        key, value = stripped.split(':', 1)
        key_text = str(key).strip().lower()
        if not key_text:
            return {}, SkillUsabilityIssue(
                code=FAILURE_CODE_INVALID_FRONTMATTER,
                message='Frontmatter contains empty key.',
            )
        value_text = str(value).strip().strip('"').strip("'")
        payload[key_text] = value_text
    return payload, None


def _validate_description(
    *,
    description: str,
    min_description_words: int,
    max_description_words: int,
) -> list[SkillUsabilityIssue]:
    issues: list[SkillUsabilityIssue] = []
    words = [item for item in str(description).replace('\n', ' ').split(' ') if item.strip()]
    if len(words) < min_description_words:
        issues.append(
            SkillUsabilityIssue(
                code=FAILURE_CODE_WEAK_DESCRIPTION,
                message='Description must have at least %s words.' % min_description_words,
            )
        )
    if len(words) > max_description_words:
        issues.append(
            SkillUsabilityIssue(
                code=FAILURE_CODE_DESCRIPTION_TOO_LONG,
                message='Description exceeds max words (%s > %s).' % (len(words), max_description_words),
            )
        )
    lowered = str(description).strip().lower()
    if not any(marker in lowered for marker in _DESCRIPTION_TRIGGER_HINTS):
        issues.append(
            SkillUsabilityIssue(
                code=FAILURE_CODE_WEAK_DESCRIPTION,
                message='Description should include explicit trigger wording (for example "Use when ...").',
            )
        )
    return issues


def _detect_absolute_path_leak(markdown: str) -> list[SkillUsabilityIssue]:
    issues: list[SkillUsabilityIssue] = []
    windows_match = WINDOWS_ABSOLUTE_PATH_PATTERN.search(markdown)
    if windows_match:
        issues.append(
            SkillUsabilityIssue(
                code=FAILURE_CODE_ABSOLUTE_PATH_LEAK,
                message='Detected Windows absolute path leak: %s' % windows_match.group(0),
            )
        )
    posix_match = POSIX_ABSOLUTE_PATH_PATTERN.search(markdown)
    if posix_match:
        issues.append(
            SkillUsabilityIssue(
                code=FAILURE_CODE_ABSOLUTE_PATH_LEAK,
                message='Detected POSIX absolute path leak: %s' % posix_match.group(0),
            )
        )
    return issues


def _detect_secret_leak(markdown: str) -> list[SkillUsabilityIssue]:
    issues: list[SkillUsabilityIssue] = []
    direct = TOKEN_LIKE_SECRET_PATTERN.search(markdown)
    if direct:
        issues.append(
            SkillUsabilityIssue(
                code=FAILURE_CODE_SECRET_TOKEN_LEAK,
                message='Detected token-like secret marker: %s' % direct.group(0),
            )
        )
        return issues

    for line in markdown.splitlines():
        lowered = line.strip().lower()
        if not lowered:
            continue
        if ':' not in line and '=' not in line:
            continue
        chunks = re.split(r'[:=]', line, maxsplit=1)
        if len(chunks) != 2:
            continue
        key = chunks[0].strip()
        value = chunks[1].strip().strip('"').strip("'")
        if not key or not value:
            continue
        if is_sensitive_key(key) and value not in {'[REDACTED]', '***', '<redacted>'}:
            issues.append(
                SkillUsabilityIssue(
                    code=FAILURE_CODE_SECRET_TOKEN_LEAK,
                    message='Detected sensitive key/value pair leak for key: %s' % key,
                )
            )
            break
        if 'bearer ' in lowered and '[redacted]' not in lowered:
            issues.append(
                SkillUsabilityIssue(
                    code=FAILURE_CODE_SECRET_TOKEN_LEAK,
                    message='Detected unredacted Bearer token pattern.',
                )
            )
            break
        long_token = LONG_TOKEN_PATTERN.search(value)
        if long_token and any(marker in key.lower() for marker in ('token', 'secret', 'key', 'password')):
            issues.append(
                SkillUsabilityIssue(
                    code=FAILURE_CODE_SECRET_TOKEN_LEAK,
                    message='Detected long token value for sensitive key: %s' % key,
                )
            )
            break
    return issues


def _detect_dangerous_command_markers(markdown: str) -> list[SkillUsabilityIssue]:
    lowered = markdown.lower()
    for marker in _DANGEROUS_COMMAND_MARKERS:
        if marker in lowered:
            return [
                SkillUsabilityIssue(
                    code=FAILURE_CODE_DANGEROUS_COMMAND_MARKER,
                    message='Detected dangerous command marker: %s' % marker,
                )
            ]
    return []


def _validate_review_approval(*, markdown: str, package_metadata_path: Path) -> list[SkillUsabilityIssue]:
    issues: list[SkillUsabilityIssue] = []
    status = ''
    try:
        import json

        payload = json.loads(package_metadata_path.read_text(encoding='utf-8'))
        status = str(payload.get('review_status', '')).strip().lower() if isinstance(payload, dict) else ''
    except Exception:
        status = ''

    if status == 'published':
        return issues

    lowered = markdown.lower()
    approved_markers = (
        'review_status: `published`',
        'review_status: published',
        'human review approved',
        'review approved',
    )
    if any(marker in lowered for marker in approved_markers):
        return issues

    issues.append(
        SkillUsabilityIssue(
            code=FAILURE_CODE_REVIEW_APPROVAL_MISSING,
            message='Skill package lacks explicit review approval signal (metadata or markdown marker).',
        )
    )
    return issues
