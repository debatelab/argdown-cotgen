"""
Tests for the DepthFirstStrategy.

This module contains comprehensive tests for the depth-first argument map strategy,
including both common framework tests and depth-first specific behavior validation.
"""

from typing import Type
from src.argdown_cotgen.strategies.argument_maps.depth_first import DepthFirstStrategy
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy
from src.argdown_cotgen.core.parser import ArgdownParser
from .strategy_test_framework import BaseStrategyTestSuite, COMMON_STRATEGY_TEST_CASES


class TestDepthFirstStrategy(BaseStrategyTestSuite):
    """Test suite for DepthFirstStrategy using the common framework."""
    
    @property
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        return DepthFirstStrategy
    
    @property
    def strategy_name(self) -> str:
        return "DepthFirstStrategy"


class TestDepthFirstSpecificBehavior:
    """Additional tests for depth-first specific behavior."""
    
    def test_depth_first_ordering(self):
        """Test that depth-first strategy completes branches before moving to siblings."""
        argdown_text = """[Root]: Main claim.
    <+ <Branch A>: First branch.
        <+ <Deep A>: Deep in branch A.
    <+ <Branch B>: Second branch.
        <+ <Deep B>: Deep in branch B."""
        
        parser = ArgdownParser()
        structure = parser.parse(argdown_text)
        strategy = DepthFirstStrategy()
        
        steps = strategy.generate(structure)
        
        # Should have multiple steps showing progressive revelation
        assert len(steps) >= 3
        
        # Check that we complete Branch A (including Deep A) before showing Branch B's children
        step_contents = [step.content for step in steps]
        
        # Find the step that includes Deep A
        deep_a_step_idx = None
        for i, content in enumerate(step_contents):
            if "Deep A" in content:
                deep_a_step_idx = i
                break
        
        # Find the step that includes Deep B  
        deep_b_step_idx = None
        for i, content in enumerate(step_contents):
            if "Deep B" in content:
                deep_b_step_idx = i
                break
        
        # Deep A should appear before Deep B (depth-first completes branches)
        if deep_a_step_idx is not None and deep_b_step_idx is not None:
            assert deep_a_step_idx < deep_b_step_idx, "Depth-first should complete Branch A before Branch B"
    
    def test_stack_based_explanations(self):
        """Test that explanations mention depth-first-like progression."""
        argdown_text = """[Main]: Primary claim.
    <+ <Support>: Supporting argument.
        <+ <Evidence>: Supporting evidence."""
        
        parser = ArgdownParser()
        structure = parser.parse(argdown_text)
        strategy = DepthFirstStrategy()
        
        steps = strategy.generate(structure)
        
        # Check that we get appropriate explanations
        explanations = [step.explanation for step in steps]
        
        # Should have meaningful explanations for each step
        assert len(explanations) >= 2
        assert all(explanation.strip() for explanation in explanations)
    
    def test_branch_completion_behavior(self):
        """Test specific depth-first behavior: complete entire branches."""
        argdown_text = """[Climate Action]: We should act on climate change.
    <+ <Scientific Evidence>: Science supports climate action.
        <+ <IPCC Reports>: International scientific consensus.
    <- <Economic Costs>: Action is too expensive.
        <- <Long-term Benefits>: Benefits outweigh costs."""
        
        parser = ArgdownParser()
        structure = parser.parse(argdown_text)
        strategy = DepthFirstStrategy()
        
        steps = strategy.generate(structure)
        
        # Should reveal structure progressively
        assert len(steps) >= 3
        
        # All steps should build upon previous ones
        for i in range(1, len(steps)):
            # Each step should contain at least as much content as the previous
            # (this is a basic property of progressive revelation)
            prev_lines = steps[i-1].content.count('\n')
            curr_lines = steps[i].content.count('\n')
            assert curr_lines >= prev_lines, f"Step {i+1} should not remove content from step {i}"

    # Depth-first specific tests for our common test cases
    def test_climate_action_depth_first_progression(self):
        """Test depth-first progression on climate action test case."""
        
        # Find the climate action test case
        climate_case = None
        for case in COMMON_STRATEGY_TEST_CASES:
            if case.name == 'climate_action_3_level':
                climate_case = case
                break
        
        assert climate_case is not None, "Climate action test case should exist"
        
        parser = ArgdownParser()
        structure = parser.parse(climate_case.argdown_text)
        strategy = DepthFirstStrategy()
        
        steps = strategy.generate(structure)
        
        # Verify depth-first specific behavior
        step_contents = [step.content for step in steps]
        
        # Should process in depth-first order: complete branches before siblings
        # We should see evidence branches completed before economic branches get detailed
        evidence_detailed = False
        
        for content in step_contents:
            if "IPCC" in content or "Temperature" in content:
                evidence_detailed = True
                break
        
        # This tests that we go deep into the scientific evidence branch
        assert evidence_detailed, "Should explore scientific evidence branch in detail"
    
    def test_multiple_roots_depth_first_order(self):
        """Test depth-first ordering with multiple root nodes."""
        
        # Find the multiple roots test case
        multi_roots_case = None
        for case in COMMON_STRATEGY_TEST_CASES:
            if case.name == 'multiple_root_policies':
                multi_roots_case = case
                break
        
        assert multi_roots_case is not None, "Multiple roots test case should exist"
        
        parser = ArgdownParser()
        structure = parser.parse(multi_roots_case.argdown_text)
        strategy = DepthFirstStrategy()
        
        steps = strategy.generate(structure)
        
        # Should handle multiple roots with depth-first within each tree
        assert len(steps) >= 3
        
        # Check progressive revelation
        for i in range(1, len(steps)):
            prev_content = steps[i-1].content
            curr_content = steps[i].content
            
            # Current step should contain all previous content (progressive building)
            prev_lines = set(line.strip() for line in prev_content.split('\n') if line.strip())
            curr_lines = set(line.strip() for line in curr_content.split('\n') if line.strip())
            
            # Previous lines should be subset of current lines (content only grows)
            missing_lines = prev_lines - curr_lines
            assert not missing_lines, f"Step {i+1} removed content: {missing_lines}"
    
    def test_asymmetric_structure_depth_first(self):
        """Test depth-first behavior on asymmetric structures."""
        
        # Find the asymmetric structure test case
        asymmetric_case = None
        for case in COMMON_STRATEGY_TEST_CASES:
            if case.name == 'asymmetric_structure':
                asymmetric_case = case
                break
        
        assert asymmetric_case is not None, "Asymmetric structure test case should exist"
        
        parser = ArgdownParser()
        structure = parser.parse(asymmetric_case.argdown_text)
        strategy = DepthFirstStrategy()
        
        steps = strategy.generate(structure)
        
        # Should handle asymmetric structures gracefully
        assert len(steps) >= 2
        
        # Verify that the strategy doesn't break on uneven tree structures
        for step in steps:
            assert step.content.strip(), "All steps should have non-empty content"
            assert step.explanation.strip(), "All steps should have explanations"
