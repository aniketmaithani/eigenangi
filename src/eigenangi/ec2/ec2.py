from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import boto3
import botocore
from ..config import resolved_aws_settings
from ..exceptions import CredentialsNotFound, PermissionDenied, ServiceUnavailable


@dataclass(frozen=True)
class InstanceTypeInfo:
    instance_type: str
    vcpu: int
    memory_mib: int
    family: Optional[str] = None
    arch: Optional[List[str]] = None
    network_performance: Optional[str] = None
    supports_ena: Optional[bool] = None
    burstable: Optional[bool] = None

    @staticmethod
    def from_aws(d: Dict[str, Any]) -> "InstanceTypeInfo":
        it = d.get("InstanceType", "")
        vcpu = d.get("VCpuInfo", {}).get("DefaultVCpus", 0)
        mem = d.get("MemoryInfo", {}).get("SizeInMiB", 0)
        family = it.split(".")[0] if "." in it else None
        arch = d.get("ProcessorInfo", {}).get("SupportedArchitectures", None)
        net_perf = d.get("NetworkInfo", {}).get("NetworkPerformance")
        ena = d.get("NetworkInfo", {}).get("EnaSupport") in ("required", "supported")
        burst = d.get("BurstablePerformanceSupported", False)
        return InstanceTypeInfo(
            instance_type=it,
            vcpu=vcpu,
            memory_mib=mem,
            family=family,
            arch=arch,
            network_performance=net_perf,
            supports_ena=ena,
            burstable=burst,
        )


class EC2Client:
    """
    Thin wrapper around boto3 for high-level EC2 helpers.
    Auth/region resolution follows boto3 defaults plus eigenangi config helpers.
    """

    def __init__(self, region_name: Optional[str] = None) -> None:
        cfg = resolved_aws_settings()
        region = region_name or cfg.get("AWS_DEFAULT_REGION")
        try:
            session = boto3.session.Session(
                aws_access_key_id=cfg.get("AWS_ACCESS_KEY_ID") or None,
                aws_secret_access_key=cfg.get("AWS_SECRET_ACCESS_KEY") or None,
                aws_session_token=cfg.get("AWS_SESSION_TOKEN") or None,
                region_name=region or None,
            )
        except Exception as e:
            raise CredentialsNotFound(str(e)) from e

        self._session = session
        self._region = session.region_name
        if not self._region:
            raise CredentialsNotFound(
                "AWS region not resolved. Set AWS_DEFAULT_REGION or configure your AWS profile."
            )

        self._ec2 = session.client("ec2")

    @property
    def region(self) -> str:
        return self._region

    def list_machine_types(
        self,
        families: Optional[Iterable[str]] = None,
        arch: Optional[str] = None,  # "arm64" | "x86_64"
        burstable_only: Optional[bool] = None,  # True | False | None
        max_results: int = 1000,
    ) -> List[InstanceTypeInfo]:
        """
        Discover instance types available to the account in this region.

        Args:
            families: Optional iterable of instance *families* (prefix before the dot),
                      e.g. ["t4g", "m7g"].
            arch:     Optional architecture filter: "arm64" | "x86_64".
            burstable_only: If True, only T-family (burstable). If False, exclude them.
            max_results: Trim the returned list to at most this many items.

        Returns:
            A list of InstanceTypeInfo objects.
        """
        filters: List[Dict[str, Any]] = []
        if families:
            # NOTE: EC2 filter "instance-type" does not support wildcards reliably;
            # many accounts use pagination anyway. We request broadly and filter client-side.
            # If you prefer API-side filtering, you could expand to exact types.
            pass

        if arch:
            filters.append(
                {"Name": "processor-info.supported-architecture", "Values": [arch]}
            )

        try:
            paginator = self._ec2.get_paginator("describe_instance_types")
            page_it = paginator.paginate(
                Filters=filters if filters else None,
                PaginationConfig={"PageSize": 100},
            )

            out: List[InstanceTypeInfo] = []
            for page in page_it:
                for it in page.get("InstanceTypes", []):
                    info = InstanceTypeInfo.from_aws(it)

                    # Client-side family filter (prefix before the dot)
                    if families:
                        fam = info.family or ""
                        if fam not in set(families):
                            continue

                    if burstable_only is True and not info.burstable:
                        continue
                    if burstable_only is False and info.burstable:
                        continue

                    out.append(info)

            return out[:max_results]

        except botocore.exceptions.NoCredentialsError as e:
            raise CredentialsNotFound(
                "AWS credentials not found. Set env vars, ~/.aws/credentials, or an IAM role."
            ) from e
        except botocore.exceptions.ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in {"AccessDenied", "UnauthorizedOperation"}:
                raise PermissionDenied(
                    f"Access denied for DescribeInstanceTypes: {code}"
                ) from e
            if code in {"Throttling", "RequestLimitExceeded", "ServiceUnavailable"}:
                raise ServiceUnavailable(
                    f"EC2 service throttled/unavailable: {code}"
                ) from e
            raise
        except botocore.exceptions.BotoCoreError as e:
            raise ServiceUnavailable(f"Boto core error: {e}") from e


