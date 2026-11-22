"""Checks every study file in studies/ so a typo can't break the site.

Each problem is reported with the file name and a plain-language message.
"""

import re
from pathlib import Path

import pytest
import yaml

STUDIES_DIR = Path(__file__).parent.parent / "studies"
STUDY_FILES = sorted(p for p in STUDIES_DIR.glob("*.yaml") if not p.name.startswith("_"))

REQUIRED = [
    "title", "authors", "year_published", "country", "study_start_year",
    "program", "transfer_type", "recipient", "design", "status",
]
ALLOWED = {
    "transfer_type": {"unconditional", "conditional", "labelled"},
    "recipient": {"household", "women", "men", "individual"},
    "design": {"rct", "quasi_experimental"},
    "status": {"draft", "validated", "excluded"},
}
FILENAME = re.compile(r"^[a-z]+-\d{4}-[a-z]{3}(-[a-z0-9]+)?\.yaml$")


def problems(path: Path) -> list[str]:
    try:
        study = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"the file is not valid YAML ({exc.__class__.__name__}); check quotes and indentation"]
    if not isinstance(study, dict):
        return ["the file is empty or not a list of fields"]

    errs = []
    for field in REQUIRED:
        if study.get(field) in (None, "", []):
            errs.append(f"'{field}' is missing or empty")
    for field, allowed in ALLOWED.items():
        value = study.get(field)
        if value not in (None, "") and value not in allowed:
            errs.append(f"'{field}' is '{value}', expected one of: {', '.join(sorted(allowed))}")

    country = str(study.get("country", ""))
    if country and not re.fullmatch(r"[A-Z]{3}", country):
        errs.append(f"'country' should be a 3-letter uppercase ISO code like KEN, got '{country}'")

    for field in ("year_published", "study_start_year"):
        year = study.get(field)
        if year not in (None, "") and not (isinstance(year, int) and 1990 <= year <= 2030):
            errs.append(f"'{field}' should be a year between 1990 and 2030, got '{year}'")
    start, pub = study.get("study_start_year"), study.get("year_published")
    if isinstance(start, int) and isinstance(pub, int) and start > pub:
        errs.append("'study_start_year' is after 'year_published'")

    if study.get("status") == "validated" and not study.get("validated_by"):
        errs.append("status is 'validated' but 'validated_by' is empty")

    if not FILENAME.match(path.name):
        errs.append("file name should look like 'author-2016-ken.yaml' (lowercase)")
    return errs


@pytest.mark.parametrize("path", STUDY_FILES, ids=lambda p: p.name)
def test_study_file_is_valid(path):
    errs = problems(path)
    assert not errs, f"\n{path.name}:\n  - " + "\n  - ".join(errs)


def test_no_duplicate_studies():
    seen = {}
    for path in STUDY_FILES:
        study = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        key = (str(study.get("title", "")).strip().lower(), study.get("country"))
        assert key not in seen, f"{path.name} duplicates {seen[key]}"
        seen[key] = path.name
