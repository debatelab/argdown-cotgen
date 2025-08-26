"""
Tests for ByFeatureStrategy using the argument strategy testing framework.

This test file demonstrates how to use the BaseArgumentStrategyTestSuite
for testing the feature-based argument reconstruction strategy.
"""

from typing import Type

from .argument_strategy_test_framework import BaseArgumentStrategyTestSuite
from src.argdown_cotgen.strategies.arguments.by_feature import ByFeatureStrategy
from src.argdown_cotgen.strategies.base import BaseArgumentStrategy
from src.argdown_cotgen.core.parser import ArgdownParser
from src.argdown_cotgen.core.models import ArgumentStructure
from src.argdown_cotgen.core.models import ArgumentStructure


class TestByFeatureArgumentStrategy(BaseArgumentStrategyTestSuite):
    """Test suite for ByFeatureStrategy using the common framework."""
    
    @property
    def strategy_class(self) -> Type[BaseArgumentStrategy]:
        return ByFeatureStrategy
    
    @property
    def strategy_name(self) -> str:
        return "ByFeatureStrategy"


class TestByFeatureStrategySpecificBehavior:
    """Additional tests for ByFeatureStrategy-specific behavior."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ArgdownParser()
        self.strategy = ByFeatureStrategy()
    
    def test_feature_based_progression(self):
        """Test that by_feature builds by adding features in order: premises -> intermediates -> rules."""
        argdown_text = """<Environmental Argument>: We should protect the environment.

(1) Climate change causes suffering. {certainty: 0.9}
(2) We have a duty to prevent suffering. // Kantian principle
-- modus ponens --
(3) We should act against climate change.
(4) Environmental protection reduces climate change.
-- practical syllogism --
(5) We should protect the environment."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Should have 7 steps:
        # v1: Title
        # v2: Scaffold with final conclusion
        # v3: All premises (1, 2, 4)
        # v4: Intermediate conclusions (3)
        # v5: Inference rules
        # v6: YAML data
        # v7: Comments
        
        assert len(steps) == 7, f"Expected 7 steps, got {len(steps)}"
        
        # v1 should have title only
        assert "<Environmental Argument>" in steps[0].content
        assert "(1)" not in steps[0].content, "First step should only have title"
        
        # v2 should have scaffold with final conclusion
        assert "(2) We should protect the environment" in steps[1].content
        assert "// ... premises to be added here" in steps[1].content
        
        # v3 should have all premises but no intermediate conclusions
        v3_content = steps[2].content
        assert "(1) Climate change causes suffering" in v3_content
        assert "(2) We have a duty to prevent suffering" in v3_content
        assert "(3) Environmental protection reduces climate change" in v3_content  # Renumbered from original (4)
        assert "We should act against climate change" not in v3_content, "v3 should not have intermediate conclusions"
        assert "// ... intermediate conclusions to be added here" in v3_content
        
        # v4 should have premises AND intermediate conclusions
        v4_content = steps[3].content
        assert "(1) Climate change causes suffering" in v4_content
        assert "(2) We have a duty to prevent suffering" in v4_content
        assert "(3) Environmental protection reduces climate change" in v4_content  # Renumbered from original (4)
        assert "(4) We should act against climate change" in v4_content, "v4 should have intermediate conclusions"  # Renumbered from original (3)
        assert "(5) We should protect the environment" in v4_content
        
        # v4 should have proper separators
        lines = v4_content.split('\n')
        separator_indices = [i for i, line in enumerate(lines) if line.strip() == "-----"]
        assert len(separator_indices) == 2, "v4 should have exactly 2 separators"
        
        # v5 should have inference rules
        v5_content = steps[4].content
        assert "-- modus ponens --" in v5_content
        assert "-- practical syllogism --" in v5_content
        
        # v6 should have YAML data
        v6_content = steps[5].content
        assert "{certainty: 0.9}" in v6_content
        
        # v7 should have comments
        v7_content = steps[6].content
        assert "// Kantian principle" in v7_content
    
    def test_statement_classification(self):
        """Test that statements are correctly classified by feature type."""
        argdown_text = """<Test Argument>: Main conclusion.

(1) Basic premise one.
(2) Basic premise two.
-- from (1) and (2) --
(3) Intermediate conclusion.
(4) Another basic premise.
-- from (3) and (4) --
(5) Main conclusion."""
        
        structure = self.parser.parse(argdown_text)
        # Ensure we have an ArgumentStructure
        assert isinstance(structure, ArgumentStructure), "Should be an ArgumentStructure"
        
        classification = self.strategy._classify_statements_by_feature(structure)
        
        # Check premises (statements without preceding inference rules)
        premises = classification['premises']
        premise_numbers = [p.statement_number for p in premises]
        assert set(premise_numbers) == {1, 2, 4}, f"Expected premises [1, 2, 4], got {premise_numbers}"
        
        # Check intermediate conclusions (statements with preceding inference rules)
        intermediates = classification['intermediate']
        intermediate_numbers = [i.statement_number for i in intermediates]
        assert set(intermediate_numbers) == {3}, f"Expected intermediates [3], got {intermediate_numbers}"
        
        # Final conclusion should be (5)
        final_conclusion = structure.final_conclusion
        assert final_conclusion is not None, "Should have a final conclusion"
        assert final_conclusion.statement_number == 5
    
    def test_premises_step_structure(self):
        """Test that the premises step (v3) has correct structure."""
        argdown_text = """<Simple Argument>: Conclusion.

(1) First premise.
(2) Second premise.
-- inference rule --
(3) Intermediate.
(4) Third premise.
-----
(5) Conclusion."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Find v3 step
        v3_step = next(step for step in steps if step.version == "v3")
        
        # Verify key patterns are present
        content = v3_step.content
        assert "<Simple Argument>" in content
        assert "(1) First premise" in content
        assert "(2) Second premise" in content
        assert "(3) Third premise" in content  # Renumbered from original (4)
        assert "// ... intermediate conclusions to be added here" in content
        assert "(3) Intermediate" not in content, "v3 should not contain intermediate conclusions"
    
    def test_intermediate_step_structure(self):
        """Test that the intermediate conclusions step (v4) has correct structure."""
        argdown_text = """<Multi-Level Argument>: Final point.

