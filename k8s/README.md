# K8s Deployment Baseline

This directory is a P2 Kubernetes baseline for production-readiness review. It does not prove that a live cluster rollout has succeeded.

Required runtime secrets must be provisioned by the target platform or Secret Manager before rollout. This repository intentionally contains only `secretKeyRef` references and no Kubernetes Secret object with real values.

Static readiness:

```bash
python scripts/k8s_readiness.py --print-json
```

Cluster evidence readiness:

```bash
kubectl apply --dry-run=server -f k8s/
kubectl rollout status deployment/omni-skill-pipeline -n omni-skill-pipeline
kubectl logs deployment/omni-skill-pipeline -n omni-skill-pipeline --tail=200
python scripts/k8s_readiness.py --require-cluster-evidence --fail-on-blocked --print-json
```

Only the second path can support a production Kubernetes deployment claim.
