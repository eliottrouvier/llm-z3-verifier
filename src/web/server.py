from __future__ import annotations
import http.server
import json
import os
import sys
import time
from typing import Any, Dict
import z3

from ..smt_engine import SMTEngine
from ..backends import MockOfflineBackend
from ..mcts_search import MCTSProofSearch
from ..prm_verifier import SymbolicPRM
from ..visualizer import ProofTreeVisualizer
from ..bitvectors import BitVectorVerifier
from ..lemma_synthesis import LoopInvariantVerifier
from ..lean_bridge import LeanBridge

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
DATASET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "benchmarks", "dataset.json"))


class DashboardRequestHandler(http.server.SimpleHTTPRequestHandler):
    """REST API and static asset handler for llm-z3-verifier."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, data: Dict[str, Any], status_code: int = 200) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        url_path = self.path.split("?")[0]
        if url_path == "/api/status":
            self._send_json({
                "status": "online",
                "version": "0.2.0",
                "z3_version": z3.get_version_string(),
                "system": sys.platform
            })
            return

        if url_path == "/api/benchmarks":
            if os.path.exists(DATASET_PATH):
                with open(DATASET_PATH, "r", encoding="utf-8") as f:
                    benchmarks = json.load(f)
                self._send_json({"total": len(benchmarks), "benchmarks": benchmarks})
            else:
                self._send_json({"error": "dataset.json not found"}, 404)
            return

        # Default static file handling
        return super().do_GET()

    def do_POST(self):
        url_path = self.path.split("?")[0]
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            req_data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            req_data = {}

        if url_path == "/api/run-benchmarks":
            self._handle_run_benchmarks()
            return
        elif url_path == "/api/verify":
            self._handle_verify(req_data)
            return
        elif url_path == "/api/mcts":
            self._handle_mcts(req_data)
            return
        elif url_path == "/api/bitvectors":
            self._handle_bitvectors(req_data)
            return
        elif url_path == "/api/invariants":
            self._handle_invariants(req_data)
            return
        elif url_path == "/api/lean":
            self._handle_lean(req_data)
            return
        else:
            self._send_json({"error": f"Endpoint {url_path} not found"}, 404)

    def _handle_run_benchmarks(self):
        if not os.path.exists(DATASET_PATH):
            self._send_json({"error": "dataset.json not found"}, 404)
            return

        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            benchmarks = json.load(f)

        backend = MockOfflineBackend()
        engine = SMTEngine()
        results = []
        correct_count = 0
        total_latency = 0.0

        for item in benchmarks:
            t0 = time.perf_counter()
            formalization = backend.formalize_conjecture(item["id"])
            res = engine.find_counterexample(
                var_specs=formalization["variables"],
                domain_constraints=formalization["domain_constraints"],
                negated_claims=formalization["negated_formula"]
            )
            lat_ms = (time.perf_counter() - t0) * 1000
            total_latency += lat_ms
            is_correct = (res.status == item["expected_result"])
            if is_correct:
                correct_count += 1

            results.append({
                "id": item["id"],
                "name": item["name"],
                "domain": item["domain"],
                "conjecture": item["conjecture"],
                "expected": item["expected_result"],
                "actual": res.status,
                "passed": is_correct,
                "latency_ms": round(lat_ms, 2),
                "counterexample": res.counterexample
            })

        self._send_json({
            "total": len(benchmarks),
            "correct": correct_count,
            "accuracy": round((correct_count / len(benchmarks)) * 100, 2),
            "mean_latency_ms": round(total_latency / len(benchmarks), 2),
            "results": results
        })

    def _handle_verify(self, data: Dict[str, Any]):
        cid = data.get("conjecture_id")
        var_specs = data.get("var_specs")
        domain_constraints = data.get("domain_constraints", [])
        negated_claims = data.get("negated_claims", [])

        backend = MockOfflineBackend()
        engine = SMTEngine()

        t0 = time.perf_counter()
        if cid:
            form = backend.formalize_conjecture(cid)
            var_specs = form["variables"]
            domain_constraints = form["domain_constraints"]
            negated_claims = form["negated_formula"]

        if not var_specs:
            self._send_json({"error": "Must provide conjecture_id or var_specs"}, 400)
            return

        res = engine.find_counterexample(var_specs, domain_constraints, negated_claims)
        lat_ms = (time.perf_counter() - t0) * 1000

        self._send_json({
            "status": res.status,
            "counterexample": res.counterexample,
            "latency_ms": round(lat_ms, 2),
            "reason_unknown": res.reason_unknown
        })

    def _handle_mcts(self, data: Dict[str, Any]):
        premises = data.get("premises", ["(x - y)*(x + y) == 0"])
        goal = data.get("goal", "(x == y) or (x == -y)")
        sims = int(data.get("simulations", 20))

        backend = MockOfflineBackend()
        prm = SymbolicPRM()
        mcts = MCTSProofSearch(backend=backend, prm=prm)
        res = mcts.search(premises, goal, num_simulations=sims)

        trajectory = [
            {"step_id": s.step_id, "text": s.text, "is_sound": s.is_sound, "score": s.prm_score}
            for s in res.best_sound_trajectory
        ]
        mermaid_code = ProofTreeVisualizer.render_mermaid_mcts(res)

        self._send_json({
            "goal_proven": res.goal_proven,
            "total_nodes": res.total_nodes,
            "nodes_pruned": res.nodes_pruned,
            "best_trajectory": trajectory,
            "mermaid": mermaid_code
        })

    def _handle_bitvectors(self, data: Dict[str, Any]):
        bv = BitVectorVerifier()
        # XOR swap
        xor_res = bv.verify_xor_swap(width=data.get("xor_width", 32))
        # Addition overflow
        ov_res = bv.verify_addition_overflow(width=data.get("ov_width", 32), signed=data.get("signed", True))
        # Power of 2
        p2_res = bv.verify_power_of_two_hack(width=data.get("p2_width", 32))

        self._send_json({
            "xor_swap": {
                "status": xor_res.status,
                "sound": xor_res.is_sound,
                "counterexample": xor_res.counterexample
            },
            "addition_overflow": {
                "status": ov_res.status,
                "overflow_detected": ov_res.is_sound,
                "witness_pair": ov_res.counterexample
            },
            "power_of_two": {
                "status": p2_res.status,
                "sound": p2_res.is_sound,
                "counterexample": p2_res.counterexample
            }
        })

    def _handle_invariants(self, data: Dict[str, Any]):
        verifier = LoopInvariantVerifier()
        inv_str = data.get("candidate_invariant", "s == (i * (i - 1)) / 2")
        report = verifier.verify_sum_n_invariant(inv_str)

        self._send_json({
            "candidate_invariant": report.candidate_invariant,
            "initiation_holds": report.initiation_holds,
            "initiation_counterexample": report.initiation_counterexample,
            "consecution_holds": report.consecution_holds,
            "consecution_counterexample": report.consecution_counterexample,
            "safety_holds": report.safety_holds,
            "safety_counterexample": report.safety_counterexample,
            "is_valid_inductive_invariant": report.is_valid_inductive_invariant
        })

    def _handle_lean(self, data: Dict[str, Any]):
        bridge = LeanBridge()
        thm_name = data.get("theorem_name", "difference_of_squares_zero")
        var_specs = data.get("var_specs", {"x": "Int", "y": "Int"})
        hypotheses = data.get("hypotheses", ["(x - y) * (x + y) = 0"])
        goal = data.get("goal", "x = y \\/ x = -y")
        export_res = bridge.export_theorem(thm_name, var_specs, hypotheses, goal)
        lean_code = export_res.lean_code if hasattr(export_res, "lean_code") else str(export_res)

        self._send_json({
            "theorem_name": thm_name,
            "lean4_code": lean_code
        })


class DashboardServer:
    """Local web server wrapper."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.httpd = None

    def start(self, blocking: bool = True):
        self.httpd = http.server.HTTPServer((self.host, self.port), DashboardRequestHandler)
        print(f"=================================================================")
        print(f" llm-z3-verifier Web Dashboard live at: http://{self.host}:{self.port}")
        print(f" REST API endpoints: /api/benchmarks, /api/run-benchmarks, /api/mcts")
        print(f"=================================================================")
        if blocking:
            try:
                self.httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down server gracefully...")
                self.httpd.server_close()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()


def start_server(host: str = "127.0.0.1", port: int = 8080, blocking: bool = True) -> DashboardServer:
    server = DashboardServer(host=host, port=port)
    server.start(blocking=blocking)
    return server
