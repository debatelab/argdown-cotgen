"""
Common testing framework for argument strategies.

This module provides a unified testing framework that can be used by all
argument strategy implementations to ensure consistent behavior and
comprehensive test coverage.

USAGE GUIDE FOR NEW ARGUMENT STRATEGY IMPLEMENTATIONS:
======================================================

To create a test suite for a new argument strategy, follow this exact pattern:

1. Create a test file: tests/strategies/test_your_argument_strategy.py

2. Use this template structure:

```python
from typing import Type
from src.argdown_cotgen.strategies.arguments.your_strategy import YourStrategy
from src.argdown_cotgen.strategies.base import BaseArgumentStrategy
from .argument_strategy_test_framework import BaseArgumentStrategyTestSuite

class TestYourArgumentStrategy(BaseArgumentStrategyTestSuite):
    '''Test suite for YourStrategy using the common framework.'''
    
    @property
    def strategy_class(self) -> Type[BaseArgumentStrategy]:
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
- MUST inherit from BaseArgumentStrategyTestSuite
- MUST implement strategy_class and strategy_name as @property methods
- DO NOT use @pytest.fixture for strategy/strategy_class
- The property approach ensures pytest collects all common test cases
- This gives you comprehensive test coverage for argument reconstruction

AUTOMATIC TEST COVERAGE:
========================
By inheriting from BaseArgumentStrategyTestSuite, your strategy automatically gets:
- Common argument test cases with various structures
- Framework tests (wrong structure type, empty lines, etc.)
- Content reconstruction validation
- Quality validation (step structure, explanations, versions)
- Abortion functionality testing
- Step count validation with flexible ranges

For complete documentation, examples, and troubleshooting, see:
docs/STRATEGY_TESTING_FRAMEWORK.md
"""

from pprint import pprint
import pytest
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type, Union
from dataclasses import dataclass

from src.argdown_cotgen.core.parser import ArgdownParser
from src.argdown_cotgen.strategies.base import BaseArgumentStrategy
from src.argdown_cotgen.core.models import ArgumentStructure, CotStep, ArgumentMapStructure


@dataclass
class ArgumentStrategyTestCase:
    """Test case for argument strategy testing."""
    name: str
    argdown_text: str
    description: str
    expected_step_count: Union[int, Dict[str, int]]
    expected_features: Dict[str, Any]
    abortion_rate: float = 0.0


