import pytest
from src.dataset_generator import SyntheticPRMDatasetGenerator


def test_synthetic_prm_generation():
    gen = SyntheticPRMDatasetGenerator(seed=42)
    trajs = gen.generate_dataset(num_samples=4)
    assert len(trajs) == 4

    sound_trajs = [t for t in trajs if not t.has_mutation]
    flawed_trajs = [t for t in trajs if t.has_mutation]

    assert len(sound_trajs) == 2
    assert len(flawed_trajs) == 2

    # Check sound trajectory
    for t in sound_trajs:
        for s in t.steps:
            assert s.prm_label == 1.0
            assert s.is_sound is True
            assert s.counterexample is None

    # Check flawed trajectory
    for t in flawed_trajs:
        assert t.first_flawed_step_index is not None
        flawed_step = t.steps[t.first_flawed_step_index]
        assert flawed_step.prm_label == -1.0
        assert flawed_step.is_sound is False
        assert flawed_step.counterexample is not None
