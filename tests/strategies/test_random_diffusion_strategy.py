"""
Test suite for RandomDiffusionStrategy using the common testing framework.

This module provides comprehensive testing for the RandomDiffusionStrategy including:
- Framework automatic tests (14 tests from BaseStrategyTestSuite)
- Strategy-specific error mechanism tests (5 tests)
- Strategy behavior tests (3 tests, skipping 2 as requested)
- Edge cases and error handling tests (3 tests)
- Content reconstruction validation tests (2 tests)

Total expected tests: ~27 tests
"""

import pytest
from typing import Type
from src.argdown_cotgen.strategies.argument_maps.random_diffusion import (
    RandomDiffusionStrategy,
    DialecticalRelationError,
    LabelError,
    NodeTypeError,
    PlacementError,
    SyntaxErrorMechanism
)
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy
from src.argdown_cotgen.core.models import ArgumentMapStructure
from .strategy_test_framework import BaseStrategyTestSuite


class TestRandomDiffusionStrategy(BaseStrategyTestSuite):
    """Test suite for RandomDiffusionStrategy using the common framework."""
    
    @property
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        return RandomDiffusionStrategy
    
    @property
    def strategy_name(self) -> str:
        return "RandomDiffusionStrategy"
    
    def _validate_step_count(self, steps, test_case):
        """Override step count validation for RandomDiffusionStrategy."""
        actual = len(steps)
        
        # RandomDiffusionStrategy generates steps based on:
        # 1. Base error-correction steps (varies based on structure complexity)
        # 2. Optional YAML step (if YAML data present)  
        # 3. Optional comments step (if comments present)
        
        # Allow more flexibility since this strategy's step count depends on:
        # - Random error mechanisms chosen
        # - Structure complexity
        # - Presence of YAML/comments
        
        # Minimum: at least 1 step for any structure
        assert actual >= 1, f"Should have at least 1 step for {test_case.name}, got {actual}"
        
        # Maximum: reasonable upper bound (error steps + YAML + comments)
        max_reasonable = 15  # Conservative upper bound
        assert actual <= max_reasonable, f"Too many steps for {test_case.name}, got {actual}"
        
        # For single claim, should be minimal steps
        if test_case.name == "single_claim":
            assert actual <= 3, f"Single claim should have few steps, got {actual}"


class TestRandomDiffusionErrorMechanisms:
    """Test suite for individual error mechanisms used by RandomDiffusionStrategy."""
    
    def setup_method(self):
        """Set up parser for creating test structures."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
    
    def test_dialectical_relation_error_mechanism(self):
        """Test DialecticalRelationError introduces different relations."""
        mechanism = DialecticalRelationError()
        
        # Test with structure that has dialectical relations
        argdown_text = """[Main]: Main claim.
    <+ <Support>: Supporting evidence.
    <- <Attack>: Counter-argument."""
        
        parsed_structure = self.parser.parse(argdown_text)
        assert isinstance(parsed_structure, ArgumentMapStructure)
        structure = parsed_structure  # Type narrowing for clarity
        
        # Find original relations
        original_relations = [line.support_type for line in structure.lines if line.support_type is not None]
        assert len(original_relations) > 0, "Test structure should have dialectical relations"
        
        # Introduce error
        corrupted_structure, explanation = mechanism.introduce_error(structure)
        
        # Verify structure was modified
        assert corrupted_structure is not structure, "Should return a different structure object"
        assert corrupted_structure != structure, "Should modify the structure content"
        
        # Verify explanation is meaningful
        assert explanation, "Should provide non-empty explanation"
        assert any(word in explanation.lower() for word in ['relation', 'support', 'attack', 'fix', 'correct']), \
            f"Explanation should be about relations: {explanation}"
        
        # Verify at least one relation was changed
        new_relations = [line.support_type for line in corrupted_structure.lines if line.support_type is not None]
        assert new_relations != original_relations, "At least one relation should be changed"
        
        # Test with structure that has no relations (should return unchanged)
        no_relations_text = """Statement without relations.
Another statement.
[Labeled]: But no dialectical relations."""
        
        parsed_no_relations = self.parser.parse(no_relations_text)
        assert isinstance(parsed_no_relations, ArgumentMapStructure)
        no_relations_structure = parsed_no_relations
        
        unchanged_structure, empty_explanation = mechanism.introduce_error(no_relations_structure)
        assert unchanged_structure is no_relations_structure, "Should return same structure when no relations"
        assert empty_explanation == "", "Should return empty explanation when no changes possible"
    
    def test_label_error_mechanism(self):
        """Test LabelError removes labels properly."""
        mechanism = LabelError()
        
        # Test with structure that has labels
        argdown_text = """[Main Claim]: Main argument.
    <+ <Support Arg>: Supporting evidence.
    <- [Counter Claim]: Counter-argument."""
        
        parsed_structure = self.parser.parse(argdown_text)
        assert isinstance(parsed_structure, ArgumentMapStructure)
        structure = parsed_structure
        
        # Find original labels
        original_labels = [line.label for line in structure.lines if line.label is not None]
        assert len(original_labels) > 0, "Test structure should have labels"
        
        # Introduce error
        corrupted_structure, explanation = mechanism.introduce_error(structure)
        
        # Verify structure was modified
        assert corrupted_structure is not structure, "Should return a different structure object"
        
        # Verify explanation is meaningful
        assert explanation, "Should provide non-empty explanation"
        assert any(word in explanation.lower() for word in ['label', 'missing', 'fix', 'add']), \
            f"Explanation should be about labels: {explanation}"
        
        # Verify at least one label was removed
        new_labels = [line.label for line in corrupted_structure.lines if line.label is not None]
        assert len(new_labels) < len(original_labels), "At least one label should be removed"
        
        # Test with structure that has no labels (should return unchanged)
        no_labels_text = """Statement without label.
    <+ Another statement without label.
        <- Yet another unlabeled statement."""
        
        parsed_no_labels = self.parser.parse(no_labels_text)
        assert isinstance(parsed_no_labels, ArgumentMapStructure)
        no_labels_structure = parsed_no_labels
        
        unchanged_structure, empty_explanation = mechanism.introduce_error(no_labels_structure)
        assert unchanged_structure is no_labels_structure, "Should return same structure when no labels"
        assert empty_explanation == "", "Should return empty explanation when no changes possible"
    
    def test_node_type_error_mechanism(self):
        """Test NodeTypeError flips claim/argument types."""
        mechanism = NodeTypeError()
        
        # Test with structure that has labeled nodes (both claims and arguments)
        argdown_text = """[Main Claim]: Main argument.
    <+ <Support Arg>: Supporting evidence.
    <- [Counter Claim]: Counter-argument."""
        
        parsed_structure = self.parser.parse(argdown_text)
        assert isinstance(parsed_structure, ArgumentMapStructure)
        structure = parsed_structure
        
        # Find original node types
        original_types = [(line.label, line.is_claim) for line in structure.lines if line.label is not None]
        assert len(original_types) > 0, "Test structure should have labeled nodes"
        
        # Introduce error
        corrupted_structure, explanation = mechanism.introduce_error(structure)
        
        # Verify structure was modified
        assert corrupted_structure is not structure, "Should return a different structure object"
        
        # Verify explanation is meaningful
        assert explanation, "Should provide non-empty explanation"
        assert any(word in explanation.lower() for word in ['node', 'type', 'bracket', 'fix', 'correct']), \
            f"Explanation should be about node types: {explanation}"
        
        # Verify at least one node type was flipped
        new_types = [(line.label, line.is_claim) for line in corrupted_structure.lines if line.label is not None]
        assert new_types != original_types, "At least one node type should be changed"
        
        # Test with structure that has no labels (should return unchanged)
        no_labels_text = """Statement without label.
    <+ Another statement without label."""
        
        parsed_no_labels = self.parser.parse(no_labels_text)
        assert isinstance(parsed_no_labels, ArgumentMapStructure)
        no_labels_structure = parsed_no_labels
        
        unchanged_structure, empty_explanation = mechanism.introduce_error(no_labels_structure)
        assert unchanged_structure is no_labels_structure, "Should return same structure when no labeled nodes"
        assert empty_explanation == "", "Should return empty explanation when no changes possible"
    
    def test_placement_error_mechanism(self):
        """Test PlacementError moves blocks correctly."""
        mechanism = PlacementError()
        
        # Test with structure that has multiple placement opportunities
        argdown_text = """[Root A]: First root.
    <+ <Support A1>: Support for A.
