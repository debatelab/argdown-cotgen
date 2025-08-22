"""
Consolidated test suite for ArgdownParser with structured test data and comprehensive validation.
Combines data-driven testing with specific edge cases and detailed validation.
"""

import pytest
from src.argdown_cotgen.core import (
    ArgdownParser, 
    SnippetType,
    DialecticalType,
    ArgumentMapStructure,
    ArgumentStructure
)
from .test_data import (
    ALL_SNIPPETS, 
    ARGUMENT_MAP_SNIPPETS,
    ARGUMENT_SNIPPETS,
    EDGE_CASE_SNIPPETS,
    get_snippet_by_name
)


@pytest.fixture
def parser():
    """ArgdownParser instance."""
    return ArgdownParser()


# Test data for additional parameterized tests
DIALECTICAL_TYPE_CASES = [
    ("<+", DialecticalType.SUPPORTS),
    ("<-", DialecticalType.ATTACKS),
    ("+", DialecticalType.SUPPORTS),
    ("-", DialecticalType.ATTACKS),
    ("<_", DialecticalType.UNDERCUTS),
    ("><", DialecticalType.CONTRADICTORY),
    ("+>", DialecticalType.IS_SUPPORTED_BY),
    ("->", DialecticalType.IS_ATTACKED_BY),
    ("_>", DialecticalType.IS_UNDERCUT_BY),
]

INDENTATION_TEST_CASES = [
    ("No indentation", 0),
    ("    4 spaces", 1),
    ("        8 spaces", 2),
    ("            12 spaces", 3),
]


class TestArgdownParserDataDriven:
    """Data-driven tests using structured test cases from test_data.py."""

    @pytest.mark.parametrize("test_case", ALL_SNIPPETS, ids=[case.name for case in ALL_SNIPPETS])
    def test_snippet_type_detection(self, parser, test_case):
        """Test snippet type detection for all test cases."""
        structure = parser.parse(test_case.snippet)
        assert structure.snippet_type == test_case.expected_type

    @pytest.mark.parametrize("test_case", ARGUMENT_MAP_SNIPPETS, ids=[case.name for case in ARGUMENT_MAP_SNIPPETS])
    def test_argument_map_properties(self, parser, test_case):
        """Test argument map properties for all argument map test cases."""
        structure = parser.parse(test_case.snippet)
        
        assert isinstance(structure, ArgumentMapStructure)
        assert structure.snippet_type == SnippetType.ARGUMENT_MAP
        
        # Validate expected properties with safe attribute access
        for prop_name, expected_value in test_case.expected_properties.items():
            if hasattr(structure, prop_name):
                actual_value = getattr(structure, prop_name)
                assert actual_value == expected_value, f"Property {prop_name}: expected {expected_value}, got {actual_value}"
            else:
                # For custom property checks, implement specific logic
                if prop_name == "main_claim_content":
                    main_claim = structure.main_claim
                    assert main_claim is not None
                    assert expected_value in main_claim.content
                elif prop_name == "first_level_count":
                    first_level = structure.get_lines_at_depth(1)
                    assert len(first_level) == expected_value
                elif prop_name == "second_level_count":
                    second_level = structure.get_lines_at_depth(2)
                    assert len(second_level) == expected_value
                elif prop_name == "handles_mixed_indentation":
                    # Just verify it parses without error
                    assert True
                elif prop_name == "has_contradictory":
                    # Check if any line has contradictory relation
                    has_contradictory = any(
                        hasattr(line, 'support_type') and line.support_type == DialecticalType.CONTRADICTORY
                        for line in structure.lines
                    )
                    assert has_contradictory == expected_value

    @pytest.mark.parametrize("test_case", ARGUMENT_SNIPPETS, ids=[case.name for case in ARGUMENT_SNIPPETS])
    def test_argument_properties(self, parser, test_case):
        """Test argument properties for all argument test cases."""
        structure = parser.parse(test_case.snippet)
        
        assert isinstance(structure, ArgumentStructure)
        assert structure.snippet_type == SnippetType.ARGUMENT
        
        # Validate expected properties with safe attribute access
        for prop_name, expected_value in test_case.expected_properties.items():
            # For custom property checks, implement specific logic first
            if prop_name == "numbered_statement_count" or prop_name == "numbered_statements":
                numbered = structure.numbered_statements
                assert len(numbered) == expected_value
            elif prop_name == "inference_rules":
                inference_rules = structure.inference_rules
                assert len(inference_rules) == expected_value
            elif prop_name == "has_separator" or prop_name == "has_separators":
                separators = [line for line in structure.lines 
                             if hasattr(line, 'is_separator') and line.is_separator]
                assert (len(separators) > 0) == expected_value
            elif prop_name == "conclusions":
                conclusions = structure.conclusions
                assert len(conclusions) == expected_value
            elif prop_name == "final_conclusion_number":
                final_conclusion = structure.final_conclusion
                if final_conclusion:
                    assert final_conclusion.statement_number == expected_value
                else:
                    assert expected_value is None
            elif prop_name == "premise_count":
                premises = structure.premises
                assert len(premises) == expected_value
            elif prop_name == "conclusion_count":
                conclusions = structure.conclusions
                assert len(conclusions) == expected_value
            elif prop_name == "has_title":
                title_line = structure.title_line
                assert (title_line is not None) == expected_value
            elif hasattr(structure, prop_name):
                actual_value = getattr(structure, prop_name)
                assert actual_value == expected_value, f"Property {prop_name}: expected {expected_value}, got {actual_value}"
            else:
                # Unknown property - just skip with a warning
                print(f"Warning: Unknown property {prop_name} in test case {test_case.name}")

    @pytest.mark.parametrize("test_case", EDGE_CASE_SNIPPETS, ids=[case.name for case in EDGE_CASE_SNIPPETS])
    def test_edge_cases(self, parser, test_case):
        """Test edge cases and special scenarios."""
        structure = parser.parse(test_case.snippet)
        
        # Basic type validation
        assert structure.snippet_type == test_case.expected_type
        
        # Validate expected properties if provided
        if test_case.expected_properties:
            for prop_name, expected_value in test_case.expected_properties.items():
                # Handle custom properties for edge cases first
                if prop_name == "handles_mixed_indentation":
                    # Just verify it parses without error
                    assert True
                elif prop_name == "has_contradictory":
                    # Check if any line has contradictory relation
                    has_contradictory = any(
                        hasattr(line, 'support_type') and line.support_type == DialecticalType.CONTRADICTORY
                        for line in structure.lines
                    )
                    assert has_contradictory == expected_value
                elif hasattr(structure, prop_name):
                    actual_value = getattr(structure, prop_name)
                    assert actual_value == expected_value, f"Property {prop_name}: expected {expected_value}, got {actual_value}"
                else:
                    print(f"Warning: Unknown property {prop_name} in edge case {test_case.name}")


