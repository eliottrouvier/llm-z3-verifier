import json
import threading
import urllib.request
import pytest
from src.web.server import DashboardServer


@pytest.fixture(scope="module")
def live_server():
    # Use port 18090 to avoid any conflict
    port = 18090
    server = DashboardServer(host="127.0.0.1", port=port)
    thread = threading.Thread(target=server.start, kwargs={"blocking": True}, daemon=True)
    thread.start()
    import time
    time.sleep(0.3)
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    server.stop()


def test_api_status(live_server):
    req = urllib.request.Request(f"{live_server}/api/status")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["status"] == "online"
        assert "z3_version" in data


def test_api_benchmarks(live_server):
    req = urllib.request.Request(f"{live_server}/api/benchmarks")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["total"] == 20
        assert len(data["benchmarks"]) == 20


def test_api_verify(live_server):
    payload = json.dumps({"conjecture_id": "matrix_zero_divisors"}).encode()
    req = urllib.request.Request(
        f"{live_server}/api/verify",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["status"] == "sat"
        assert data["counterexample"] is not None


def test_api_bitvectors(live_server):
    req = urllib.request.Request(
        f"{live_server}/api/bitvectors",
        data=b"{}",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["xor_swap"]["sound"] is True
        assert data["addition_overflow"]["overflow_detected"] is False or data["addition_overflow"]["witness_pair"] is not None
        assert data["power_of_two"]["sound"] is True


def test_api_invariants(live_server):
    payload = json.dumps({"candidate_invariant": "2 * s == i * (i - 1)"}).encode()
    req = urllib.request.Request(
        f"{live_server}/api/invariants",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["is_valid_inductive_invariant"] is True
        assert data["initiation_holds"] is True
        assert data["consecution_holds"] is True
        assert data["safety_holds"] is True


def test_api_lean(live_server):
    req = urllib.request.Request(
        f"{live_server}/api/lean",
        data=b"{}",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "theorem_name" in data
        assert "import Mathlib" in data["lean4_code"]
