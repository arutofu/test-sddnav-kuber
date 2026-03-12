#!/usr/bin/env python3

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import argparse
import subprocess
import sys
import yaml


ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = ROOT / "spec" / "stack.yaml"
HELM_CHART_DIR = ROOT / "helm" / "sddnav"


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def load_spec() -> Dict[str, Any]:
    if not SPEC_FILE.exists():
        fail(f"Spec file not found: {SPEC_FILE}")

    with SPEC_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        fail("Spec file must contain a YAML object")

    return data


def validate_requirements_structure(requirements: List[Dict[str, Any]]) -> None:
    if not isinstance(requirements, list) or not requirements:
        fail("'requirements' must be a non-empty list")

    seen_ids: Set[str] = set()

    for idx, req in enumerate(requirements, start=1):
        if not isinstance(req, dict):
            fail(f"Requirement #{idx} must be a YAML object")

        req_id = req.get("id")
        title = req.get("title")
        implemented_by = req.get("implemented_by")
        verified_by = req.get("verified_by")

        if not req_id or not isinstance(req_id, str):
            fail(f"Requirement #{idx} is missing valid 'id'")

        if req_id in seen_ids:
            fail(f"Duplicate requirement id: {req_id}")
        seen_ids.add(req_id)

        if not title or not isinstance(title, str):
            fail(f"{req_id}: missing valid 'title'")

        if not isinstance(implemented_by, list) or not implemented_by:
            fail(f"{req_id}: 'implemented_by' must be a non-empty list")

        if not isinstance(verified_by, list) or not verified_by:
            fail(f"{req_id}: 'verified_by' must be a non-empty list")

        for rel_path in implemented_by:
            if not isinstance(rel_path, str) or not rel_path.strip():
                fail(f"{req_id}: invalid path in 'implemented_by'")

            full_path = ROOT / rel_path
            if not full_path.exists():
                fail(f"{req_id}: referenced file does not exist: {rel_path}")


