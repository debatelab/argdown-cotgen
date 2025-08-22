"""
Common testing framework for argument map strategies.

This module provides a unified testing framework that can be used by all
argument map strategy implementations to ensure consistent behavior and
comprehensive test coverage.
"""

import pytest
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type
from dataclasses import dataclass

from src.argdown_cotgen.core.parser import ArgdownParser
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy
from src.argdown_cotgen.core.models import ArgumentMapStructure, CotStep, ArgumentStructure


@dataclass
class StrategyTestCase:
    """Test case for strategy testing."""
    name: str
    argdown_text: str
    description: str
    expected_step_count: int
    expected_features: Dict[str, Any]
    abortion_rate: float = 0.0


# Common test cases that all strategies should handle
COMMON_STRATEGY_TEST_CASES = [
    StrategyTestCase(
        name="simple_two_level",
        argdown_text="""[Main Claim]: The main argument.
    <+ <Support>: Supporting evidence.
    <- <Objection>: Counter-argument.""",
        description="Basic two-level argument map",
        expected_step_count=2,  # Will vary by strategy
        expected_features={
            "has_root": True,
            "has_support": True,
            "has_attack": True,
            "max_depth": 1
        }
    ),
    
    StrategyTestCase(
        name="deep_nesting",
        argdown_text="""[Root]: Main claim.
    <+ <Level1>: First level support.
        <+ <Level2>: Second level support.
            <- <Level3>: Third level objection.""",
        description="Deep nesting test",
        expected_step_count=4,  # Will vary by strategy
        expected_features={
            "max_depth": 3,
            "has_deep_nesting": True
        }
    ),
    
    StrategyTestCase(
        name="with_yaml",
        argdown_text="""[Claim]: Main claim. {confidence: 0.9}
    <+ <Support>: Evidence. {strength: high}""",
        description="Argument map with YAML data",
        expected_step_count=3,  # Base + YAML step
        expected_features={
            "has_yaml": True
        }
    ),
    
    StrategyTestCase(
        name="with_comments", 
        argdown_text="""[Claim]: Main claim. // Important note
    <+ <Support>: Evidence. // Latest data""",
        description="Argument map with comments",
        expected_step_count=3,  # Base + comments step
        expected_features={
            "has_comments": True
        }
    ),
    
    StrategyTestCase(
        name="yaml_and_comments",
        argdown_text="""[Claim]: Main claim. {conf: 0.8} // Note
    <+ <Support>: Evidence. {strength: high} // Data""",
        description="Argument map with both YAML and comments",
        expected_step_count=4,  # Base + YAML + comments steps
        expected_features={
            "has_yaml": True,
            "has_comments": True
        }
    ),
    
    StrategyTestCase(
        name="single_claim",
        argdown_text="""[Only Claim]: Just one claim.""",
        description="Single root claim only",
        expected_step_count=1,
        expected_features={
            "max_depth": 0,
            "single_claim": True
        }
    ),
    
    # Examples from breadth_first_examples.md
    StrategyTestCase(
        name="climate_action_3_level",
        argdown_text="""[Climate Action]: We should act on climate change.
    <+ <Scientific Evidence>: Science supports climate action.
        <+ <IPCC Reports>: International scientific consensus.
        <+ <Temperature Data>: Rising global temperatures.
    <- <Economic Costs>: Action is too expensive.
        <- <Long-term Benefits>: Benefits outweigh costs.
            <+ <Health Savings>: Reduced healthcare costs.""",
        description="Complex 3-level climate action argument map",
        expected_step_count=5,  # Will vary by strategy
        expected_features={
            "max_depth": 3,
            "has_support": True,
            "has_attack": True,
            "has_deep_nesting": True
        }
    ),
    
    StrategyTestCase(
        name="multiple_root_policies",
        argdown_text="""[Policy A]: We should implement policy A.
    <+ <Benefit 1>: First major benefit.
    <+ <Benefit 2>: Second major benefit.
[Policy B]: We should implement policy B instead.
    <- <Conflict>: Policies conflict with each other.
        <+ <Resource Limitation>: Limited resources available.
    <+ <Alternative Benefit>: Different advantages.""",
        description="Multiple root claims with competing policies",
        expected_step_count=4,  # Will vary by strategy
        expected_features={
            "multiple_roots": True,
            "has_support": True,
            "has_attack": True,
            "max_depth": 2
        }
    ),
    
    StrategyTestCase(
        name="asymmetric_structure",
        argdown_text="""[Main Claim]: Central argument.
    <+ <Support>: Supporting evidence.
        <+ <Deep Support>: Deeper evidence.
            <+ <Deepest>: Very deep support.
    <- <Simple Attack>: Basic objection.
    <+ <Another Support>: Additional evidence.""",
        description="Asymmetric argument structure with varied depths",
        expected_step_count=4,  # Will vary by strategy
        expected_features={
            "asymmetric": True,
            "has_support": True,
            "has_attack": True,
            "max_depth": 3
        }
    )
]


