"""Test that INDENT_SIZE constant is used consistently."""

from pprint import pprint
from src.argdown_cotgen.core.models import INDENT_SIZE
from src.argdown_cotgen.core.parser import ArgdownParser
from src.argdown_cotgen.strategies.argument_maps.by_rank import ByRankStrategy

# NOTE: This is slightly outdated as we're calculating indent_size for each snippet.


class TestIndentSizeConstant:
    """Test that the INDENT_SIZE constant is used consistently across the codebase."""
    
    def test_indent_size_constant_exists(self):
        """Test that INDENT_SIZE constant is defined."""
        assert INDENT_SIZE == 4
        assert isinstance(INDENT_SIZE, int)
    
    def test_parser_uses_indent_size_constant(self):
        """Test that parser correctly uses INDENT_SIZE for indent calculation."""
        parser = ArgdownParser()
        
        # Test different levels of indentation
        test_cases = [
            ("# Main", 0),
            ("    ## Level 1", 1), 
            ("        ### Level 2", 2),
            ("            #### Level 3", 3),
        ]
        
        for line, expected_level in test_cases:
            calculated_level = parser._calculate_indent_level(line)
            assert calculated_level == expected_level, \
                f"Expected level {expected_level} for '{line}', got {calculated_level}"
    
    def test_by_rank_strategy_uses_indent_size_constant(self):
        """Test that by_rank strategy properly formats indentation using INDENT_SIZE."""
        parser = ArgdownParser()
        strategy = ByRankStrategy()
        
        # Test with multi-level structure
        argdown_text = """Main claim
    <- Sub-claim
        +> Evidence"""
        
        structure = parser.parse(argdown_text)
        steps = strategy.generate(structure)
        
        # Check that final step has proper indentation
        final_step = steps[-1]
        lines = final_step.content.split('\n')

        pprint(final_step)

        # Find the evidence line
        evidence_line = None
        for line in lines:
            if "Evidence" in line:
                evidence_line = line
                break
        
        assert evidence_line is not None
        # Should have 2 levels * INDENT_SIZE = 8 spaces
        expected_spaces = 2 * INDENT_SIZE
        leading_spaces = len(evidence_line) - len(evidence_line.lstrip())
        assert leading_spaces == expected_spaces, \
            f"Expected {expected_spaces} spaces, got {leading_spaces}"
    
    def test_indent_size_consistency(self):
        """Test that changing INDENT_SIZE would affect both parsing and formatting."""
        # This test documents the behavior for future modifications
        parser = ArgdownParser()
        
        # Test with 8-space indentation (2 levels of default 4-space)
        test_line = "        # Test"
        calculated_level = parser._calculate_indent_level(test_line)
        
        # Should be level 2 with INDENT_SIZE=4
        assert calculated_level == 2
        
        # This shows that if we changed INDENT_SIZE to 2, 
        # the same line would be parsed as level 4
        # (This is why using a constant is better than magic numbers!)
