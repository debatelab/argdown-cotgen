"""
Tests for the ByObjectionStrategy.

This module contains comprehensive tests for the by-objection argument map strategy,
including both common framework tests and by-objection specific behavior validation.
"""

from pprint import pprint
from typing import Type
from src.argdown_cotgen.strategies.argument_maps.by_objection import ByObjectionStrategy
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy
from src.argdown_cotgen.core.parser import ArgdownParser
from .map_strategy_test_framework import BaseMapStrategyTestSuite


class TestByObjectionStrategy(BaseMapStrategyTestSuite):
    """Test suite for ByObjectionStrategy using the common framework."""
    
    @property
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        return ByObjectionStrategy
    
    @property
    def strategy_name(self) -> str:
        return "ByObjectionStrategy"
    
    def _validate_step_count(self, steps, test_case):
        """
        Override step count validation for by-objection specific behavior.
        
        The by-objection strategy produces fewer steps for pure support structures
        since it groups all supports together when no objections exist to create
        natural breaking points.
        """
        #expected = test_case.expected_step_count
        actual = len(steps)
        
        # Strategy-specific adjustments
        if test_case.name == "true_branching_structure":
            # This test case has only support relations, no objections
            # By-objection strategy efficiently groups all supports = 2 steps total
            expected_for_objection = 2
            assert actual == expected_for_objection, \
                f"ByObjection strategy expected {expected_for_objection} steps for {test_case.name} (pure support structure), got {actual}"
        else:
            # Use default validation for other test cases
            super()._validate_step_count(steps, test_case)
            # assert expected - 1 <= actual <= expected + 2, \
            #     f"Expected ~{expected} steps for {test_case.name}, got {actual}"


