"""Every default test is offline; live providers belong in opt-in suites."""
import socket
from copy import deepcopy

import pytest

from kst.core import DATA, load_pack, load_targets


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Network access is forbidden in the offline test suite")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


@pytest.fixture
def pack():
    return deepcopy(load_pack(DATA / "demo-pack.json"))


@pytest.fixture
def targets():
    return deepcopy(load_targets(DATA / "demo-targets.json"))


@pytest.fixture
def one_target(targets):
    targets["targets"] = targets["targets"][:1]
    return targets
