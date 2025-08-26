"""
Tests for ByRankStrategy (arguments) using the common testing framework.

This demonstrates how to use the argument strategy testing framework
for testing individual argument reconstruction strategies.
"""

from typing import Type

from .argument_strategy_test_framework import BaseArgumentStrategyTestSuite
from src.argdown_cotgen.strategies.arguments.by_rank import ByRankStrategy
from src.argdown_cotgen.strategies.base import BaseArgumentStrategy


class TestByRankArgumentStrategy(BaseArgumentStrategyTestSuite):
    """Test suite for ByRankStrategy (arguments)."""
    
    @property
    def strategy_class(self) -> Type[BaseArgumentStrategy]:
        return ByRankStrategy
    
    @property
    def strategy_name(self) -> str:
        return "ByRankArgumentStrategy"
    
    # Strategy-specific test cases
    
    def test_rank_based_progression(self):
        """Test that by_rank builds by adding sub-arguments in order."""
        argdown_text = """<Democracy Argument>: Why democracy is best.

(1) Democracy allows citizen participation.
(2) Citizen participation ensures government accountability.
-- from 1,2 --
(3) Democracy ensures government accountability.
(4) Government accountability prevents corruption.
-- modus ponens --
(5) Democracy prevents corruption."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Should have 6 steps based on actual output:
        # v1: Title
        # v2: Scaffold with final conclusion
        # v3: Main inference step (statements that directly lead to final conclusion)
        # v4: First sub-argument (for statement 3)
        # v5: Second sub-argument (for statement 4) - actually shows premise for statement 3
        # v6: Complete argument with all inference rules
        
        assert len(steps) == 6, f"Expected 6 steps, got {len(steps)}"
        
        # Check step progression
        
        # v1 should have title only
        assert "<Democracy Argument>" in steps[0].content
        assert "(1)" not in steps[0].content, "First step should only have title"
        
        # v2 should have scaffold with final conclusion
        assert "(2) Democracy prevents corruption" in steps[1].content
        assert "// ... premises to be added here" in steps[1].content, \
            "Second step should have scaffold structure"
        
        # v3 should have main inference (final conclusion and its immediate premises)
        main_inference_step = steps[2].content
        assert "(3) Democracy prevents corruption" in main_inference_step, \
            "Main inference should have final conclusion renumbered as (3)"
        assert "(1) Democracy ensures government accountability" in main_inference_step, \
            "Main inference should include the direct premise for final conclusion"
        
        # Check that final step has complete structure
        final_step = steps[-1].content
        assert "-- from 1,2 --" in final_step, "Final step should have first inference rule"
        assert "-- modus ponens --" in final_step, "Final step should have second inference rule"
    
    def test_consecutive_numbering(self):
        """Test that statements are renumbered consecutively in each complete step."""
        argdown_text = """<Complex Argument>: Multi-step reasoning.

(1) A leads to B.
(2) B leads to C.
-- transitivity --
(3) A leads to C.
(4) C is good.
-- modus ponens --
(5) A is good."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Check that each step has consecutive numbering (except scaffold step which has placeholders)
        for step in steps:
            lines = step.content.split('\n')
            numbered_lines = [line for line in lines if line.strip() and line.strip().startswith('(')]
            
            # Skip scaffold step (v2) which has placeholders like "(1) // ... premises"
            if any("// ..." in line for line in numbered_lines):
                continue
                
            if len(numbered_lines) > 1:
                # Extract numbers and check they're consecutive starting from 1
                numbers = []
                for line in numbered_lines:
                    if '(' in line and ')' in line:
                        try:
                            num_str = line.split('(')[1].split(')')[0]
                            numbers.append(int(num_str))
                        except (ValueError, IndexError):
                            continue
                
                if numbers:
                    numbers.sort()
                    expected_sequence = list(range(1, len(numbers) + 1))
                    assert numbers == expected_sequence, \
                        f"Step {step.version} has non-consecutive numbering: {numbers}, expected: {expected_sequence}"
    
    def test_sub_argument_integration(self):
        """Test that sub-arguments are properly integrated."""
        argdown_text = """<Integration Test>: Test sub-argument building.

(1) First premise.
(2) Second premise.
-- rule1 --
(3) Intermediate conclusion.
(4) Third premise.
-- rule2 --
(5) Final conclusion."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Find the step where statement 3 is expanded into a sub-argument
        sub_arg_step = None
        for step in steps:
            if "(1)" in step.content and "(2)" in step.content and "(3)" in step.content:
                # This step should show the sub-argument for statement 3
                if "-- rule1 --" in step.content:
                    sub_arg_step = step
                    break
        
        assert sub_arg_step is not None, "Should find a step with the sub-argument for statement 3"
        
        # The sub-argument step should have:
        # - Statements 1, 2, 3 renumbered consecutively
        # - The inference rule "rule1"
        # - Proper structure
        content_lines = [line.strip() for line in sub_arg_step.content.split('\n') if line.strip()]
        
        # Should have consecutive numbering in this sub-argument
        numbered_lines = [line for line in content_lines if line.startswith('(')]
        assert len(numbered_lines) >= 3, "Sub-argument should have at least 3 numbered statements"
        
        # Should have the inference rule
        rule_lines = [line for line in content_lines if "rule1" in line and "--" in line]
        assert len(rule_lines) > 0, "Sub-argument should include the inference rule"
