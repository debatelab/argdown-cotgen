"""
Comparative tests for different argument map strategies.

This module tests that different strategies produce different but valid results
for the same input, demonstrating their unique approaches.
"""

import pytest
from .strategy_test_framework import (
    run_strategy_comparison, 
    assert_strategies_differ,
    COMMON_STRATEGY_TEST_CASES
)
from src.argdown_cotgen.strategies.argument_maps.by_rank import ByRankStrategy
from src.argdown_cotgen.strategies.argument_maps.breadth_first import BreadthFirstStrategy
from src.argdown_cotgen.strategies.argument_maps.depth_first import DepthFirstStrategy


class TestStrategyComparisons:
    """Test comparisons between different strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategies = [
            ByRankStrategy(),
            BreadthFirstStrategy(),
            DepthFirstStrategy()
        ]
    
    @pytest.mark.parametrize("test_case", COMMON_STRATEGY_TEST_CASES, ids=lambda tc: tc.name)
    def test_strategies_produce_different_results(self, test_case):
        """Test that different strategies produce different approaches."""
        if test_case.name == "single_claim":
            # Skip for single claims as there's not much room for variation
            return
            
        results = run_strategy_comparison(self.strategies, test_case)
        assert_strategies_differ(results)
    
    def test_breadth_vs_depth_ordering(self):
        """Test the key difference between breadth-first and by-rank ordering."""
        test_case_text = """[Root]: Main claim.
    <+ <A>: Support A.
        <+ <A1>: Deep support for A.
    <+ <B>: Support B.
        <+ <B1>: Deep support for B."""
        
        from .strategy_test_framework import StrategyTestCase
        test_case = StrategyTestCase(
            name="ordering_test",
            argdown_text=test_case_text,
            description="Test ordering differences",
            expected_step_count=4,
            expected_features={}
        )
        
        results = run_strategy_comparison(self.strategies, test_case)
        
        by_rank_steps = results["ByRankStrategy"]
        breadth_first_steps = results["BreadthFirstStrategy"]
        
        # Convert to step content for analysis
        by_rank_content = [step.content for step in by_rank_steps]
        breadth_first_content = [step.content for step in breadth_first_steps]
        
        # Find when nodes first appear in each strategy
        def find_first_appearance(contents, node_name):
            for i, content in enumerate(contents):
                if node_name in content:
                    return i
            return -1
        
        # By-rank should show A and B before A1 and B1 (siblings before children)
        by_rank_a = find_first_appearance(by_rank_content, "<A>")
        by_rank_b = find_first_appearance(by_rank_content, "<B>")
        by_rank_a1 = find_first_appearance(by_rank_content, "<A1>")
        by_rank_b1 = find_first_appearance(by_rank_content, "<B1>")
        
        # Breadth-first should also show A and B before A1 and B1, but the 
        # specific step progression might differ
        breadth_a = find_first_appearance(breadth_first_content, "<A>")
        breadth_b = find_first_appearance(breadth_first_content, "<B>")
        breadth_a1 = find_first_appearance(breadth_first_content, "<A1>")
        breadth_b1 = find_first_appearance(breadth_first_content, "<B1>")
        
        # Both should follow the pattern: siblings before children
        if by_rank_a >= 0 and by_rank_a1 >= 0:
            assert by_rank_a < by_rank_a1, "ByRank: A should appear before A1"
        if by_rank_b >= 0 and by_rank_b1 >= 0:
            assert by_rank_b < by_rank_b1, "ByRank: B should appear before B1"
            
        if breadth_a >= 0 and breadth_a1 >= 0:
            assert breadth_a < breadth_a1, "BreadthFirst: A should appear before A1"
        if breadth_b >= 0 and breadth_b1 >= 0:
            assert breadth_b < breadth_b1, "BreadthFirst: B should appear before B1"
        
        # The strategies should produce different step sequences
        assert by_rank_content != breadth_first_content, \
            "Different strategies should produce different step sequences"
    
    def test_explanation_style_differences(self):
        """Test that strategies have different explanation styles."""
        test_case_text = """[Main]: Main claim.
    <+ <Support>: Supporting evidence."""
        
        from .strategy_test_framework import StrategyTestCase
        test_case = StrategyTestCase(
            name="explanation_test",
            argdown_text=test_case_text,
            description="Test explanation differences",
            expected_step_count=2,
            expected_features={}
        )
        
        results = run_strategy_comparison(self.strategies, test_case)
        
        # Collect all explanations from both strategies
        by_rank_explanations = [step.explanation.lower() for step in results["ByRankStrategy"]]
        breadth_explanations = [step.explanation.lower() for step in results["BreadthFirstStrategy"]]
        
        # Strategies should have some different explanations
        # (Even if they don't use specific vocabulary, they should differ)
        all_by_rank = " ".join(by_rank_explanations)
        all_breadth = " ".join(breadth_explanations)
        
        assert all_by_rank != all_breadth, \
            "Different strategies should produce different explanations"
        
        # Check for some strategy-specific patterns (more flexible)
        # By-rank often mentions "level", "primary", "first-order", or "main"
        by_rank_patterns = any(word in all_by_rank for word in ["level", "primary", "first-order", "main"])
        
        # Breadth-first often mentions "processing", "immediate", "direct", or "children"
        breadth_patterns = any(word in all_breadth for word in ["processing", "immediate", "direct", "children"])
        
        # At least one strategy should show some characteristic language
        assert by_rank_patterns or breadth_patterns, \
            f"Expected some characteristic vocabulary. ByRank: '{all_by_rank}', BreadthFirst: '{all_breadth}'"
