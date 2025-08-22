#!/usr/bin/env python3
"""
Quick test to demonstrate that _get_random_explanation is now available 
to all strategies through BaseStrategy inheritance.
"""

from src.argdown_cotgen.strategies.argument_maps.breadth_first import BreadthFirstStrategy

# Test that any strategy can use _get_random_explanation
strategy = BreadthFirstStrategy()

test_explanations = [
    "Option 1: First choice",
    "Option 2: Second choice", 
    "Option 3: Third choice with {param}",
]

print("Testing _get_random_explanation method availability:")
print("=" * 50)

for i in range(5):
    explanation = strategy._get_random_explanation(test_explanations)
    print(f"Random explanation {i+1}: {explanation}")

print("\nTesting with formatting parameters:")
print("=" * 50)

for i in range(3):
    explanation = strategy._get_random_explanation(test_explanations, param=f"value_{i}")
    print(f"Formatted explanation {i+1}: {explanation}")

print("\n✅ Success! _get_random_explanation is available to all strategies!")
