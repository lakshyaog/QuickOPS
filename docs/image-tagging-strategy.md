# Container Image Tagging & CD Strategy

This document outlines the container image tagging strategy, registry architecture, and security scanning policies implemented for QuickOPS.

---

## 1. Registry Architecture: GitHub Container Registry (GHCR)

All container images are published to **GitHub Container Registry (GHCR)**:
```
ghcr.io/<owner>/quickops/backend:<tag>
```

### Why GHCR?
- **Integrated Authentication**: Native access within GitHub Actions via `${{ secrets.GITHUB_TOKEN }}` without requiring third-party credentials.
- **Fine-Grained Permissions**: Access controlled via GitHub repository and organization settings.
- **Proximity**: Co-located with GitHub Actions runners, resulting in fast layer caching and upload speeds.

### Required GitHub Actions Permissions
Publishing to GHCR requires the following permissions in the workflow:
```yaml
permissions:
  contents: read          # Read repository code
  packages: write          # Push container images to ghcr.io
  security-events: write   # Upload Trivy SARIF security scan results
```

---

## 2. Image Tagging Convention

Images are automatically tagged via `docker/metadata-action` during the CI/CD pipeline based on git context:

| Tag Type | Example | Trigger / Source | Purpose |
| :--- | :--- | :--- | :--- |
| **Commit SHA (Prefixed)** | `sha-a1b2c3d` | Every push / tag | Immutable reference directly traceable to git commit. |
| **Commit SHA (Raw)** | `a1b2c3d` | Every push / tag | Short git commit SHA. |
| **Semantic Version (Full)** | `v1.2.3` | Git tag `v*.*.*` | Production releases and milestone deployments. |
| **Semantic Version (Major.Minor)** | `v1.2` | Git tag `v*.*.*` | Floating minor version pointer. |
| **Branch** | `main` | Push to branch | Tracks the latest build on a specific branch. |
| **Latest** | `latest` | Push to default branch (`main`) | Convenience tag for local development / testing. |
| **Pull Request** | `pr-42` | Pull request events | Ephemeral tag for PR validation / preview environments. |

---

## 3. Why `latest` is an Anti-Pattern in Production

Relying exclusively on the `:latest` tag is dangerous in production environments for several key reasons:

1. **Non-Deterministic Deployments**:
   - `:latest` is a mutable pointer. If two nodes in a cluster pull `:latest` at different times during a rollout, they may run completely different code.
2. **Broken Rollbacks**:
   - If a deployment fails, rolling back to `:latest` does nothing because `:latest` already points to the broken image. Pinning by `sha-<commit_sha>` or `v1.2.3` allows instant rollbacks to an exact, known-good image.
3. **Caching & Pull Policy Issues**:
   - Kubernetes and Docker engines cache images locally. If `imagePullPolicy: IfNotPresent` is set with `:latest`, nodes that have an older `:latest` cached will never pull updates.
4. **Auditability & Traceability**:
   - Given an image tagged `sha-a1b2c3d`, an engineer can instantly inspect `git show a1b2c3d` to know the exact code, commits, and dependencies running in production.

---

## 4. Trivy Container Vulnerability Scanning

Container security scanning is executed before any image is published to GHCR.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Lint & Test │ ──► │ Docker Build │ ──► │ Trivy Scan   │ ──► │ Push to GHCR │
│ (flake8/test)│     │  (local)     │     │ (Vuln Gate)  │     │ (Versioned)  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

- **Scanner**: [Trivy](https://github.com/aquasecurity/trivy) CLI (installed directly from official GitHub releases, avoiding third-party action wrapper dependencies).
- **Scan Targets**: Both OS packages (Alpine/Debian) and application libraries (`pip` dependencies).
- **Severity Levels**: Flags `HIGH` and `CRITICAL` vulnerabilities.
- **Reporting**:
  - **Console Table**: Full table report printed in GitHub Actions job output.
  - **SARIF Report**: Saved to `trivy-results.sarif` and uploaded to the GitHub Repository **Security → Code scanning alerts** tab.

---

## 5. Pulling & Running the Published Image

### Authenticate locally with GHCR
Create a GitHub Personal Access Token (PAT) with `read:packages` scope:
```bash
echo $CR_PAT | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin
```

### Pull specific immutable version
```bash
# Pull by commit SHA (Recommended for production/staging)
docker pull ghcr.io/<owner>/quickops/backend:sha-a1b2c3d

# Pull by release version
docker pull ghcr.io/<owner>/quickops/backend:v1.0.0
```

### Run the container
```bash
docker run -d \
  --name quickops_api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/dbname" \
  ghcr.io/<owner>/quickops/backend:sha-a1b2c3d
```
