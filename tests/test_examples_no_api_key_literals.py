"""Examples must not ship inference.sh API keys in source (commit a928ae9).

Copy-paste keys in example scripts end up in git history and in clones;
they must read INFERENCE_API_KEY like the SDK factories do.
"""

import re
from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

# Production-style keys: 1nfsh-<id> (not the Makefile dev placeholder 1nfsh-dev-...).
_KEY_LITERAL = re.compile(r"""['"]1nfsh-(?!dev-)[a-z0-9]+['"]""", re.IGNORECASE)
_READS_ENV = re.compile(r"""environ\.get\(\s*['"]INFERENCE_API_KEY['"]""")


def test_examples_contain_no_inference_api_key_string_literals():
    offenders: list[str] = []
    for path in sorted(EXAMPLES_DIR.glob("*.py")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.strip().startswith("#"):
                continue
            if _KEY_LITERAL.search(line):
                offenders.append(f"{path.name}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Remove hardcoded keys; read INFERENCE_API_KEY instead:\n" + "\n".join(offenders)
    )


def test_examples_that_use_the_client_read_inference_api_key_from_environ():
    """Any script that builds inference()/async_inference() clients must load the key from the env."""
    missing: list[str] = []
    for path in sorted(EXAMPLES_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "inference(" not in text and "async_inference(" not in text:
            continue
        if not _READS_ENV.search(text):
            missing.append(path.name)
    assert not missing, (
        "These examples call the client but do not read INFERENCE_API_KEY: " + ", ".join(missing)
    )