# Common test cases that all argument strategies should handle
COMMON_ARGUMENT_STRATEGY_TEST_CASES = [
    ArgumentStrategyTestCase(
        name="simple_argument",
        argdown_text="""<Simple Argument>: A basic argument.

(1) First premise.
(2) Second premise.
-----
(3) Conclusion.""",
        description="Basic argument with premises and conclusion",
        expected_step_count={
            # v1: title, v2: scaffold, v3: premises
            "ByFeatureStrategy": 3,
            # v1: title, v2: scaffold, v3: main inference
            "ByRankStrategy": 3    
        },
        expected_features={
            "has_title": True,
            "has_premises": True,
            "has_conclusion": True,
            "has_separator": True,
            "statement_count": 3
        }
    ),
    
    ArgumentStrategyTestCase(
        name="argument_with_inference_rule",
        argdown_text="""<Logical Argument>: Modus ponens example.

(1) If it rains, the streets get wet.
(2) It is raining.
-- modus ponens --
(3) The streets are wet.""",
        description="Argument with explicit inference rule",
        expected_step_count={
            # v1: title, v2: scaffold, v3: premises, v4: inference rules
            "ByFeatureStrategy": 4,  
            # v1: title, v2: scaffold, v3: premises, v4: inference rules
            "ByRankStrategy": 4     
        },
        expected_features={
            "has_title": True,
            "has_inference_rule": True,
            "has_premises": True,
            "has_conclusion": True,
            "statement_count": 3
        }
    ),
    
    ArgumentStrategyTestCase(
        name="complex_argument",
        argdown_text="""<Democracy Argument>: Why democracy is best.

(1) Democracy allows citizen participation.
(2) Citizen participation ensures government accountability.
-- from 1,2 --
(3) Democracy ensures government accountability.
(4) Government accountability prevents corruption.
-- modus ponens --
(5) Democracy prevents corruption.""",
        description="Complex argument with multiple inference steps",
        expected_step_count={
            # v1: title, v2: scaffold, v3: premises, v4: intermediate conclusions, v5: inference rules
            "ByFeatureStrategy": 5,  
            # v1: title, v2: scaffold, v3: main inference, v4: 1st intermediate step, v5: inference rules
            "ByRankStrategy": 5      
        },
        expected_features={
            "has_title": True,
            "has_multiple_inferences": True,
            "has_intermediate_conclusions": True,
            "statement_count": 5
        }
    ),
    
    ArgumentStrategyTestCase(
        name="with_yaml_data",
        argdown_text="""<Confidence Argument>: Argument with confidence values.

(1) Climate change is happening. {confidence: 0.95}
(2) Climate change causes extreme weather. {confidence: 0.8}
-----
(3) We will see more extreme weather. {confidence: 0.76}""",
        description="Argument with YAML inline data",
        expected_step_count={
            # v1: title, v2: scaffold, v3: premises, v4: add YAML data
            "ByFeatureStrategy": 4,  
            # v1: title, v2: scaffold, v3: main inference, v4: add YAML data
            "ByRankStrategy": 4
        },
        expected_features={
            "has_yaml": True,
            "has_title": True,
            "statement_count": 3
        }
    ),
    
    ArgumentStrategyTestCase(
        name="with_comments",
        argdown_text="""<Evidence Argument>: Argument with evidence notes.

(1) Studies show X. // Latest research
(2) X implies Y. // Logical connection
-----
(3) Therefore Y. // Main conclusion""",
        description="Argument with comments",
        expected_step_count={
            # v1: title, v2: premises, v3: conclusion, v4: add comments
            "ByFeatureStrategy": 4,  
            # v1: title, v2: scaffold, v3: main inference, v4: add comments
            "ByRankStrategy": 4
        },
        expected_features={
            "has_comments": True,
            "has_title": True,
            "statement_count": 3
        }
    ),
    
    ArgumentStrategyTestCase(
        name="yaml_and_comments",
        argdown_text="""<Mixed Argument>: Argument with both YAML and comments.

(1) Economic growth increases prosperity. {strength: high} // Well-established
(2) Prosperity improves quality of life. {strength: medium} // Generally true
-----
(3) Economic growth improves quality of life. {strength: medium} // Conclusion""",
        description="Argument with both YAML and comments",
        expected_step_count={
            # v1: title, v2: premises, v3: conclusion, v4: add YAML, v5: add comments
            "ByFeatureStrategy": 5,  
            # v1: title, v2: scaffold, v3: main inference, v4: add YAML, v5: add comments
            "ByRankStrategy": 5
        },
        expected_features={
            "has_yaml": True,
            "has_comments": True,
            "has_title": True,
            "statement_count": 3
        }
    ),
    
    ArgumentStrategyTestCase(
        name="title_only",
        argdown_text="""<Simple Claim>: Just a claim without premises.

(1) This is the only statement.
-----
(2) This is the conclusion.""",
        description="Minimal argument structure (edge case)",
        expected_step_count={
            # v1: title, v2: scaffold, v3: premises
            "ByFeatureStrategy": 3,
            # v1: title, v2: scaffold, v3: main inference
            "ByRankStrategy": 3
        },
        expected_features={
            "has_title": True,
            "minimal_structure": True,
            "statement_count": 2
        }
    ),
    
    ArgumentStrategyTestCase(
        name="no_title_argument",
        argdown_text="""(1) Technology improves efficiency.
(2) Efficiency reduces costs.
-----
(3) Technology reduces costs.""",
        description="Argument without title",
        expected_step_count={
            # v1: scaffold, v2: premises
            "ByFeatureStrategy": 2,
            # v1: scaffold, v2: main inference
            "ByRankStrategy": 2
        },
        expected_features={
            "no_title": True,
            "has_premises": True,
            "has_conclusion": True,
            "statement_count": 3
        }
    ),
    
    ArgumentStrategyTestCase(
        name="multi_step_inference",
        argdown_text="""<Chain Argument>: Multi-step reasoning chain.

(1) A leads to B.
(2) B leads to C.
-- transitivity --
(3) A leads to C.
(4) C is desirable.
-- modus ponens --
(5) A is desirable.""",
        description="Argument with chained inferences",
        expected_step_count={
            # v1: title, v2: scaffold, v3: premises, v4: intermediate conclusions, v5: inference rules
            "ByFeatureStrategy": 5,
            # v1: title, v2: scaffold, v3: main inference, v4: 1st intermediate step, v5: inference rules
            "ByRankStrategy": 5
        },
        expected_features={
            "has_title": True,
            "has_chain_inference": True,
            "has_multiple_rules": True,
            "statement_count": 5
        }
    ),
    
    ArgumentStrategyTestCase(
        name="three_step_inference_with_seps",
        argdown_text="""(1) A leads to B.
(2) B leads to C.
-----
(3) A leads to C.
(4) C leads to D.
-----
(5) A leads to D.
(6) D is desirable.
-----
(7) A is desirable.""",
        description="Argument with chained inferences",
        expected_step_count={
            # v1: scaffold, v2: premises, v3: intermediate conclusions, v4: inference rules
            "ByFeatureStrategy": 3,
            # v1: scaffold, v2: main inference, v3: 1st intermediate step, v4: 2nd intermediate step, 
            "ByRankStrategy": 4
        },
        expected_features={
            "has_title": False,
            "has_chain_inference": True,
            "has_multiple_rules": False,
            "statement_count": 7
        }
    ),

    ArgumentStrategyTestCase(
        name="asymmetric_premises",
        argdown_text="""<Unbalanced Argument>: Different numbers of premises per inference.

(1) First major premise.
(2) Second major premise.
(3) Third major premise.
-- from 1,2,3 --
(4) Intermediate conclusion.
(5) Additional premise.
-- simple inference --
(6) Final conclusion.""",
        description="Argument with asymmetric premise structure",
        expected_step_count={
            # v1: title, v2: scaffold, v3: premises, v4: intermediate conclusions, v5: inference rules
            "ByFeatureStrategy": 5,
            # v1: title, v2: scaffold, v3: main inference, v4: 1st intermediate step, v5: inference rules
            "ByRankStrategy": 5
        },
        expected_features={
            "asymmetric": True,
            "has_title": True,
            "has_multiple_inferences": True,
            "statement_count": 6
        }
    ),
    
    ArgumentStrategyTestCase(
        name="complex_logical_argument",
        argdown_text="""(1) If someone is an occasional purchaser of CHI shampoo, then they are not a frequent consumer of Dial soap, or an occasional purchaser of Dove soap.
(2) If someone infrequently (or never) consumes Dial soap, then they don't own an Alterna Haircare shampoo.
(3) If someone occasionally purchases Dove soap, then they don't own an Alterna Haircare shampoo.
--
with generalized dilemma [negation variant] from (1) (2) (3)
--
(4) If someone occasionally purchases CHI shampoo, then they don't own an Alterna Haircare shampoo.
(5) If someone doesn't always buy Pears soap, then they occasionally purchase CHI shampoo.
--
with hypothetical syllogism [negation variant] from (4) (5)
--
(6) If someone doesn't always buy Pears soap, then they don't own an Alterna Haircare shampoo.
--
with instantiation [transposition] from (6)
--
(7) If Michael owns an Alterna Haircare shampoo, then Michael always buys Pears soap.
(8) Eusebio owns a Garnier shampoo or Earnest doesn't own a Paul Mitchell soap.
(9) If Eusebio owns a Garnier shampoo, then Michael owns an Alterna Haircare shampoo.
(10) If Earnest doesn't own a Paul Mitchell soap, then Michael owns an Alterna Haircare shampoo.
--
with case analysis [negation variant] from (8) (9) (10)
--
(11) Michael owns an Alterna Haircare shampoo.
--
with modus ponens from (7) (11)
--
(12) Michael always buys Pears soap.""",
        description="Complex logical argument with multiple inference rules and steps",
        expected_step_count={
            # v1: scaffold, v2: premises, v3: intermediate conclusions, v4: inference rules
            "ByFeatureStrategy": 4,
            # v1: scaffold, v2: main inference, v3: 1st intermediate step, v4: 2nd intermediate step, v5: 3rd intermediate step, v6: 4th intermediate step, v7: inference rules
            "ByRankStrategy": 7
        },
        expected_features={
            "no_title": True,
            "has_multiple_inferences": True,
            "has_intermediate_conclusions": True,
            "has_complex_logic": True,
            "has_named_inference_rules": True,
            "statement_count": 12
        }
    )
]


