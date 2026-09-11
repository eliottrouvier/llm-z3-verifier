"""
Proof Tree Visualizer & Graph Exporter.
Exports reasoning and proof search trees into:
1. Publication-grade Mermaid flowcharts with color-coded nodes (Valid, Pruned, Q.E.D.).
2. Structured JSON traces for downstream evaluation and dashboards.
"""

from __future__ import annotations
import json
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from .tree_search import TreeSearchResult
from .mcts_search import MCTSResult


class ProofTreeVisualizer:
    """Generates Mermaid diagrams and JSON representations of proof search trees."""

    @staticmethod
    def render_mermaid_tree_search(result: TreeSearchResult) -> str:
        """Renders a Mermaid flowchart from a TreeSearchResult."""
        lines = [
            "```mermaid",
            "flowchart TD",
            "    classDef rootStyle fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;",
            "    classDef soundStyle fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;",
            "    classDef prunedStyle fill:#ffebee,stroke:#d32f2f,stroke-width:2px;",
            "    classDef qedStyle fill:#fff8e1,stroke:#fbc02d,stroke-width:3px;",
            "",
            '    R["Initial Mathematical Premises"]:::rootStyle'
        ]

        prev_node = "R"
        for i, step in enumerate(result.sound_path):
            node_id = f"S{step.step_id}"
            escaped_text = step.text.replace('"', "'")
            lines.append(f'    {node_id}["[Step {step.step_id}] {escaped_text}"]:::soundStyle')
            lines.append(f"    {prev_node} --> {node_id}")
            prev_node = node_id

        for j, bad_step in enumerate(result.pruned_steps):
            bad_id = f"P{bad_step.step_id}"
            escaped_bad = bad_step.text.replace('"', "'")
            ce_str = str(bad_step.counterexample).replace('"', "'") if bad_step.counterexample else "Unsound"
            lines.append(f'    {bad_id}["[PRUNED Step {bad_step.step_id}] {escaped_bad}<br/><b>Counterexample:</b> {ce_str}"]:::prunedStyle')
            # Link from the step before it
            lines.append(f"    S0 -.->|Unsound Jump| {bad_id}")

        if result.success:
            lines.append('    QED["<b>Q.E.D. (Formally Verified by Z3)</b>"]:::qedStyle')
            lines.append(f"    {prev_node} ==> QED")

        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def render_mermaid_mcts(result: MCTSResult) -> str:
        """Renders a Mermaid flowchart from an MCTSResult."""
        lines = [
            "```mermaid",
            "flowchart TD",
            "    classDef rootStyle fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;",
            "    classDef soundStyle fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;",
            "    classDef prunedStyle fill:#ffebee,stroke:#d32f2f,stroke-width:2px;",
            "    classDef qedStyle fill:#fff8e1,stroke:#fbc02d,stroke-width:3px;",
            "",
            '    R["Theorem Root State"]:::rootStyle'
        ]

        prev = "R"
        for step in result.best_sound_trajectory:
            nid = f"M{step.step_id}"
            escaped = step.text.replace('"', "'")
            lines.append(f'    {nid}["[Verified Step {step.step_id}] {escaped}"]:::soundStyle')
            lines.append(f"    {prev} --> {nid}")
            prev = nid

        for k, ce in enumerate(result.counterexamples_found):
            ce_id = f"CE_{k}"
            ce_text = str(ce).replace('"', "'")
            lines.append(f'    {ce_id}["[Branch Pruned by PRM]<br/>Countermodel: {ce_text}"]:::prunedStyle')
            lines.append(f"    R -.->|Falsified by Z3| {ce_id}")

        if result.goal_proven:
            lines.append('    QED["<b>Theorem Proven (MCTS + Z3 Soundness)</b>"]:::qedStyle')
            lines.append(f"    {prev} ==> QED")

        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def export_json(result: Any, filepath: str) -> None:
        """Exports any search result object to JSON."""
        data = asdict(result)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