class BaseStrategyTestSuite(ABC):
    """
    Abstract base class for strategy test suites.
    
    Subclasses should inherit from this and implement the abstract methods
    to get comprehensive testing for their strategy implementation.
    """
    
    @property
    @abstractmethod
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        """Return the strategy class to test."""
        pass
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Return the human-readable name of the strategy."""
        pass
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ArgdownParser()
        self.strategy = self.strategy_class()
    
    # === Core Functionality Tests ===
    
    @pytest.mark.parametrize("test_case", COMMON_STRATEGY_TEST_CASES, ids=lambda tc: tc.name)
    def test_common_cases(self, test_case: StrategyTestCase):
        """Test strategy with common test cases."""
        structure = self.parser.parse(test_case.argdown_text)
        assert isinstance(structure, ArgumentMapStructure), f"Expected ArgumentMapStructure for {test_case.name}"
        
        steps = self.strategy.generate(structure, abortion_rate=test_case.abortion_rate)
        
        # Basic step count validation (may need strategy-specific adjustment)
        self._validate_step_count(steps, test_case)
        
        # Feature validation
        self._validate_features(steps, structure, test_case.expected_features)
        
        # Common quality checks
        self._validate_step_quality(steps)
    
    def test_wrong_structure_type(self):
        """Test that strategy rejects non-ArgumentMap structures."""
        # Use argument syntax to get ArgumentStructure
        argdown_text = """<Argument Title>
