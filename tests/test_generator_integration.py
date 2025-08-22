"""
Integration tests for the CotGenerator with implemented strategies.
"""

import pytest
from src.argdown_cotgen import CotGenerator


class TestCotGeneratorIntegration:
    """Test the complete integration of CotGenerator with strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = CotGenerator(pipe_type="by_rank")
    
    def test_by_rank_argument_map_generation(self):
        """Test by_rank strategy integration with argument maps."""
        argdown_text = """# Main claim
    +> Supporting evidence
        <- Counter-argument
    <- General objection"""
        
        result = self.generator.generate(argdown_text)
        
        assert result.input_type == "ARGUMENT_MAP"
        assert result.strategy_name == "by_rank"
        assert len(result.steps) == 3  # 3 depth levels
        
        # Check progressive building
        assert "# Main claim" in result.steps[0].content
        assert "+> Supporting evidence" in result.steps[1].content
        assert "<- Counter-argument" in result.steps[2].content
    
    def test_by_rank_with_yaml_and_comments(self):
        """Test by_rank strategy with YAML and comments."""
        argdown_text = """# Climate urgent {category: env} // Important
    +> Evidence {strength: high} // Latest data"""
        
        result = self.generator.generate(argdown_text)
        
        # Should have 4 steps: depth 0, depth 1, YAML, comments
        assert len(result.steps) == 4
        
        # Check YAML step
        yaml_step = result.steps[2]
        assert "{category: env}" in yaml_step.content
        assert "{strength: high}" in yaml_step.content
        assert "// Important" not in yaml_step.content
        
        # Check comments step
        comments_step = result.steps[3]
        assert "// Important" in comments_step.content
        assert "// Latest data" in comments_step.content
    
    def test_call_method_formatting(self):
        """Test the __call__ method produces formatted output."""
        argdown_text = """# Simple claim
    +> Evidence"""
        
        formatted_output = self.generator(argdown_text)
        
        assert isinstance(formatted_output, str)
        # Check for CotFormatter output format
        assert "```argdown {version='v1'}" in formatted_output
        assert "```argdown {version='v2'}" in formatted_output
        assert "# Simple claim" in formatted_output
        assert "+> Evidence" in formatted_output
        # Should have natural language explanations
        assert any(word in formatted_output.lower() for word in ["start", "add", "include", "identify"])
    
    def test_unsupported_strategy_error(self):
        """Test that unsupported strategies raise appropriate errors."""
        generator = CotGenerator(pipe_type="unsupported_strategy")
        
        argdown_text = "# Test claim"
        
        with pytest.raises(NotImplementedError, match="Strategy 'unsupported_strategy' not yet implemented"):
            generator.generate(argdown_text)
    
    def test_argument_structure_not_implemented(self):
        """Test that argument structures raise NotImplementedError."""
        argdown_text = """<Test Argument>
(1) Premise
----
(2) Conclusion"""
        
        with pytest.raises(NotImplementedError, match="Argument strategies not yet implemented"):
            self.generator.generate(argdown_text)
    
    def test_single_depth_map(self):
        """Test argument map with only root level content."""
        argdown_text = """# Main claim
# Another claim"""
        
        result = self.generator.generate(argdown_text)
        
        # Should have only 1 step for depth 0
        assert len(result.steps) == 1
        assert "# Main claim" in result.steps[0].content
        assert "# Another claim" in result.steps[0].content
    
    def test_deep_nesting(self):
        """Test argument map with deep nesting."""
        argdown_text = """# Root
    ## Level 1
        ### Level 2
            #### Level 3
                ##### Level 4"""
        
        result = self.generator.generate(argdown_text)
        
        # Should have 5 steps for depths 0-4
        assert len(result.steps) == 5
        
        # Check progressive building
        for i, step in enumerate(result.steps):
            # Each step should include all content up to its depth
            assert "# Root" in step.content
            if i >= 1:
                assert "## Level 1" in step.content
            if i >= 2:
                assert "### Level 2" in step.content
            if i >= 3:
                assert "#### Level 3" in step.content
            if i >= 4:
                assert "##### Level 4" in step.content