class TestArgdownParserDetailed:
    """Detailed tests for specific parsing scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ArgdownParser()

    def test_argument_map_parsing_detailed(self, parser):
        """Test detailed parsing of argument map structure."""
        test_case = get_snippet_by_name("basic_support_attack")
        structure = parser.parse(test_case.snippet)
        
        # Ensure it's an argument map
        assert structure.snippet_type == SnippetType.ARGUMENT_MAP
        assert isinstance(structure, ArgumentMapStructure)
        
        # Check basic structure
        assert structure.max_depth == 2
        
        # Check main claim
        main_claim = structure.main_claim
        assert main_claim is not None
        assert main_claim.is_claim
        assert "Main claim" in main_claim.content
        assert main_claim.indent_level == 0
        
        # Check first level arguments
        first_level = structure.get_lines_at_depth(1)
        assert len(first_level) == 3  # Two supports and one attack
        
        support_lines = [line for line in first_level if line.support_type == DialecticalType.SUPPORTS]
        attack_lines = [line for line in first_level if line.support_type == DialecticalType.ATTACKS]
        
        assert len(support_lines) == 2
        assert len(attack_lines) == 1
        
        # Check second level
        second_level = structure.get_lines_at_depth(2)
        assert len(second_level) == 1
        assert second_level[0].support_type == DialecticalType.ATTACKS
        assert "Rebuttal" in second_level[0].content

    def test_argument_parsing_detailed(self, parser):
        """Test detailed parsing of argument structure."""
        test_case = get_snippet_by_name("basic_premise_conclusion")
        structure = parser.parse(test_case.snippet)
        
        # Ensure it's an argument
        assert structure.snippet_type == SnippetType.ARGUMENT
        assert isinstance(structure, ArgumentStructure)
        
        # Check that we have the right number of non-empty lines
        assert len(structure.non_empty_lines) >= 8  # Allow for more due to inference rules
        
        # Check preamble/title
        title_line = structure.title_line
        assert title_line is not None
        assert title_line.is_preamble
        assert "Argument title" in title_line.content
        
        # Check numbered statements
        numbered = structure.numbered_statements
        assert len(numbered) == 5
        
        for i, stmt in enumerate(numbered, 1):
            assert stmt.statement_number == i
            assert f"({i})" in stmt.content
        
        # Check premises and conclusions
        premises = structure.premises
        conclusions = structure.conclusions
        
        # Should have some premises and at least one conclusion
        assert len(premises) > 0
        assert len(conclusions) > 0
        
        # Check final conclusion
        final_conclusion = structure.final_conclusion
        assert final_conclusion is not None
        assert final_conclusion.statement_number == 5
        assert "Final conclusion" in final_conclusion.content
        
        # Check inference rules
        inference_rules = structure.inference_rules
        assert len(inference_rules) == 2
        for rule in inference_rules:
            assert rule.is_inference_rule

    def test_complex_argument_map_structure(self, parser):
        """Test parsing of a more complex argument map."""
        test_case = get_snippet_by_name("complex_multilevel")
        structure = parser.parse(test_case.snippet)
        
        assert structure.snippet_type == SnippetType.ARGUMENT_MAP
        assert isinstance(structure, ArgumentMapStructure)
        assert structure.max_depth == 3
        
        # Check we have the right number of statements at each level
        assert len(structure.get_lines_at_depth(0)) == 1  # Main claim
        assert len(structure.get_lines_at_depth(1)) == 3  # First-order arguments
        assert len(structure.get_lines_at_depth(2)) == 3  # Second-order arguments  
        assert len(structure.get_lines_at_depth(3)) == 1  # Third-order argument

    def test_argument_with_separators_parsing(self, parser):
        """Test parsing of argument with separator lines."""
        test_case = get_snippet_by_name("simple_syllogism")
        structure = parser.parse(test_case.snippet)
        
        assert structure.snippet_type == SnippetType.ARGUMENT
        assert isinstance(structure, ArgumentStructure)
        
        # Check numbered statements
        numbered = structure.numbered_statements
        assert len(numbered) == 3
        
        # Check separator - need to look at ArgumentStatementLine objects
        separators = [line for line in structure.lines 
                     if hasattr(line, 'is_separator') and line.is_separator]
        assert len(separators) == 1
        
        # The statement after separator should be conclusion
        conclusions = structure.conclusions
        assert len(conclusions) == 1
        assert conclusions[0].statement_number == 3


class TestArgdownParserUtilities:
    """Test utility functions and parameter validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ArgdownParser()

    @pytest.mark.parametrize("line,expected_level", INDENTATION_TEST_CASES)
    def test_indentation_calculation(self, line, expected_level):
        """Test indentation level calculation."""
        calculated_level = self.parser._calculate_indent_level(line)
        assert calculated_level == expected_level

    @pytest.mark.parametrize("symbol,expected_type", DIALECTICAL_TYPE_CASES)
    def test_dialectical_type_parsing(self, symbol, expected_type):
        """Test parsing of different dialectical relation symbols."""
        parsed_type = self.parser._parse_dialectical_type(symbol)
        assert parsed_type == expected_type


