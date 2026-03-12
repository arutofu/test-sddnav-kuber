---
applyTo: "helm/**,ansible/**,docker/**"
---

- Use Helm values instead of hardcoded literals where practical.
- Do not introduce `namespace: default` in templates.
- Keep service naming consistent with runtime URLs.
- Validate changes with `helm lint`, `helm template`, and `ansible-lint`.
