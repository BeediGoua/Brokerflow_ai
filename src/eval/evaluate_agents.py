"""
Evaluation utilities for agent performance.

Provides basic metrics for the note parser, reviewer and summary writer.  For
the sake of brevity, only the note parser evaluation is implemented.  You
can extend this module to cover more comprehensive agent tests.
"""

from typing import List, Dict

from src.agents.note_parser import parse_note


def evaluate_note_parser(test_cases: List[Dict]) -> Dict[str, float]:
    """Evaluate note parser precision and recall on annotated examples.

    Each test case must be a dict with keys ``note`` and ``expected_flags``.

    Args:
        test_cases: List of test case dictionaries.

    Returns:
        Dictionary of overall precision, recall and F1 score.
    """
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    for case in test_cases:
        note = case["note"]
        expected = case["expected_flags"]
        predicted = parse_note(note)
        for flag, expected_value in expected.items():
            pred_value = predicted.get(flag, False)
            if expected_value and pred_value:
                true_positives += 1
            elif not expected_value and pred_value:
                false_positives += 1
            elif expected_value and not pred_value:
                false_negatives += 1
    precision = true_positives / (true_positives + false_positives + 1e-9)
    recall = true_positives / (true_positives + false_negatives + 1e-9)
    f1 = 2 * precision * recall / (precision + recall + 1e-9)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }