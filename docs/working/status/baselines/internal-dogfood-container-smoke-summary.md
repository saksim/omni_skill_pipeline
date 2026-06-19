# Container Smoke Summary

- Decision: `FAIL`
- Failure stage: `image_build`
- Failure category: `docker_base_image_pull_failed`
- Image tag: `omni-skill-pipeline:dogfood`
- Container name: `omni-skill-pipeline-smoke`
- Health URL: `http://127.0.0.1:18000/healthz`

## Stages

- `docker_cli`: `pass` - Docker CLI found in PATH.
- `docker_daemon`: `pass` - Docker daemon is reachable.
- `image_build`: `fail` - Docker image build failed while pulling base image metadata.