class BaseArgumentStrategyTestSuite(ABC):
    """
    Abstract base class for argument strategy test suites.
    
    This class provides comprehensive testing for argument strategies by running
    a suite of common test cases and validations. All argument strategy implementations 
    should inherit from this class to ensure consistent quality and behavior.
    
    INHERITANCE REQUIREMENTS:
    ========================
    Subclasses MUST implement these abstract properties:
    
    @property
    def strategy_class(self) -> Type[BaseArgumentStrategy]:
        '''Return the strategy class to test.'''
        return YourArgumentStrategyClass
    
    @property  
    def strategy_name(self) -> str:
        '''Return human-readable name of the strategy.'''
        return "YourArgumentStrategyName"
    
    CRITICAL: Use @property, NOT @pytest.fixture!
    The property approach ensures pytest properly collects all parametrized tests.
    
    AUTOMATIC TEST COVERAGE:
    =======================
    By inheriting from this class, your strategy automatically gets:
    
    1. Common Test Cases (test_common_argument_cases):
       - simple_argument: Basic premise-conclusion structure
       - argument_with_inference_rule: Explicit inference rules
       - complex_argument: Multi-step inference chains
       - with_yaml_data: YAML inline data handling
       - with_comments: Comment preservation
       - yaml_and_comments: Combined YAML and comments
       - title_only: Title-only arguments (edge case)
       - no_title_argument: Arguments without titles
       - multi_step_inference: Chained reasoning
       - asymmetric_premises: Unbalanced premise structures
    
    2. Framework Tests:
       - test_wrong_structure_type: Rejects ArgumentMapStructure (not ArgumentStructure)
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
    
    EXAMPLE IMPLEMENTATION:
    ======================
    See tests/strategies/test_by_rank_argument_strategy.py for a complete example.
    """
    
    @property
    @abstractmethod
    def strategy_class(self) -> Type[BaseArgumentStrategy]:
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
    
    @pytest.mark.parametrize("test_case", COMMON_ARGUMENT_STRATEGY_TEST_CASES, ids=lambda tc: tc.name)
    def test_common_argument_cases(self, test_case: ArgumentStrategyTestCase):
        """Test strategy with common argument test cases."""
        structure = self.parser.parse(test_case.argdown_text)
        assert isinstance(structure, ArgumentStructure), f"Expected ArgumentStructure for {test_case.name}"
        
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
        """Test that strategy rejects non-Argument structures."""
        # Use argument map syntax to get ArgumentMapStructure
        argdown_text = """[Main Claim]: This is a claim.
    <+ <Support>: Supporting evidence."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        with pytest.raises(ValueError, match=f"{self.strategy_class.__name__} requires an ArgumentStructure"):
            self.strategy.generate(structure, abortion_rate=0.0)
    
    def test_empty_lines_handling(self):
        """Test that empty lines are properly handled."""
        argdown_text = """<Test Argument>: Test with empty lines.

