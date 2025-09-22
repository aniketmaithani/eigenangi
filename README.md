# eigenangi

> *Work in progress.*
> A small, opinionated Python library (and CLI) to **discover EC2 instance types today** and eventually **spin up EC2 + basic infra quickly** with sane defaults, minimal ceremony, and room to grow.

There are many cloud scripts and wrappers out there—but why not one more that’s:

* **Tiny & composable** (bring your own IaC; use this where it’s convenient)
* **Pragmatic** (focus on the 80% workflows devs repeat daily)
* **Safe by default** (explicit region/credentials; clear errors)

---

## Status

* ✅ `ec2.list_machine_types(...)` — list instance types available to your account/region
* ✅ CLI: `eigenangi-ec2 list-machine-types ...`
* 🚧 Upcoming: create EC2 instances with opinionated defaults (VPC/SG/KeyPair), tags, name, SSH bootstrap
* 🚧 Roadmap: spot/on-demand pricing helpers, AMI search, user data templates, minimal VPC scaffolding, teardown, dry-run planner

---

## Why eigenangi?

Because you often need **just enough** glue between AWS and your scripts:

* Don’t want a full framework or to memorize every EC2 flag?
* Want a **Pythonic** API you can drop into a notebook, script, or CI job?
* Want predictable config resolution (env, `.env`, toml), clear exceptions, and a simple CLI?

Same. That’s this project.

---

## Install

```bash
pip install eigenangi
```

Python ≥ 3.9 is supported.

---

## Quick Start

### Python

```python
from eigenangi.ec2 import ec2

# List a subset of instance types (e.g., ARM burstable)
types = ec2.list_machine_types(families=["t4g"], arch="arm64")
for t in types[:10]:
    print(t.instance_type, t.vcpu, t.memory_mib)
```

### CLI

```bash
eigenangi-ec2 list-machine-types --region ap-south-1 --family t4g --arch arm64 --limit 50
```

---

## Configuration & Auth

eigenangi defers to standard **boto3** auth (recommended):

* **Env vars**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` (optional), `AWS_DEFAULT_REGION`
* **Shared credentials**: `~/.aws/credentials`, `~/.aws/config`
* **IAM role**: on EC2/Lambda/etc.

Extras (optional, for local dev):

* **`.env`** in your project:

  ```
  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
  AWS_DEFAULT_REGION=ap-south-1
  ```

* **`~/.config/eigenangi/config.toml`**:

  ```toml
  [aws]
  AWS_DEFAULT_REGION = "ap-south-1"
  # AWS_ACCESS_KEY_ID = "..."
  # AWS_SECRET_ACCESS_KEY = "..."
  # AWS_SESSION_TOKEN = "..."
  ```

> Region is required; you’ll get a friendly `CredentialsNotFound` if it’s missing.

---

## API (current)

```python
from eigenangi.ec2 import ec2, EC2Client

# Quick, singleton-style
types = ec2.list_machine_types(
    families=["t4g", "m7g", "c7g"],  # optional
    arch="arm64",                    # optional: "arm64" | "x86_64"
    burstable_only=None,             # True | False | None
    max_results=1000,                # trim results
)

# Explicit client for per-region usage
client = EC2Client(region_name="ap-south-1")
types = client.list_machine_types(burstable_only=True)
```

**Errors you may see**

* `CredentialsNotFound` — region/creds not resolved
* `PermissionDenied` — AWS says AccessDenied/UnauthorizedOperation
* `ServiceUnavailable` — throttling/outage/botocore error

---

## Roadmap (high-level)

* **Create EC2**: simple `ec2.create_instance(...)` with:

  * sensible defaults (latest Amazon Linux / Debian, EBS gp3, t-family by default)
  * tags, Name, key pair handling (create if missing), basic SG (SSH), public IP toggle
  * optional user data (cloud-init), dry-run
* **Discover**: AMI search helpers, pricing (on-demand/spot), capacity checks
* **Scaffold**: tiny VPC/IGW/Subnet/RouteTable helpers for quick labs
* **Ops**: terminate/stop/start, waiters, state polling with progress
* **DX**: caching, tty tables, JSON output, richer CLI flags
* **Safety**: confirmation prompts, max-cost guardrails, tag-based protection

If you have opinions on defaults or must-have flags, please open an issue!

---

## Design Principles

1. **Boring dependencies**: boto3, nothing fancy.
2. **Clear fallbacks**: env → `.env` → `~/.config/eigenangi/config.toml`.
3. **Small surface area**: each helper should be obvious and testable.
4. **No lock-in**: compose with Terraform/CloudFormation/Pulumi freely.
5. **Explicit errors**: fail loudly with actionable messages.

---

## Contributing

WIP and open to contributions. Suggested areas:

* Region-agnostic tests (with skips when creds/region absent)
* CLI UX polish (e.g., `--json`, column selection)
* Pricing/AMI discovery helpers
* Docs examples for common flows

**Dev setup**

```bash
git clone https://github.com/yourname/eigenangi
cd eigenangi
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
ruff check .
mypy src
```

---

## Versioning & Stability

Pre-1.0.0: Expect breaking changes as features land. Pin minor versions if needed.

---

## License

**** STILL THINKING ABOUT THIS ****

---

## FAQ

**Q: Why not just use the AWS CLI or Terraform?**
A: Use them! eigenangi is a **thin Python layer** to script “small but frequent” tasks, prototype quickly, and integrate into code where shelling out is awkward.

**Q: Will this manage complex infra?**
A: No. It’s intentionally lightweight. For production stacks, stick with IaC. Use eigenangi to **bootstrap**, **explore**, or **glue**.
