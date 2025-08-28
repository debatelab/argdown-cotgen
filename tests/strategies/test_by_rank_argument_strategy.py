"""
Tests for ByRankStrategy (arguments) using the common testing framework.

This demonstrates how to use the argument strategy testing framework
for testing individual argument reconstruction strategies.
"""

from typing import Type

from .argument_strategy_test_framework import BaseArgumentStrategyTestSuite
from src.argdown_cotgen.strategies.arguments.by_rank import ByRankStrategy
from src.argdown_cotgen.strategies.base import BaseArgumentStrategy
from src.argdown_cotgen.core.models import ArgumentStructure


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
        
        # Should have 5 steps based on actual output:
        # v1: Title
        # v2: Scaffold with final conclusion
        # v3: Main inference step (statements that directly lead to final conclusion)
        # v4: First sub-argument (for statement 3)
        # v5: Complete argument with all inference rules
        
        assert len(steps) == 5, f"Expected 5 steps, got {len(steps)}"
        
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

    def test_intermediate_conclusion_notes(self):
        """Test that intermediate conclusions get annotated with notes in the main inference step."""
        argdown_text = """<Note Test>: Test intermediate conclusion notes.

(1) Basic premise one.
(2) Basic premise two.
-- from (1) and (2) --
(3) Intermediate conclusion.
(4) Another basic premise.
-- from (3) and (4) --
(5) Final conclusion."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Find the main inference step (v3)
        main_inference_step = None
        for step in steps:
            if step.version == "v3":
                main_inference_step = step
                break
        
        assert main_inference_step is not None, "Should find v3 main inference step"
        
        # The main inference step should include premises that directly support the final conclusion
        # In this case, statement 3 (intermediate conclusion) and statement 4 should be the direct premises
        content = main_inference_step.content
        
        # Check that statement 3 (the intermediate conclusion) gets a note
        lines = content.split('\n')
        statement_3_line = None
        for line in lines:
            # Look for the line containing "Intermediate conclusion" (content of statement 3)
            if "Intermediate conclusion" in line and line.strip().startswith('('):
                statement_3_line = line
                break
        
        assert statement_3_line is not None, "Should find the intermediate conclusion in main inference step"
        
        # Check that it has a note (// comment)
        assert "//" in statement_3_line, "Intermediate conclusion should have a note comment"
        
        # Verify the note contains one of the expected phrases
        expected_note_phrases = [
            "not sure here",
            "need to revisit this", 
            "might be an intermediate conclusion",
            "revisit later and add supporting premises if required",
            "🤔 Is this a conclusion?"
        ]
        
        note_found = any(phrase in statement_3_line for phrase in expected_note_phrases)
        assert note_found, f"Note should contain one of the expected phrases. Line: {statement_3_line}"
        
        # Also verify that basic premises (like statement 4) don't get notes
        statement_4_line = None
        for line in lines:
            if "Another basic premise" in line and line.strip().startswith('('):
                statement_4_line = line
                break
        
        if statement_4_line:
            # If statement 4 appears in this step, it should NOT have a note
            # (unless it's also an intermediate conclusion, which it's not in this test)
            assert "//" not in statement_4_line, "Basic premises should not have notes"

    def test_intermediate_conclusion_detection_method(self):
        """Test the _is_intermediate_conclusion method directly."""
        argdown_text = """<Detection Test>: Test intermediate conclusion detection.

(1) First premise.
(2) Second premise.
-- inference --
(3) Intermediate conclusion.
(4) Third premise.
-- final inference --
(5) Final conclusion."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentStructure), "Should be ArgumentStructure for this test"
        arg_structure = structure  # Type is now narrowed to ArgumentStructure
        
        # Cast strategy to the correct type to access the specific method
        rank_strategy = self.strategy
        assert isinstance(rank_strategy, ByRankStrategy), "Strategy should be ByRankStrategy"
        
        # Get all numbered statements
        numbered_statements = rank_strategy._get_numbered_statements(arg_structure)
        statements_by_number = {stmt.statement_number: stmt for stmt in numbered_statements}
        
        # Test each statement
        assert not rank_strategy._is_intermediate_conclusion(arg_structure, statements_by_number[1]), \
            "Statement 1 should not be intermediate conclusion (it's a premise)"
        assert not rank_strategy._is_intermediate_conclusion(arg_structure, statements_by_number[2]), \
            "Statement 2 should not be intermediate conclusion (it's a premise)"
        assert rank_strategy._is_intermediate_conclusion(arg_structure, statements_by_number[3]), \
            "Statement 3 should be intermediate conclusion (derived by inference, not final)"
        assert not rank_strategy._is_intermediate_conclusion(arg_structure, statements_by_number[4]), \
            "Statement 4 should not be intermediate conclusion (it's a premise)"
        assert not rank_strategy._is_intermediate_conclusion(arg_structure, statements_by_number[5]), \
            "Statement 5 should not be intermediate conclusion (it's the final conclusion)"