(1) First premise.

(2) Second premise.

-----

(3) Conclusion."""
        
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
        argdown_text = """<Test Argument>: Test argument.

(1) First premise.
(2) Second premise.
-----
(3) Conclusion."""
        
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
        argdown_text = """<Test Argument>: Test for abortion.

(1) First premise.
(2) Second premise.
-----
(3) Conclusion."""
    
        structure = self.parser.parse(argdown_text)
        
        # Test with maximum abortion rate
        steps = self.strategy.generate(structure, abortion_rate=1.0)
        
        # Should still produce at least one step
        assert len(steps) >= 1
        
        # 1. Check that the LAST step is not aborted
        last_step = steps[-1]
        assert not self._is_step_aborted(last_step), \
            "Last step should never be aborted - must end with clean content"
        
        # 2. Check that with abortion_rate=1.0, at least one abortion occurs somewhere
        abortion_found = any(self._is_step_aborted(step) for step in steps)
        assert abortion_found, \
            "With abortion_rate=1.0, at least one abortion should occur"

    def _is_step_aborted(self, step: CotStep) -> bool:
        """
        Check if a step contains abortion by looking for ABORTION_COMMENTS.
        
        This uses the actual ABORTION_COMMENTS from base.py to robustly detect
        abortion without relying on fragile string matching.
        """
        from src.argdown_cotgen.strategies.base import AbortionMixin
        
        # Check if step content contains any abortion comment
        step_content_lower = step.content.lower()
        
        for abort_comment in AbortionMixin.ABORTION_COMMENTS:
            # Extract the key part of the comment (without "//" prefix that gets added)
            comment_core = abort_comment.lower().strip()
            if comment_core in step_content_lower:
                return True
        
        return False
    
    # === Strategy-Specific Hooks ===
    
    def _validate_step_count(self, steps: List[CotStep], test_case: ArgumentStrategyTestCase):
        """
        Validate step count with strict expectations.
        
        Supports both single expected count (int) and strategy-specific counts (Dict[str, int]).
        Strategy-specific counts are now required and checked strictly without flexibility.
        """
        expected_count = test_case.expected_step_count
        actual = len(steps)
        
        if isinstance(expected_count, dict):
            # Strategy-specific expected counts - strict validation
            strategy_name = self.strategy_class.__name__
            if strategy_name in expected_count:
                expected = expected_count[strategy_name]
                # Strict check - no flexibility
                assert actual == expected, \
                    f"Expected exactly {expected} steps for {test_case.name} with {self.strategy_name}, got {actual}"
            else:
                # Strategy not specified in dict - this is now an error
                available_strategies = list(expected_count.keys())
                assert False, \
                    f"Strategy {strategy_name} not found in expected_step_count dict for {test_case.name}. " \
                    f"Available strategies: {available_strategies}. Please add {strategy_name} to the expected counts."
        else:
            # Single expected count for all strategies - keep some flexibility for backward compatibility
            expected = expected_count
            assert expected - 1 <= actual <= expected + 2, \
                f"Expected ~{expected} steps for {test_case.name} with {self.strategy_name}, got {actual}"
    
    def _validate_features(self, steps: List[CotStep], structure: ArgumentStructure, 
                          expected: Dict[str, Any]):
        """Validate that expected features are present in the generated steps."""
        if expected.get("has_yaml"):
            assert any("{" in step.content for step in steps), "YAML data should appear in some step"
            
        if expected.get("has_comments"):
            assert any("//" in step.content for step in steps), "Comments should appear in some step"
            
        if expected.get("has_title"):
            assert any("<" in step.content and ">" in step.content for step in steps), \
                "Title should appear in some step"
            
        if expected.get("title_only"):
            # For title-only arguments, should have minimal structure
            assert len(structure.numbered_statements) == 0, "Title-only should have no numbered statements"
            
        if expected.get("minimal_structure"):
            # For minimal arguments, should have very few statements
            assert len(structure.numbered_statements) <= 2, "Minimal structure should have few statements"
            
        if expected.get("has_premises"):
            numbered_statements = structure.numbered_statements
            premises = [stmt for stmt in numbered_statements if stmt.is_premise]
            assert len(premises) > 0, "Should have premise statements"
            
        if expected.get("has_conclusion"):
            numbered_statements = structure.numbered_statements
            conclusions = [stmt for stmt in numbered_statements if stmt.is_conclusion]
            assert len(conclusions) > 0, "Should have conclusion statements"
            
        if expected.get("has_inference_rule"):
            assert any("--" in step.content and "--" in step.content for step in steps), \
                "Inference rule should appear in some step"
            
        if expected.get("statement_count"):
            expected_count = expected["statement_count"]
            actual_count = len(structure.numbered_statements)
            assert actual_count == expected_count, \
                f"Expected {expected_count} numbered statements, got {actual_count}"
    
    def _validate_step_quality(self, steps: List[CotStep]):
        """Validate general quality of generated steps."""
        assert len(steps) >= 1, "Should generate at least one step"
        
        # Check that first step is always v1
        assert steps[0].version == "v1", f"First step should always be v1, got {steps[0].version}"
        
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
        
        # Check consecutive numbering within each step
        self._validate_consecutive_numbering(steps)
        
        # Check consecutive version numbering across steps
        self._validate_consecutive_version_numbering(steps)
    
    def _validate_consecutive_numbering(self, steps: List[CotStep]):
        """
        Validate that statements within each step are consecutively numbered starting from 1.
        
        This is a critical requirement for argument strategies to ensure that each step
        presents a coherent argument structure with proper numbering.
        """
        import re
        
        for step in steps:
            lines = step.content.split('\n')
            numbered_lines = [line for line in lines if line.strip() and re.match(r'^\s*\(\d+\)', line.strip())]
            
            if len(numbered_lines) <= 1:
                continue  # Skip steps with 0 or 1 numbered statements
            
            # Extract numbers from numbered lines
            numbers = []
            for line in numbered_lines:
                match = re.search(r'\((\d+)\)', line.strip())
                if match:
                    numbers.append(int(match.group(1)))
            
            if numbers:
                # Check that numbers are consecutive starting from 1
                numbers.sort()
                expected_sequence = list(range(1, len(numbers) + 1))
                
                if numbers != expected_sequence:
                    # Provide detailed error message
                    formatted_lines = [f"    {line.strip()}" for line in numbered_lines]
                    step_preview = '\n'.join(formatted_lines)
                    
                    assert False, (
                        f"Step {step.version} has non-consecutive statement numbering.\n"
                        f"Found numbers: {numbers}\n"
                        f"Expected: {expected_sequence}\n"
                        f"Numbered lines in step:\n{step_preview}"
                    )

    def _validate_consecutive_version_numbering(self, steps: List[CotStep]):
        """
        Validate that step versions are consecutive starting from v1.
        
        This is critical to ensure strategy implementation doesn't skip steps
        or have version numbering bugs.
        
        Args:
            steps: Generated CoT steps from the strategy
            
        Raises:
            AssertionError: If versions are not consecutive starting from v1
        """
        if not steps:
            return
        
        for i, step in enumerate(steps):
            expected_version = f"v{i + 1}"
            actual_version = step.version
            
            assert actual_version == expected_version, (
                f"Step {i + 1} has version '{actual_version}', expected '{expected_version}'. "
                f"This indicates a bug in strategy version numbering - steps should be "
                f"consecutively numbered starting from v1."
            )

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
        - Statement numbering errors
        - Inference rule formatting issues
        
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
        
        pprint(steps)

        final_content = steps[-1].content.strip()
        
        print("\n--- Original Argdown Text ---")
        print(original_text)
        print("\n--- Final Step Content ---")
        print(final_content)

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

def run_argument_strategy_comparison(strategies: List[BaseArgumentStrategy], 
                                   test_case: ArgumentStrategyTestCase) -> Dict[str, List[CotStep]]:
    """
    Run multiple argument strategies on the same test case for comparison.
    
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


def assert_argument_strategies_differ(strategy_results: Dict[str, List[CotStep]]):
    """
    Assert that different argument strategies produce different step sequences.
    
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
