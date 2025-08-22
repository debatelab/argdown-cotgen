"""
Tests for the by_rank strategy implementation.
"""

import pytest
from src.argdown_cotgen.core.parser import ArgdownParser
from src.argdown_cotgen.strategies.argument_maps.by_rank import ByRankStrategy
from src.argdown_cotgen.core.models import ArgumentStructure


class TestByRankStrategy:
    """Test cases for the by_rank argument map strategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ArgdownParser()
        self.strategy = ByRankStrategy()
    
    def test_simple_argument_map(self):
        """Test by_rank strategy with a simple argument map."""
        argdown_text = """# Main claim
    ## Sub-claim
        +> Supporting evidence
    <- Objection"""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Should have 3 steps for depths 0, 1, 2
        assert len(steps) == 3
        
        # Check step progressions
        assert "# Main claim" in steps[0].content
        assert "## Sub-claim" not in steps[0].content
        
        assert "## Sub-claim" in steps[1].content
        assert "<- Objection" in steps[1].content
        assert "+> Supporting evidence" not in steps[1].content
        
        assert "+> Supporting evidence" in steps[2].content
    
    def test_with_yaml_inline_data(self):
        """Test by_rank strategy with YAML inline data."""
        argdown_text = """# Climate action {category: environmental}
    +> Scientific evidence {strength: high}"""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Should have 3 steps: depth 0, depth 1, then YAML
        assert len(steps) == 3
        
        # First two steps should not have YAML
        assert "{category: environmental}" not in steps[0].content
        assert "{strength: high}" not in steps[1].content
        
        # Last step should have YAML
        assert "{category: environmental}" in steps[2].content
        assert "{strength: high}" in steps[2].content
        # Check that explanation mentions YAML (flexible matching)
        yaml_explanation = steps[2].explanation.lower()
        assert "yaml" in yaml_explanation or "metadata" in yaml_explanation
    
    def test_with_comments(self):
        """Test by_rank strategy with comments."""
        argdown_text = """# Main claim // Important note
    +> Evidence // Latest data"""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Should have 3 steps: depth 0, depth 1, then comments
        assert len(steps) == 3
        
        # First two steps should not have comments
        assert "// Important note" not in steps[0].content
        assert "// Latest data" not in steps[1].content
        
        # Last step should have comments
        assert "// Important note" in steps[2].content
        assert "// Latest data" in steps[2].content
        # Check that explanation mentions comments (flexible matching)
        comment_explanation = steps[2].explanation.lower()
        assert "comment" in comment_explanation
    
    def test_with_yaml_and_comments(self):
        """Test by_rank strategy with both YAML and comments."""
        argdown_text = """# Main claim {category: test} // Comment
    +> Evidence {strength: high} // Data"""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Should have 4 steps: depth 0, depth 1, YAML, comments
        assert len(steps) == 4
        
        # YAML step should have YAML but not comments
        yaml_step = steps[2]
        assert "{category: test}" in yaml_step.content
        assert "{strength: high}" in yaml_step.content
        assert "// Comment" not in yaml_step.content
        assert "// Data" not in yaml_step.content
        
        # Comments step should have both YAML and comments
        comments_step = steps[3]
        assert "{category: test}" in comments_step.content
        assert "// Comment" in comments_step.content
    
    def test_single_depth_structure(self):
        """Test by_rank strategy with only root level content."""
        argdown_text = """# Main claim
# Another claim"""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # Should have only 1 step since max_depth is 0
        assert len(steps) == 1
        assert "# Main claim" in steps[0].content
        assert "# Another claim" in steps[0].content
    
    def test_wrong_structure_type(self):
        """Test that by_rank strategy rejects non-ArgumentMap structures."""
        # Use argument syntax to get ArgumentStructure
        argdown_text = """<Argument Title>
(1) Premise
----
(2) Conclusion"""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentStructure)
        
        with pytest.raises(ValueError, match="ByRankStrategy requires an ArgumentMapStructure"):
            self.strategy.generate(structure, abortion_rate=0.0)
    
    def test_step_explanations(self):
        """Test that step explanations are appropriate for each depth."""
        argdown_text = """# Root
    ## Level 1
        ### Level 2
            #### Level 3"""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        assert len(steps) == 4
        
        # Check that explanations are contextually appropriate (flexible matching)
        root_explanation = steps[0].explanation.lower()
        assert any(word in root_explanation for word in ["main", "claims", "primary", "core", "root", "start", "first"])
        
        first_order_explanation = steps[1].explanation.lower()
        assert any(word in first_order_explanation for word in ["first", "level 1", "direct", "immediate", "tier"])
        
        level_2_explanation = steps[2].explanation.lower()
        assert "level 2" in level_2_explanation or "2" in level_2_explanation
        
        final_explanation = steps[3].explanation.lower()
        assert any(word in final_explanation for word in ["level 3", "final", "deepest", "complete", "last", "bottom"])
        assert "3" in final_explanation
    
    def test_empty_lines_handling(self):
        """Test that empty lines are properly handled."""
        argdown_text = """# Main claim

    +> Supporting evidence

        <- Counter-evidence"""
        
        structure = self.parser.parse(argdown_text)
        steps = self.strategy.generate(structure, abortion_rate=0.0)
        
        # All steps should have clean content without extra empty lines
        for step in steps:
            lines = step.content.split('\n')
            # Should not have consecutive empty lines
            for i in range(len(lines) - 1):
                if not lines[i].strip():
                    assert lines[i + 1].strip(), f"Consecutive empty lines found in step {step.version}"
