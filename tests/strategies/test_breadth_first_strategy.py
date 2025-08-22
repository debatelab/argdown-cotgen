"""
Tests for BreadthFirstStrategy using the common testing framework.

This file serves as a REFERENCE IMPLEMENTATION for new strategy test files.
See strategy_test_framework.py docstring for detailed documentation.

CRITICAL: Use @property methods (not @pytest.fixture) for strategy_class and strategy_name!
"""

from typing import Type

from .strategy_test_framework import BaseStrategyTestSuite
from src.argdown_cotgen.strategies.argument_maps.breadth_first import BreadthFirstStrategy
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy


class TestBreadthFirstStrategy(BaseStrategyTestSuite):
    """Test suite for BreadthFirstStrategy."""
    
    @property
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        return BreadthFirstStrategy
    
    @property
    def strategy_name(self) -> str:
        return "BreadthFirstStrategy"
    
    # Strategy-specific test cases
    
    def test_breadth_first_ordering(self):
        """Test that breadth-first ordering is followed correctly."""
        argdown_text = """[Root]: Main claim.
    <+ <A>: Support A.
        <+ <A1>: Deep support for A.
        <+ <A2>: Another deep support for A.
    <+ <B>: Support B.
        <+ <B1>: Deep support for B."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # In breadth-first, we should see:
        # 1. Root
        # 2. A and B (siblings) before A1, A2, B1 (deeper levels)
        # 3. Then A1, A2, B1
        
        # Check that A and B appear before A1, A2, B1 in the step progression
        step_contents = [step.content for step in steps]
        
        # Find steps where A and B first appear (should be early)
        a_appears = next(i for i, content in enumerate(step_contents) if "<A>" in content)
        b_appears = next(i for i, content in enumerate(step_contents) if "<B>" in content)
        
        # Find steps where deep supports first appear (should be later)
        try:
            a1_appears = next(i for i, content in enumerate(step_contents) if "<A1>" in content)
            a2_appears = next(i for i, content in enumerate(step_contents) if "<A2>" in content)
            b1_appears = next(i for i, content in enumerate(step_contents) if "<B1>" in content)
            
            # Breadth-first: siblings before children
            assert a_appears < a1_appears, "A should appear before A1 (breadth-first order)"
            assert a_appears < a2_appears, "A should appear before A2 (breadth-first order)"
            assert b_appears < b1_appears, "B should appear before B1 (breadth-first order)"
            
        except StopIteration:
            # It's possible deep supports appear in later steps
            pass
    
    def test_queue_processing_explanations(self):
        """Test that explanations reference queue-style processing."""
        argdown_text = """[Main]: Main claim.
    <+ <Support1>: First support.
    <+ <Support2>: Second support."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Look for explanations that indicate breadth-first processing
        explanations = [step.explanation.lower() for step in steps]
        
        # Should have some explanations mentioning processing/examining nodes
        processing_explanations = [exp for exp in explanations 
                                 if any(word in exp for word in ["processing", "examine", "check", "expand", "consider"])]
        
        assert len(processing_explanations) > 0, f"Should have explanations about processing nodes. Got: {explanations}"
    
    def test_immediate_children_expansion(self):
        """Test that only immediate children are revealed at each step."""
        argdown_text = """[Root]: Main claim.
    <+ <Level1>: First level.
        <+ <Level2>: Second level.
            <+ <Level3>: Third level."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Check that deeper levels don't appear prematurely
        step_contents = [step.content for step in steps]
        
        # Level2 should not appear until after Level1 has been processed
        level1_step = next((i for i, content in enumerate(step_contents) if "<Level1>" in content), -1)
        level2_step = next((i for i, content in enumerate(step_contents) if "<Level2>" in content), len(steps))
        level3_step = next((i for i, content in enumerate(step_contents) if "<Level3>" in content), len(steps))
        
        if level1_step >= 0 and level2_step < len(steps):
            assert level1_step < level2_step, "Level1 should appear before Level2"
            
        if level2_step < len(steps) and level3_step < len(steps):
            assert level2_step < level3_step, "Level2 should appear before Level3"
    
    # Breadth-first specific tests based on breadth_first_examples.md
    
    def test_climate_action_breadth_first_progression(self):
        """Test the climate action example follows breadth-first order."""
        argdown_text = """[Climate Action]: We should act on climate change.
    <+ <Scientific Evidence>: Science supports climate action.
        <+ <IPCC Reports>: International scientific consensus.
        <+ <Temperature Data>: Rising global temperatures.
    <- <Economic Costs>: Action is too expensive.
        <- <Long-term Benefits>: Benefits outweigh costs.
            <+ <Health Savings>: Reduced healthcare costs."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Verify breadth-first progression matches expected pattern
        step_contents = [step.content for step in steps]
        
        # Find when each key node first appears (root is always in step 0)
        
        scientific_step = next((i for i, content in enumerate(step_contents) 
                               if "<Scientific Evidence>" in content), -1)
        economic_step = next((i for i, content in enumerate(step_contents) 
                             if "<Economic Costs>" in content), -1)
        
        ipcc_step = next((i for i, content in enumerate(step_contents) 
                         if "<IPCC Reports>" in content), -1)
        temp_step = next((i for i, content in enumerate(step_contents) 
                         if "<Temperature Data>" in content), -1)
        
        benefits_step = next((i for i, content in enumerate(step_contents) 
                            if "<Long-term Benefits>" in content), -1)
        
        health_step = next((i for i, content in enumerate(step_contents) 
                          if "<Health Savings>" in content), -1)
        
        # Breadth-first order: siblings before children
        if scientific_step >= 0 and economic_step >= 0:
            # Scientific Evidence and Economic Costs are siblings (children of Climate Action)
            # They should appear in the same step (when Climate Action is processed)
            assert abs(scientific_step - economic_step) <= 1, \
                "Scientific Evidence and Economic Costs should appear together as siblings"
        
        if ipcc_step >= 0 and temp_step >= 0 and benefits_step >= 0:
            # IPCC and Temperature are children of Scientific Evidence
            # Benefits is child of Economic Costs
            # All should appear after their parents but order may vary
            assert ipcc_step > scientific_step, "IPCC Reports should appear after Scientific Evidence"
            assert temp_step > scientific_step, "Temperature Data should appear after Scientific Evidence"
            assert benefits_step > economic_step, "Long-term Benefits should appear after Economic Costs"
        
        if health_step >= 0 and benefits_step >= 0:
            assert health_step > benefits_step, "Health Savings should appear after Long-term Benefits"
    
    def test_multiple_roots_breadth_first_order(self):
        """Test multiple root claims are processed in breadth-first order."""
        argdown_text = """[Policy A]: We should implement policy A.
    <+ <Benefit 1>: First major benefit.
    <+ <Benefit 2>: Second major benefit.
[Policy B]: We should implement policy B instead.
    <- <Conflict>: Policies conflict with each other.
        <+ <Resource Limitation>: Limited resources available.
    <+ <Alternative Benefit>: Different advantages."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        step_contents = [step.content for step in steps]
        
        # Both roots should appear in first step
        assert "[Policy A]" in steps[0].content, "Policy A should be in first step"
        assert "[Policy B]" in steps[0].content, "Policy B should be in first step"
        
        # Find when children first appear
        benefit1_step = next((i for i, content in enumerate(step_contents) 
                             if "<Benefit 1>" in content), -1)
        benefit2_step = next((i for i, content in enumerate(step_contents) 
                             if "<Benefit 2>" in content), -1)
        conflict_step = next((i for i, content in enumerate(step_contents) 
                            if "<Conflict>" in content), -1)
        alternative_step = next((i for i, content in enumerate(step_contents) 
                               if "<Alternative Benefit>" in content), -1)
        resource_step = next((i for i, content in enumerate(step_contents) 
                            if "<Resource Limitation>" in content), -1)
        
        # Children of Policy A should appear when Policy A is processed
        if benefit1_step >= 0 and benefit2_step >= 0:
            assert abs(benefit1_step - benefit2_step) <= 1, \
                "Benefits should appear together when Policy A is processed"
        
        # Children of Policy B should appear when Policy B is processed  
        if conflict_step >= 0 and alternative_step >= 0:
            assert abs(conflict_step - alternative_step) <= 1, \
                "Conflict and Alternative Benefit should appear together when Policy B is processed"
        
        # Resource Limitation should appear after Conflict (its parent)
        if resource_step >= 0 and conflict_step >= 0:
            assert resource_step > conflict_step, \
                "Resource Limitation should appear after Conflict"
    
    def test_asymmetric_structure_breadth_first(self):
        """Test asymmetric structure follows breadth-first traversal."""
        argdown_text = """[Main Claim]: Central argument.
    <+ <Support>: Supporting evidence.
        <+ <Deep Support>: Deeper evidence.
            <+ <Deepest>: Very deep support.
    <- <Simple Attack>: Basic objection.
    <+ <Another Support>: Additional evidence."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        step_contents = [step.content for step in steps]
        
        # Find when nodes appear
        support_step = next((i for i, content in enumerate(step_contents) 
                           if "<Support>" in content and "Another" not in content and "Deep" not in content), -1)
        attack_step = next((i for i, content in enumerate(step_contents) 
                          if "<Simple Attack>" in content), -1)
        another_step = next((i for i, content in enumerate(step_contents) 
                           if "<Another Support>" in content), -1)
        deep_step = next((i for i, content in enumerate(step_contents) 
                        if "<Deep Support>" in content), -1)
        deepest_step = next((i for i, content in enumerate(step_contents) 
                           if "<Deepest>" in content), -1)
        
        # All immediate children of Main Claim should appear together
        if support_step >= 0 and attack_step >= 0 and another_step >= 0:
            max_immediate = max(support_step, attack_step, another_step)
            min_immediate = min(support_step, attack_step, another_step)
            assert max_immediate - min_immediate <= 1, \
                "All immediate children should appear in the same processing step"
        
        # Deep Support should appear after Support (its parent)
        if deep_step >= 0 and support_step >= 0:
            assert deep_step > support_step, "Deep Support should appear after Support"
        
        # Deepest should appear after Deep Support (its parent)
        if deepest_step >= 0 and deep_step >= 0:
            assert deepest_step > deep_step, "Deepest should appear after Deep Support"
    
    # Override step count validation for breadth-first specific behavior
    def _validate_step_count(self, steps, test_case):
        """Breadth-first may have different step counts than other strategies."""
        actual = len(steps)
        
        # Breadth-first might need different step counts due to queue processing
        if test_case.name == "deep_nesting":
            # Breadth-first might process each level separately
            assert 3 <= actual <= 6, f"Deep nesting should have 3-6 steps for breadth-first, got {actual}"
        elif test_case.name == "climate_action_3_level":
            # Complex 3-level structure with multiple branches
            assert 4 <= actual <= 7, f"Climate action should have 4-7 steps for breadth-first, got {actual}"
        elif test_case.name == "multiple_root_policies":
            # Multiple roots with varied children
            assert 3 <= actual <= 6, f"Multiple policies should have 3-6 steps for breadth-first, got {actual}"
        elif test_case.name == "asymmetric_structure":
            # Asymmetric with deep chain
            assert 3 <= actual <= 6, f"Asymmetric structure should have 3-6 steps for breadth-first, got {actual}"
        else:
            # Use default validation for other cases
            super()._validate_step_count(steps, test_case)
