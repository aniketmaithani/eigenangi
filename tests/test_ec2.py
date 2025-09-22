import os
import pytest

from eigenangi.ec2 import ec2


def test_imports():
    assert callable(ec2.list_machine_types)


@pytest.mark.skipif(
    not os.getenv("AWS_DEFAULT_REGION"),
    reason="Set AWS_DEFAULT_REGION and credentials to run this live test",
)
def test_list_machine_types_live():
    out = ec2.list_machine_types()
    assert isinstance(out, list)
