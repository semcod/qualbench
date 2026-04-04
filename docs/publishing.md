# Publishing Guide

## PyPI (pip install qualbench)

### Automatic (via GitHub Actions)

1. Bump version in `pyproject.toml`
2. Commit and push
3. Create and push a tag:
   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```
4. GitHub Actions automatically builds and publishes

### Manual (for testing)

```bash
# Build
pip install build twine
python -m build

# Check
twine check dist/*

# Test PyPI
twine upload --repository testpypi dist/*

# Production PyPI
twine upload dist/*
```

## Docker Hub

### Automatic (via GitHub Actions)

Pushes to `main` automatically build and push to Docker Hub.

### Manual

```bash
# Build
docker build -t semcod/qualbench-action:latest action/

# Tag with version
docker tag semcod/qualbench-action:latest semcod/qualbench-action:v0.3.0

# Push
docker push semcod/qualbench-action:latest
docker push semcod/qualbench-action:v0.3.0
```

## GitHub Releases

Created automatically when tags are pushed.

## Version Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` (if exists)
- [ ] Run tests: `make test`
- [ ] Commit: `git commit -m "Bump version to X.Y.Z"`
- [ ] Tag: `git tag vX.Y.Z`
- [ ] Push: `git push && git push origin vX.Y.Z`
- [ ] Verify PyPI: https://pypi.org/project/qualbench/X.Y.Z/
- [ ] Verify Docker Hub: https://hub.docker.com/r/semcod/qualbench-action/tags
