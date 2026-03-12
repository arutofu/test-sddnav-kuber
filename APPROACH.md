# Approach

## Goal

Deploy the SDD Navigator stack in Kubernetes using Helm and Ansible, and validate infrastructure code in CI.

## AI-assisted workflow

This task was implemented using an AI-assisted workflow:

1. Define requirements and acceptance criteria
2. Produce initial infrastructure drafts
3. Validate and refine Helm, Ansible, and CI configuration
4. Add machine-checkable traceability
5. Verify the stack in Kubernetes

AI-generated outputs were treated as drafts and corrected through linting, templating, and runtime verification.

## Specification-driven layer

The repository includes:

- `spec/spec.md`
- `spec/plan.md`
- `spec/stack.yaml`

These artifacts describe requirements before or alongside implementation and connect them to validation.

## Automated validation

The repository validates:

- Specification syntax
- Requirement traceability
- Docker image builds
- Helm templates
- Ansible playbook quality
- Requirement traceability is validated by `scripts/validate_traceability.py`

## Manual corrections made after validation

Key issues found and corrected during implementation:

- Namespace handling in Helm
- Frontend image pull behavior in Minikube
- Frontend API service URL mismatch
- Ansible lint compliance
- Frontend aligned with Next.js requirement

## Runtime verification

The stack was deployed and verified in Kubernetes:

- PostgreSQL pod running
- Rust API pod running
- Frontend pod running
- Services created successfully
