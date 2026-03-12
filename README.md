# SDD Navigator Kubernetes Deployment

Infrastructure-as-Code deployment of the **SDD Navigator stack** in Kubernetes.

## Stack

Application services:

- Rust API
- PostgreSQL
- Next.js frontend

Infrastructure and automation:

- Docker
- Kubernetes
- Helm
- Ansible
- GitHub Actions

## Task Goal

This repository contains the solution for a DevOps test task:

- deploy the SDD Navigator stack in Kubernetes
- package Kubernetes resources with Helm
- automate deployment with Ansible
- validate infrastructure code in CI

## Specification and Traceability

This repository follows a lightweight spec-first workflow.

- `spec/spec.md` - functional specification
- `spec/plan.md` - technical implementation plan
- `spec/stack.yaml` - machine-readable requirement traceability
- `scripts/validate_traceability.py` - automated traceability checks

CI validates specification, traceability, container builds, Helm templates, and Ansible automation.

## Approach

The task was implemented using an AI-assisted workflow described in the APPROACH.md.

## Repository Structure

```text
.github/workflows/    CI validation
ansible/              deployment automation
docker/               container definitions
helm/sddnav/          Helm chart
instructions/         instructions for AI-assistent
scripts/              validation utilities
spec/                 stack specification
```

## Build Images

Build local Docker images:

```bash
docker build -t rust-api ./docker/rust-api
docker build -t nextjs ./docker/nextjs
```

If you use Minikube, load images into the cluster:

```bash
minikube image load rust-api:latest
minikube image load nextjs:latest
```

## Deploy

Deploy the stack with Ansible:

```bash
ansible-playbook ansible/deploy.yml
```

Or directly with Helm:

```bash
helm upgrade --install sddnav ./helm/sddnav --namespace sddnav --create-namespace
```

## Validation

### Specification

```bash
yamllint spec/
python3 scripts/validate_traceability.py --release-name test
```

### Helm

```bash
helm lint ./helm/sddnav
helm template test ./helm/sddnav
```

### Ansible

```bash
ansible-lint ansible/deploy.yml
```

## Runtime Checks

Check deployed resources:

```bash
kubectl get pods -n sddnav
kubectl get svc -n sddnav
kubectl get deployments -n sddnav
```

## Notes

Prerequisites:

- Docker
- Kubernetes cluster (for example Minikube)
- Helm
- Ansible
- Python 3

For local Kubernetes testing with Minikube, Docker images must be available inside the Minikube image cache.

The project is focused on infrastructure deployment and validation for the test task.
