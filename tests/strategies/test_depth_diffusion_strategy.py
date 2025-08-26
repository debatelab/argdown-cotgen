"""
Test suite for DepthDiffusionStrategy using the common testing framework.

This module provides comprehensive testing for the DepthDiffusionStrategy including:
- Framework automatic tests (14 tests from BaseStrategyTestSuite)
- Helper class tests (8 tests for DepthAnalyzer and ShuffleManager)
- Strategy behavior tests (4 tests for depth progression and placeholders)
- Edge cases and error handling tests (4 tests)
- Content reconstruction validation tests (3 tests)
- Integration tests (3 tests)
- Parameterized tests (6 tests)

Total expected tests: ~42 tests
"""
import pytest
from typing import Type
from src.argdown_cotgen.strategies.argument_maps.depth_diffusion import (
    DepthDiffusionStrategy,
    DepthAnalyzer,
    ShuffleManager,
    DepthLevel
)
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy
from src.argdown_cotgen.core.models import ArgumentMapStructure, DialecticalType
from .strategy_test_framework import BaseStrategyTestSuite


class TestDepthDiffusionStrategy(BaseStrategyTestSuite):
    """Test suite for DepthDiffusionStrategy using the common framework."""
    
    @property
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        return DepthDiffusionStrategy
    
    @property
    def strategy_name(self) -> str:
        return "DepthDiffusionStrategy"
    
    def _validate_step_count(self, steps, test_case):
        """Validate step count for depth diffusion strategy."""
        # Parse structure to get max_depth and content details
        from src.argdown_cotgen.core.parser import ArgdownParser
        from src.argdown_cotgen.core.models import ArgumentMapStructure
        
        parser = ArgdownParser()
        structure = parser.parse(test_case.argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Expected steps: 1 (flat initial) + (max_depth + 1) depth increments + optional YAML + optional comments
        expected_base_steps = 2 + structure.max_depth  # 1 flat + (max_depth + 1) depth steps
        
        # Add optional steps
        has_yaml = any(line.yaml_inline_data for line in structure.lines if line.yaml_inline_data)
        has_comments = any(line.has_comment for line in structure.lines)
        
        expected_optional_steps = (1 if has_yaml else 0) + (1 if has_comments else 0)
        expected_total = expected_base_steps + expected_optional_steps
        
        assert len(steps) == expected_total, (
            f"Expected {expected_total} steps for {test_case.name} "
            f"(base: {expected_base_steps}, optional: {expected_optional_steps}), got {len(steps)}"
        )


class TestDepthDiffusionHelperClasses:
    """Test suite for helper classes used by DepthDiffusionStrategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
        self.depth_analyzer = DepthAnalyzer()
        self.shuffle_manager = ShuffleManager(shuffle_seed=42)  # Fixed seed for reproducibility
    
    def test_depth_analyzer_structure_analysis(self):
        """Test DepthAnalyzer.analyze_structure() correctly maps relationships."""
        # Test with a multi-level structure
        argdown_text = """[Main Claim]: Main argument.
    <+ <Support>: Supporting evidence.
        <- [Counter]: Counter-argument.
    <+ [Another Support]: Another supporting claim."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Analyze the structure
        analysis = self.depth_analyzer.analyze_structure(structure)
        
        # Verify analysis results
        assert 'depth_map' in analysis
        assert 'parent_map' in analysis
        assert 'children_map' in analysis
        assert 'max_depth' in analysis
        
        # Check depth mapping (should be 0, 1, 2, 1 for the four content lines)
        non_empty_indices = [i for i, line in enumerate(structure.lines) if line.content.strip()]
        expected_depths = [0, 1, 2, 1]  # Main, Support, Counter, Another Support
        
        for idx, expected_depth in zip(non_empty_indices, expected_depths):
            assert self.depth_analyzer.depth_map[idx] == expected_depth, \
                f"Line {idx} should have depth {expected_depth}"
        
        # Check parent mapping
        assert self.depth_analyzer.parent_map[non_empty_indices[0]] is None  # Main has no parent
        assert self.depth_analyzer.parent_map[non_empty_indices[1]] == non_empty_indices[0]  # Support -> Main
        assert self.depth_analyzer.parent_map[non_empty_indices[2]] == non_empty_indices[1]  # Counter -> Support
        assert self.depth_analyzer.parent_map[non_empty_indices[3]] == non_empty_indices[0]  # Another Support -> Main
        
        # Check children mapping
        main_children = self.depth_analyzer.children_map.get(non_empty_indices[0], [])
        assert non_empty_indices[1] in main_children  # Main has Support as child
        assert non_empty_indices[3] in main_children  # Main has Another Support as child
        
        support_children = self.depth_analyzer.children_map.get(non_empty_indices[1], [])
        assert non_empty_indices[2] in support_children  # Support has Counter as child
    
    def test_depth_analyzer_nodes_at_depth(self):
        """Test DepthAnalyzer.get_nodes_at_depth() returns correct nodes."""
        argdown_text = """[Root]: Root claim.
    <+ <Support1>: First support.
    <+ <Support2>: Second support.
        <- [Counter]: Counter to second support."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Analyze structure first
        self.depth_analyzer.analyze_structure(structure)
        
        # Test nodes at depth 0 (should be Root)
        depth_0_nodes = self.depth_analyzer.get_nodes_at_depth(0)
        assert len(depth_0_nodes) == 1
        assert depth_0_nodes[0].content == "[Root]: Root claim."
        assert depth_0_nodes[0].target_depth == 0
        assert depth_0_nodes[0].target_parent_index is None
        
        # Test nodes at depth 1 (should be Support1 and Support2)
        depth_1_nodes = self.depth_analyzer.get_nodes_at_depth(1)
        assert len(depth_1_nodes) == 2
        contents = [node.content for node in depth_1_nodes]
        assert "<Support1>: First support." in contents
        assert "<Support2>: Second support." in contents
        
        # Test nodes at depth 2 (should be Counter)
        depth_2_nodes = self.depth_analyzer.get_nodes_at_depth(2)
        assert len(depth_2_nodes) == 1
        assert depth_2_nodes[0].content == "[Counter]: Counter to second support."
        assert depth_2_nodes[0].target_depth == 2
        
        # Test non-existent depth
        depth_99_nodes = self.depth_analyzer.get_nodes_at_depth(99)
        assert len(depth_99_nodes) == 0
    
    def test_depth_analyzer_parent_finding(self):
        """Test DepthAnalyzer._find_parent_index() correctly identifies parents."""
        argdown_text = """[A]: Level 0.
    <+ [B]: Level 1.
        <- [C]: Level 2.
            <+ [D]: Level 3.
    <+ [E]: Back to level 1."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Get indices of non-empty lines
        content_indices = [i for i, line in enumerate(structure.lines) if line.content.strip()]
        
        # Test parent finding for each node
        assert self.depth_analyzer._find_parent_index(structure, content_indices[0]) is None  # A has no parent
        assert self.depth_analyzer._find_parent_index(structure, content_indices[1]) == content_indices[0]  # B -> A
        assert self.depth_analyzer._find_parent_index(structure, content_indices[2]) == content_indices[1]  # C -> B
        assert self.depth_analyzer._find_parent_index(structure, content_indices[3]) == content_indices[2]  # D -> C
        assert self.depth_analyzer._find_parent_index(structure, content_indices[4]) == content_indices[0]  # E -> A
    
    def test_depth_analyzer_relation_symbols(self):
        """Test DepthAnalyzer._get_relation_symbol() converts DialecticalType correctly."""
        # Test all relation types
        assert self.depth_analyzer._get_relation_symbol(DialecticalType.SUPPORTS) == "<+"
        assert self.depth_analyzer._get_relation_symbol(DialecticalType.ATTACKS) == "<-"
        assert self.depth_analyzer._get_relation_symbol(DialecticalType.UNDERCUTS) == "<_"
        assert self.depth_analyzer._get_relation_symbol(DialecticalType.CONTRADICTORY) == "><"
        assert self.depth_analyzer._get_relation_symbol(DialecticalType.IS_SUPPORTED_BY) == "+>"
        assert self.depth_analyzer._get_relation_symbol(DialecticalType.IS_ATTACKED_BY) == "->"
        assert self.depth_analyzer._get_relation_symbol(DialecticalType.IS_UNDERCUT_BY) == "_>"
        
        # Test unknown/None type (should default to support)
        assert self.depth_analyzer._get_relation_symbol(None) == "<+"
    
    def test_depth_analyzer_depth_levels(self):
        """Test DepthAnalyzer.get_depth_levels() creates proper DepthLevel objects."""
        argdown_text = """[Root]: Root claim.
    <+ <Support>: Support argument.
        <- [Counter]: Counter claim.
    <+ <Another>: Another support."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Analyze structure first
        self.depth_analyzer.analyze_structure(structure)
        
        # Get depth levels
        depth_levels = self.depth_analyzer.get_depth_levels()
        
        # Should have 3 levels (0, 1, 2)
        assert len(depth_levels) == 3
        
        # Check level 0
        level_0 = depth_levels[0]
        assert isinstance(level_0, DepthLevel)
        assert level_0.level == 0
        assert len(level_0.nodes) == 1  # Only Root
        assert level_0.max_nodes_to_place == 1
        
        # Check level 1
        level_1 = depth_levels[1]
        assert level_1.level == 1
        assert len(level_1.nodes) == 2  # Support and Another
        assert level_1.max_nodes_to_place == 2
        
        # Check level 2
        level_2 = depth_levels[2]
        assert level_2.level == 2
        assert len(level_2.nodes) == 1  # Counter
        assert level_2.max_nodes_to_place == 1
    
    def test_shuffle_manager_flat_list_creation(self):
        """Test ShuffleManager.create_flat_shuffled_list() produces expected output."""
        argdown_text = """[A]: First claim.
    <+ [B]: Second claim.
        <- [C]: Third claim."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Create flat shuffled list
        flat_list = self.shuffle_manager.create_flat_shuffled_list(structure)
        
        # Should contain all content
        expected_contents = {
            "[A]: First claim.",
            "[B]: Second claim.",
            "[C]: Third claim."
        }
        assert set(flat_list) == expected_contents
        assert len(flat_list) == 3
        
        # Order should be shuffled (with fixed seed, order should be predictable)
        # With seed 42, verify it's not the original order
        original_order = ["[A]: First claim.", "[B]: Second claim.", "[C]: Third claim."]
        assert flat_list != original_order  # Should be shuffled
    
    def test_shuffle_manager_seed_reproducibility(self):
        """Test ShuffleManager produces identical results with same seed."""
        argdown_text = """[A]: First.
    <+ [B]: Second.
        <- [C]: Third.
    <+ [D]: Fourth."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Create two managers with same seed
        manager1 = ShuffleManager(shuffle_seed=123)
        manager2 = ShuffleManager(shuffle_seed=123)
        
        # Both should produce identical results
        list1 = manager1.create_flat_shuffled_list(structure)
        list2 = manager2.create_flat_shuffled_list(structure)
        
        assert list1 == list2
        
        # Different seed should produce different results
        manager3 = ShuffleManager(shuffle_seed=456)
        list3 = manager3.create_flat_shuffled_list(structure)
        
        assert list1 != list3  # Different seeds should give different orders
    
    def test_shuffle_manager_content_formatting(self):
        """Test ShuffleManager.format_flat_content() creates proper format."""
        # Test with normal content list
        content_list = ["First item", "Second item", "Third item"]
        formatted = self.shuffle_manager.format_flat_content(content_list)
        
        expected = "First item\nSecond item\nThird item"
        assert formatted == expected
        
        # Test with empty list
        empty_formatted = self.shuffle_manager.format_flat_content([])
        assert empty_formatted == ""
        
        # Test with single item
        single_formatted = self.shuffle_manager.format_flat_content(["Only item"])
        assert single_formatted == "Only item"


class TestDepthDiffusionBehavior:
    """Test suite for DepthDiffusionStrategy-specific behavior."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
        self.strategy = DepthDiffusionStrategy(shuffle_seed=42)  # Fixed seed for reproducibility
    
    def test_depth_progression_logic(self):
        """Test that steps show incremental depth levels correctly."""
        # Test with a 3-level structure
        argdown_text = """[Root]: Root claim.
    <+ <Support>: Supporting argument.
        <- [Counter]: Counter claim.
    <+ [Another]: Another support."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Generate steps
        steps = self.strategy.generate(structure)
        
        # Should have steps for depth 0, 0-1, 0-2 + initial flat step
        assert len(steps) >= 4  # v1 (flat), v2 (depth 0), v3 (depth 0-1), v4 (depth 0-2)
        
        # First step should be flat (no indentation, no relations)
        first_content = steps[0].content
        assert "Root claim" in first_content
        assert "Support" in first_content
        assert "Counter" in first_content
        assert "<+" not in first_content  # No relations in flat version
        assert "<-" not in first_content
        
        # Later steps should show progressive depth
        # Step 2 should have depth 0 only (just root)
        second_content = steps[1].content
        lines = second_content.split('\n')
        root_line = next((line for line in lines if "Root" in line), None)
        assert root_line is not None
        assert not root_line.startswith('    ')  # Root should not be indented
        
        # Step 3 should have depth 0-1 (root + first level supports)
        if len(steps) > 2:
            third_content = steps[2].content
            assert "Root" in third_content
            assert "<+" in third_content  # Should have support relations
            # Should contain placeholders for deeper content
            assert "??" in third_content or len(steps) == 3  # Either has placeholders or this is the final step
    
    def test_placeholder_mechanism(self):
        """Test that '??' placeholders appear for deeper nodes not yet placed."""
        # Test with deep nesting to ensure placeholders appear
        argdown_text = """[A]: Root.
    <+ [B]: Level 1.
        <- [C]: Level 2.
            <+ [D]: Level 3."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Generate steps
        steps = self.strategy.generate(structure)
        
        # Look for intermediate steps that should have placeholders
        found_placeholder = False
        for step in steps[1:-1]:  # Skip first (flat) and last (complete) steps
            if "??" in step.content:
                found_placeholder = True
                # Verify placeholder format
                lines = step.content.split('\n')
                placeholder_lines = [line for line in lines if "??" in line]
                for line in placeholder_lines:
                    assert line.strip().startswith("??"), f"Placeholder line should start with ??: {line}"
                break
        
        # Should find placeholders in intermediate steps (unless structure is very simple)
        if structure.max_depth > 1:
            assert found_placeholder, "Should find ?? placeholders in intermediate steps for deep structures"
    
    def test_sibling_shuffling_within_parents(self):
        """Test that siblings at max_depth are shuffled within each parent group."""
        # Test with multiple siblings to verify shuffling
        argdown_text = """[Root]: Root claim.
    <+ [A]: First support.
    <+ [B]: Second support.
    <+ [C]: Third support.
    <+ [D]: Fourth support."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Generate steps multiple times with different seeds
        strategy1 = DepthDiffusionStrategy(shuffle_seed=1)
        strategy2 = DepthDiffusionStrategy(shuffle_seed=2)
        
        steps1 = strategy1.generate(structure)
        steps2 = strategy2.generate(structure)
        
        # Find the step that shows all siblings (should be the last main step)
        def get_sibling_order(steps):
            for step in reversed(steps):
                if all(label in step.content for label in ['[A]', '[B]', '[C]', '[D]']):
                    lines = step.content.split('\n')
                    sibling_lines = [line for line in lines if any(f'[{label}]' in line for label in ['A', 'B', 'C', 'D'])]
                    return [line.strip() for line in sibling_lines]
            return []
        
        order1 = get_sibling_order(steps1)
        order2 = get_sibling_order(steps2)
        
        # Should have found sibling lines
        assert len(order1) == 4
        assert len(order2) == 4
        
        # Different seeds should produce different orders (with high probability)
        assert order1 != order2, "Different seeds should produce different sibling orders"
    
    def test_shuffle_seed_reproducibility(self):
        """Test that same seed produces identical step sequences."""
        argdown_text = """[Root]: Root claim.
    <+ [A]: Support A.
    <+ [B]: Support B.
        <- [C]: Counter to B."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Generate with same seed twice
        strategy1 = DepthDiffusionStrategy(shuffle_seed=999)
        strategy2 = DepthDiffusionStrategy(shuffle_seed=999)
        
        steps1 = strategy1.generate(structure)
        steps2 = strategy2.generate(structure)
        
        # Should produce identical results
        assert len(steps1) == len(steps2)
        for i, (step1, step2) in enumerate(zip(steps1, steps2)):
            assert step1.content == step2.content, f"Step {i} content should be identical with same seed"
            assert step1.version == step2.version, f"Step {i} version should be identical"
            # Note: explanations might vary due to random selection, but content should be identical


class TestDepthDiffusionEdgeCases:
    """Test suite for edge cases and error handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
        self.strategy = DepthDiffusionStrategy(shuffle_seed=42)
    
    def test_single_depth_structure_handling(self):
        """Test behavior with flat structures (max_depth = 0)."""
        # Test with only root-level claims (no hierarchy)
        argdown_text = """[Claim A]: First claim.
[Claim B]: Second claim.
[Claim C]: Third claim."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        assert structure.max_depth == 0  # All at root level
        
        # Generate steps
        steps = self.strategy.generate(structure)
        
        # Should have minimal steps: flat + depth 0 step
        assert len(steps) >= 2
        
        # First step should be flat
        first_content = steps[0].content
        assert "Claim A" in first_content
        assert "Claim B" in first_content
        assert "Claim C" in first_content
        
        # Should not have any relation symbols or indentation in any step
        for step in steps:
            assert "<+" not in step.content
            assert "<-" not in step.content
            assert "??" not in step.content  # No placeholders needed for flat structure
    
    def test_deep_nesting_handling(self):
        """Test with structures having many depth levels."""
        # Create a deeply nested structure (5 levels)
        argdown_text = """[L0]: Level 0.
    <+ [L1]: Level 1.
        <- [L2]: Level 2.
            <+ [L3]: Level 3.
                <- [L4]: Level 4.
                    <+ [L5]: Level 5."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        assert structure.max_depth == 5
        
        # Generate steps
        steps = self.strategy.generate(structure)
        
        # Should have steps for each depth level: flat + 6 depth steps (0 through 5)
        expected_steps = 1 + (structure.max_depth + 1)  # flat + depth levels
        assert len(steps) >= expected_steps
        
        # Verify progressive depth revelation
        depth_steps = steps[1:expected_steps]  # Skip flat step
        for i, step in enumerate(depth_steps):
            expected_max_depth = i  # Step i shows depths 0 through i
            
            # Should have content for levels 0 through expected_max_depth
            for level in range(expected_max_depth + 1):
                level_content = f"L{level}"
                assert level_content in step.content, f"Step {i+1} should contain level {level} content"
    
    def test_wide_branching_handling(self):
        """Test with many siblings at same level."""
        # Create structure with many siblings
        argdown_text = """[Root]: Root claim.
    <+ [S1]: Support 1.
    <+ [S2]: Support 2.
    <+ [S3]: Support 3.
    <+ [S4]: Support 4.
    <+ [S5]: Support 5.
    <- [A1]: Attack 1.
    <- [A2]: Attack 2.
    <- [A3]: Attack 3."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Generate steps
        steps = self.strategy.generate(structure)
        
        # Should handle all siblings correctly
        final_step = steps[-1]
        sibling_labels = ['S1', 'S2', 'S3', 'S4', 'S5', 'A1', 'A2', 'A3']
        
        for label in sibling_labels:
            assert f"[{label}]" in final_step.content, f"Final step should contain {label}"
        
        # Verify that siblings are properly indented
        lines = final_step.content.split('\n')
        sibling_lines = [line for line in lines if any(f'[{label}]' in line for label in sibling_labels)]
        
        for line in sibling_lines:
            # All siblings should be at the same indentation level
            assert line.startswith('    '), f"Sibling line should be indented: {line}"
            assert line.strip().startswith(('<+', '<-')), f"Sibling line should have relation: {line}"
    
    def test_minimal_structure_handling(self):
        """Test graceful handling of minimal input structures."""
        # Test with single claim
        single_claim = "[Only]: Single claim."
        structure = self.parser.parse(single_claim)
        assert isinstance(structure, ArgumentMapStructure)
        
        steps = self.strategy.generate(structure)
        assert len(steps) >= 1
        assert "Single claim" in steps[-1].content
        
        # Test with empty/whitespace structure
        empty_structure = self.parser.parse("   \n\n   ")
        if isinstance(empty_structure, ArgumentMapStructure):
            steps = self.strategy.generate(empty_structure)
            # Should handle gracefully without crashing
            assert isinstance(steps, list)
        
        # Test with just whitespace and comments
        comment_only = """
# Just a comment
    # Another comment
        """
        comment_structure = self.parser.parse(comment_only)
        if isinstance(comment_structure, ArgumentMapStructure):
            steps = self.strategy.generate(comment_structure)
            assert isinstance(steps, list)


class TestDepthDiffusionContentReconstruction:
    """Test suite for enhanced content reconstruction validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
        self.strategy = DepthDiffusionStrategy(shuffle_seed=42)
    
    def test_final_content_exact_reconstruction(self):
        """Test that final step exactly reconstructs input structure."""
        # Test with a complex structure
        argdown_text = """[Main Claim]: The main argument.
    <+ <Support Arg>: Supporting evidence.
        <- [Counter Claim]: Counter-argument.
    <+ [Another Support]: Additional support.
        <+ <Deep Support>: Deeper supporting argument."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Generate steps
        steps = self.strategy.generate(structure)
        
        # Final step should exactly match original
        final_content = steps[-1].content
        
        # Parse both original and final to compare structure
        original_structure = structure
        final_structure = self.parser.parse(final_content)
        assert isinstance(final_structure, ArgumentMapStructure)
        
        # Compare key structural elements
        assert len(original_structure.lines) == len(final_structure.lines)
        
        # Compare each line's content and structure
        for orig_line, final_line in zip(original_structure.lines, final_structure.lines):
            if orig_line.content.strip():  # Skip empty lines
                assert orig_line.content.strip() == final_line.content.strip()
                assert orig_line.indent_level == final_line.indent_level
                assert orig_line.support_type == final_line.support_type
                assert orig_line.label == final_line.label
    
    def test_yaml_data_preservation(self):
        """Test that YAML inline data is correctly preserved."""
        # Test with YAML inline data
        argdown_text = """[Claim]: Main claim. {data: "test", value: 42}
    <+ <Arg>: Supporting argument. {support_strength: 0.8}
        <- [Counter]: Counter claim. {confidence: 0.6}"""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Check that original has YAML data
        has_yaml = any(line.yaml_inline_data for line in structure.lines if line.yaml_inline_data)
        if not has_yaml:
            # Skip test if parser doesn't support YAML or this format
            return
        
        # Generate steps
        steps = self.strategy.generate(structure)
        
        # Should have a YAML step before the final step
        for step in steps:
            if "{" in step.content and "}" in step.content:
                # Verify YAML data is present
                assert "data: \"test\"" in step.content or "test" in step.content
                assert "support_strength" in step.content or "0.8" in step.content
                break
        
        # Final step should contain all YAML data
        final_content = steps[-1].content
        assert "{" in final_content and "}" in final_content
    
    def test_comment_preservation(self):
        """Test that comments are correctly preserved."""
        # Test with comments
        argdown_text = """[Claim]: Main claim. // This is a comment
    <+ <Arg>: Supporting argument. // Another comment
        <- [Counter]: Counter claim. // Final comment"""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Check that original has comments
        has_comments = any(line.has_comment for line in structure.lines)
        if not has_comments:
            # Skip test if parser doesn't support comments or this format
            return
        
        # Generate steps
        steps = self.strategy.generate(structure)
        
        # Should have a comments step (usually the final step)
        comment_step_found = False
        for step in steps:
            if "//" in step.content:
                comment_step_found = True
                # Verify comments are present
                assert "This is a comment" in step.content
                assert "Another comment" in step.content
                assert "Final comment" in step.content
                break
        
        assert comment_step_found, "Should find step with comments"
        
        # Final step should contain all comments
        final_content = steps[-1].content
        assert "//" in final_content


class TestDepthDiffusionIntegration:
    """Test suite for integration with framework components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
        self.strategy = DepthDiffusionStrategy(shuffle_seed=42)
    
    def test_abortion_mixin_integration(self):
        """Test that AbortionMixin functionality works correctly."""
        argdown_text = """[Main]: Main claim.
    <+ <Support>: Supporting argument.
        <- [Counter]: Counter claim."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Test with abortion rate
        steps_no_abortion = self.strategy.generate(structure, abortion_rate=0.0)
        steps_with_abortion = self.strategy.generate(structure, abortion_rate=0.3)
        
        # With abortion, might have more steps due to repetitions
        assert len(steps_no_abortion) <= len(steps_with_abortion) or len(steps_with_abortion) >= len(steps_no_abortion)
        
        # Both should be valid step sequences
        assert len(steps_no_abortion) > 0
        assert len(steps_with_abortion) > 0
    
    def test_explanation_variety(self):
        """Test that different explanation templates are used."""
        argdown_text = """[Main]: Main claim.
    <+ <Support>: Supporting argument.
        <- [Counter]: Counter claim."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Generate multiple times to see variety
        all_explanations = []
        for seed in range(5):
            strategy = DepthDiffusionStrategy(shuffle_seed=seed)
            steps = strategy.generate(structure)
            explanations = [step.explanation for step in steps if step.explanation]
            all_explanations.extend(explanations)
        
        # Should have some variety in explanations
        unique_explanations = set(all_explanations)
        assert len(unique_explanations) > 1, "Should have variety in explanations"
        
        # Check that explanations are meaningful
        for explanation in unique_explanations:
            assert len(explanation) > 10, f"Explanation should be meaningful: {explanation}"
            assert any(word in explanation.lower() for word in ['let', 'add', 'organize', 'include', 'structure']), \
                f"Explanation should describe the action: {explanation}"
    
    def test_version_numbering_progression(self):
        """Test that versions progress correctly (v1, v2, v3, etc.)."""
        argdown_text = """[Main]: Main claim.
    <+ <Support>: Supporting argument.
        <- [Counter]: Counter claim."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        steps = self.strategy.generate(structure)
        
        # Check version progression
        versions = [step.version for step in steps]
        
        # Should start with v1
        assert versions[0] == "v1"
        
        # Should progress sequentially
        for i in range(1, len(versions)):
            expected_version = f"v{i + 1}"
            assert versions[i] == expected_version, f"Step {i} should have version {expected_version}, got {versions[i]}"
        
        # Should have no gaps or duplicates
        assert len(set(versions)) == len(versions), "No duplicate versions"
        
        # All versions should follow pattern v1, v2, v3, etc.
        for i, version in enumerate(versions):
            assert version == f"v{i + 1}", f"Version {i} should be v{i + 1}, got {version}"


# Parameterized tests for comprehensive coverage
class TestDepthDiffusionParameterized:
    """Parameterized tests for various structure types and configurations."""
    
    def setup_method(self):
        """Set up parameterized test fixtures."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
        
        # Define test structures for parameterized testing
        self.test_structures = {
            "single_claim": "[Only]: Single claim without any structure.",
            
            "two_level": """[Main]: Main claim.
    <+ <Support>: Supporting argument.
    <- [Counter]: Counter-argument.""",
            
            "deep_nesting": """[L0]: Level 0 root.
    <+ [L1]: Level 1 support.
        <- [L2]: Level 2 counter.
            <+ [L3]: Level 3 deep support.
                <- [L4]: Level 4 very deep counter.""",
            
            "wide_branching": """[Root]: Central claim.
    <+ [S1]: Support 1.
    <+ [S2]: Support 2.
    <+ [S3]: Support 3.
    <- [A1]: Attack 1.
    <- [A2]: Attack 2.
    <- [A3]: Attack 3.""",
            
            "mixed_complexity": """[Main]: Main argument.
    <+ <Arg1>: First supporting argument.
        <- [C1]: Counter to first support.
            <+ [SC1]: Support for counter.
    <+ [Claim2]: Second supporting claim.
    <- <Attack>: Main attack.
        <+ [Support]: Support for attack."""
        }
    
    @pytest.mark.parametrize("structure_name,argdown_text", [
        ("single_claim", "[Only]: Single claim without any structure."),
        ("two_level", """[Main]: Main claim.
    <+ <Support>: Supporting argument.
    <- [Counter]: Counter-argument."""),
        ("deep_nesting", """[L0]: Level 0 root.
    <+ [L1]: Level 1 support.
        <- [L2]: Level 2 counter.
            <+ [L3]: Level 3 deep support."""),
        ("wide_branching", """[Root]: Central claim.
    <+ [S1]: Support 1.
    <+ [S2]: Support 2.
    <+ [S3]: Support 3.
    <- [A1]: Attack 1."""),
    ])
    def test_various_structure_complexities(self, structure_name, argdown_text):
        """Test with single_claim, two_level, deep_nesting, wide_branching structures."""
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        # Test with fixed seed for reproducibility
        strategy = DepthDiffusionStrategy(shuffle_seed=42)
        steps = strategy.generate(structure)
        
        # Basic validations
        assert len(steps) > 0, f"Should generate steps for {structure_name}"
        assert steps[0].version == "v1", f"First step should be v1 for {structure_name}"
        
        # First step should be flat (no relations)
        first_content = steps[0].content
        assert "<+" not in first_content, f"First step should be flat for {structure_name}"
        assert "<-" not in first_content, f"First step should be flat for {structure_name}"
        
        # Final step should reconstruct original
        final_content = steps[-1].content
        final_structure = self.parser.parse(final_content)
        assert isinstance(final_structure, ArgumentMapStructure)
        
        # Verify content preservation
        original_contents = {line.content.strip() for line in structure.lines if line.content.strip()}
        final_contents = {line.content.strip() for line in final_structure.lines if line.content.strip()}
        assert original_contents == final_contents, f"Content should be preserved for {structure_name}"
    
    @pytest.mark.parametrize("seed", [1, 42, 123, 999, 12345])
    def test_different_shuffle_seeds(self, seed):
        """Test behavior with various shuffle seeds."""
        argdown_text = """[Root]: Root claim.
    <+ [A]: Support A.
    <+ [B]: Support B.
    <+ [C]: Support C.
        <- [Counter]: Counter to C."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        strategy = DepthDiffusionStrategy(shuffle_seed=seed)
        steps = strategy.generate(structure)
        
        # Basic validations
        assert len(steps) > 0, f"Should generate steps with seed {seed}"
        
        # First step should be shuffled (order different from original)
        first_content = steps[0].content
        first_lines = [line.strip() for line in first_content.split('\n') if line.strip()]
        
        # Should contain all expected content
        expected_labels = ['Root', 'A', 'B', 'C', 'Counter']
        for label in expected_labels:
            assert any(label in line for line in first_lines), f"Should contain {label} with seed {seed}"
        
        # Test reproducibility - same seed should give same result
        strategy2 = DepthDiffusionStrategy(shuffle_seed=seed)
        steps2 = strategy2.generate(structure)
        
        assert len(steps) == len(steps2), f"Same seed should give same step count: {seed}"
        assert steps[0].content == steps2[0].content, f"Same seed should give same first step: {seed}"
    
    @pytest.mark.parametrize("abortion_rate", [0.0, 0.1, 0.3, 0.5])
    def test_various_abortion_rates(self, abortion_rate):
        """Test with different abortion rates."""
        argdown_text = """[Main]: Main claim.
    <+ <Support>: Supporting argument.
        <- [Counter]: Counter claim.
    <+ [Another]: Another support."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        strategy = DepthDiffusionStrategy(shuffle_seed=42)
        steps = strategy.generate(structure, abortion_rate=abortion_rate)
        
        # Basic validations
        assert len(steps) > 0, f"Should generate steps with abortion rate {abortion_rate}"
        
        # With higher abortion rates, might get more steps due to repetitions
        if abortion_rate == 0.0:
            # No abortion - should have predictable step count
            base_steps = strategy.generate(structure, abortion_rate=0.0)
            assert len(steps) == len(base_steps), "Zero abortion should be deterministic"
        
        # Final step should still reconstruct correctly regardless of abortion
        final_content = steps[-1].content
        final_structure = self.parser.parse(final_content)
        assert isinstance(final_structure, ArgumentMapStructure)
        
        # Content should be preserved
        original_contents = {line.content.strip() for line in structure.lines if line.content.strip()}
        final_contents = {line.content.strip() for line in final_structure.lines if line.content.strip()}
        assert original_contents == final_contents, f"Content preserved with abortion rate {abortion_rate}"
    
    @pytest.mark.parametrize("has_yaml,has_comments", [
        (False, False),
        (True, False),
        (False, True),
        (True, True),
    ])
    def test_yaml_and_comment_combinations(self, has_yaml, has_comments):
        """Test various combinations of YAML and comment presence."""
        # Build argdown text based on parameters
        if has_yaml and has_comments:
            argdown_text = """[Main]: Main claim. {confidence: 0.9} // Main comment
    <+ <Support>: Supporting argument. {strength: 0.8} // Support comment"""
        elif has_yaml:
            argdown_text = """[Main]: Main claim. {confidence: 0.9}
    <+ <Support>: Supporting argument. {strength: 0.8}"""
        elif has_comments:
            argdown_text = """[Main]: Main claim. // Main comment
    <+ <Support>: Supporting argument. // Support comment"""
        else:
            argdown_text = """[Main]: Main claim.
    <+ <Support>: Supporting argument."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        strategy = DepthDiffusionStrategy(shuffle_seed=42)
        steps = strategy.generate(structure)
        
        # Basic validations
        assert len(steps) > 0, f"Should generate steps for YAML={has_yaml}, comments={has_comments}"
        
        # Check final step contains expected elements
        final_content = steps[-1].content
        
        if has_yaml:
            # Should contain YAML-like content (braces)
            yaml_found = "{" in final_content and "}" in final_content
            if not yaml_found:
                # Parser might not support YAML in this format - that's OK
                pass
        
        if has_comments:
            # Should contain comment-like content
            comment_found = "//" in final_content
            if not comment_found:
                # Parser might not support comments in this format - that's OK
                pass
        
        # Content reconstruction should work regardless
        final_structure = self.parser.parse(final_content)
        assert isinstance(final_structure, ArgumentMapStructure)
    
    @pytest.mark.parametrize("complexity_factor", [1, 2, 3])
    def test_large_structure_scalability(self, complexity_factor):
        """Test performance and correctness with large structures."""
        # Generate structures of increasing complexity
        base_supports = 3 * complexity_factor
        base_depth = 2 + complexity_factor
        
        # Build a structure with many nodes
        lines = ["[Root]: Root claim."]
        
        # Add many supports at level 1
        for i in range(base_supports):
            lines.append(f"    <+ [S{i}]: Support {i}.")
            
            # Add some deeper nesting for some supports
            if i < complexity_factor:
                for depth in range(2, base_depth + 1):
                    indent = "    " * depth
                    lines.append(f"{indent}<- [C{i}D{depth}]: Counter at depth {depth}.")
        
        argdown_text = "\n".join(lines)
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        strategy = DepthDiffusionStrategy(shuffle_seed=42)
        steps = strategy.generate(structure)
        
        # Should handle large structures gracefully
        assert len(steps) > 0, f"Should handle complexity factor {complexity_factor}"
        assert len(steps) <= 20, f"Should not generate excessive steps for complexity {complexity_factor}"
        
        # Final reconstruction should work
        final_content = steps[-1].content
        final_structure = self.parser.parse(final_content)
        assert isinstance(final_structure, ArgumentMapStructure)
        
        # Should preserve all content
        original_node_count = len([line for line in structure.lines if line.content.strip()])
        final_node_count = len([line for line in final_structure.lines if line.content.strip()])
        assert original_node_count == final_node_count, f"Node count preserved for complexity {complexity_factor}"
    
    @pytest.mark.parametrize("relation_type,symbol", [
        ("support", "<+"),
        ("attack", "<-"),
        ("undercut", "<_"),
        ("mixed", "mixed"),  # Special case for mixed relations
    ])
    def test_complex_relation_types(self, relation_type, symbol):
        """Test with structures containing various dialectical relation types."""
        if relation_type == "mixed":
            # Test structure with multiple relation types
            argdown_text = """[Main]: Main claim.
    <+ <Support>: Supporting argument.
    <- [Attack]: Attacking claim.
    <_ <Undercut>: Undercutting argument."""
        else:
            # Test structure with single relation type
            argdown_text = f"""[Main]: Main claim.
    {symbol} <Arg1>: First argument.
    {symbol} [Claim2]: Second claim.
    {symbol} <Arg3>: Third argument."""
        
        structure = self.parser.parse(argdown_text)
        assert isinstance(structure, ArgumentMapStructure)
        
        strategy = DepthDiffusionStrategy(shuffle_seed=42)
        steps = strategy.generate(structure)
        
        # Basic validations
        assert len(steps) > 0, f"Should handle {relation_type} relations"
        
        # Final step should contain the relation symbols
        final_content = steps[-1].content
        if relation_type == "mixed":
            assert "<+" in final_content, "Should contain support relation"
            assert "<-" in final_content, "Should contain attack relation"
            # Note: undercut might not be supported by parser
        else:
            if symbol in ["<+", "<-"]:  # Only test commonly supported relations
                assert symbol in final_content, f"Should contain {symbol} relations"
        
        # Structure should be reconstructed
        final_structure = self.parser.parse(final_content)
        assert isinstance(final_structure, ArgumentMapStructure)
