"""Tests for placeholder comment feature in by_rank strategy."""

from src.argdown_cotgen import CotGenerator


def test_placeholder_comments_in_early_steps():
    """Test that placeholder comments are added when content exists at deeper levels."""
    argdown_text = """[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.
    <+ <Argument 2>: The second reason.
    <- <Objection>: An objection to the main claim.
        <- <Rebuttal>: The objection can be rebutted.
"""
    
    generator = CotGenerator(pipe_type="by_rank")
    result = generator.generate(argdown_text)
    
    # Step 1 (roots only) should have a placeholder comment at level 1
    step1_content = result.steps[0].content
    assert "//" in step1_content
    placeholder_keywords = ["arguments", "content", "missing", "add", "need"]
    step1_lower = step1_content.lower()
    assert any(keyword in step1_lower for keyword in placeholder_keywords), f"Expected placeholder comment in: {step1_content}"
    
    # Step 2 (first order) should have a placeholder comment at level 2  
    step2_content = result.steps[1].content
    assert "//" in step2_content
    step2_lower = step2_content.lower()
    assert any(keyword in step2_lower for keyword in placeholder_keywords), f"Expected placeholder comment in: {step2_content}"
    
    # Step 3 (second order) should NOT have placeholder comment (no deeper content)
    step3_content = result.steps[2].content
    placeholder_keywords = ["arguments", "content", "missing", "add", "need"]
    placeholder_lines = [line for line in step3_content.split('\n') 
                        if '//' in line and any(keyword in line.lower() for keyword in placeholder_keywords)]
    assert len(placeholder_lines) == 0


def test_no_placeholder_when_no_deeper_content():
    """Test that no placeholder comments are added when there's no deeper content."""
    argdown_text = """[Main claim]: This is the main claim."""
    
    generator = CotGenerator(pipe_type="by_rank")
    result = generator.generate(argdown_text)
    
    # Should only have one step with no placeholder comments
    step1_content = result.steps[0].content
    assert "//" not in step1_content


def test_placeholder_comment_indentation():
    """Test that placeholder comments are indented correctly."""
    argdown_text = """[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.
        <- <Objection>: An objection.
"""
    
    generator = CotGenerator(pipe_type="by_rank")
    result = generator.generate(argdown_text)
    
    # Step 1: placeholder should be at 4 spaces (under Main claim)
    step1_lines = result.steps[0].content.split('\n')
    placeholder_line = [line for line in step1_lines if '//' in line][0]
    assert placeholder_line.startswith('    //')  # 4 spaces
    
    # Step 2: placeholder should be at 8 spaces (under Argument 1)  
    step2_lines = result.steps[1].content.split('\n')
    placeholder_lines = [line for line in step2_lines if '//' in line]
    # Find the placeholder under Argument 1 (deeper indentation)
    arg1_placeholder = [line for line in placeholder_lines if line.startswith('        //')]
    assert len(arg1_placeholder) > 0, "Should have placeholder under Argument 1"
    assert arg1_placeholder[0].startswith('        //')  # 8 spaces


def test_random_placeholder_variations():
    """Test that different placeholder comment variations are used."""
    argdown_text = """[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.
"""
    
    generator = CotGenerator(pipe_type="by_rank")
    
    # Generate multiple times to see different variations
    placeholder_texts = set()
    for _ in range(10):
        result = generator.generate(argdown_text)
        step1_content = result.steps[0].content
        placeholder_line = [line for line in step1_content.split('\n') if '//' in line][0]
        placeholder_text = placeholder_line.strip()
        placeholder_texts.add(placeholder_text)
    
    # Should have at least 2 different variations in 10 runs
    assert len(placeholder_texts) >= 2


def test_placeholder_comment_positioned_correctly_in_middle():
    """Test that placeholder comments appear in the correct position, not just at the end."""
    argdown_text = """[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.
    <+ <Argument 2>: The second reason.
        <- <Sub-objection>: A deeper argument under Argument 2.
    <- <Objection>: An objection to the main claim.
"""
    
    generator = CotGenerator(pipe_type="by_rank")
    result = generator.generate(argdown_text)
    
    # Step 2 should show first order arguments with placeholder under Argument 2
    step2_content = result.steps[1].content
    lines = step2_content.split('\n')
    
    # Find the indices of key lines
    arg2_index = None
    objection_index = None
    placeholder_index = None
    
    for i, line in enumerate(lines):
        if '<Argument 2>' in line:
            arg2_index = i
        elif '<Objection>' in line:
            objection_index = i
        elif '//' in line:
            placeholder_keywords = ["arguments", "content", "missing", "add", "need"]
            if any(keyword in line.lower() for keyword in placeholder_keywords):
                placeholder_index = i
    
    # Verify the structure is correct
    assert arg2_index is not None, "Should find Argument 2"
    assert objection_index is not None, "Should find Objection"
    assert placeholder_index is not None, "Should find placeholder comment"
    
    # The placeholder should be between Argument 2 and Objection
    assert arg2_index < placeholder_index < objection_index, \
        f"Placeholder at {placeholder_index} should be between Argument 2 at {arg2_index} and Objection at {objection_index}"
    
    # The placeholder should be indented more than Argument 2 (indicating it's under Argument 2)
    arg2_line = lines[arg2_index]
    placeholder_line = lines[placeholder_index]
    arg2_indent = len(arg2_line) - len(arg2_line.lstrip())
    placeholder_indent = len(placeholder_line) - len(placeholder_line.lstrip())
    
    assert placeholder_indent > arg2_indent, \
        f"Placeholder indent {placeholder_indent} should be greater than Argument 2 indent {arg2_indent}"