class _EC2Facade:
    """
    Convenience facade so callers can do:
        from eigenangi.ec2 import ec2
        ec2.list_machine_types(...)
        ec2() -> EC2Client  # construct explicitly
    """

    def __call__(self, *args: Any, **kwargs: Any) -> EC2Client:
        return EC2Client(*args, **kwargs)

    def list_machine_types(self, *args: Any, **kwargs: Any) -> List[InstanceTypeInfo]:
        return EC2Client().list_machine_types(*args, **kwargs)


# Singleton-style convenience export
ec2 = _EC2Facade()


def list_machine_types(*args: Any, **kwargs: Any) -> List[InstanceTypeInfo]:
    """Functional alias: eigenangi.ec2.list_machine_types(...)."""
    return EC2Client().list_machine_types(*args, **kwargs)


def _print_table(rows: List[InstanceTypeInfo]) -> None:
    """Simple tab-separated table for CLI output."""
    if not rows:
        print("No instance types returned.")
        return
    headers: List[str] = [
        "instance_type",
        "vcpu",
        "memory_mib",
        "family",
        "arch",
        "network",
        "burstable",
    ]
    print("\t".join(headers))
    for r in rows:
        arch = ",".join(r.arch or []) if r.arch else ""
        net = r.network_performance or ""
        fam = r.family or ""
        print(
            f"{r.instance_type}\t{r.vcpu}\t{r.memory_mib}\t{fam}\t{arch}\t{net}\t{r.burstable}"
        )


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="eigenangi-ec2", description="EC2 machine type discovery"
    )
    parser.add_argument("command", choices=["list-machine-types"])
    parser.add_argument("--region", help="AWS region (overrides env/profile)")
    parser.add_argument(
        "--family", action="append", help="Filter by instance family (repeatable)"
    )
    parser.add_argument(
        "--arch", choices=["arm64", "x86_64"], help="Filter by architecture"
    )
    parser.add_argument(
        "--burstable-only", action="store_true", help="Only show T-family burstable"
    )
    parser.add_argument(
        "--non-burstable-only", action="store_true", help="Exclude burstable"
    )
    parser.add_argument("--limit", type=int, default=200, help="Max results")

    args = parser.parse_args(argv)

    try:
        client = EC2Client(region_name=args.region)
        if args.command == "list-machine-types":
            burstable: Optional[bool]
            if args.burstable_only:
                burstable = True
            elif args.non_burstable_only:
                burstable = False
            else:
                burstable = None

            rows = client.list_machine_types(
                families=args.family,
                arch=args.arch,
                burstable_only=burstable,
                max_results=args.limit,
            )
            _print_table(rows)
        return 0
    except (CredentialsNotFound, PermissionDenied, ServiceUnavailable) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 3