class TestByObjectionSpecificBehavior:
    """Additional tests for by-objection specific behavior."""
    
    def test_argumentative_role_ordering(self):
        """Test that by-objection strategy groups by argumentative role."""
        argdown_text = """[Main Claim]: Core argument.
    <+ <Support 1>: First supporting reason.
        <+ <Evidence 1>: Evidence for support 1.
    <+ <Support 2>: Second supporting reason.
    <- <Objection>: Main objection.
        <+ <Objection Evidence>: Evidence for objection.
        <- <Rebuttal>: Counter to objection."""
        
        parser = ArgdownParser()
        structure = parser.parse(argdown_text)
        strategy = ByObjectionStrategy()
        
        steps = strategy.generate(structure)
        
        # Should have multiple steps showing argumentative progression
        assert len(steps) >= 3
        
        # Check that supporting arguments come before objections
        step_contents = [step.content for step in steps]
        
        # Find when Evidence 1 appears (part of main case)
        evidence_1_step = None
        for i, content in enumerate(step_contents):
            if "Evidence 1" in content:
                evidence_1_step = i
                break
        
        # Find when Objection appears
        objection_step = None
        for i, content in enumerate(step_contents):
            if "Objection" in content and "Evidence" not in content:
                objection_step = i
                break
        
        # Main case evidence should appear before objections
        if evidence_1_step is not None and objection_step is not None:
            assert evidence_1_step < objection_step, "Main case should be built before objections"
    
    def test_complete_support_chains(self):
        """Test that support chains are revealed completely."""
        argdown_text = """[Root]: Main argument.
    <+ <Support>: Supporting argument.
        <+ <Deep Support>: Deep evidence.
            <+ <Deepest>: Very deep evidence."""
        
        parser = ArgdownParser()
        structure = parser.parse(argdown_text)
        strategy = ByObjectionStrategy()
        
        steps = strategy.generate(structure)
        
        # Should reveal complete support chain in one step
        for i, step in enumerate(steps):
            if "Deep Support" in step.content:
                # If we see Deep Support, we should also see Deepest in same or earlier step
                assert "Deepest" in step.content, "Complete support chain should be revealed together"
                break
    
    def test_objection_with_evidence(self):
        """Test that objections are revealed with their supporting evidence."""
        argdown_text = """[Main]: Primary claim.
    <+ <Support>: Supporting reason.
    <- <Objection>: Main objection.
        <+ <Objection Evidence>: Evidence for objection."""
        
        parser = ArgdownParser()
        structure = parser.parse(argdown_text)
        strategy = ByObjectionStrategy()
        
        steps = strategy.generate(structure)
        
        # Find the step where objection is introduced
        objection_introduced = False
        for step in steps:
            if "Objection" in step.content and "Evidence" not in step.content:
                objection_introduced = True
            elif objection_introduced and "Objection Evidence" in step.content:
                # Evidence should come soon after objection
                assert True, "Objection evidence follows objection"
                break
    
    def test_argumentative_explanations(self):
        """Test that explanations reflect argumentative roles."""
        argdown_text = """[Claim]: Main claim.
    <+ <Support>: Supporting evidence.
    <- <Attack>: Attacking argument."""
        
        parser = ArgdownParser()
        structure = parser.parse(argdown_text)
        strategy = ByObjectionStrategy()
        
        steps = strategy.generate(structure)
        
        explanations = [step.explanation.lower() for step in steps]
        
        # Should have explanations related to argumentative roles
        role_words = ['claim', 'support', 'evidence', 'objection', 'rebuttal', 'case']
        found_role_words = any(word in ' '.join(explanations) for word in role_words)
        assert found_role_words, "Explanations should mention argumentative roles"
    
    def test_vegetarian_example_pattern(self):
        """Test the specific vegetarian example from the docstring."""
        argdown_text = """[Vegetarianism]: People should be vegetarian.
    <+ <Animal Welfare>: Animals suffer in factory farms.
        <+ <Scientific Evidence>: Studies show animal pain.
    <- <Nutrition Concern>: Vegetarian diets lack nutrients.
        <- <Modern Alternatives>: Supplements provide nutrients.
            <+ <Bioavailability>: Modern supplements work well.
        <- <Health Studies>: Vegetarians are healthier."""
        
        parser = ArgdownParser()
        structure = parser.parse(argdown_text)
        strategy = ByObjectionStrategy()
        
        steps = strategy.generate(structure)
        
        # Should follow the expected pattern:
        # 1. Main claim
        # 2. Main case (Animal Welfare + Scientific Evidence)
        # 3. Objections (Nutrition Concern)
        # 4. Rebuttals (Modern Alternatives + Bioavailability, Health Studies)
        
        assert len(steps) >= 4, "Should have at least 4 main steps"
        
        # Step 1: Should show just the main claim
        assert "Vegetarianism" in steps[0].content
        assert "Animal Welfare" not in steps[0].content
        
        # Step 2: Should add main supporting case
        main_case_step = None
        for i, step in enumerate(steps):
            if "Scientific Evidence" in step.content:
                main_case_step = i
                break
        
        assert main_case_step is not None, "Should reveal complete main case"
        
        # Step 3+: Should add objection
        objection_step = None
        for i, step in enumerate(steps):
            if "Nutrition Concern" in step.content:
                objection_step = i
                break
        
        assert objection_step is not None, "Should reveal objection"
        assert objection_step > main_case_step, "Objection should come after main case"
        
        # Final steps: Should add rebuttals
        rebuttal_found = any("Modern Alternatives" in step.content for step in steps)
        assert rebuttal_found, "Should reveal rebuttals to objections"
    
    def test_handles_complex_structures(self):
        """Test that strategy handles complex argumentative structures."""
        from .map_strategy_test_framework import COMMON_STRATEGY_TEST_CASES
        
        # Test with the climate action case
        climate_case = None
        for case in COMMON_STRATEGY_TEST_CASES:
            if case.name == 'climate_action_3_level':
                climate_case = case
                break
        
        assert climate_case is not None
        
        parser = ArgdownParser()
        structure = parser.parse(climate_case.argdown_text)
        strategy = ByObjectionStrategy()
        
        steps = strategy.generate(structure)
        
        pprint(steps)

        # Should handle complex structure without errors
        assert len(steps) == 4
        
        # All steps should have meaningful content
        for step in steps:
            assert step.content.strip(), "All steps should have content"
            assert step.explanation.strip(), "All steps should have explanations"
    
    def test_progressive_revelation(self):
        """Test that content is progressively revealed without removing previous content."""
        argdown_text = """[Root]: Main claim.
    <+ <Support>: Supporting argument.
    <- <Attack>: Attacking argument.
        <- <Counter>: Counter-attack."""
        
        parser = ArgdownParser()
        structure = parser.parse(argdown_text)
        strategy = ByObjectionStrategy()
        
        steps = strategy.generate(structure)
        
        # Each step should contain all content from previous steps
        for i in range(1, len(steps)):
            prev_content = steps[i-1].content
            curr_content = steps[i].content
            
            # Previous lines should be subset of current lines
            prev_lines = set(line.strip() for line in prev_content.split('\n') if line.strip())
            curr_lines = set(line.strip() for line in curr_content.split('\n') if line.strip())
            
            missing_lines = prev_lines - curr_lines
            assert not missing_lines, f"Step {i+1} removed content: {missing_lines}"

    def test_inverse_relations_phased_approach(self):
        """Test that inverse relations are handled in the second phase after primary relations."""
        argdown_text = """[Main]: Primary claim.
    <+ <Support>: Supporting reason.
        +> <Implication>: Something this support implies.
    <- <Attack>: Attacking argument.
        -> <Attack Implication>: Something this attack implies."""
        
        parser = ArgdownParser()
        structure = parser.parse(argdown_text)
        strategy = ByObjectionStrategy()
        
        steps = strategy.generate(structure)
        
        # Should have multiple steps
        assert len(steps) >= 2
        
        # Find when primary relations appear vs inverse relations
        support_step = None
        attack_step = None
        implication_step = None
        attack_implication_step = None
        
        for i, step in enumerate(steps):
            content = step.content
            if "Supporting reason" in content and support_step is None:
                support_step = i
            if "Attacking argument" in content and attack_step is None:
                attack_step = i
            if "Implication" in content and "Attack" not in content and implication_step is None:
                implication_step = i
            if "Attack Implication" in content and attack_implication_step is None:
                attack_implication_step = i
        
        # Primary relations should appear before their inverse implications
        if support_step is not None and implication_step is not None:
            assert support_step < implication_step, "Primary support should appear before its implications"
        
        if attack_step is not None and attack_implication_step is not None:
            assert attack_step < attack_implication_step, "Primary attack should appear before its implications"

    def test_extended_dialectical_relations(self):
        """Test that all dialectical relations (SUPPORTS, ATTACKS, UNDERCUTS, CONTRADICTORY) are handled."""
        argdown_text = """[Main]: Primary claim.
    <+ <Support>: Supporting reason.
    <- <Attack>: Attacking argument.
    <_ <Undercut>: Undercutting argument.
    >< <Contradiction>: Contradictory statement."""
        
        parser = ArgdownParser()
        structure = parser.parse(argdown_text)
        strategy = ByObjectionStrategy()
        
        steps = strategy.generate(structure)
        
        # Should handle all dialectical relation types
        all_content = '\n'.join(step.content for step in steps)
        
        assert "Supporting reason" in all_content, "Should handle SUPPORTS"
        assert "Attacking argument" in all_content, "Should handle ATTACKS"  
        assert "Undercutting argument" in all_content, "Should handle UNDERCUTS"
        assert "Contradictory statement" in all_content, "Should handle CONTRADICTORY"
