from .ec2 import (
    EC2Client as EC2Client,
    ec2 as ec2,
    list_machine_types as list_machine_types,
)

__all__ = ["EC2Client", "ec2", "list_machine_types"]
