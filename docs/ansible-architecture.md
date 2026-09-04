# Ansible Infrastructure Automation Architecture — QuickOPS

## 1. Overview

Day 5 introduces enterprise-grade infrastructure automation using **Ansible**. The configuration provisions clean Debian/Ubuntu servers into fully operational container hosts ready for Kubernetes deployments, with guaranteed **idempotency** and zero plaintext secrets.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ansible/site.yml                                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│   Role: common   │          │   Role: docker   │          │ Role: k8s_tools  │
├──────────────────┤          ├──────────────────┤          ├──────────────────┤
│ • apt cache      │          │ • Docker GPG key │          │ • kubectl CLI    │
│ • base tools     │          │ • Docker deb822  │          │ • Helm package   │
│ • sysctl tuning  │          │ • Docker Engine  │          │   manager        │
│ • devops user    │          │ • Compose plugin │          │ • Client version │
│ • sudoers config │          │ • daemon.json    │          │   validation     │
└──────────────────┘          └──────────────────┘          └──────────────────┘
```

---

## 2. Directory Structure

```
QuickOPS/ansible/
├── ansible.cfg             # Default configurations (roles_path, inventory, become, pipelining)
├── inventory.ini           # Node inventory (remote servers + local test container)
├── site.yml                # Master entrypoint playbook
├── vault.example.yml       # Template for encrypted secrets
├── group_vars/
│   └── all.yml             # Global defaults with env-variable lookups
└── roles/
    ├── common/             # Base OS updates, sysctl network rules, devops user
    │   └── tasks/main.yml
    ├── docker/             # Docker CE, containerd, plugins, daemon.json, docker group
    │   ├── tasks/main.yml
    │   └── handlers/main.yml
    └── k8s_tools/          # kubectl and Helm installation with version verification
        └── tasks/main.yml
```

---

## 3. Role Breakdown

### Role: `common`
- **Package Updates**: Executes `apt: update_cache=yes cache_valid_time=3600`.
- **Base Utilities**: Installs `ca-certificates`, `curl`, `gnupg`, `lsb-release`, `git`, `jq`, `sudo`, `tar`, `gzip`, `procps`, `iproute2`, and `python3-debian`.
- **Sysctl Networking**: Enforces `/etc/sysctl.d/99-kubernetes-cri.conf` with:
  - `net.ipv4.ip_forward = 1`
  - `net.bridge.bridge-nf-call-iptables = 1`
  - `net.bridge.bridge-nf-call-ip6tables = 1`
- **User Management**:
  - Creates the administrative `devops` user (UID `1001`, shell `/bin/bash`).
  - Configures passwordless sudo in `/etc/sudoers.d/90-devops-user`.
  - Injects authorized public SSH keys if supplied.

### Role: `docker`
- **Modern APT deb822 Setup**: Downloads official Docker ASCII key to `/etc/apt/keyrings/docker.asc` and configures modern deb822 source file.
- **Docker Engine Packages**: Installs `docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-buildx-plugin`, and `docker-compose-plugin`.
- **Daemon Configuration**: Writes `/etc/docker/daemon.json` with:
  - `native.cgroupdriver=systemd` (required for Kubernetes CRI compatibility)
  - `json-file` log driver with `max-size=50m` and `max-file=3`.
- **Group Membership**: Automatically adds `devops` user to the `docker` group.

### Role: `k8s_tools`
- **`kubectl`**: Downloads official Linux release binary (`v1.31.0`), verifies existence and version, installs to `/usr/local/bin/kubectl`.
- **`helm`**: Fetches official release archive (`v3.16.2`), extracts binary to `/usr/local/bin/helm`, cleans up temporary extraction files.
- **Verification**: Executes `kubectl version --client` and `helm version --short`.

---

## 4. Execution Targets

### Local Test Target (Docker)
Ansible connects to a container using `community.docker.docker` without needing SSH keys or cloud credentials:
```ini
[test_nodes]
quickops-node ansible_connection=docker ansible_user=root
```

To run locally:
```bash
docker run -d --name quickops-node --privileged ubuntu:24.04 sleep infinity
ansible-playbook -i ansible/inventory.ini ansible/site.yml
```

### Remote Target (Bare-metal / Cloud VMs)
In `ansible/inventory.ini`:
```ini
[servers]
node1.example.com ansible_host=203.0.113.10 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519
```

---

## 5. Secrets Management

Secrets are kept **strictly out of Git**:

1. **Environment Variables**:
   `ansible/group_vars/all.yml` reads from environment variables with safe defaults:
   ```yaml
   devops_user: "{{ lookup('env', 'QUICKOPS_DEVOPS_USER') | default('devops', true) }}"
   devops_ssh_public_key: "{{ lookup('env', 'QUICKOPS_SSH_PUBLIC_KEY') | default('', true) }}"
   ```

2. **Ansible Vault**:
   For encrypted credentials (API keys, password hashes, registry tokens):
   ```bash
   # Create encrypted vault
   ansible-vault create ansible/group_vars/vault.yml

   # Run playbook with password prompt
   ansible-playbook -i ansible/inventory.ini ansible/site.yml --ask-vault-pass

   # Or using a password file (ignored in .gitignore)
   echo "mysecretvaultpassword" > ansible/.vault_password
   ansible-playbook -i ansible/inventory.ini ansible/site.yml --vault-password-file ansible/.vault_password
   ```

---

## 6. Verification & Idempotency Proof

### Run #1 (Initial Provisioning)
```text
PLAY RECAP *********************************************************************
quickops-node              : ok=28   changed=7    unreachable=0    failed=0    skipped=3
```

### Run #2 (Idempotency Check)
```text
PLAY RECAP *********************************************************************
quickops-node              : ok=23   changed=0    unreachable=0    failed=0    skipped=8
```
**Result**: `changed=0`, confirming full idempotency across package management, user config, Docker setup, and tool downloads.