[Root B]: Second root.
    <+ <Support B1>: Support for B.
        <+ <Deep B>: Deep support for B."""
        
        parsed_structure = self.parser.parse(argdown_text)
        assert isinstance(parsed_structure, ArgumentMapStructure)
        structure = parsed_structure
        
        # Capture original structure for comparison
        original_lines = [(line.content, line.indent_level, line.label) for line in structure.lines]
        
        # Introduce error (may or may not succeed depending on structure)
        corrupted_structure, explanation = mechanism.introduce_error(structure)
        
        # This mechanism might not always find valid moves, so we test both cases
        if corrupted_structure is not structure:
            # Error was introduced
            assert explanation, "Should provide explanation when changes are made"
            assert any(word in explanation.lower() for word in ['place', 'move', 'repositioned', 'structure, ''hierarchy', 'reorganize', 'placement']), \
                f"Explanation should be about placement: {explanation}"
            
            # Verify structure was actually modified
            new_lines = [(line.content, line.indent_level, line.label) for line in corrupted_structure.lines]
            assert new_lines != original_lines, "Structure should be modified when error introduced"
        else:
            # No valid placement found
            assert explanation == "", "Should return empty explanation when no changes possible"
        
        # Test with minimal structure (should return unchanged)
        minimal_text = """[Only Statement]: Just one statement."""
        parsed_minimal = self.parser.parse(minimal_text)
        assert isinstance(parsed_minimal, ArgumentMapStructure)
        minimal_structure = parsed_minimal
        
        unchanged_structure, empty_explanation = mechanism.introduce_error(minimal_structure)
        assert unchanged_structure is minimal_structure, "Should return same structure when no moves possible"
        assert empty_explanation == "", "Should return empty explanation when no changes possible"
    
    def test_syntax_error_mechanism(self):
        """Test SyntaxErrorMechanism introduces formatting errors."""
        mechanism = SyntaxErrorMechanism()
        
        # Test with well-formatted structure
        argdown_text = """[Main Claim]: Main argument.
    <+ <Support>: Supporting evidence.
        <- <Counter>: Counter-argument."""
        
        parsed_structure = self.parser.parse(argdown_text)
        assert isinstance(parsed_structure, ArgumentMapStructure)
        structure = parsed_structure
        
        # SyntaxErrorMechanism should ALWAYS produce detectable changes
        corrupted_structure, explanation = mechanism.introduce_error(structure)
        
        # Basic checks that should always pass
        assert corrupted_structure is not structure, "Should return a different structure object"
        assert explanation, "Should provide non-empty explanation"
        assert any(word in explanation.lower() for word in ['syntax', 'format', 'indent', 'fix', 'clean']), \
            f"Explanation should be about syntax/formatting: {explanation}"
        
        # Compare all aspects of the structure to detect changes
        original_content = [line.content for line in structure.lines]
        new_content = [line.content for line in corrupted_structure.lines]
        original_indents = [line.indent_level for line in structure.lines]
        new_indents = [line.indent_level for line in corrupted_structure.lines]
        original_labels = [line.label for line in structure.lines]
        new_labels = [line.label for line in corrupted_structure.lines]
        original_support_types = [line.support_type for line in structure.lines]
        new_support_types = [line.support_type for line in corrupted_structure.lines]
        
        # Check each type of change
        content_changed = original_content != new_content
        indents_changed = original_indents != new_indents
        labels_changed = original_labels != new_labels
        support_types_changed = original_support_types != new_support_types
        structure_changed = len(structure.lines) != len(corrupted_structure.lines)
        
        # At least one aspect MUST be changed
        any_change = any([content_changed, indents_changed, labels_changed, 
                        support_types_changed, structure_changed])
        
        assert any_change, \
            "SyntaxErrorMechanism MUST produce detectable changes in content, indentation, labels, support types, or structure"
        
        # Test with structure that has no labels (should still work via indentation changes)
        no_labels_text = """Statement without label.
    Another statement without label.
        Yet another unlabeled statement."""
        
        parsed_no_labels = self.parser.parse(no_labels_text)
        assert isinstance(parsed_no_labels, ArgumentMapStructure)
        no_labels_structure = parsed_no_labels
        
        corrupted_no_labels, explanation_no_labels = mechanism.introduce_error(no_labels_structure)
        
        # Should still produce changes (at minimum, indentation changes)
        assert corrupted_no_labels is not no_labels_structure, "Should return different structure object even without labels"
        assert explanation_no_labels, "Should provide explanation even without labels"
        
        # Should detect changes (primarily indentation)
        orig_indents_no_labels = [line.indent_level for line in no_labels_structure.lines]
        new_indents_no_labels = [line.indent_level for line in corrupted_no_labels.lines]
        orig_content_no_labels = [line.content for line in no_labels_structure.lines]
        new_content_no_labels = [line.content for line in corrupted_no_labels.lines]
        
        indents_changed_no_labels = orig_indents_no_labels != new_indents_no_labels
        content_changed_no_labels = orig_content_no_labels != new_content_no_labels
        
        assert indents_changed_no_labels or content_changed_no_labels, \
            "Should produce detectable changes even in structures without labels"


class TestRandomDiffusionBehavior:
    """Test suite for RandomDiffusionStrategy-specific behavior."""
    
    def setup_method(self):
        """Set up parser and strategy for behavior tests."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
    
    def test_error_mechanism_selection_randomness(self):
        """Test that different error mechanisms are selected across runs."""
        strategy = RandomDiffusionStrategy()
        
        # Test with a structure that supports all error mechanisms
        argdown_text = """[Main Claim]: Central argument.
    <+ <Support A>: First support.
    <- [Counter B]: Counter-claim.
        <+ <Sub Support>: Sub-support."""
        
        parsed_structure = self.parser.parse(argdown_text)
        assert isinstance(parsed_structure, ArgumentMapStructure)
        
        # Collect mechanism selections over multiple runs
        mechanism_selections = []
        for _ in range(50):  # Run multiple times to collect data
            mechanism = strategy._choose_error_mechanism()
            mechanism_selections.append(mechanism.__class__.__name__)
        
        # Test that multiple different mechanisms are selected
        unique_mechanisms = set(mechanism_selections)
        assert len(unique_mechanisms) >= 2, f"Should use multiple mechanisms, got: {unique_mechanisms}"
        
        # Test that selection follows approximate weight distribution
        from collections import Counter
        counts = Counter(mechanism_selections)
        
        # All mechanisms should appear at least once in 50 runs (with reasonable probability)
        # Note: This is probabilistic, so we use a reasonable threshold
        total_mechanisms = len(strategy.error_mechanisms)
        mechanisms_used = len(unique_mechanisms)
        
        # Should use at least half of available mechanisms in 50 runs
        assert mechanisms_used >= total_mechanisms // 2, \
            f"Should use multiple mechanisms, used {mechanisms_used} of {total_mechanisms}"
        
        # Test that weights influence selection (most frequent should have higher weight)
        most_common = counts.most_common(1)[0][0]
        most_common_weight = strategy.mechanism_weights.get(most_common, 1.0)
        
        # The most frequently selected mechanism should have a reasonable weight
        assert most_common_weight > 0, "Most common mechanism should have positive weight"
    
    def test_step_count_scales_with_complexity(self):
        """Test that complex structures get more steps than simple ones."""
        strategy = RandomDiffusionStrategy()
        
        # Simple structure (single claim)
        simple_text = """[Simple]: Just one claim."""
        simple_structure = self.parser.parse(simple_text)
        assert isinstance(simple_structure, ArgumentMapStructure)
        
        # Medium structure (two levels)
        medium_text = """[Main]: Main claim.
    <+ <Support>: Supporting evidence.
    <- <Attack>: Counter-argument."""
        medium_structure = self.parser.parse(medium_text)
        assert isinstance(medium_structure, ArgumentMapStructure)
        
        # Complex structure (deep nesting, many nodes)
        complex_text = """[Root]: Complex argument.
    <+ <Branch A>: First branch.
        <+ <Sub A1>: Deep support A1.
            <+ <Deep A>: Very deep support.
        <+ <Sub A2>: Deep support A2.
    <- <Branch B>: Second branch.
        <- <Sub B1>: Deep counter B1.
            <+ <Counter-Counter>: Counter to counter.
        <+ <Sub B2>: Deep support B2.
    <+ <Branch C>: Third branch."""
        complex_structure = self.parser.parse(complex_text)
        assert isinstance(complex_structure, ArgumentMapStructure)
        
        # Test that step count generally increases with complexity
        # Note: Due to randomness, we test over multiple runs and look for trends
        simple_counts = []
        medium_counts = []
        complex_counts = []
        
        for _ in range(10):  # Multiple runs to account for randomness
            simple_counts.append(len(strategy.generate(simple_structure)))
            medium_counts.append(len(strategy.generate(medium_structure)))
            complex_counts.append(len(strategy.generate(complex_structure)))
        
        avg_simple = sum(simple_counts) / len(simple_counts)
        avg_medium = sum(medium_counts) / len(medium_counts)
        avg_complex = sum(complex_counts) / len(complex_counts)
        
        # Simple should generally have fewer steps than complex
        assert avg_simple <= avg_complex + 1, \
            f"Simple ({avg_simple:.1f}) should have ≤ steps than complex ({avg_complex:.1f})"
        
        # All should be within reasonable bounds
        assert avg_simple >= 1, "Simple structure should have at least 1 step"
        assert avg_complex <= 15, "Complex structure should not exceed reasonable upper bound"
        
        # Medium should be between simple and complex (with some tolerance for randomness)
        assert avg_simple <= avg_medium + 2, "Medium should generally have ≥ steps than simple"
        assert avg_medium <= avg_complex + 2, "Medium should generally have ≤ steps than complex"
    
    def test_explanation_quality_and_variety(self):
        """Test explanations are meaningful and show variety."""
        strategy = RandomDiffusionStrategy()
        
        # Test structure with multiple error opportunities
        argdown_text = """[Main Claim]: Central argument.
    <+ <Support>: Supporting evidence.
    <- [Counter]: Counter-argument.
        <+ <Sub Support>: Sub-level support."""
        
        parsed_structure = self.parser.parse(argdown_text)
        assert isinstance(parsed_structure, ArgumentMapStructure)
        
        # Generate multiple sets of steps to collect explanations
        all_explanations = []
        for _ in range(10):  # Multiple runs
            steps = strategy.generate(parsed_structure)
            for step in steps:
                all_explanations.append(step.explanation)
        
        # Test explanation quality
        for explanation in all_explanations:
            # All explanations should be non-empty
            assert explanation.strip(), f"Explanation should not be empty: '{explanation}'"
            
            # All explanations should be reasonable length (not too short)
            assert len(explanation.strip()) >= 10, \
                f"Explanation too short: '{explanation}'"
            
            # Should contain action words indicating what's being done
            action_words = ['fix', 'correct', 'add', 'move', 'adjust', 'clean', 'improve', 'include', 
                          'reorganize', 'try', 'let me', 'reposition', 'change', 'modify']
            has_action = any(word in explanation.lower() for word in action_words)
            assert has_action, f"Explanation should indicate action: '{explanation}'"
        
        # Test explanation variety
        unique_explanations = set(all_explanations)
        
        # Should have multiple different explanations (not all identical)
        assert len(unique_explanations) >= 3, \
            f"Should have varied explanations, got {len(unique_explanations)} unique from {len(all_explanations)} total"
        
        # Test that explanations reference different error types
        error_type_indicators = {
            'relation': ['relation', 'support', 'attack'],
            'label': ['label', 'labeling', 'missing'],
            'placement': ['place', 'position', 'move', 'hierarchy'],
            'syntax': ['syntax', 'format', 'indent'],
            'node_type': ['node', 'type', 'bracket']
        }
        
        found_error_types = set()
        for explanation in all_explanations:
            explanation_lower = explanation.lower()
            for error_type, indicators in error_type_indicators.items():
                if any(indicator in explanation_lower for indicator in indicators):
                    found_error_types.add(error_type)
        
        # Should find explanations for multiple error types
        assert len(found_error_types) >= 2, \
            f"Should have explanations for multiple error types, found: {found_error_types}"
        
        # Test that explanations can reference node labels when available
        label_referencing_explanations = [
            exp for exp in all_explanations 
            if any(label in exp for label in ['Main Claim', 'Support', 'Counter', 'Sub Support'])
        ]
        
        # Should have at least some explanations that reference specific labels
        assert len(label_referencing_explanations) > 0, \
            "Should have some explanations that reference specific node labels"


