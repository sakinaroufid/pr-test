#!/usr/bin/env python3
"""Structural checks on the REST (OpenAPI) and MCP (OpenRPC) bindings.

The transport artifacts under source/services are what SDKs and conformance
suites are generated from, so their response declarations have to match the
outcomes the specification defines:

  - A create operation returns 201 with the created resource, or 200 with
    the UCP error envelope when nothing was created (the REST pages'
    "Business Outcomes" sections). Declaring only 201 hid the error
    outcome from generated clients and left the docs' response-header
    table empty on every page built from a create operation.
  - Every success response is application/json and declares the signed
    response headers (Signature, Signature-Input, Content-Digest).
  - A REST binding and its MCP binding expose the same operations.

Run: uv run python scripts/test_rest_bindings.py
Exit: 0 on all pass, 1 on any failure.
"""

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES = REPO_ROOT / "source" / "services"

ERROR_RESPONSE_REF = "../../schemas/common/types/error_response.json"
SIGNED_RESPONSE_HEADERS = {"Signature", "Signature-Input", "Content-Digest"}

# REST and MCP bindings of the same service.
PAIRED_BINDINGS = [
  ("shopping/rest.openapi.json", "shopping/mcp.openrpc.json"),
  ("common/rest.openapi.json", "common/mcp.openrpc.json"),
  ("lodging/rest.openapi.json", "lodging/mcp.openrpc.json"),
]

# -----------------------------------------------------------
# Test harness (minimal, no deps)
# -----------------------------------------------------------

_RESULTS: list[tuple[str, bool, str]] = []


def _check(name: str, condition: bool, detail: str = "") -> None:
  """Record a test result."""
  _RESULTS.append((name, condition, detail))


def _report() -> int:
  """Print results and return exit code."""
  passed = sum(1 for _, ok, _ in _RESULTS if ok)
  failed = [(n, d) for n, ok, d in _RESULTS if not ok]
  for name, ok, detail in _RESULTS:
    status = "PASS" if ok else "FAIL"
    suffix = f" — {detail}" if detail and not ok else ""
    print(f"  {status}  {name}{suffix}")
  print(f"\n{passed} passed, {len(failed)} failed")
  return 0 if not failed else 1


def _load(rel: str) -> dict:
  return json.loads((SERVICES / rel).read_text(encoding="utf-8"))


def _operations(openapi: dict):
  """Yield (operationId, method, path, operation) for every path operation."""
  for path, item in openapi.get("paths", {}).items():
    for method, op in item.items():
      if isinstance(op, dict) and "operationId" in op:
        yield op["operationId"], method.upper(), path, op


def _schema_ref(response: dict) -> str | None:
  content = response.get("content", {}).get("application/json", {})
  return content.get("schema", {}).get("$ref")


# -----------------------------------------------------------
# Tests
# -----------------------------------------------------------


def test_create_operations_declare_both_outcomes() -> None:
  """A 201 create also declares the 200 error-envelope outcome."""
  found = 0
  for rel in (rest for rest, _ in PAIRED_BINDINGS):
    for op_id, _method, _path, op in _operations(_load(rel)):
      responses = op.get("responses", {})
      if "201" not in responses:
        continue
      found += 1
      ok_200 = _schema_ref(responses.get("200", {})) == ERROR_RESPONSE_REF
      _check(f"create_declares_200_error_envelope[{op_id}]", ok_200)
      r201 = _schema_ref(responses["201"]) or ""
      _check(
        f"create_201_is_resource_not_union[{op_id}]",
        r201.startswith("#/components/schemas/")
        and not r201.endswith("_response"),
        r201,
      )
      same_headers = set(responses["201"].get("headers", {})) == set(
        responses.get("200", {}).get("headers", {})
      )
      _check(f"create_outcomes_share_headers[{op_id}]", same_headers)
  _check("create_operations_found", found >= 3, str(found))


def test_success_responses_are_signed_json() -> None:
  """Every 2xx response is JSON and declares the signed response headers."""
  for rel in (rest for rest, _ in PAIRED_BINDINGS):
    for op_id, _method, _path, op in _operations(_load(rel)):
      for code, response in op.get("responses", {}).items():
        if not code.startswith("2"):
          continue
        _check(
          f"success_is_json[{op_id}:{code}]",
          "application/json" in response.get("content", {}),
        )
        _check(
          f"success_declares_signed_headers[{op_id}:{code}]",
          set(response.get("headers", {})) >= SIGNED_RESPONSE_HEADERS,
          str(sorted(response.get("headers", {}))),
        )


def test_non_create_operations_declare_only_200() -> None:
  """Read, update, complete and cancel operations succeed with 200 alone."""
  for rel in (rest for rest, _ in PAIRED_BINDINGS):
    for op_id, _method, _path, op in _operations(_load(rel)):
      codes = {c for c in op.get("responses", {}) if c.startswith("2")}
      if "201" in codes:
        continue
      _check(
        f"non_create_declares_200_only[{op_id}]", codes == {"200"}, str(codes)
      )


def test_rest_and_mcp_expose_the_same_operations() -> None:
  """Each REST operationId has an MCP method of the same name, and back."""
  for rest_rel, mcp_rel in PAIRED_BINDINGS:
    rest_ops = {op_id for op_id, *_ in _operations(_load(rest_rel))}
    mcp_ops = {m["name"] for m in _load(mcp_rel)["methods"]}
    _check(
      f"rest_mcp_parity[{rest_rel}]",
      rest_ops == mcp_ops,
      f"rest-only={sorted(rest_ops - mcp_ops)} "
      f"mcp-only={sorted(mcp_ops - rest_ops)}",
    )


# -----------------------------------------------------------
# Runner
# -----------------------------------------------------------


def main() -> int:
  """Run every test and report."""
  for test in (
    test_create_operations_declare_both_outcomes,
    test_success_responses_are_signed_json,
    test_non_create_operations_declare_only_200,
    test_rest_and_mcp_expose_the_same_operations,
  ):
    try:
      test()
    except Exception as e:  # noqa: BLE001
      _check(test.__name__, False, f"{type(e).__name__}: {e}")
  return _report()


if __name__ == "__main__":
  sys.exit(main())
