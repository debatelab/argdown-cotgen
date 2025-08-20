"""Integration tests using the examples from README.md."""

from src.argdown_cotgen.core import (
    ArgdownParser, 
    SnippetType,
    ArgumentMapStructure,
    ArgumentStructure
)


class TestReadmeExamples:
    """Test the exact examples from the README file."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ArgdownParser()
    
    def test_readme_argument_map_example(self):
        """Test the argument map example from README."""
        argdown_snippet = """
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.
    <+ <Argument 2>: The second reason.
    <- <Objection>: An objection to the main claim.
        <- <Rebuttal>: The objection can be rebutted. 
"""
        structure = self.parser.parse(argdown_snippet)
        
        # Verify it's detected as argument map
        assert structure.snippet_type == SnippetType.ARGUMENT_MAP
        assert isinstance(structure, ArgumentMapStructure)
        
        # Check basic structure
        assert len(structure.statement_lines) == 5
        assert structure.max_depth == 2
        
        # Check main claim exists
        main_claim = structure.main_claim
        assert main_claim is not None
        assert "Main claim" in main_claim.content
        
        # Check we have arguments at different levels
        first_level = structure.get_lines_at_depth(1)
        second_level = structure.get_lines_at_depth(2)
        
        assert len(first_level) == 3  # 2 supports + 1 attack
        assert len(second_level) == 1  # 1 rebuttal
        
        # Verify content
        assert any("Argument 1" in line.content for line in first_level)
        assert any("Argument 2" in line.content for line in first_level)
        assert any("Objection" in line.content for line in first_level)
        assert any("Rebuttal" in line.content for line in second_level)
    
    def test_readme_argument_example(self):
        """Test the argument example from README."""
        argdown_snippet = """
<Argument title>: Gist of the argument.

(1) Premise 1.
(2) Premise 2.
-- inference rule --
(3) Intermediary conclusion 1.
(4) Premise 3.
-- inference rule --
(5) Final conclusion.
"""
        structure = self.parser.parse(argdown_snippet)
        
        # Verify it's detected as argument
        assert structure.snippet_type == SnippetType.ARGUMENT
        assert isinstance(structure, ArgumentStructure)
        
        # Check we have the right components
        assert structure.title_line is not None
        assert "Argument title" in structure.title_line.content
        
        # Check numbered statements
        numbered = structure.numbered_statements
        assert len(numbered) == 5
        
        # Check specific statements exist
        statement_contents = [stmt.content for stmt in numbered]
        assert any("Premise 1" in content for content in statement_contents)
        assert any("Premise 2" in content for content in statement_contents)
        assert any("Intermediary conclusion" in content for content in statement_contents)
        assert any("Premise 3" in content for content in statement_contents)
        assert any("Final conclusion" in content for content in statement_contents)
        
        # Check inference rules
        inference_rules = structure.inference_rules
        assert len(inference_rules) == 2
        
        # Check final conclusion
        final_conclusion = structure.final_conclusion
        assert final_conclusion is not None
        assert final_conclusion.statement_number == 5
        assert "Final conclusion" in final_conclusion.content
    
    def test_mixed_content_detection(self):
        """Test that we can distinguish between argument types."""
        
        # This should be detected as argument map
        map_snippet = "[Claim]: A claim.\n    <+ <Support>: Supporting argument."
        map_structure = self.parser.parse(map_snippet)
        assert map_structure.snippet_type == SnippetType.ARGUMENT_MAP
        
        # This should be detected as argument
        arg_snippet = "(1) Premise.\n-----\n(2) Conclusion."
        arg_structure = self.parser.parse(arg_snippet)
        assert arg_structure.snippet_type == SnippetType.ARGUMENT
        
        # This should also be detected as argument (has numbered statements)
        numbered_snippet = "(1) First premise.\n(2) Second premise."
        numbered_structure = self.parser.parse(numbered_snippet)
        assert numbered_structure.snippet_type == SnippetType.ARGUMENT