class TestRandomDiffusionEdgeCases:
    """Test suite for edge cases and error handling."""
    
    def setup_method(self):
        """Set up parser and strategy for edge case tests."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
        self.strategy = RandomDiffusionStrategy()
    
    def test_infinite_loop_protection(self):
        """Test that strategy doesn't get stuck in infinite loops."""
        # Test with structure that could resist error introduction
        resistant_text = """[Single]: Only one claim with no children."""
        
        parsed_structure = self.parser.parse(resistant_text)
        assert isinstance(parsed_structure, ArgumentMapStructure)
        
        # The strategy should terminate even with resistant structures
        # Test multiple runs to ensure consistent termination
        for attempt in range(5):
            steps = self.strategy.generate(parsed_structure)
            
            # Should always terminate and produce at least some steps
            assert len(steps) >= 1, f"Should produce at least 1 step, got {len(steps)} in attempt {attempt + 1}"
            assert len(steps) <= 15, f"Should not produce excessive steps, got {len(steps)} in attempt {attempt + 1}"
        
        # Test with empty-like structure (minimal content)
        minimal_text = """[A]: B."""
        minimal_structure = self.parser.parse(minimal_text)
        assert isinstance(minimal_structure, ArgumentMapStructure)
        
        # Should handle minimal structures without infinite loops
        steps = self.strategy.generate(minimal_structure)
        assert len(steps) >= 1, "Should handle minimal structures"
        assert len(steps) <= 10, "Should not produce excessive steps for minimal structure"
        
        # Test that error mechanisms can handle resistant structures
        # (structures where some mechanisms might not apply)
        no_relations_text = """[Claim A]: Statement A.
[Claim B]: Statement B.
[Claim C]: Statement C."""
        
        no_relations_structure = self.parser.parse(no_relations_text)
        assert isinstance(no_relations_structure, ArgumentMapStructure)
        
        # Should not get stuck trying to find relations that don't exist
        steps = self.strategy.generate(no_relations_structure)
        assert len(steps) >= 1, "Should handle structures without relations"
        
        # Verify that all steps have valid content and explanations
        for i, step in enumerate(steps):
            assert step.content.strip(), f"Step {i + 1} should have non-empty content"
            assert step.explanation.strip(), f"Step {i + 1} should have non-empty explanation"
    
    def test_minimal_structure_handling(self):
        """Test handling of very simple structures (single claim)."""
        # Test single claim
        single_claim_text = """[Simple]: Just one claim."""
        single_structure = self.parser.parse(single_claim_text)
        assert isinstance(single_structure, ArgumentMapStructure)
        
        steps = self.strategy.generate(single_structure)
        
        # Should handle single claim gracefully
        assert len(steps) >= 1, "Should produce at least 1 step for single claim"
        assert len(steps) <= 5, "Should not produce too many steps for single claim"
        
        # Final step should reconstruct the original
        final_content = steps[-1].content.strip()
        assert "[Simple]" in final_content, "Should preserve the label"
        assert "Just one claim" in final_content, "Should preserve the content"
        
        # Test single unlabeled statement
        unlabeled_text = """Just a statement without label."""
        unlabeled_structure = self.parser.parse(unlabeled_text)
        assert isinstance(unlabeled_structure, ArgumentMapStructure)
        
        steps = self.strategy.generate(unlabeled_structure)
        assert len(steps) >= 1, "Should handle unlabeled statements"
        
        # Should preserve the unlabeled content
        final_content = steps[-1].content.strip()
        assert "Just a statement without label" in final_content, "Should preserve unlabeled content"
        
        # Test that appropriate error mechanisms are selected for simple structures
        # Run multiple times to see what mechanisms are used
        mechanism_usage = set()
        for _ in range(10):
            mechanism = self.strategy._choose_error_mechanism()
            mechanism_usage.add(mechanism.__class__.__name__)
        
        # Should use mechanisms that can work on simple structures
        assert len(mechanism_usage) > 0, "Should select at least some mechanisms"
        
        # SyntaxErrorMechanism should always be available for simple structures
        steps_sample = self.strategy.generate(single_structure)
        # Just verify it completes without errors - specific mechanisms are random
        assert len(steps_sample) >= 1, "Should consistently handle simple structures"
    
    def test_complex_structure_handling(self):
        """Test handling of very complex nested structures."""
        # Create a deeply nested structure
        deep_nesting_text = """[Root]: Main argument.
    <+ <Level 1A>: First level support.
        <+ <Level 2A>: Second level support.
            <+ <Level 3A>: Third level support.
                <+ <Level 4A>: Fourth level support.
                    <+ <Level 5A>: Fifth level support.
                <- <Level 5B>: Fifth level counter.
            <- <Level 3B>: Third level counter.
        <- <Level 2B>: Second level counter.
    <- <Level 1B>: First level counter.
        <+ <Level 2C>: Support for counter.
            <+ <Level 3C>: Deep support for counter."""
        
        deep_structure = self.parser.parse(deep_nesting_text)
        assert isinstance(deep_structure, ArgumentMapStructure)
        
        # Should handle deep nesting without errors
        steps = self.strategy.generate(deep_structure)
        assert len(steps) >= 1, "Should handle deep nesting"
        assert len(steps) <= 15, "Should not produce excessive steps for deep structure"
        
        # Verify all steps are valid
        for i, step in enumerate(steps):
            assert step.content.strip(), f"Deep structure step {i + 1} should have content"
            assert step.explanation.strip(), f"Deep structure step {i + 1} should have explanation"
        
        # Final step should preserve the deep structure
        final_content = steps[-1].content
        assert "Root" in final_content, "Should preserve root"
        assert "Level 5A" in final_content, "Should preserve deep nodes"
        
        # Create a wide branching structure
        wide_branching_text = """[Central]: Central claim.
    <+ <Branch A>: Branch A.
    <+ <Branch B>: Branch B.
    <+ <Branch C>: Branch C.
    <+ <Branch D>: Branch D.
    <+ <Branch E>: Branch E.
    <- <Counter A>: Counter A.
    <- <Counter B>: Counter B.
    <- <Counter C>: Counter C.
    <- <Counter D>: Counter D."""
        
        wide_structure = self.parser.parse(wide_branching_text)
        assert isinstance(wide_structure, ArgumentMapStructure)
        
        # Should handle wide branching
        steps = self.strategy.generate(wide_structure)
        assert len(steps) >= 1, "Should handle wide branching"
        assert len(steps) <= 15, "Should not produce excessive steps for wide structure"
        
        # Performance test - should complete in reasonable time
        import time
        start_time = time.time()
        
        # Generate multiple times to test performance
        for _ in range(3):
            test_steps = self.strategy.generate(wide_structure)
            assert len(test_steps) >= 1, "Should consistently handle wide structures"
        
        elapsed_time = time.time() - start_time
        assert elapsed_time < 5.0, f"Should complete in reasonable time, took {elapsed_time:.2f}s"
        
        # Test that all error mechanisms can operate on complex structures
        mechanism_success = {}
        
        for _ in range(20):  # Test multiple times due to randomness
            mechanism = self.strategy._choose_error_mechanism()
            mechanism_name = mechanism.__class__.__name__
            
            # Try to apply the mechanism to the complex structure
            try:
                corrupted, explanation = mechanism.introduce_error(deep_structure)
                if corrupted is not deep_structure:  # Change was made
                    mechanism_success[mechanism_name] = mechanism_success.get(mechanism_name, 0) + 1
            except Exception as e:
                # No mechanism should fail on valid structures
                assert False, f"Mechanism {mechanism_name} failed on complex structure: {e}"
        
        # At least some mechanisms should successfully operate on complex structures
        assert len(mechanism_success) > 0, "At least some mechanisms should work on complex structures"
        
        # Test mixed complexity (both deep and wide)
        mixed_text = """[Root]: Complex mixed structure.
    <+ <Wide A>: Wide branch A.
        <+ <Deep A1>: Deep in A.
            <+ <Deeper A>: Very deep in A.
        <+ <Deep A2>: Also deep in A.
    <+ <Wide B>: Wide branch B.
    <+ <Wide C>: Wide branch C.
        <- <Counter C1>: Counter to C.
            <- <Deep Counter>: Deep counter.
    <- <Main Counter>: Main counter."""
        
        mixed_structure = self.parser.parse(mixed_text)
        assert isinstance(mixed_structure, ArgumentMapStructure)
        
        steps = self.strategy.generate(mixed_structure)
        assert len(steps) >= 1, "Should handle mixed complexity"
        assert len(steps) <= 15, "Should not produce excessive steps for mixed structure"
        
        # Final reconstruction should preserve the mixed structure
        final_content = steps[-1].content
        assert "Root" in final_content, "Should preserve root"
        assert "Wide A" in final_content and "Wide B" in final_content, "Should preserve wide branches"
        assert "Deep A1" in final_content and "Deeper A" in final_content, "Should preserve deep nesting"


