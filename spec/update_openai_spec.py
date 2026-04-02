#!/usr/bin/env python3
"""Fetch the latest OpenAI OpenAPI spec and extract chat completions schemas.

Usage:
    python spec/update_openai_spec.py

Outputs:
    spec/openai-chat-completions.yml  — self-contained schema for chat completions
"""

import urllib.request
import yaml
import sys
from pathlib import Path

SPEC_URL = "https://app.stainless.com/api/spec/documented/openai/openapi.documented.yml"

SEED_SCHEMAS = [
    "CreateChatCompletionRequest",
    "CreateChatCompletionResponse",
    "CreateChatCompletionStreamResponse",
    "ChatCompletionRequestMessage",
    "ChatCompletionRequestUserMessage",
    "ChatCompletionRequestAssistantMessage",
    "ChatCompletionRequestSystemMessage",
    "ChatCompletionRequestToolMessage",
    "ChatCompletionRequestDeveloperMessage",
    "ChatCompletionRequestMessageContentPartText",
    "ChatCompletionRequestMessageContentPartImage",
    "ChatCompletionRequestMessageContentPartFile",
    "ChatCompletionRequestMessageContentPartAudio",
    "ChatCompletionRequestMessageContentPartRefusal",
    "ChatCompletionRequestAssistantMessageContentPart",
    "ChatCompletionRequestSystemMessageContentPart",
    "ChatCompletionRequestToolMessageContentPart",
]

HEADER = """\
# OpenAI Chat Completions API Schema (extracted)
# Source: {url}
# Repository: https://github.com/openai/openai-openapi
# Extracted: chat completions request/response + all referenced schemas
# To update: python spec/update_openai_spec.py
"""


def find_refs(obj):
    """Recursively find all $ref schema names."""
    refs = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str) and v.startswith("#/components/schemas/"):
                refs.add(v.split("/")[-1])
            refs |= find_refs(v)
    elif isinstance(obj, list):
        for item in obj:
            refs |= find_refs(item)
    return refs


def resolve_all(schemas, seeds):
    """Starting from seed schema names, resolve all transitive $ref dependencies."""
    resolved = set(seeds)
    queue = list(seeds)
    while queue:
        name = queue.pop(0)
        if name not in schemas:
            print(f"  warning: schema {name!r} not found in spec", file=sys.stderr)
            continue
        for ref in find_refs(schemas[name]):
            if ref not in resolved and ref in schemas:
                resolved.add(ref)
                queue.append(ref)
    return resolved


def main():
    out_dir = Path(__file__).parent
    out_path = out_dir / "openai-chat-completions.yml"

    print(f"Fetching spec from {SPEC_URL} ...")
    req = urllib.request.Request(SPEC_URL, headers={"User-Agent": "inferencesh-spec-updater"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    print(f"  downloaded {len(raw)} bytes")

    spec = yaml.safe_load(raw)
    schemas = spec.get("components", {}).get("schemas", {})
    print(f"  found {len(schemas)} total schemas in spec")

    resolved = resolve_all(schemas, SEED_SCHEMAS)
    extracted = {k: schemas[k] for k in sorted(resolved) if k in schemas}
    print(f"  extracted {len(extracted)} schemas (from {len(SEED_SCHEMAS)} seeds)")

    output = HEADER.format(url=SPEC_URL) + "\n" + yaml.dump(
        {"components": {"schemas": extracted}},
        default_flow_style=False,
        sort_keys=True,
    )

    out_path.write_text(output)
    print(f"  wrote {output.count(chr(10))} lines to {out_path}")


if __name__ == "__main__":
    main()