(1) Base premise.
(2) Another base premise.
-- from (1) and (2) --
(3) First intermediate.
(4) Additional premise.
-- from (3) and (4) --
(5) Second intermediate.
-----
(6) Final point."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Find v4 step
        v4_step = next(step for step in steps if step.version == "v4")
        v4_content = v4_step.content
        
        # Should have all statements with proper separators (consecutive numbering)
        assert "(1) Base premise" in v4_content
        assert "(2) Another base premise" in v4_content
        assert "(3) Additional premise" in v4_content  # Renumbered from original (4)
        assert "(4) First intermediate" in v4_content  # Renumbered from original (3)
        assert "(5) Second intermediate" in v4_content  # Renumbered from original (5)
        assert "(6) Final point" in v4_content
        
        # Check for exactly 2 separators
        separator_count = v4_content.count("-----")
        assert separator_count == 2, f"Expected 2 separators in v4, got {separator_count}"
    
    def test_consecutive_numbering_in_feature_steps(self):
        """Test that all feature steps maintain consecutive numbering."""
        argdown_text = """<Numbering Test>: End result.

(1) First statement.
(3) Third statement.  
-- rule --
(5) Derived statement.
(7) Another statement.
-----
(9) End result."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # All feature steps should renumber consecutively
        for step in steps:
            if step.version in ["v3", "v4"]:
                # Check that statement numbers are consecutive
                content = step.content
                import re
                numbers = re.findall(r'\((\d+)\)', content)
                if len(numbers) > 1:
                    int_numbers = [int(n) for n in numbers]
                    expected = list(range(1, len(int_numbers) + 1))
                    assert int_numbers == expected, f"Non-consecutive numbering in {step.version}: {int_numbers}"
    
    def test_no_intermediate_conclusions_case(self):
        """Test behavior when there are no intermediate conclusions."""
        argdown_text = """<Simple Case>: Direct conclusion.

(1) Only premise one.
(2) Only premise two.
-----
(3) Direct conclusion."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Should skip v4 step if no intermediate conclusions
        versions = [step.version for step in steps]
        
        # v3 should exist (premises step)
        assert "v3" in versions
        
        # v4 might be skipped if no intermediate conclusions, or be minimal
        if "v4" in versions:
            v4_step = next(step for step in steps if step.version == "v4")
            # If v4 exists, it should be essentially the same as v3 or add no new numbered statements
            assert "(1) Only premise one" in v4_step.content
            assert "(2) Only premise two" in v4_step.content
            assert "(3) Direct conclusion" in v4_step.content