class TestRandomDiffusionContentReconstruction:
    """Test suite for enhanced content reconstruction validation."""
    
    def setup_method(self):
        """Set up parser and strategy for content reconstruction tests."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
        self.strategy = RandomDiffusionStrategy()
    
    def test_final_content_exact_reconstruction(self):
        """Test final step exactly matches original (enhanced validation)."""
        # Test with structure containing various formatting challenges
        complex_formatting_text = """[Main Claim]: Primary argument with precise formatting.
    <+ <Support A>: First supporting argument.
        <- <Counter A1>: Counter to first support.
            <+ <Sub Support>: Deep support for counter.
    <- [Main Counter]: Primary counter-argument.
        <+ <Counter Support>: Support for counter."""
        
        parsed_structure = self.parser.parse(complex_formatting_text)
        assert isinstance(parsed_structure, ArgumentMapStructure)
        
        # Generate steps multiple times to ensure consistent reconstruction
        for attempt in range(3):
            steps = self.strategy.generate(parsed_structure)
            assert len(steps) >= 1, f"Should generate steps (attempt {attempt + 1})"
            
            final_content = steps[-1].content.strip()
            
            # Test exact label preservation
            assert "[Main Claim]" in final_content, "Should preserve main claim label exactly"
            assert "<Support A>" in final_content, "Should preserve argument label exactly"
            assert "[Main Counter]" in final_content, "Should preserve counter claim label exactly"
            
            # Test dialectical relation symbol accuracy
            assert "<+" in final_content, "Should preserve support symbols"
            assert "<-" in final_content, "Should preserve attack symbols"
            
            # Count expected dialectical relations
            support_count = final_content.count("<+")
            attack_count = final_content.count("<-")
            assert support_count >= 2, f"Should have at least 2 support relations, found {support_count}"
            assert attack_count >= 2, f"Should have at least 2 attack relations, found {attack_count}"
            
            # Test content preservation
            assert "Primary argument with precise formatting" in final_content, "Should preserve exact content"
            assert "First supporting argument" in final_content, "Should preserve support content"
            assert "Deep support for counter" in final_content, "Should preserve deep content"
            
            # Test structural integrity by parsing the result
            reparsed_structure = self.parser.parse(final_content)
            assert isinstance(reparsed_structure, ArgumentMapStructure), "Final content should be parseable"
            
            # Compare line counts (should be same number of content lines)
            original_content_lines = [line for line in parsed_structure.lines if line.content.strip()]
            reparsed_content_lines = [line for line in reparsed_structure.lines if line.content.strip()]
            assert len(original_content_lines) == len(reparsed_content_lines), \
                f"Should preserve line count: {len(original_content_lines)} vs {len(reparsed_content_lines)}"
        
        # Test indentation correctness after potential placement errors
        indentation_test_text = """[Root]: Root level.
    <+ <Level 1>: First level.
        <+ <Level 2>: Second level.
            <+ <Level 3>: Third level.
        <- <Level 2B>: Second level counter.
    <- <Root Counter>: Root level counter."""
        
        indentation_structure = self.parser.parse(indentation_test_text)
        assert isinstance(indentation_structure, ArgumentMapStructure)
        
        steps = self.strategy.generate(indentation_structure)
        final_content = steps[-1].content
        
        # Check that indentation is consistent in final result
        lines = final_content.split('\n')
        root_lines = [line for line in lines if line.strip() and not line.startswith(' ')]
        level1_lines = [line for line in lines if line.startswith('    ') and not line.startswith('        ')]
        level2_lines = [line for line in lines if line.startswith('        ') and not line.startswith('            ')]
        level3_lines = [line for line in lines if line.startswith('            ')]
        
        assert len(root_lines) >= 1, "Should have root level lines"
        assert len(level1_lines) >= 1, "Should have first level lines"
        assert len(level2_lines) >= 1, "Should have second level lines"
        assert len(level3_lines) >= 1, "Should have third level lines"
        
        # Test that final result maintains proper hierarchy
        reparsed = self.parser.parse(final_content)
        assert isinstance(reparsed, ArgumentMapStructure)
        
        # Find the deepest indentation level
        max_indent = max(line.indent_level for line in reparsed.lines if line.content.strip())
        assert max_indent >= 3, f"Should preserve deep indentation, max found: {max_indent}"
    
    def test_yaml_and_comments_preservation(self):
        """Test YAML and comments are properly preserved and formatted."""
        # Test with YAML inline data (using correct inline format)
        yaml_text = """[Main Claim]: Primary argument. {confidence: 0.9}
    <+ <Support>: Supporting evidence. {strength: high, quality: good}"""
        
        yaml_structure = self.parser.parse(yaml_text)
        assert isinstance(yaml_structure, ArgumentMapStructure)
        
        # Test that YAML is preserved in generation
        steps = self.strategy.generate(yaml_structure)
        
        # Find YAML step (should be near the end)
        yaml_steps = [step for step in steps if "{" in step.content and "}" in step.content]
        assert len(yaml_steps) > 0, "Should have at least one step with YAML data"
        
        # Check final step contains YAML
        final_content = steps[-1].content
        assert "{confidence: 0.9}" in final_content, "Should preserve YAML confidence data"
        assert "{strength: high, quality: good}" in final_content, "Should preserve YAML strength data"
        
        # Test YAML spacing precision
        assert ". {confidence:" in final_content, "YAML should have proper spacing after content"
        assert ". {strength:" in final_content, "YAML should have proper spacing after content"
        
        # Test with comments
        comments_text = """[Main Claim]: Primary argument.  // This is the main point
    <+ <Support>: Supporting evidence.  // Strong evidence here
        <- <Counter>: Counter-argument.  // Potential weakness"""
        
        comments_structure = self.parser.parse(comments_text)
        assert isinstance(comments_structure, ArgumentMapStructure)
        
        steps = self.strategy.generate(comments_structure)
        
        # Find comment steps (should be at the end)
        comment_steps = [step for step in steps if "//" in step.content]
        assert len(comment_steps) > 0, "Should have at least one step with comments"
        
        # Check final step contains comments
        final_content = steps[-1].content
        assert "// This is the main point" in final_content, "Should preserve inline comments"
        assert "// Strong evidence here" in final_content, "Should preserve support comments"
        assert "// Potential weakness" in final_content, "Should preserve counter comments"
        
        # Test comment positioning accuracy
        lines = final_content.split('\n')
        main_claim_line = next((line for line in lines if "[Main Claim]" in line), None)
        assert main_claim_line is not None, "Should find main claim line"
        assert "// This is the main point" in main_claim_line, "Comment should be on same line as claim"
        
        # Test mixed YAML and comments
        mixed_text = """[Complex Arg]: Multi-faceted argument. {confidence: 0.8} // Key insight
    <+ <Evidence A>: First evidence. {strength: high}
    <- <Objection B>: First objection. {weakness: moderate} // Weak point"""
        
        mixed_structure = self.parser.parse(mixed_text)
        assert isinstance(mixed_structure, ArgumentMapStructure)
        
        steps = self.strategy.generate(mixed_structure)
        final_content = steps[-1].content
        
        # Should contain both YAML and comments
        assert "{confidence: 0.8}" in final_content, "Should contain YAML confidence data"
        assert "{strength: high}" in final_content, "Should contain YAML strength data"
        assert "{weakness: moderate}" in final_content, "Should contain YAML weakness data"
        assert "// Key insight" in final_content, "Should contain inline comments"
        assert "// Weak point" in final_content, "Should contain objection comments"
        
        # Test spacing and formatting precision
        # YAML should have proper formatting
        assert ". {confidence: 0.8} //" in final_content, "YAML and comment should have proper spacing"
        assert ". {strength: high}" in final_content, "YAML should have proper spacing"
        assert ". {weakness: moderate} //" in final_content, "YAML and comment should have proper spacing"
        
        # Comments should maintain spacing
        comment_lines = [line for line in final_content.split('\n') if "//" in line]
        for line in comment_lines:
            # Inline comments should have proper spacing (at least one space before //)
            assert " //" in line, f"Inline comment should have space before //: '{line}'"
        
        # Test that YAML and comments work together without interference
        reparsed = self.parser.parse(final_content)
        assert isinstance(reparsed, ArgumentMapStructure), "Mixed content should be parseable"
        
        # Should preserve argument structure despite YAML and comments
        assert "[Complex Arg]" in final_content, "Should preserve main argument"
        assert "<Evidence A>" in final_content, "Should preserve evidence"
        assert "<Objection B>" in final_content, "Should preserve objection"
        
        # Test step-by-step addition of YAML and comments
        # YAML should be added before comments in the step sequence
        yaml_only_step_index = None
        final_comment_step_index = None
        
        for i, step in enumerate(steps):
            # Find step that has YAML but not the final comments (YAML-only step)
            if "{confidence:" in step.content and "}" in step.content and "// Key insight" not in step.content:
                yaml_only_step_index = i
            # Find step that has both YAML and final comments (final step)
            if "{confidence:" in step.content and "// Key insight" in step.content:
                final_comment_step_index = i
        
        if yaml_only_step_index is not None and final_comment_step_index is not None:
            assert yaml_only_step_index < final_comment_step_index, "YAML should be added before final comments"
        
        # Test preservation across multiple generations
        for attempt in range(3):
            test_steps = self.strategy.generate(mixed_structure)
            test_final = test_steps[-1].content
            
            # Core elements should always be preserved
            assert "{confidence: 0.8}" in test_final, f"YAML confidence missing in attempt {attempt + 1}"
            assert "// Key insight" in test_final, f"Inline comment missing in attempt {attempt + 1}"
            assert "{strength: high}" in test_final, f"YAML strength missing in attempt {attempt + 1}"
        
        # Test complex inline YAML structures
        complex_yaml_text = """[Research]: Scientific research findings. {methodology: experimental, sample_size: 1000, p_value: 0.01}
    <+ <Data Quality>: High quality data collection. {reliability: 0.95, validity: confirmed}"""
        
        complex_yaml_structure = self.parser.parse(complex_yaml_text)
        assert isinstance(complex_yaml_structure, ArgumentMapStructure)
        
        steps = self.strategy.generate(complex_yaml_structure)
        final_content = steps[-1].content
        
        # Should preserve complex YAML structures
        assert "methodology: experimental" in final_content, "Should preserve methodology"
        assert "sample_size: 1000" in final_content, "Should preserve sample size"
        assert "p_value: 0.01" in final_content, "Should preserve p-value"
        assert "reliability: 0.95" in final_content, "Should preserve reliability"
        assert "validity: confirmed" in final_content, "Should preserve validity"


