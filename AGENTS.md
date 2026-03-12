# AGENTS.md

## Goal

Deploy the SDD Navigator stack in Kubernetes using Helm and Ansible, with CI validation.

## Workflow

1. Read `spec/spec.md`, `spec/plan.md`, and `spec/stack.yaml`
2. Implement changes in Docker / Helm / Ansible
3. Run validation:
   - yamllint spec/
   - python3 scripts/validate_traceability.py --release-name test
   - docker build -t rust-api ./docker/rust-api
   - docker build -t nextjs ./docker/nextjs
   - helm lint ./helm/sddnav
   - helm template test ./helm/sddnav
   - ansible-lint ansible/deploy.yml

## Non-negotiable rules

- No hardcoded Kubernetes namespace in Helm templates
- No broken traceability links
- No CI regression