def render_helm_template(release_name: str) -> List[Dict[str, Any]]:
    if not HELM_CHART_DIR.exists():
        fail(f"Helm chart directory not found: {HELM_CHART_DIR}")

    try:
        result = subprocess.run(
            ["helm", "template", release_name, str(HELM_CHART_DIR)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        fail("helm command not found in PATH")
    except subprocess.CalledProcessError as e:
        fail(f"helm template failed:\n{e.stderr or e.stdout}")

    documents: List[Dict[str, Any]] = []
    for doc in yaml.safe_load_all(result.stdout):
        if isinstance(doc, dict):
            documents.append(doc)

    if not documents:
        fail("helm template produced no Kubernetes resources")

    return documents


def build_resource_index(
    resources: List[Dict[str, Any]]
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    index: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for resource in resources:
        kind = resource.get("kind")
        metadata = resource.get("metadata", {})
        name = metadata.get("name")

        if isinstance(kind, str) and isinstance(name, str):
            index[(kind, name)] = resource

    return index


def resolve_expected_name(expected: Dict[str, Any], release_name: str, req_id: str) -> str:
    name = expected.get("name")
    name_template = expected.get("name_template")

    if isinstance(name, str) and name:
        return name

    if isinstance(name_template, str) and name_template:
        return name_template.format(release_name=release_name)

    fail(f"{req_id}: expected resource must have 'name' or 'name_template'")
    raise RuntimeError("unreachable")


def find_container_port(resource: Dict[str, Any], port: int) -> bool:
    containers = (
        resource.get("spec", {})
        .get("template", {})
        .get("spec", {})
        .get("containers", [])
    )

    for container in containers:
        for port_entry in container.get("ports", []):
            if port_entry.get("containerPort") == port:
                return True

    return False


def find_env_value(resource: Dict[str, Any], env_name: str) -> Optional[str]:
    containers = (
        resource.get("spec", {})
        .get("template", {})
        .get("spec", {})
        .get("containers", [])
    )

    for container in containers:
        for env_entry in container.get("env", []):
            if env_entry.get("name") == env_name:
                return env_entry.get("value")

    return None


def validate_resource_checks(
    req_id: str,
    resource: Dict[str, Any],
    resolved_name: str,
    checks: Dict[str, Any],
) -> None:
    if not isinstance(checks, dict):
        fail(f"{req_id}: 'checks' must be an object")

    container_port = checks.get("container_port")
    if container_port is not None:
        if resource.get("kind") != "Deployment":
            fail(f"{req_id}: container_port check is only valid for Deployment resources")

        if not isinstance(container_port, int):
            fail(f"{req_id}: 'container_port' must be an integer")

        if not find_container_port(resource, container_port):
            fail(
                f"{req_id}: Deployment/{resolved_name} does not contain "
                f"containerPort {container_port}"
            )

    env_checks = checks.get("env")
    if env_checks is not None:
        if resource.get("kind") != "Deployment":
            fail(f"{req_id}: env check is only valid for Deployment resources")

        if not isinstance(env_checks, dict) or not env_checks:
            fail(f"{req_id}: 'env' must be a non-empty object")

        for env_name, expected_value in env_checks.items():
            actual_value = find_env_value(resource, env_name)
            if actual_value != expected_value:
                fail(
                    f"{req_id}: Deployment/{resolved_name} has env {env_name}="
                    f"{actual_value!r}, expected {expected_value!r}"
                )


def validate_expected_resources(
    requirements: List[Dict[str, Any]],
    rendered_resources: List[Dict[str, Any]],
    release_name: str,
) -> None:
    resource_index = build_resource_index(rendered_resources)

    for req in requirements:
        req_id = req["id"]
        expected_resources = req.get("expected_resources", [])

        if not expected_resources:
            continue

        if not isinstance(expected_resources, list):
            fail(f"{req_id}: 'expected_resources' must be a list")

        for expected in expected_resources:
            if not isinstance(expected, dict):
                fail(f"{req_id}: each item in 'expected_resources' must be an object")

            kind = expected.get("kind")
            if not isinstance(kind, str) or not kind:
                fail(f"{req_id}: expected resource missing valid 'kind'")

            resolved_name = resolve_expected_name(expected, release_name, req_id)
            key = (kind, resolved_name)

            if key not in resource_index:
                fail(f"{req_id}: rendered manifests do not contain {kind}/{resolved_name}")

            checks = expected.get("checks")
            if checks:
                validate_resource_checks(req_id, resource_index[key], resolved_name, checks)


def read_text_file(rel_path: str, req_id: str) -> str:
    file_path = ROOT / rel_path
    if not file_path.exists():
        fail(f"{req_id}: file does not exist: {rel_path}")
    return file_path.read_text(encoding="utf-8")


def validate_ansible_requirement(requirements: List[Dict[str, Any]]) -> None:
    target_req = None
    for req in requirements:
        if req.get("id") == "REQ-004":
            target_req = req
            break

    if target_req is None:
        return

    implemented_by = target_req.get("implemented_by", [])
    if "ansible/deploy.yml" not in implemented_by:
        fail("REQ-004: expected 'ansible/deploy.yml' in implemented_by")

    content = read_text_file("ansible/deploy.yml", "REQ-004")

    if "helm upgrade --install" not in content:
        fail("REQ-004: ansible/deploy.yml does not contain 'helm upgrade --install'")


def validate_ci_requirement(requirements: List[Dict[str, Any]]) -> None:
    target_req = None
    for req in requirements:
        if req.get("id") == "REQ-005":
            target_req = req
            break

    if target_req is None:
        return

    implemented_by = target_req.get("implemented_by", [])
    if ".github/workflows/ci.yml" not in implemented_by:
        fail("REQ-005: expected '.github/workflows/ci.yml' in implemented_by")

    content = read_text_file(".github/workflows/ci.yml", "REQ-005")

    required_snippets = [
        "yamllint",
        "validate_traceability.py",
        "docker build",
        "helm lint",
        "helm template",
        "ansible-lint",
    ]

    for snippet in required_snippets:
        if snippet not in content:
            fail(f"REQ-005: ci.yml does not contain required snippet: {snippet}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-name", default="test")
    args = parser.parse_args()

    spec = load_spec()
    requirements = spec.get("requirements")

    validate_requirements_structure(requirements)

    rendered_resources = render_helm_template(args.release_name)
    validate_expected_resources(requirements, rendered_resources, args.release_name)

    validate_ansible_requirement(requirements)
    validate_ci_requirement(requirements)

    print(f"OK: validated {len(requirements)} requirement(s)")
    print(f"OK: validated {len(rendered_resources)} rendered Helm resource(s)")
    print("OK: validated Ansible automation requirement")
    print("OK: validated CI requirement")


if __name__ == "__main__":
    main()