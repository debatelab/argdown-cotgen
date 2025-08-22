"""
Test cases specifically for YAML inline data extraction in argdown parser.
"""

from src.argdown_cotgen.core.parser import ArgdownParser


class TestYamlInlineDataExtraction:
    """Test YAML inline data extraction functionality."""
    
    def test_yaml_inline_data_extraction(self):
        """Test extraction of YAML inline data."""
        parser = ArgdownParser()
        snippet = """
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason. {key1: "value1"}
    <- <Objection>: An objection. {type: "attack", strength: 0.8}
"""
        result = parser.parse(snippet.strip())
        
        # Find lines with YAML data
        yaml_lines = [line for line in result.lines if line.yaml_inline_data]
        
        assert len(yaml_lines) == 2
        
        # Check first line with YAML
        arg1_line = next(line for line in result.lines if "first reason" in line.content)
        assert arg1_line.yaml_inline_data == '{key1: "value1"}'
        assert "first reason" in arg1_line.content
        assert "{" not in arg1_line.content  # YAML should be stripped from content
        
        # Check second line with YAML
        objection_line = next(line for line in result.lines if "objection" in line.content)
        assert objection_line.yaml_inline_data == '{type: "attack", strength: 0.8}'
        assert "objection" in objection_line.content
        assert "{" not in objection_line.content  # YAML should be stripped from content
    
    def test_yaml_and_comment_together(self):
        """Test that YAML inline data and comments can coexist."""
        parser = ArgdownParser()
        snippet = """
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason. {key1: "value1"} // This is a comment
    <- <Objection>: An objection. {type: "attack"} // Another comment
"""
        result = parser.parse(snippet.strip())
        
        # Find the line with both YAML and comment
        arg1_line = next(line for line in result.lines if "first reason" in line.content)
        assert arg1_line.yaml_inline_data == '{key1: "value1"}'
        assert arg1_line.has_comment
        assert arg1_line.comment_content == "This is a comment"
        assert "first reason" in arg1_line.content
        assert "{" not in arg1_line.content  # YAML should be stripped
        assert "//" not in arg1_line.content  # Comment should be stripped
        
        objection_line = next(line for line in result.lines if "objection" in line.content)
        assert objection_line.yaml_inline_data == '{type: "attack"}'
        assert objection_line.has_comment
        assert objection_line.comment_content == "Another comment"
    
    def test_no_yaml_lines(self):
        """Test that lines without YAML are correctly identified."""
        parser = ArgdownParser()
        snippet = """
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.
    <- <Objection>: An objection.
"""
        result = parser.parse(snippet.strip())
        
        # None of these lines should have YAML data
        for line in result.lines:
            assert line.yaml_inline_data is None
    
    def test_complex_yaml_extraction(self):
        """Test extraction of complex YAML structures."""
        parser = ArgdownParser()
        snippet = """
[Main claim]: This is the main claim.
    <+ <Argument 1>: Complex YAML. {nested: {key: "value"}, array: [1, 2, 3]}
    <- <Objection>: Simple YAML. {flag: true, number: 42}
"""
        result = parser.parse(snippet.strip())
        
        # Check complex YAML extraction
        arg1_line = next(line for line in result.lines if "Complex YAML" in line.content)
        assert arg1_line.yaml_inline_data == '{nested: {key: "value"}, array: [1, 2, 3]}'
        
        objection_line = next(line for line in result.lines if "Simple YAML" in line.content)
        assert objection_line.yaml_inline_data == '{flag: true, number: 42}'
    
    def test_yaml_with_spaces_before_comment(self):
        """Test YAML extraction when there are spaces before a comment."""
        parser = ArgdownParser()
        snippet = """
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason. {key: "value"}   // Comment with spaces
"""
        result = parser.parse(snippet.strip())
        
        arg1_line = next(line for line in result.lines if "first reason" in line.content)
        assert arg1_line.yaml_inline_data == '{key: "value"}'
        assert arg1_line.has_comment
        assert arg1_line.comment_content == "Comment with spaces"
        assert "first reason" in arg1_line.content