# Parameterized tests for comprehensive coverage
class TestRandomDiffusionParameterized:
    """Parameterized tests for comprehensive coverage of error mechanisms."""
    
    def setup_method(self):
        """Set up parser for parameterized tests."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
    
    @pytest.mark.parametrize("mechanism_class", [
        DialecticalRelationError,
        LabelError, 
        NodeTypeError,
        PlacementError,
        SyntaxErrorMechanism
    ])
    def test_individual_error_mechanisms(self, mechanism_class):
        """Test each error mechanism individually."""
        # Test instantiation
        mechanism = mechanism_class()
        assert mechanism is not None, f"{mechanism_class.__name__} should instantiate"
        
        # Test with appropriate structure for each mechanism
        if mechanism_class == DialecticalRelationError:
            # Test with structure that has dialectical relations
            test_text = """[Main]: Main claim.
    <+ <Support>: Supporting evidence.
    <- <Attack>: Counter-argument."""
            
            parsed_structure = self.parser.parse(test_text)
            assert isinstance(parsed_structure, ArgumentMapStructure)
            
            corrupted, explanation = mechanism.introduce_error(parsed_structure)
            
            if corrupted is not parsed_structure:
                # Error was introduced
                assert explanation, "Should provide explanation when changes made"
                assert any(word in explanation.lower() for word in ['relation', 'support', 'attack']), \
                    f"Explanation should mention relations: {explanation}"
                
                # Should change dialectical relations
                original_relations = [line.support_type for line in parsed_structure.lines if line.support_type]
                new_relations = [line.support_type for line in corrupted.lines if line.support_type]
                assert original_relations != new_relations, "Should modify dialectical relations"
            else:
                # No changes possible
                assert explanation == "", "Should return empty explanation when no changes"
            
            # Test with inappropriate structure (no relations)
            no_relations_text = """[A]: Statement A.
