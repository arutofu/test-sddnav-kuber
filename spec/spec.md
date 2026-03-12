# SDD Navigator Infrastructure Spec

## Goal

Deploy the SDD Navigator stack in Kubernetes using Helm and Ansible.

## Scope

- Rust API
- PostgreSQL
- Next.js frontend
- CI validation for infrastructure code

## Acceptance criteria

- API image builds successfully
- Frontend image builds successfully
- Helm chart renders Kubernetes resources without errors
- Ansible playbook passes lint
- Stack deploys successfully to Kubernetes
- PostgreSQL, API, and frontend reach Running state
