#!/usr/bin/env python3
"""
Example 12: SMT-Guided Synthetic PRM Training Dataset Generation.
Demonstrates:
1. Automated generation of sound multi-step deduction trajectories (+1.0).
2. Injection of controlled mathematical mutations (division by zero, inequality squaring errors).
3. Automated Z3 formal certification and counterexample extraction (-1.0).
4. Exporting to HuggingFace / OpenAI JSONL format.
"""

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.dataset_generator import SyntheticPRMDatasetGenerator


def main():
    print("=" * 75)
    print("Example 12: Automated SMT-Oracle Synthetic PRM Dataset Generation")
    print("=" * 75)

    gen = SyntheticPRMDatasetGenerator(seed=1337)
    dataset = gen.generate_dataset(num_samples=6)

    output_file = "benchmarks/synthetic_prm_dataset.jsonl"
    gen.export_jsonl(dataset, output_file)

    print(f"Generated {len(dataset)} reasoning trajectories.")
    print(f"Saved to: {output_file}\n")

    print("Sample Trajectory Preview:")
    with open(output_file, "r") as f:
        for idx, line in enumerate(f):
            if idx >= 2:
                break
            entry = json.loads(line)
            print(f"\n--- Trajectory [{entry['trajectory_id']}] ---")
            print(f"Problem: {entry['problem_statement']}")
            print(f"Contains Mutation? {entry['has_flaw']}")
            for step in entry["steps"]:
                lbl = step["label"]
                lbl_str = "[+1.0 SOUND]" if lbl > 0 else "[-1.0 UNSOUND]"
                print(f"  {lbl_str} Step {step['step_id']}: {step['text']}")
                if step["counterexample"]:
                    print(f"    -> Z3 Countermodel: {step['counterexample']}")

    print("\n" + "=" * 75)
    print("Ready for direct fine-tuning of Process Reward Models (PRMs).")
    print("=" * 75)


if __name__ == "__main__":
    main()