[B]: Statement B."""
            no_relations_structure = self.parser.parse(no_relations_text)
            assert isinstance(no_relations_structure, ArgumentMapStructure)
            
            unchanged, empty_explanation = mechanism.introduce_error(no_relations_structure)
            assert unchanged is no_relations_structure, "Should return same structure when no relations"
            assert empty_explanation == "", "Should return empty explanation when no relations"
        
        elif mechanism_class == LabelError:
            # Test with structure that has labels
            test_text = """[Main Claim]: Main argument.
    <+ <Support Arg>: Supporting evidence.
    <- [Counter Claim]: Counter-argument."""
            
            parsed_structure = self.parser.parse(test_text)
            assert isinstance(parsed_structure, ArgumentMapStructure)
            
            corrupted, explanation = mechanism.introduce_error(parsed_structure)
            
            if corrupted is not parsed_structure:
                # Error was introduced
                assert explanation, "Should provide explanation when changes made"
                assert any(word in explanation.lower() for word in ['label', 'missing']), \
                    f"Explanation should mention labels: {explanation}"
                
                # Should remove at least one label
                original_labels = [line.label for line in parsed_structure.lines if line.label]
                new_labels = [line.label for line in corrupted.lines if line.label]
                assert len(new_labels) < len(original_labels), "Should remove at least one label"
            
            # Test with inappropriate structure (no labels)
            no_labels_text = """Statement without label.
    <+ Another statement without label."""
            no_labels_structure = self.parser.parse(no_labels_text)
            assert isinstance(no_labels_structure, ArgumentMapStructure)
            
            unchanged, empty_explanation = mechanism.introduce_error(no_labels_structure)
            assert unchanged is no_labels_structure, "Should return same structure when no labels"
            assert empty_explanation == "", "Should return empty explanation when no labels"
        
        elif mechanism_class == NodeTypeError:
            # Test with structure that has labeled nodes
            test_text = """[Main Claim]: Main argument.
    <+ <Support Arg>: Supporting evidence.
    <- [Counter Claim]: Counter-argument."""
            
            parsed_structure = self.parser.parse(test_text)
            assert isinstance(parsed_structure, ArgumentMapStructure)
            
            corrupted, explanation = mechanism.introduce_error(parsed_structure)
            
            if corrupted is not parsed_structure:
                # Error was introduced
                assert explanation, "Should provide explanation when changes made"
                assert any(word in explanation.lower() for word in ['node', 'type', 'bracket']), \
                    f"Explanation should mention node types: {explanation}"
                
                # Should flip at least one node type
                original_types = [(line.label, line.is_claim) for line in parsed_structure.lines if line.label]
                new_types = [(line.label, line.is_claim) for line in corrupted.lines if line.label]
                assert original_types != new_types, "Should change at least one node type"
            
            # Test with inappropriate structure (no labeled nodes)
            no_labels_text = """Statement without label.
    <+ Another statement without label."""
            no_labels_structure = self.parser.parse(no_labels_text)
            assert isinstance(no_labels_structure, ArgumentMapStructure)
            
            unchanged, empty_explanation = mechanism.introduce_error(no_labels_structure)
            assert unchanged is no_labels_structure, "Should return same structure when no labeled nodes"
            assert empty_explanation == "", "Should return empty explanation when no labeled nodes"
        
        elif mechanism_class == PlacementError:
            # Test with structure that allows movement
            test_text = """[Root A]: First root.
    <+ <Support A>: Support for A.
