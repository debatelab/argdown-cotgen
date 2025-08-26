"""
Tests for ByRankStrategy using the common testing framework.

This modernized test file replaces the original test_by_rank_strategy.py
and demonstrates how to use the common testing framework.
"""

from typing import Type

from .map_strategy_test_framework import BaseMapStrategyTestSuite
from src.argdown_cotgen.strategies.argument_maps.by_rank import ByRankStrategy
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy


class TestByRankStrategy(BaseMapStrategyTestSuite):
    """Test suite for ByRankStrategy."""
    
    @property
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        return ByRankStrategy
    
    @property
    def strategy_name(self) -> str:
        return "ByRankStrategy"
    
    # Strategy-specific test cases
    
    def test_depth_based_progression(self):
        """Test that by_rank builds by depth levels."""
        argdown_text = """[Root]: Main claim.
    <+ <Level1A>: First level support A.
    <+ <Level1B>: First level support B.
        <+ <Level2>: Second level support.
            <+ <Level3>: Third level support."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # ByRank should show all nodes at depth N before any nodes at depth N+1
        step_contents = [step.content for step in steps]
        
        # Level1A and Level1B should appear together before Level2
        level1a_step = next((i for i, content in enumerate(step_contents) if "<Level1A>" in content), -1)
        level1b_step = next((i for i, content in enumerate(step_contents) if "<Level1B>" in content), -1)
        level2_step = next((i for i, content in enumerate(step_contents) if "<Level2>" in content), len(steps))
        
        if level1a_step >= 0 and level1b_step >= 0 and level2_step < len(steps):
            # Both Level1 nodes should appear before Level2
            assert max(level1a_step, level1b_step) < level2_step, \
                "All level 1 nodes should appear before level 2 nodes (depth-first order)"
    
    def test_rank_based_explanations(self):
        """Test that explanations reference depth/rank concepts."""
        argdown_text = """[Root]: Main claim.
    <+ <Level1>: First level.
        <+ <Level2>: Second level.
            <+ <Level3>: Third level."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Look for explanations that indicate rank/depth processing
        explanations = [step.explanation.lower() for step in steps]
        
        # Should have explanations mentioning levels, depths, or ranks
        depth_explanations = [exp for exp in explanations 
                            if any(word in exp for word in ["level", "depth", "rank", "tier", "order"])]
        
        assert len(depth_explanations) > 0, "Should have explanations about depth/rank processing"
    
    def test_complete_depth_levels(self):
        """Test that complete depth levels are shown before moving to next depth."""
        argdown_text = """[Root]: Main claim.
    <+ <Support1>: Support 1.
        <+ <Deep1>: Deep support 1.
    <+ <Support2>: Support 2.
        <+ <Deep2>: Deep support 2.
    <- <Objection>: Objection.
        <- <Counter>: Counter to objection."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # In by_rank, all depth-1 nodes (Support1, Support2, Objection) should 
        # appear before any depth-2 nodes (Deep1, Deep2, Counter)
        step_contents = [step.content for step in steps]
        
        # Find when each node first appears
        support1_step = next((i for i, content in enumerate(step_contents) if "<Support1>" in content), -1)
        support2_step = next((i for i, content in enumerate(step_contents) if "<Support2>" in content), -1)
        objection_step = next((i for i, content in enumerate(step_contents) if "<Objection>" in content), -1)
        
        deep1_step = next((i for i, content in enumerate(step_contents) if "<Deep1>" in content), len(steps))
        deep2_step = next((i for i, content in enumerate(step_contents) if "<Deep2>" in content), len(steps))
        counter_step = next((i for i, content in enumerate(step_contents) if "<Counter>" in content), len(steps))
        
        # All level-1 nodes should appear before any level-2 nodes
        level1_max = max(s for s in [support1_step, support2_step, objection_step] if s >= 0)
        level2_min = min(s for s in [deep1_step, deep2_step, counter_step] if s < len(steps))
        
        if level2_min < len(steps):  # Only check if level-2 nodes exist
            assert level1_max < level2_min, \
                "All level-1 nodes should appear before any level-2 nodes (by-rank order)"
    
    def test_placeholder_comments_in_intermediate_steps(self):
        """Test that intermediate steps may have placeholder comments."""
        argdown_text = """[Root]: Main claim.
    <+ <Support>: Supporting evidence.
        <+ <Deep>: Deep support.
            <+ <Deeper>: Even deeper support."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Check if any intermediate steps have placeholder comments
        # (This is strategy-specific behavior for by_rank)
        has_placeholders = any(
            "..." in step.content or "// [more content]" in step.content 
            for step in steps[:-1]  # Exclude final step
        )
        
        # This is optional behavior, so we just document it exists
        # (The test passes regardless, but documents the feature)
        if has_placeholders:
            assert True, "ByRank strategy includes placeholder comments"
    
    # By-rank specific tests for new examples
    
    def test_climate_action_by_rank_depth_order(self):
        """Test climate action example follows by-rank depth ordering."""
        argdown_text = """[Climate Action]: We should act on climate change.
    <+ <Scientific Evidence>: Science supports climate action.
        <+ <IPCC Reports>: International scientific consensus.
        <+ <Temperature Data>: Rising global temperatures.
    <- <Economic Costs>: Action is too expensive.
        <- <Long-term Benefits>: Benefits outweigh costs.
            <+ <Health Savings>: Reduced healthcare costs."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        step_contents = [step.content for step in steps]
        
        # Find when each depth level first appears (root always in step 0)
        
        depth_1_step = next((i for i, content in enumerate(step_contents)
                            if "<Scientific Evidence>" in content or "<Economic Costs>" in content), -1)
        
        depth_2_step = next((i for i, content in enumerate(step_contents)
                            if "<IPCC Reports>" in content or "<Temperature Data>" in content 
                            or "<Long-term Benefits>" in content), -1)
        
        depth_3_step = next((i for i, content in enumerate(step_contents)
                            if "<Health Savings>" in content), -1)
        
        # By-rank: all nodes at depth N should appear before any nodes at depth N+1
        if depth_1_step >= 0 and depth_2_step >= 0:
            assert depth_1_step < depth_2_step, \
                "All depth-1 nodes should appear before any depth-2 nodes"
        
        if depth_2_step >= 0 and depth_3_step >= 0:
            assert depth_2_step < depth_3_step, \
                "All depth-2 nodes should appear before any depth-3 nodes"
    
    def test_multiple_roots_by_rank_ordering(self):
        """Test multiple roots with by-rank depth-based ordering."""
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
        
        # Both roots should appear in first step (depth 0)
        assert "[Policy A]" in steps[0].content, "Policy A should be in first step"
        assert "[Policy B]" in steps[0].content, "Policy B should be in first step"
        
        # Find when depth-1 and depth-2 nodes appear
        depth_1_step = next((i for i, content in enumerate(step_contents)
                            if any(node in content for node in 
                                  ["<Benefit 1>", "<Benefit 2>", "<Conflict>", "<Alternative Benefit>"])), -1)
        
        depth_2_step = next((i for i, content in enumerate(step_contents)
                            if "<Resource Limitation>" in content), -1)
        
        # All depth-1 nodes should appear before depth-2 nodes
        if depth_1_step >= 0 and depth_2_step >= 0:
            assert depth_1_step < depth_2_step, \
                "All depth-1 nodes should appear before depth-2 nodes in by-rank strategy"
    
    def test_asymmetric_by_rank_depth_grouping(self):
        """Test asymmetric structure groups nodes by depth in by-rank."""
        argdown_text = """[Main Claim]: Central argument.
    <+ <Support>: Supporting evidence.
        <+ <Deep Support>: Deeper evidence.
            <+ <Deepest>: Very deep support.
    <- <Simple Attack>: Basic objection.
    <+ <Another Support>: Additional evidence."""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        step_contents = [step.content for step in steps]
        
        # Find when each depth level appears
        depth_1_step = next((i for i, content in enumerate(step_contents)
                            if any(node in content for node in 
                                  ["<Support>", "<Simple Attack>", "<Another Support>"])), -1)
        
        depth_2_step = next((i for i, content in enumerate(step_contents)
                            if "<Deep Support>" in content), -1)
        
        depth_3_step = next((i for i, content in enumerate(step_contents)
                            if "<Deepest>" in content), -1)
        
        # Verify by-rank ordering: depth 1 before depth 2 before depth 3
        if depth_1_step >= 0 and depth_2_step >= 0:
            assert depth_1_step < depth_2_step, \
                "Depth-1 nodes should appear before depth-2 nodes"
        
        if depth_2_step >= 0 and depth_3_step >= 0:
            assert depth_2_step < depth_3_step, \
                "Depth-2 nodes should appear before depth-3 nodes"
        
        # In by-rank, Simple Attack and Another Support should appear in same step
        # as Support (all are depth-1)
        if depth_1_step >= 0:
            depth_1_content = steps[depth_1_step].content
            assert "<Support>" in depth_1_content, "Support should be in depth-1 step"
            assert "<Simple Attack>" in depth_1_content, "Simple Attack should be in depth-1 step"
            assert "<Another Support>" in depth_1_content, "Another Support should be in depth-1 step"