(1) Premise
----
(2) Conclusion"""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentStructure)
        
        with pytest.raises(ValueError, match=f"{self.strategy_class.__name__} requires an ArgumentMapStructure"):
            self.strategy.generate(structure, abortion_rate=0.0)
    
    def test_empty_lines_handling(self):
        """Test that empty lines are properly handled."""
        argdown_text = """[Main Claim]: The main claim.

    <+ <Support>: Supporting evidence.

        <- <Counter>: Counter-evidence."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # All steps should have clean content without consecutive empty lines
        for step in steps:
            lines = step.content.split('\n')
            for i in range(len(lines) - 1):
                if not lines[i].strip():
                    assert lines[i + 1].strip(), f"Consecutive empty lines found in step {step.version}"
    
    def test_step_explanations_quality(self):
        """Test that step explanations are meaningful and varied."""
        argdown_text = """[Root]: Main claim.
    <+ <Support1>: First support.
    <+ <Support2>: Second support."""
        
        structure = self.parser.parse(argdown_text)
        
        # Generate multiple times to test explanation variety
        explanations = []
        for _ in range(5):
            steps = self.strategy.generate(structure, abortion_rate=0.0)
            explanations.extend([step.explanation for step in steps])
        
        # Check that explanations are non-empty and varied
        assert all(exp.strip() for exp in explanations), "All explanations should be non-empty"
        assert len(set(explanations)) > 1, "Explanations should show some variety"
    
    # === Abortion Testing ===
    
    def test_abortion_functionality(self):
        """Test abortion with high abortion rate."""
        argdown_text = """[Main]: Main claim.
    <+ <Support>: Supporting evidence.
        <+ <Deep>: Deep support."""
        
        structure = self.parser.parse(argdown_text)
        
        # Test with maximum abortion rate
        steps = self.strategy.generate(structure, abortion_rate=1.0)
        
        # Should still produce at least one step
        assert len(steps) >= 1
        
        # First step should always be clean (no abortion in first step)
        assert "//" not in steps[0].explanation or "abort" not in steps[0].explanation.lower()
    
    # === Strategy-Specific Hooks ===
    
    def _validate_step_count(self, steps: List[CotStep], test_case: StrategyTestCase):
        """
        Validate step count. Override in subclasses for strategy-specific logic.
        
        Default implementation allows some flexibility around expected count.
        """
        expected = test_case.expected_step_count
        actual = len(steps)
        
        # Allow some flexibility (±1) as different strategies may vary slightly
        assert expected - 1 <= actual <= expected + 2, \
            f"Expected ~{expected} steps for {test_case.name}, got {actual}"
    
    def _validate_features(self, steps: List[CotStep], structure: ArgumentMapStructure, 
                          expected: Dict[str, Any]):
        """Validate that expected features are present in the generated steps."""
        if expected.get("has_yaml"):
            assert any("{" in step.content for step in steps), "YAML data should appear in some step"
            
        if expected.get("has_comments"):
            assert any("//" in step.content for step in steps), "Comments should appear in some step"
            
        if expected.get("has_root"):
            assert "[" in steps[0].content, "Root claim should appear in first step"
            
        if expected.get("single_claim"):
            # For single claims, all steps should have the same basic content structure
            root_content = "[" + steps[0].content.split("]")[0].split("[")[1] if "[" in steps[0].content else ""
            assert root_content, "Single claim should have identifiable root content"
    
    def _validate_step_quality(self, steps: List[CotStep]):
        """Validate general quality of generated steps."""
        assert len(steps) >= 1, "Should generate at least one step"
        
        # Check version numbering
        for i, step in enumerate(steps):
            assert step.version, f"Step {i} should have a version"
            assert step.content.strip(), f"Step {i} should have non-empty content"
            assert step.explanation.strip(), f"Step {i} should have non-empty explanation"
        
        # Check content progression (final step should have most content)
        if len(steps) > 1:
            final_line_count = len([line for line in steps[-1].content.split('\n') if line.strip()])
            first_line_count = len([line for line in steps[0].content.split('\n') if line.strip()])
            assert final_line_count >= first_line_count, "Content should generally grow across steps"


# === Utility Functions ===

def run_strategy_comparison(strategies: List[BaseArgumentMapStrategy], 
                          test_case: StrategyTestCase) -> Dict[str, List[CotStep]]:
    """
    Run multiple strategies on the same test case for comparison.
    
    Useful for ensuring strategies produce different but valid approaches.
    """
    parser = ArgdownParser()
    structure = parser.parse(test_case.argdown_text)
    
    results = {}
    for strategy in strategies:
        strategy_name = strategy.__class__.__name__
        steps = strategy.generate(structure, abortion_rate=test_case.abortion_rate)
        results[strategy_name] = steps
    
    return results


def assert_strategies_differ(strategy_results: Dict[str, List[CotStep]]):
    """Assert that different strategies produce different step sequences."""
    strategy_names = list(strategy_results.keys())
    
    if len(strategy_names) < 2:
        return  # Need at least 2 strategies to compare
    
    # Compare step sequences between strategies
    for i in range(len(strategy_names)):
        for j in range(i + 1, len(strategy_names)):
            steps1 = strategy_results[strategy_names[i]]
            steps2 = strategy_results[strategy_names[j]]
            
            # They should differ in some meaningful way
            # (step count, content order, or explanations)
            differs = (
                len(steps1) != len(steps2) or
                any(s1.content != s2.content for s1, s2 in zip(steps1, steps2)) or
                any(s1.explanation != s2.explanation for s1, s2 in zip(steps1, steps2))
            )
            
            assert differs, f"{strategy_names[i]} and {strategy_names[j]} produced identical results"
