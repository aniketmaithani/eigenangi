"""
Configuration resolution:

1) Standard AWS discovery via boto3 (env, shared credentials, IAM role).
2) Optional `.env` in CWD or project root:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_SESSION_TOKEN (optional)
   - AWS_DEFAULT_REGION or AWS_REGION
3) Optional TOML file at ~/.config/eigenangi/config.toml with same keys.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Optional

from .utils import getenv_str

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv(*args, **kwargs):
        return False

try:
    import tomllib  # py311+
except ModuleNotFoundError:  # Python 3.9–3.10
    import tomli as tomllib  # type: ignore


def load_env_files() -> None:
    load_dotenv()


def load_toml_config() -> Dict[str, str]:
    cfg_path = Path.home() / ".config" / "eigenangi" / "config.toml"
    if cfg_path.exists():
        with cfg_path.open("rb") as f:
            data = tomllib.load(f)
        section = data.get("aws", {})
        return {k.upper(): str(v) for k, v in section.items()}
    return {}


def resolved_aws_settings() -> Dict[str, Optional[str]]:
    load_env_files()
    toml_cfg = load_toml_config()

    access_key = getenv_str("AWS_ACCESS_KEY_ID",
                            toml_cfg.get("AWS_ACCESS_KEY_ID"))
    secret_key = getenv_str("AWS_SECRET_ACCESS_KEY",
                            toml_cfg.get("AWS_SECRET_ACCESS_KEY"))
    session_token = getenv_str(
        "AWS_SESSION_TOKEN", toml_cfg.get("AWS_SESSION_TOKEN"))
    region = getenv_str("AWS_DEFAULT_REGION", getenv_str(
        "AWS_REGION", toml_cfg.get("AWS_DEFAULT_REGION")))

    return {
        "AWS_ACCESS_KEY_ID": access_key,
        "AWS_SECRET_ACCESS_KEY": secret_key,
        "AWS_SESSION_TOKEN": session_token,
        "AWS_DEFAULT_REGION": region,
    }