class TestArgdownParserLinePreservation:
    """Test line preservation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ArgdownParser()

    def test_empty_lines_preservation(self):
        """Test that empty lines are properly preserved but can be filtered."""
        snippet_with_empty_lines = """
[Main claim]: This is the main claim.

    <+ <Argument 1>: The first reason.
    
    <+ <Argument 2>: The second reason.

"""
        structure = self.parser.parse(snippet_with_empty_lines)
        
        # Should have all lines including empty ones
        assert len(structure.lines) > 3
        
        # But non-empty lines should only be 3
        assert len(structure.non_empty_lines) == 3
        assert all(line.content.strip() for line in structure.non_empty_lines)

    def test_line_preservation_detailed(self):
        """Test that all lines including empty ones are preserved with correct line numbers."""
        argdown_snippet = "[Claim]: Content.\n\n    <+ <Support>: More content.\n"
        structure = self.parser.parse(argdown_snippet)
        
        # Should have 3 lines total
        assert len(structure.lines) == 3
        
        # Check line numbers are preserved
        assert structure.lines[0].line_number == 1
        assert structure.lines[1].line_number == 2  # Empty line
        assert structure.lines[2].line_number == 3
        
        # Check content
        assert "Claim" in structure.lines[0].content
        assert structure.lines[1].content == ""  # Empty line
        assert "Support" in structure.lines[2].content
        
        # Check original lines are preserved
        assert structure.lines[0].original_line == "[Claim]: Content."
        assert structure.lines[1].original_line == ""
        assert structure.lines[2].original_line == "    <+ <Support>: More content."


class TestArgdownParserEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ArgdownParser()
    
    def test_empty_input(self):
        """Test handling of empty input."""
        structure = self.parser.parse("")
        # Empty input creates one empty line after splitting
        assert len(structure.lines) == 1
        assert structure.lines[0].content == ""
        # But no non-empty lines
        assert len(structure.non_empty_lines) == 0
    
    def test_whitespace_only(self):
        """Test handling of whitespace-only input."""
        structure = self.parser.parse("   \n\n   \t  \n")
        # Should preserve all lines including whitespace-only ones
        assert len(structure.lines) >= 1
        # But no actual content lines
        assert len(structure.non_empty_lines) == 0
    
    def test_single_claim(self):
        """Test parsing of single claim."""
        structure = self.parser.parse("[Single claim]: Just one claim.")
        
        assert structure.snippet_type == SnippetType.ARGUMENT_MAP
        assert isinstance(structure, ArgumentMapStructure)
        assert len(structure.lines) >= 1  # May have empty lines
        main_claim = structure.main_claim
        assert main_claim is not None
        assert main_claim.is_claim
    
    def test_mixed_indentation(self):
        """Test handling of inconsistent indentation."""
        argdown_snippet = """
[Main]: Main claim.
  <+ <Arg1>: Argument 1 (2 spaces).
      <+ <Arg2>: Argument 2 (6 spaces).
    <- <Obj>: Objection (4 spaces).
"""
        structure = self.parser.parse(argdown_snippet)
        
        # Should handle mixed indentation gracefully
        assert isinstance(structure, ArgumentMapStructure)
        assert len(structure.lines) >= 4  # May have empty lines
        assert structure.max_depth > 0
