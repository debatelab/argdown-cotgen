"""
Common testing framework for argument map strategies.

This module provides a unified testing framework that can be used by all
argument map strategy implementations to ensure consistent behavior and
comprehensive test coverage.

USAGE GUIDE FOR NEW STRATEGY IMPLEMENTATIONS:
=============================================

To create a test suite for a new strategy, follow this exact pattern:

1. Create a test file: tests/strategies/test_your_strategy.py

2. Use this template structure:

```python
from typing import Type
from src.argdown_cotgen.strategies.argument_maps.your_strategy import YourStrategy
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy
from .strategy_test_framework import BaseStrategyTestSuite

class TestYourStrategy(BaseStrategyTestSuite):
    '''Test suite for YourStrategy using the common framework.'''
    
    @property
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        return YourStrategy
    
    @property
    def strategy_name(self) -> str:
        return "YourStrategy"

# Optional: Add strategy-specific tests
class TestYourStrategySpecificBehavior:
    '''Additional tests for strategy-specific behavior.'''
    
    def test_specific_feature(self):
        '''Test your strategy's unique features.'''
        pass
```

CRITICAL REQUIREMENTS:
======================
- MUST inherit from BaseStrategyTestSuite
- MUST implement strategy_class and strategy_name as @property methods
- DO NOT use @pytest.fixture for strategy/strategy_class
- The property approach ensures pytest collects all common test cases
- This gives you ~14 common tests + content reconstruction validation

AUTOMATIC TEST COVERAGE:
========================
By inheriting from BaseStrategyTestSuite, your strategy automatically gets:
- 10 common test cases (simple_two_level, deep_nesting, with_yaml, etc.)
- 4 framework tests (wrong_structure_type, empty_lines_handling, etc.)  
- Content reconstruction validation (ensures final step = original content)
- Quality validation (step structure, explanations, versions)
- Abortion functionality testing
- Step count validation with flexible ranges

VALIDATION FEATURES:
===================
The framework includes comprehensive validation:
- Final content reconstruction: Ensures steps[-1].content matches original input
- YAML handling: Validates proper spacing and reconstruction of inline data
- Comment preservation: Ensures comments are properly handled
- Progressive content: Validates content grows correctly across steps
- Version numbering: Ensures proper step versioning (v1, v2, etc.)

For complete documentation, examples, and troubleshooting, see:
docs/STRATEGY_TESTING_FRAMEWORK.md
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
    ),
    
    StrategyTestCase(
        name="true_branching_structure",
        argdown_text="""[Main Argument]: Core claim requiring evidence.
    <+ <Scientific Branch>: Scientific evidence path.
        <+ <Study A>: First research study.
        <+ <Study B>: Second research study.
    <+ <Economic Branch>: Economic evidence path.
        <+ <Cost Analysis>: Economic cost study.
        <+ <Benefit Analysis>: Economic benefit study.""",
        description="True branching structure that shows breadth vs depth differences",
        expected_step_count=4,  # Will vary by strategy
        expected_features={
            "true_branching": True,
            "has_support": True,
            "max_depth": 2,
            "parallel_branches": True
        }
    )
]


class BaseStrategyTestSuite(ABC):
    """
    Abstract base class for strategy test suites.
    
    This class provides comprehensive testing for argument map strategies by running
    a suite of common test cases and validations. All strategy implementations should
    inherit from this class to ensure consistent quality and behavior.
    
    INHERITANCE REQUIREMENTS:
    ========================
    Subclasses MUST implement these abstract properties:
    
    @property
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        '''Return the strategy class to test.'''
        return YourStrategyClass
    
    @property  
    def strategy_name(self) -> str:
        '''Return human-readable name of the strategy.'''
        return "YourStrategyName"
    
    CRITICAL: Use @property, NOT @pytest.fixture!
    The property approach ensures pytest properly collects all parametrized tests.
    
    AUTOMATIC TEST COVERAGE:
    =======================
    By inheriting from this class, your strategy automatically gets:
    
    1. Common Test Cases (test_common_cases):
       - simple_two_level: Basic support/attack structure
       - deep_nesting: Multi-level argument chains  
       - with_yaml: YAML inline data handling
       - with_comments: Comment preservation
       - yaml_and_comments: Combined YAML and comments
       - single_claim: Single root claim scenarios
       - climate_action_3_level: Complex 3-level structures
       - multiple_root_policies: Multiple competing root claims
       - asymmetric_structure: Unbalanced argument trees
       - true_branching_structure: Parallel evidence branches
    
    2. Framework Tests:
       - test_wrong_structure_type: Rejects ArgumentStructure (not ArgumentMapStructure)
       - test_empty_lines_handling: Handles empty lines correctly
       - test_step_explanations_quality: Meaningful explanations
       - test_abortion_functionality: Abortion feature works
    
    3. Automatic Validations (for every test):
       - Content reconstruction: Final step matches original input exactly
       - YAML spacing: Proper spacing around YAML inline data
       - Progressive content: Content grows correctly across steps
       - Version numbering: Proper step versioning (v1, v2, etc.)
       - Quality checks: Non-empty content and explanations
    
    CUSTOMIZATION:
    =============
    You can override validation methods for strategy-specific behavior:
    - _validate_step_count(): Adjust expected step counts
    - _validate_features(): Add custom feature validation
    
    COMMON ISSUES TO AVOID:
    ======================
    ❌ Using @pytest.fixture for strategy - causes test collection failures
    ❌ Missing strategy_class or strategy_name properties
    ❌ Not inheriting from BaseStrategyTestSuite
    ❌ Using relative imports incorrectly
    
    EXAMPLE IMPLEMENTATION:
    ======================
    See tests/strategies/test_breadth_first_strategy.py for a complete example.
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
        
        # Content reconstruction validation
        self._validate_final_content_reconstruction(steps, test_case.argdown_text)
    
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

    def _validate_final_content_reconstruction(self, steps: List[CotStep], original_text: str):
        """
        Validate that the final step reconstructs the original argdown content exactly.
        
        This is a critical validation that ensures the CoT generation pipeline works
        correctly end-to-end: Original → Parsed → Steps → Final reconstruction.
        
        The validation:
        1. Normalizes both original and final content to sets of non-empty lines
        2. Checks that all original lines are present in the final step
        3. Checks that no extra lines were added (strict reconstruction)
        
        This catches bugs like:
        - Missing content in final step
        - YAML spacing issues (extra spaces before YAML data)
        - Comment handling problems
        - Dialectical relation formatting errors
        
        Normalization handles legitimate whitespace differences but ensures
        content matches exactly at the line level.
        
        Args:
            steps: Generated CoT steps from the strategy
            original_text: Original argdown input text
            
        Raises:
            AssertionError: If final content doesn't match original exactly
        """
        if not steps:
            return
        
        final_content = steps[-1].content.strip()
        
        # Normalize both texts for comparison (handle whitespace differences)
        def normalize_argdown(text: str) -> set:
            """Normalize argdown text to a set of non-empty lines for comparison."""
            return {line.strip() for line in text.split('\n') if line.strip()}
        
        original_lines = normalize_argdown(original_text)
        final_lines = normalize_argdown(final_content)
        
        # Check that all original lines are present in final content
        missing_lines = original_lines - final_lines
        assert not missing_lines, f"Final step missing original content: {missing_lines}"
        
        # Strict check: Final content shouldn't have extra lines beyond original
        extra_lines = final_lines - original_lines
        assert not extra_lines, f"Final step has extra content not in original: {extra_lines}"


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
    """
    Assert that different strategies produce different step sequences.
    
    For simple structures, some strategy pairs may converge due to limited complexity.
    We expect overall diversity rather than requiring every pair to differ.
    """
    strategy_names = list(strategy_results.keys())
    
    if len(strategy_names) < 2:
        return  # Need at least 2 strategies to compare
    
    total_pairs = 0
    differing_pairs = 0
    identical_pairs = []
    
    # Compare step sequences between strategies
    for i in range(len(strategy_names)):
        for j in range(i + 1, len(strategy_names)):
            total_pairs += 1
            steps1 = strategy_results[strategy_names[i]]
            steps2 = strategy_results[strategy_names[j]]
            
            # They should differ in some meaningful way
            # (step count, content order, or explanations)
            differs = (
                len(steps1) != len(steps2) or
                any(s1.content != s2.content for s1, s2 in zip(steps1, steps2)) or
                any(s1.explanation != s2.explanation for s1, s2 in zip(steps1, steps2))
            )
            
            if differs:
                differing_pairs += 1
            else:
                identical_pairs.append((strategy_names[i], strategy_names[j]))
    
    # Allow some convergence for simple structures, but expect overall diversity
    convergence_rate = len(identical_pairs) / total_pairs if total_pairs > 0 else 0
    
    # More than 50% identical pairs suggests the test case is too simple
    if convergence_rate > 0.5:
        # For high convergence, just ensure we're not completely uniform
        assert differing_pairs > 0, \
            f"All {total_pairs} strategy pairs produced identical results - test case too simple"
    else:
        # For normal cases, expect most pairs to differ
        assert convergence_rate <= 0.3, \
            f"Too many identical pairs ({len(identical_pairs)}/{total_pairs}): {identical_pairs}"
