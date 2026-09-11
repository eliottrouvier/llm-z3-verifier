// llm-z3-verifier Web Dashboard Controller
document.addEventListener("DOMContentLoaded", () => {
  if (window.mermaid) {
    mermaid.initialize({ startOnLoad: false, theme: "dark" });
  }

  // Tab switching
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      tabs.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const target = document.getElementById("tab-" + btn.dataset.tab);
      if (target) target.classList.add("active");
    });
  });

  // Benchmark Runner
  const btnBenchmarks = document.getElementById("btn-run-benchmarks");
  if (btnBenchmarks) {
    btnBenchmarks.addEventListener("click", async () => {
      btnBenchmarks.disabled = true;
      btnBenchmarks.innerText = "Running Z3 Solvers...";
      try {
        const resp = await fetch("/api/run-benchmarks", { method: "POST" });
        const data = await resp.json();
        
        document.getElementById("stat-accuracy").innerText = data.accuracy + "%";
        document.getElementById("stat-latency").innerText = data.mean_latency_ms + " ms";

        const tbody = document.getElementById("benchmarks-tbody");
        tbody.innerHTML = "";
        data.results.forEach(item => {
          const tr = document.createElement("tr");
          const isSat = item.actual === "sat";
          const badgeClass = isSat ? "badge-sat" : "badge-unsat";
          const badgeText = isSat ? "SAT (Falsified)" : "UNSAT (Verified)";
          
          let witnessStr = "-";
          if (item.counterexample) {
            witnessStr = JSON.stringify(item.counterexample);
          } else if (item.actual === "unsat") {
            witnessStr = "Sound (Vacuous / Valid Claim)";
          }

          tr.innerHTML = `
            <td><code>${item.id}</code></td>
            <td><span class="badge-tag">${item.domain}</span></td>
            <td><strong>${item.name}</strong></td>
            <td><code>${item.expected}</code></td>
            <td><span class="badge-tag ${badgeClass}">${badgeText}</span></td>
            <td><code>${item.latency_ms} ms</code></td>
            <td style="font-family: monospace; font-size: 11px;">${witnessStr}</td>
          `;
          tbody.appendChild(tr);
        });
      } catch (err) {
        console.error(err);
        alert("Error executing benchmark suite: " + err);
      } finally {
        btnBenchmarks.disabled = false;
        btnBenchmarks.innerText = "▶ Run Full Suite (Live Z3)";
      }
    });
  }

  // MCTS Search & Mermaid Renderer
  const btnMcts = document.getElementById("btn-run-mcts");
  if (btnMcts) {
    btnMcts.addEventListener("click", async () => {
      btnMcts.disabled = true;
      btnMcts.innerText = "Searching Proof Space...";
      const premises = [document.getElementById("mcts-premises").value];
      const goal = document.getElementById("mcts-goal").value;
      const sims = parseInt(document.getElementById("mcts-sims").value, 10);

      try {
        const resp = await fetch("/api/mcts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ premises, goal, simulations: sims })
        });
        const data = await resp.json();

        document.getElementById("mcts-proven").innerText = data.goal_proven ? "✅ TRUE" : "❌ FALSE";
        document.getElementById("mcts-nodes").innerText = data.total_nodes;
        document.getElementById("mcts-pruned").innerText = data.nodes_pruned;

        const container = document.getElementById("mcts-mermaid-container");
        if (data.mermaid && window.mermaid) {
          const { svg } = await mermaid.render("mcts-svg-" + Date.now(), data.mermaid);
          container.innerHTML = svg;
        } else {
          container.innerHTML = `<pre>${data.mermaid}</pre>`;
        }
      } catch (err) {
        console.error(err);
        alert("Error running MCTS: " + err);
      } finally {
        btnMcts.disabled = false;
        btnMcts.innerText = "⚡ Run MCTS Simulation";
      }
    });
  }

  // Bit-Vector Verifier
  const btnBitvectors = document.getElementById("btn-run-bitvectors");
  if (btnBitvectors) {
    btnBitvectors.addEventListener("click", async () => {
      btnBitvectors.disabled = true;
      btnBitvectors.innerText = "Verifying QF_BV...";
      try {
        const resp = await fetch("/api/bitvectors", { method: "POST" });
        const data = await resp.json();

        document.getElementById("bv-xor-res").innerHTML = `
          <div><strong>Soundness:</strong> ${data.xor_swap.sound ? "<span class="text-emerald">PROVEN (No counterexample in 2^32)</span>" : "<span class="text-crimson">FALSIFIED</span>"}</div>
          <div><strong>Status:</strong> ${data.xor_swap.status.toUpperCase()}</div>
        `;

        document.getElementById("bv-overflow-res").innerHTML = `
          <div><strong>Overflow Detected:</strong> <span class="text-crimson">YES (Sound Countermodel)</span></div>
          <div><strong>Witness Pair:</strong> x = ${data.addition_overflow.witness_pair.x}, y = ${data.addition_overflow.witness_pair.y}</div>
        `;

        document.getElementById("bv-p2-res").innerHTML = `
          <div><strong>Soundness:</strong> ${data.power_of_two.sound ? "<span class="text-emerald">PROVEN (Sound over 2^32)</span>" : "<span class="text-crimson">FALSIFIED</span>"}</div>
          <div><strong>Status:</strong> ${data.power_of_two.status.toUpperCase()}</div>
        `;
      } catch (err) {
        console.error(err);
      } finally {
        btnBitvectors.disabled = false;
        btnBitvectors.innerText = "⚡ Run Bit-Vector Solvers";
      }
    });
  }

  // Loop Invariants
  const btnInvariants = document.getElementById("btn-run-invariants");
  if (btnInvariants) {
    btnInvariants.addEventListener("click", async () => {
      btnInvariants.disabled = true;
      btnInvariants.innerText = "Checking Induction...";
      const cand = document.getElementById("inv-candidate").value;
      try {
        const resp = await fetch("/api/invariants", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ candidate_invariant: cand })
        });
        const d = await resp.json();

        document.getElementById("inv-init-body").innerHTML = d.initiation_holds
          ? "<span class="text-emerald">✓ HOLDS (Base case s=0, i=0 satisfies I)</span>"
          : `<span class="text-crimson">✗ FAILED! Counterexample: ${JSON.stringify(d.initiation_counterexample)}</span>`;

        document.getElementById("inv-cons-body").innerHTML = d.consecution_holds
          ? "<span class="text-emerald">✓ HOLDS (Inductive step I(i,s) => I(i+1, s+i))</span>"
          : `<span class="text-crimson">✗ FAILED! Counterexample: ${JSON.stringify(d.consecution_counterexample)}</span>`;

        document.getElementById("inv-safe-body").innerHTML = d.safety_holds
          ? "<span class="text-emerald">✓ HOLDS (Post-condition guaranteed upon exit)</span>"
          : `<span class="text-crimson">✗ FAILED! Counterexample: ${JSON.stringify(d.safety_counterexample)}</span>`;

        const verdict = document.getElementById("inv-verdict");
        if (d.is_valid_inductive_invariant) {
          verdict.innerHTML = "<span class="text-emerald">🎉 CERTIFIED INDUCTIVE INVARIANT: All 3 Hoare conditions formally satisfied!</span>";
        } else {
          verdict.innerHTML = "<span class="text-crimson">⚠️ INVALID INVARIANT: One or more inductive clauses falsified by Z3.</span>";
        }
      } catch (err) {
        console.error(err);
      } finally {
        btnInvariants.disabled = false;
        btnInvariants.innerText = "⚡ Verify Candidate Invariant";
      }
    });
  }

  // Lean 4 Bridge
  const btnLean = document.getElementById("btn-gen-lean");
  if (btnLean) {
    btnLean.addEventListener("click", async () => {
      btnLean.disabled = true;
      btnLean.innerText = "Synthesizing Lean 4...";
      try {
        const resp = await fetch("/api/lean", { method: "POST" });
        const d = await resp.json();
        document.getElementById("lean-code-output").innerText = d.lean4_code;
      } catch (err) {
        console.error(err);
      } finally {
        btnLean.disabled = false;
        btnLean.innerText = "⚡ Generate Lean 4 Theorem";
      }
    });
  }
});
