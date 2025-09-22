from typing import Optional
import os


def getenv_str(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name)
    return val if (val is not None and val.strip() != "") else default
