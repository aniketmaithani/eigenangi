# src/eigenangi/config.py
from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import Any, Dict, Optional, Union, IO, cast

from .utils import getenv_str

# --- dotenv import with typed fallback (mypy needs identical signature) ---
try:
    from dotenv import load_dotenv  # real function with proper typing
except Exception:

    def load_dotenv(  # identical signature to python-dotenv
        dotenv_path: Optional[Union[str, PathLike[str]]] = None,
        stream: Optional[IO[str]] = None,
        verbose: bool = False,
        override: bool = False,
        interpolate: bool = True,
        encoding: Optional[str] = None,
    ) -> bool:
        return False


# --- tomllib for 3.11+, tomli for 3.9/3.10 (no inline ignores needed) ---
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.9–3.10
    import tomli as tomllib


def load_env_files() -> None:
    """Load environment variables from a .env if present (no-op if absent)."""
    load_dotenv()


def load_toml_config() -> Dict[str, str]:
    """Read ~/.config/eigenangi/config.toml [aws] and return upper-cased keys."""
    cfg_path = Path.home() / ".config" / "eigenangi" / "config.toml"
    if cfg_path.exists():
        with cfg_path.open("rb") as f:
            data = cast("dict[str, Any]", tomllib.load(f))
        section = cast("dict[str, Any]", data.get("aws", {}))
        return {k.upper(): str(v) for k, v in section.items()}
    return {}


def resolved_aws_settings() -> Dict[str, Optional[str]]:
    """
    Resolve AWS settings from env/.env/config.toml.
    Returns a dict with AWS_* keys (values may be None).
    """
    load_env_files()
    toml_cfg = load_toml_config()

    access_key = getenv_str("AWS_ACCESS_KEY_ID", toml_cfg.get("AWS_ACCESS_KEY_ID"))
    secret_key = getenv_str(
        "AWS_SECRET_ACCESS_KEY", toml_cfg.get("AWS_SECRET_ACCESS_KEY")
    )
    session_token = getenv_str("AWS_SESSION_TOKEN", toml_cfg.get("AWS_SESSION_TOKEN"))
    region = getenv_str(
        "AWS_DEFAULT_REGION",
        getenv_str("AWS_REGION", toml_cfg.get("AWS_DEFAULT_REGION")),
    )

    return {
        "AWS_ACCESS_KEY_ID": access_key,
        "AWS_SECRET_ACCESS_KEY": secret_key,
        "AWS_SESSION_TOKEN": session_token,
        "AWS_DEFAULT_REGION": region,
    }