[Root B]: Second root.
    <+ <Support B>: Support for B."""
            
            parsed_structure = self.parser.parse(test_text)
            assert isinstance(parsed_structure, ArgumentMapStructure)
            
            corrupted, explanation = mechanism.introduce_error(parsed_structure)
            
            # PlacementError might not always find valid moves
            if corrupted is not parsed_structure:
                # Movement was made
                assert explanation, "Should provide explanation when changes made"
                assert any(word in explanation.lower() for word in ['place', 'move', 'position', 'reorganize', 'hierarchy']), \
                    f"Explanation should mention placement: {explanation}"
                
                # Structure should be different
                original_structure = [(line.content, line.indent_level) for line in parsed_structure.lines]
                new_structure = [(line.content, line.indent_level) for line in corrupted.lines]
                assert original_structure != new_structure, "Should change structure when movement made"
            else:
                # No valid movement found
                assert explanation == "", "Should return empty explanation when no movement possible"
            
            # Test with inappropriate structure (single node)
            single_text = """[Only]: Single statement."""
            single_structure = self.parser.parse(single_text)
            assert isinstance(single_structure, ArgumentMapStructure)
            
            unchanged, empty_explanation = mechanism.introduce_error(single_structure)
            assert unchanged is single_structure, "Should return same structure when no movement possible"
            assert empty_explanation == "", "Should return empty explanation when no movement possible"
        
        elif mechanism_class == SyntaxErrorMechanism:
            # Test with any structure (SyntaxErrorMechanism should always work)
            test_text = """[Main]: Main argument.
    <+ <Support>: Supporting evidence.
        <- <Counter>: Counter-argument."""
            
            parsed_structure = self.parser.parse(test_text)
            assert isinstance(parsed_structure, ArgumentMapStructure)
            
            corrupted, explanation = mechanism.introduce_error(parsed_structure)
            
            # SyntaxErrorMechanism should ALWAYS produce changes
            assert corrupted is not parsed_structure, "SyntaxErrorMechanism should always return different structure"
            assert explanation, "SyntaxErrorMechanism should always provide explanation"
            assert any(word in explanation.lower() for word in ['syntax', 'format', 'indent']), \
                f"Explanation should mention syntax/formatting: {explanation}"
            
            # Should detect some kind of change
            original_content = [line.content for line in parsed_structure.lines]
            new_content = [line.content for line in corrupted.lines]
            original_indents = [line.indent_level for line in parsed_structure.lines]
            new_indents = [line.indent_level for line in corrupted.lines]
            
            content_changed = original_content != new_content
            indents_changed = original_indents != new_indents
            structure_changed = len(parsed_structure.lines) != len(corrupted.lines)
            
            assert content_changed or indents_changed or structure_changed, \
                "SyntaxErrorMechanism should produce detectable changes"
            
            # Test with minimal structure
            minimal_text = """[A]: B."""
            minimal_structure = self.parser.parse(minimal_text)
            assert isinstance(minimal_structure, ArgumentMapStructure)
            
            minimal_corrupted, minimal_explanation = mechanism.introduce_error(minimal_structure)
            assert minimal_corrupted is not minimal_structure, "Should work even on minimal structures"
            assert minimal_explanation, "Should provide explanation even for minimal structures"
    
    @pytest.mark.parametrize("complexity_level", [
        "single_claim",
        "two_level", 
        "deep_nesting",
        "wide_branching"
    ])
    def test_complexity_scaling(self, complexity_level):
        """Test step count scaling with different complexity levels."""
        strategy = RandomDiffusionStrategy()
        
        # Define test structures for each complexity level
        test_structures = {
            "single_claim": """[Simple]: Just one claim.""",
            
            "two_level": """[Main]: Main claim.
    <+ <Support>: Supporting evidence.
    <- <Attack>: Counter-argument.""",
            
            "deep_nesting": """[Root]: Deep argument.
    <+ <Level 1>: First level.
        <+ <Level 2>: Second level.
            <+ <Level 3>: Third level.
                <+ <Level 4>: Fourth level.
                    <+ <Level 5>: Fifth level.""",
            
            "wide_branching": """[Central]: Central claim.
    <+ <Branch A>: Branch A.
    <+ <Branch B>: Branch B.
    <+ <Branch C>: Branch C.
    <+ <Branch D>: Branch D.
    <+ <Branch E>: Branch E.
    <- <Counter A>: Counter A.
    <- <Counter B>: Counter B.
    <- <Counter C>: Counter C."""
        }
        
        # Parse the structure for this complexity level
        argdown_text = test_structures[complexity_level]
        parsed_structure = self.parser.parse(argdown_text)
        assert isinstance(parsed_structure, ArgumentMapStructure)
        
        # Generate steps multiple times to account for randomness
        step_counts = []
        for _ in range(10):  # Multiple runs for statistical validity
            steps = strategy.generate(parsed_structure)
            step_counts.append(len(steps))
        
        avg_steps = sum(step_counts) / len(step_counts)
        min_steps = min(step_counts)
        max_steps = max(step_counts)
        
        # Test expectations for each complexity level
        if complexity_level == "single_claim":
            # Single claim should have minimal steps
            assert min_steps >= 1, "Single claim should have at least 1 step"
            assert avg_steps <= 5, f"Single claim should have few steps on average, got {avg_steps:.1f}"
            assert max_steps <= 8, f"Single claim should not exceed reasonable maximum, got {max_steps}"
        
        elif complexity_level == "two_level":
            # Two level should have moderate steps
            assert min_steps >= 1, "Two level should have at least 1 step"
            assert avg_steps >= 2, f"Two level should have multiple steps on average, got {avg_steps:.1f}"
            assert avg_steps <= 10, f"Two level should not be excessive, got {avg_steps:.1f}"
            assert max_steps <= 15, f"Two level should not exceed reasonable maximum, got {max_steps}"
        
        elif complexity_level == "deep_nesting":
            # Deep nesting might have more steps due to placement opportunities
            assert min_steps >= 1, "Deep nesting should have at least 1 step"
            assert avg_steps >= 2, f"Deep nesting should have multiple steps, got {avg_steps:.1f}"
            assert avg_steps <= 12, f"Deep nesting should not be excessive, got {avg_steps:.1f}"
            assert max_steps <= 15, f"Deep nesting should not exceed reasonable maximum, got {max_steps}"
        
        elif complexity_level == "wide_branching":
            # Wide branching has many nodes and relations to work with
            assert min_steps >= 1, "Wide branching should have at least 1 step"
            assert avg_steps >= 2, f"Wide branching should have multiple steps, got {avg_steps:.1f}"
            assert avg_steps <= 12, f"Wide branching should not be excessive, got {avg_steps:.1f}"
            assert max_steps <= 15, f"Wide branching should not exceed reasonable maximum, got {max_steps}"
        
        # Test that all generated steps are valid
        steps = strategy.generate(parsed_structure)
        for i, step in enumerate(steps):
            assert step.content.strip(), f"Step {i + 1} should have non-empty content"
            assert step.explanation.strip(), f"Step {i + 1} should have non-empty explanation"
        
        # Test that final step preserves the structure appropriately
        final_content = steps[-1].content
        
        if complexity_level == "single_claim":
            assert "[Simple]" in final_content, "Should preserve single claim label"
            assert "Just one claim" in final_content, "Should preserve single claim content"
        
        elif complexity_level == "two_level":
            assert "[Main]" in final_content, "Should preserve main claim"
            assert "<Support>" in final_content, "Should preserve support"
            assert "<Attack>" in final_content, "Should preserve attack"
        
        elif complexity_level == "deep_nesting":
            assert "[Root]" in final_content, "Should preserve root"
            assert "<Level 1>" in final_content, "Should preserve first level"
            assert "<Level 5>" in final_content, "Should preserve deep level"
        
        elif complexity_level == "wide_branching":
            assert "[Central]" in final_content, "Should preserve central claim"
            assert "<Branch A>" in final_content, "Should preserve branches"
            assert "<Counter A>" in final_content, "Should preserve counters"
        
        # Test that structure can be reparsed
        reparsed = self.parser.parse(final_content)
        assert isinstance(reparsed, ArgumentMapStructure), f"Final content should be parseable for {complexity_level}"
        
        # Test consistency across multiple generations
        consistency_test_counts = []
        for _ in range(5):
            consistency_steps = strategy.generate(parsed_structure)
            consistency_test_counts.append(len(consistency_steps))
        
        # Should show some consistency (not wildly different each time)
        consistency_range = max(consistency_test_counts) - min(consistency_test_counts)
        assert consistency_range <= 8, f"Step count should be reasonably consistent, range was {consistency_range}"


class TestRandomDiffusionIntegration:
    """Integration tests with other framework features."""
    
    def setup_method(self):
        """Set up parser for integration tests."""
        from src.argdown_cotgen.core.parser import ArgdownParser
        self.parser = ArgdownParser()
    
    def test_error_mechanism_selection_distribution(self):
        """Test that error mechanism selection follows configured weights over many runs."""
        strategy = RandomDiffusionStrategy()
        
        # Test with default weights first
        mechanism_selections = []
        num_runs = 1000  # Large sample for statistical significance
        
        for _ in range(num_runs):
            mechanism = strategy._choose_error_mechanism()
            mechanism_selections.append(mechanism.__class__.__name__)
        
        from collections import Counter
        counts = Counter(mechanism_selections)
        
        # Verify all mechanisms are represented (no mechanism should be completely unused)
        expected_mechanisms = {
            'DialecticalRelationError',
            'LabelError', 
            'NodeTypeError',
            'PlacementError',
            'SyntaxErrorMechanism'
        }
        selected_mechanisms = set(counts.keys())
        assert expected_mechanisms == selected_mechanisms, \
            f"All mechanisms should be used, missing: {expected_mechanisms - selected_mechanisms}"
        
        # Test that selection frequency roughly matches weights
        total_weight = sum(strategy.mechanism_weights.values())
        
        for mechanism_name, count in counts.items():
            expected_weight = strategy.mechanism_weights.get(mechanism_name, 1.0)
            expected_frequency = expected_weight / total_weight
            actual_frequency = count / num_runs
            
            # Allow 5% tolerance for statistical variation
            tolerance = 0.05
            assert abs(actual_frequency - expected_frequency) <= tolerance, \
                f"Mechanism {mechanism_name}: expected ~{expected_frequency:.3f}, got {actual_frequency:.3f}"
        
        # Test with custom weights
        custom_weights = {
            'SyntaxErrorMechanism': 5.0,  # Much higher weight
            'LabelError': 2.0,
            'DialecticalRelationError': 1.0,
            'NodeTypeError': 0.5,
            'PlacementError': 0.5
        }
        
        custom_strategy = RandomDiffusionStrategy(mechanism_weights=custom_weights)
        custom_selections = []
        
        for _ in range(1000):  # Large sample
            mechanism = custom_strategy._choose_error_mechanism()
            custom_selections.append(mechanism.__class__.__name__)
        
        custom_counts = Counter(custom_selections)
        custom_total_weight = sum(custom_weights.values())
        
        # SyntaxErrorMechanism should be most frequent with weight 5.0
        most_frequent = custom_counts.most_common(1)[0][0]
        assert most_frequent == 'SyntaxErrorMechanism', \
            f"SyntaxErrorMechanism should be most frequent with high weight, got {most_frequent}"
        
        # Verify weighted distribution
        for mechanism_name, count in custom_counts.items():
            expected_weight = custom_weights[mechanism_name]
            expected_frequency = expected_weight / custom_total_weight
            actual_frequency = count / 1000
            
            # Allow 5% tolerance
            tolerance = 0.05
            assert abs(actual_frequency - expected_frequency) <= tolerance, \
                f"Custom weights: {mechanism_name} expected ~{expected_frequency:.3f}, got {actual_frequency:.3f}"
        
        # Test edge case: single mechanism with weight 1.0, others with weight 0.0
        single_mechanism_weights = {
            'SyntaxErrorMechanism': 1.0,
            'LabelError': 0.0,
            'DialecticalRelationError': 0.0,
            'NodeTypeError': 0.0,
            'PlacementError': 0.0
        }
        
        single_strategy = RandomDiffusionStrategy(mechanism_weights=single_mechanism_weights)
        single_selections = []
        
        for _ in range(100):
            mechanism = single_strategy._choose_error_mechanism()
            single_selections.append(mechanism.__class__.__name__)
        
        # Should only select SyntaxErrorMechanism
        unique_single = set(single_selections)
        assert unique_single == {'SyntaxErrorMechanism'}, \
            f"Should only select SyntaxErrorMechanism with zero weights for others, got {unique_single}"
        
        # Test that zero-weight mechanisms are properly excluded
        assert all(selection == 'SyntaxErrorMechanism' for selection in single_selections), \
            "All selections should be SyntaxErrorMechanism when others have zero weight"
    
    def test_explanation_generation_calls_correct_methods(self):
        """Test that explanation generation integrates properly with error mechanisms."""
        strategy = RandomDiffusionStrategy()
        
        # Test with structure that has labels for explanation testing
        test_text = """[Main Claim]: Central argument with labels.
    <+ <Support A>: First support argument.
    <- [Counter B]: Counter-claim argument.
        <+ <Sub Support>: Sub-support for counter."""
        
        parsed_structure = self.parser.parse(test_text)
        assert isinstance(parsed_structure, ArgumentMapStructure)
        
        # Generate steps and collect explanations
        steps = strategy.generate(parsed_structure)
        explanations = [step.explanation for step in steps]
        
        # Test that all explanations are generated properly
        assert len(explanations) > 0, "Should generate at least one explanation"
        
        for i, explanation in enumerate(explanations):
            # Every explanation should be non-empty
            assert explanation.strip(), f"Step {i + 1} explanation should not be empty"
            
            # Explanations should be reasonable length
            assert len(explanation.strip()) >= 5, f"Step {i + 1} explanation too short: '{explanation}'"
            
            # Should contain meaningful content (not just placeholder text)
            assert not explanation.lower().startswith('todo'), f"Step {i + 1} should not contain TODO: '{explanation}'"
            assert 'placeholder' not in explanation.lower(), f"Step {i + 1} should not contain placeholder: '{explanation}'"
        
        # Test that explanations reference appropriate error types
        error_type_keywords = {
            'DialecticalRelationError': ['relation', 'support', 'attack', 'arrow', 'symbol'],
            'LabelError': ['label', 'labeling', 'missing', 'bracket'],
            'NodeTypeError': ['node', 'type', 'claim', 'argument', 'bracket'],
            'PlacementError': ['place', 'position', 'move', 'hierarchy', 'indent', 'structure'],
            'SyntaxErrorMechanism': ['syntax', 'format', 'formatting', 'indent', 'spacing', 'clean']
        }
        
        # Collect explanations over multiple runs to see different mechanisms
        all_explanations = []
        explanation_types_found = set()
        
        for _ in range(20):  # Multiple runs to capture different mechanisms
            test_steps = strategy.generate(parsed_structure)
            for step in test_steps:
                all_explanations.append(step.explanation)
                
                # Check which error type this explanation likely refers to
                explanation_lower = step.explanation.lower()
                for error_type, keywords in error_type_keywords.items():
                    if any(keyword in explanation_lower for keyword in keywords):
                        explanation_types_found.add(error_type)
        
        # Should find explanations for multiple error types
        assert len(explanation_types_found) >= 2, \
            f"Should find explanations for multiple error types, found: {explanation_types_found}"
        
        # Test that explanations can reference specific node labels
        label_references = []
        for explanation in all_explanations:
            # Check if explanation references specific labels from our test structure
            test_labels = ['Main Claim', 'Support A', 'Counter B', 'Sub Support']
            for label in test_labels:
                if label in explanation:
                    label_references.append((explanation, label))
        
        # Should have at least some explanations that reference specific labels
        assert len(label_references) > 0, \
            "Should have some explanations that reference specific node labels"
        
        # Test explanation quality and variety across different mechanisms
        # Force specific mechanisms to test their explanation generation
        mechanisms_to_test = [
            DialecticalRelationError(),
            LabelError(),
            NodeTypeError(),
            PlacementError(),
            SyntaxErrorMechanism()
        ]
        
        mechanism_explanations = {}
        
        for mechanism in mechanisms_to_test:
            mechanism_name = mechanism.__class__.__name__
            
            # Try to get explanation from this mechanism
            corrupted_structure, explanation = mechanism.introduce_error(parsed_structure)
            
            if explanation:  # Some mechanisms might not apply to this structure
                mechanism_explanations[mechanism_name] = explanation
                
                # Test explanation quality for this specific mechanism
                assert explanation.strip(), f"{mechanism_name} should provide non-empty explanation"
                assert len(explanation.strip()) >= 10, f"{mechanism_name} explanation should be substantial: '{explanation}'"
                
                # Check that explanation is appropriate for the mechanism type
                expected_keywords = error_type_keywords.get(mechanism_name, [])
                if expected_keywords:
                    has_relevant_keyword = any(keyword in explanation.lower() for keyword in expected_keywords)
                    assert has_relevant_keyword, \
                        f"{mechanism_name} explanation should contain relevant keywords {expected_keywords}: '{explanation}'"
        
        # Should have collected explanations from multiple mechanisms
        assert len(mechanism_explanations) >= 3, \
            f"Should collect explanations from multiple mechanisms, got: {list(mechanism_explanations.keys())}"
        
        # Test that different mechanisms produce different explanation styles
        unique_explanation_patterns = set()
        for mechanism_name, explanation in mechanism_explanations.items():
            # Create a "pattern" based on key words to identify explanation style
            explanation_words = set(explanation.lower().split())
            pattern_words = explanation_words.intersection({
                'relation', 'support', 'attack', 'label', 'missing', 'node', 'type', 
                'place', 'move', 'syntax', 'format', 'indent', 'fix', 'correct'
            })
            if pattern_words:
                unique_explanation_patterns.add(frozenset(pattern_words))
        
        # Different mechanisms should produce explanations with different patterns
        assert len(unique_explanation_patterns) >= 2, \
            "Different mechanisms should produce explanations with different patterns"
        
        # Test integration with YAML and comments
        yaml_comments_text = """[Research]: Scientific findings. {confidence: 0.9} // High confidence
    <+ <Evidence>: Strong evidence. {quality: high}
    <- <Objection>: Potential objection. // Needs addressing"""
        
        yaml_structure = self.parser.parse(yaml_comments_text)
        assert isinstance(yaml_structure, ArgumentMapStructure)
        
        yaml_steps = strategy.generate(yaml_structure)
        
        # Should handle YAML and comments without breaking explanation generation
        for step in yaml_steps:
            assert step.explanation.strip(), "Should generate explanations even with YAML/comments"
            # Explanations should not contain raw YAML or comment markers as errors
            assert not step.explanation.startswith('{'), "Explanation should not start with raw YAML"
            assert not step.explanation.startswith('//'), "Explanation should not start with raw comment"
        
        # Final step should preserve YAML and comments
        final_yaml_content = yaml_steps[-1].content
        assert "{confidence: 0.9}" in final_yaml_content, "Should preserve YAML in final step"
        assert "// High confidence" in final_yaml_content, "Should preserve comments in final step"
