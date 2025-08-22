"""
Tests for the CotFormatter output formatting.
"""

from src.argdown_cotgen.formatters.output import CotFormatter
from src.argdown_cotgen.core.models import CotStep, CotResult


class TestCotFormatter:
    """Test the CotFormatter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = CotFormatter()
    
    def test_basic_formatting(self):
        """Test basic formatting of CoT steps."""
        steps = [
            CotStep("v1", "# Main claim", "I'll start with the main claim."),
            CotStep("v2", "# Main claim\n    +> Evidence", "Now I'll add evidence.")
        ]
        result = CotResult(steps, "ARGUMENT_MAP", "by_rank")
        
        formatted = self.formatter.format(result)
        
        # Check for proper structure
        assert "I'll start with the main claim." in formatted
        assert "```argdown {version='v1'}" in formatted
        assert "# Main claim" in formatted
        assert "```" in formatted
        assert "Now I'll add evidence." in formatted
        assert "```argdown {version='v2'}" in formatted
        assert "+> Evidence" in formatted
    
    def test_empty_explanation_handling(self):
        """Test handling of steps without explanations."""
        steps = [
            CotStep("v1", "# Main claim", ""),  # Empty explanation
            CotStep("v2", "# Main claim\n    +> Evidence", "Adding evidence.")
        ]
        result = CotResult(steps, "ARGUMENT_MAP", "by_rank")
        
        formatted = self.formatter.format(result)
        
        # Should still format the content even without explanation
        assert "```argdown {version='v1'}" in formatted
        assert "# Main claim" in formatted
        assert "Adding evidence." in formatted
    
    def test_empty_content_handling(self):
        """Test handling of steps with empty content."""
        steps = [
            CotStep("v1", "", "Some explanation"),  # Empty content
            CotStep("v2", "# Main claim", "Real content")
        ]
        result = CotResult(steps, "ARGUMENT_MAP", "by_rank")
        
        formatted = self.formatter.format(result)
        
        # Should include explanation but skip empty content block
        assert "Some explanation" in formatted
        assert "```argdown {version='v1'}" not in formatted
        assert "```argdown {version='v2'}" in formatted
        assert "# Main claim" in formatted
    
    def test_version_labeling(self):
        """Test that version labels are correctly applied."""
        steps = [
            CotStep("v1", "# Step 1", "First step"),
            CotStep("v2", "# Step 2", "Second step"),
            CotStep("v3", "# Step 3", "Third step")
        ]
        result = CotResult(steps, "ARGUMENT_MAP", "by_rank")
        
        formatted = self.formatter.format(result)
        
        assert "```argdown {version='v1'}" in formatted
        assert "```argdown {version='v2'}" in formatted  
        assert "```argdown {version='v3'}" in formatted
    
    def test_complex_argdown_formatting(self):
        """Test formatting with complex Argdown structures."""
        complex_content = """# Climate action urgent {priority: high}
    ## Evidence mounts // IPCC reports
        +> Scientific consensus {confidence: 99%}
        +> Economic models agree
    <- Skeptics argue costs high
        +> But benefits outweigh costs"""
        
        steps = [
            CotStep("v1", "# Climate action urgent", "Starting with main claim"),
            CotStep("v2", complex_content, "Full structure with metadata")
        ]
        result = CotResult(steps, "ARGUMENT_MAP", "by_rank")
        
        formatted = self.formatter.format(result)
        
        # Check preservation of YAML, comments, and structure
        assert "{priority: high}" in formatted
        assert "// IPCC reports" in formatted
        assert "{confidence: 99%}" in formatted
        assert "+> Scientific consensus" in formatted
        assert "<- Skeptics argue" in formatted
        assert "Starting with main claim" in formatted
        assert "Full structure with metadata" in formatted
    
    def test_whitespace_and_indentation(self):
        """Test that whitespace and indentation are preserved."""
        content_with_indentation = """# Main
    ## Level 1
        ### Level 2
            #### Level 3"""
        
        steps = [CotStep("v1", content_with_indentation, "Testing indentation")]
        result = CotResult(steps, "ARGUMENT_MAP", "by_rank")
        
        formatted = self.formatter.format(result)
        
        # Check that indentation is preserved in the output
        lines = formatted.split('\n')
        argdown_lines = []
        in_code_block = False
        
        for line in lines:
            if line.startswith('```argdown'):
                in_code_block = True
            elif line == '```':
                in_code_block = False
            elif in_code_block:
                argdown_lines.append(line)
        
        # Check that we have the right indentation levels
        assert any(line.startswith('# Main') for line in argdown_lines)
        assert any(line.startswith('    ## Level 1') for line in argdown_lines)
        assert any(line.startswith('        ### Level 2') for line in argdown_lines)
        assert any(line.startswith('            #### Level 3') for line in argdown_lines)
    
    def test_output_structure(self):
        """Test the overall structure of formatted output."""
        steps = [
            CotStep("v1", "# Step 1", "Explanation 1"),
            CotStep("v2", "# Step 2", "Explanation 2")
        ]
        result = CotResult(steps, "ARGUMENT_MAP", "by_rank")
        
        formatted = self.formatter.format(result)
        lines = formatted.split('\n')
        
        # Check overall structure pattern
        # Should be: explanation, empty line, code block start, content, code block end, empty line, repeat
        
        # Find explanation lines
        explanation_indices = []
        for i, line in enumerate(lines):
            if "Explanation" in line:
                explanation_indices.append(i)
        
        assert len(explanation_indices) == 2
        
        # Check that explanations are followed by empty lines and code blocks
        for idx in explanation_indices:
            assert lines[idx + 1] == ""  # Empty line after explanation
            assert lines[idx + 2].startswith("```argdown")  # Code block starts
