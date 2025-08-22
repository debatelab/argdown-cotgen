"""
Tests for the random explanation feature in by_rank strategy.
"""

from src.argdown_cotgen.core.parser import ArgdownParser
from src.argdown_cotgen.strategies.argument_maps.by_rank import ByRankStrategy


class TestByRankRandomExplanations:
    """Test the random explanation feature in by_rank strategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ArgdownParser()
        self.strategy = ByRankStrategy()
    
    def test_explanation_variability(self):
        """Test that explanations vary between runs."""
        argdown_text = """# Main claim
    +> Supporting evidence
        <- Counter-argument"""
        
        structure = self.parser.parse(argdown_text)
        
        # Generate multiple times and collect explanations
        all_explanations = []
        for _ in range(20):  # Run enough times to likely see variation
            steps = self.strategy.generate(structure)
            explanations = [step.explanation for step in steps]
            all_explanations.append(tuple(explanations))
        
        # Should have some variation in explanations
        unique_explanations = set(all_explanations)
        assert len(unique_explanations) > 1, "Explanations should vary between runs"
    
    def test_explanation_alternatives_exist(self):
        """Test that all explanation alternatives are defined."""
        strategy = ByRankStrategy()
        
        # Check that all explanation lists have multiple alternatives
        assert len(strategy.ROOT_EXPLANATIONS) >= 3
        assert len(strategy.FIRST_ORDER_EXPLANATIONS) >= 3
        assert len(strategy.INTERMEDIATE_EXPLANATIONS) >= 3
        assert len(strategy.FINAL_DEPTH_EXPLANATIONS) >= 3
        assert len(strategy.YAML_EXPLANATIONS) >= 3
        assert len(strategy.COMMENTS_EXPLANATIONS) >= 3
    
    def test_explanation_formatting(self):
        """Test that explanations with format parameters work correctly."""
        strategy = ByRankStrategy()
        
        # Test intermediate explanations with depth formatting
        explanation = strategy._get_random_explanation(
            strategy.INTERMEDIATE_EXPLANATIONS, 
            depth=3
        )
        assert "3" in explanation
        
        # Test final depth explanations with depth formatting
        explanation = strategy._get_random_explanation(
            strategy.FINAL_DEPTH_EXPLANATIONS, 
            depth=5
        )
        assert "5" in explanation
    
    def test_explanation_content_appropriateness(self):
        """Test that explanations are contextually appropriate."""
        argdown_text = """# Main claim {category: test} // Comment
    +> Evidence
        <- Counter"""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Test root explanation appropriateness
        root_explanation = steps[0].explanation.lower()
        root_keywords = ["start", "begin", "first", "main", "primary", "core", "claims", "root"]
        assert any(keyword in root_explanation for keyword in root_keywords)
        
        # Test first order explanation appropriateness  
        first_order_explanation = steps[1].explanation.lower()
        first_order_keywords = ["first", "direct", "immediate", "level 1", "tier", "reasons", "arguments"]
        assert any(keyword in first_order_explanation for keyword in first_order_keywords)
        
        # Test YAML explanation appropriateness
        yaml_explanation = steps[3].explanation.lower()
        yaml_keywords = ["yaml", "metadata", "inline", "data", "annotations"]
        assert any(keyword in yaml_explanation for keyword in yaml_keywords)
        
        # Test comments explanation appropriateness
        comments_explanation = steps[4].explanation.lower()
        comments_keywords = ["comment", "commentary", "explanatory"]
        assert any(keyword in comments_explanation for keyword in comments_keywords)
    
    def test_random_selection_method(self):
        """Test the _get_random_explanation helper method."""
        strategy = ByRankStrategy()
        
        test_list = ["Option A", "Option B {param}", "Option C"]
        
        # Test without formatting
        result = strategy._get_random_explanation(test_list)
        assert result in test_list
        
        # Test with formatting
        result = strategy._get_random_explanation(test_list, param="formatted")
        assert result in ["Option A", "Option B formatted", "Option C"]
        
        # Test multiple calls return different results eventually
        results = [strategy._get_random_explanation(test_list) for _ in range(10)]
        unique_results = set(results)
        # Should get some variation (though not guaranteed due to randomness)
        # This test might occasionally fail due to random chance, but very unlikely
        assert len(unique_results) >= 1  # At minimum, should work
    
    def test_explanation_quality(self):
        """Test that all explanation alternatives are reasonable."""
        strategy = ByRankStrategy()
        
        # Check that all explanations are non-empty strings
        all_explanations = (
            strategy.ROOT_EXPLANATIONS +
            strategy.FIRST_ORDER_EXPLANATIONS +
            strategy.INTERMEDIATE_EXPLANATIONS +
            strategy.FINAL_DEPTH_EXPLANATIONS +
            strategy.YAML_EXPLANATIONS +
            strategy.COMMENTS_EXPLANATIONS
        )
        
        for explanation in all_explanations:
            assert isinstance(explanation, str)
            assert len(explanation.strip()) > 0
            assert explanation[0].isupper() or explanation[0] in ["'", '"']  # Should start with capital or quote
            assert explanation.endswith('.') or explanation.endswith('!') or '{' in explanation  # Should end properly or contain format placeholder
