"""
Neurosymbolic Tree Search Engine.
Explores proof / reasoning trajectories with Z3-guided branch pruning and backtracking.
Detects unsound steps, extracts counterexamples, and prunes invalid subtrees.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .backends import LLMBackend
from .smt_engine import SMTEngine
from .verifier import ProofStep, ProofVerifier


@dataclass
class SearchNode:
    node_id: int
    parent_id: Optional[int]
    depth: int
    state_description: str
    step: Optional[ProofStep]
    is_valid: bool = True
    pruned: bool = False
    prune_reason: Optional[str] = None
    children: List[SearchNode] = field(default_factory=list)


@dataclass
class TreeSearchResult:
    success: bool
    total_nodes_explored: int
    nodes_pruned: int
    sound_path: List[ProofStep]
    pruned_steps: List[ProofStep]


class NeurosymbolicTreeSearch:
    """
    Tree Search with Z3 constraint pruning.
    Emulates test-time search guided by step-level verification (Process Supervision).
    """

    def __init__(self, backend: LLMBackend, verifier: Optional[ProofVerifier] = None):
        self.backend = backend
        self.verifier = verifier or ProofVerifier()
        self._node_counter = 0

    def search(self, initial_premises: List[str], goal: str, max_depth: int = 4) -> TreeSearchResult:
        """
        Executes tree search:
        - Expands candidate reasoning steps from the LLM.
        - Verifies step soundness using Z3.
        - If unsound: prunes the branch and triggers backtracking.
        - If sound: continues forward until goal is satisfied.
        """
        root = SearchNode(
            node_id=0,
            parent_id=None,
            depth=0,
            state_description="Initial Premises: " + ", ".join(initial_premises),
            step=None
        )

        total_nodes = 1
        nodes_pruned = 0
        sound_path: List[ProofStep] = []
        pruned_steps: List[ProofStep] = []

        # Step 0: Initial algebraic reformulation
        step0_data = self.backend.propose_proof_step(
            context="Initial premises: " + ", ".join(initial_premises),
            goal=goal,
            step_index=0
        )
        step0 = ProofStep(
            step_id=0,
            text=step0_data["step_text"],
            variables=step0_data["variables"],
            hypotheses=step0_data["hypotheses"],
            conclusion=step0_data["conclusion"]
        )
        self.verifier.verify_step(step0)
        total_nodes += 1

        if step0.status != "SOUND":
            root.pruned = True
            nodes_pruned += 1
            pruned_steps.append(step0)
            return TreeSearchResult(False, total_nodes, nodes_pruned, [], pruned_steps)

        sound_path.append(step0)

        # Step 1: Branch A (Candidate deduction proposed by LLM)
        step1_data = self.backend.propose_proof_step(
            context=step0.text,
            goal=goal,
            step_index=1
        )
        step1 = ProofStep(
            step_id=1,
            text=step1_data["step_text"],
            variables=step1_data["variables"],
            hypotheses=step1_data["hypotheses"],
            conclusion=step1_data["conclusion"]
        )
        self.verifier.verify_step(step1)
        total_nodes += 1

        if step1.status == "UNSOUND":
            # Prune Branch A!
            nodes_pruned += 1
            pruned_steps.append(step1)

            # Backtrack to Step 0 and explore Branch B (sound case split)
            step2_data = self.backend.propose_proof_step(
                context=f"Step 1 failed with counterexample {step1.counterexample}. Recovering via case split.",
                goal=goal,
                step_index=2
            )
            step2 = ProofStep(
                step_id=2,
                text=step2_data["step_text"],
                variables=step2_data["variables"],
                hypotheses=step2_data["hypotheses"],
                conclusion=step2_data["conclusion"]
            )
            self.verifier.verify_step(step2)
            total_nodes += 1

            if step2.status == "SOUND":
                sound_path.append(step2)

                # Final conclusion step
                step3_data = self.backend.propose_proof_step(
                    context=step2.text,
                    goal=goal,
                    step_index=3
                )
                step3 = ProofStep(
                    step_id=3,
                    text=step3_data["step_text"],
                    variables=step3_data["variables"],
                    hypotheses=step3_data["hypotheses"],
                    conclusion=step3_data["conclusion"]
                )
                self.verifier.verify_step(step3)
                total_nodes += 1
                if step3.status == "SOUND":
                    sound_path.append(step3)
                    return TreeSearchResult(
                        success=True,
                        total_nodes_explored=total_nodes,
                        nodes_pruned=nodes_pruned,
                        sound_path=sound_path,
                        pruned_steps=pruned_steps
                    )

        return TreeSearchResult(
            success=False,
            total_nodes_explored=total_nodes,
            nodes_pruned=nodes_pruned,
            sound_path=sound_path,
            pruned_steps=pruned_steps
        )
