"""
Test cases specifically for comment detection in argdown parser.
"""

from src.argdown_cotgen.core.parser import ArgdownParser


class TestCommentDetection:
    """Test comment detection functionality."""
    
    def test_inline_comment_detection(self):
        """Test detection of inline comments."""
        parser = ArgdownParser()
        snippet = """
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.  // This is an inline comment
    <- <Objection>: An objection.
"""
        result = parser.parse(snippet.strip())
        
        # Find the line with the inline comment
        comment_line = None
        for line in result.lines:
            if "first reason" in line.content:
                comment_line = line
                break
        
        assert comment_line is not None
        assert comment_line.has_comment
        assert comment_line.comment_content == "This is an inline comment"
        assert "first reason" in comment_line.content
        assert "//" not in comment_line.content  # Comment should be stripped from content
    
    def test_standalone_comment_detection(self):
        """Test detection of standalone comments."""
        parser = ArgdownParser()
        snippet = """
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.
    // This is a standalone comment
    <- <Objection>: An objection.
"""
        result = parser.parse(snippet.strip())
        
        # Find the standalone comment line
        comment_line = None
        for line in result.lines:
            if line.has_comment and line.content.strip() == "":
                comment_line = line
                break
        
        assert comment_line is not None
        assert comment_line.has_comment
        assert comment_line.comment_content == "This is a standalone comment"
        assert comment_line.content.strip() == ""  # Content should be empty after comment removal
    
    def test_no_comment_lines(self):
        """Test that lines without comments are correctly identified."""
        parser = ArgdownParser()
        snippet = """
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.
    <- <Objection>: An objection.
"""
        result = parser.parse(snippet.strip())
        
        # None of these lines should have comments
        for line in result.lines:
            assert not line.has_comment
            assert line.comment_content is None
    
    def test_multiline_comment_structure(self):
        """Test that multiline comments are preserved as separate lines."""
        parser = ArgdownParser()
        snippet = """
[Main claim]: This is the main claim.
    /* This is a multiline comment
       that spans multiple lines
       and should be preserved */
    <+ <Argument 1>: The first reason.
"""
        result = parser.parse(snippet.strip())
        
        # Should have 4 lines: main claim, and 3 lines of multiline comment, and argument
        assert len(result.lines) == 5
        
        # Check that multiline comment lines are preserved
        multiline_content = []
        for line in result.lines:
            if "multiline comment" in line.content or "spans multiple" in line.content or "should be preserved" in line.content:
                multiline_content.append(line.content.strip())
        
        assert len(multiline_content) == 3
        assert "This is a multiline comment" in multiline_content[0]
        assert "that spans multiple lines" in multiline_content[1]
        assert "and should be preserved" in multiline_content[2]
    
    def test_comment_content_preservation(self):
        """Test that comment content is properly extracted and preserved."""
        parser = ArgdownParser()
        snippet = """
[Main claim]: This is the main claim.  // Comment with special chars: !@#$%^&*()
    <+ <Argument 1>: Reason.  // Another comment with "quotes" and 'apostrophes'
"""
        result = parser.parse(snippet.strip())
        
        comments_found = []
        for line in result.lines:
            if line.has_comment:
                comments_found.append(line.comment_content)
        
        assert len(comments_found) == 2
        assert "Comment with special chars: !@#$%^&*()" in comments_found
        assert 'Another comment with "quotes" and \'apostrophes\'' in comments_found
