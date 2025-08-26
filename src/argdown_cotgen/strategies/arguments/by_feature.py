"""
Feature-based strategy for individual arguments.

This strategy builds arguments step by step by feature:
1. Title and Gist
2. Final conclusion
3. Premises
4. Intermediate Conclusions
5. Inference information
6. YAML inline data
7. Comments and Misc

Minimal Test Case:
=================
Input:
```
<Moral Argument>: We should protect the environment.

(1) Climate change causes suffering. {certainty: 0.9}
(2) We have a duty to prevent suffering. // Kantian principle
-- modus ponens --
(3) We should act against climate change.
(4) Environmental protection reduces climate change.
-- practical syllogism --
(5) We should protect the environment.
```

Expected Output Steps:
- v1: Title and gist only
- v2: Add premise-conclusion scaffold with final conclusion (5)
- v3: Add all premises (1), (2), (4) 
- v4: Add intermediate conclusion (3)
- v5: Add inference information (modus ponens, practical syllogism)
- v6: Add YAML inline data {certainty: 0.9}
- v7: Add comments // Kantian principle

Notes:
* In each step, propositions are enumerated consecutively.
* Each step may contain preliminary comments like "// inference data needs to be added here"
* Variant: Add title and gist at the very end rather than at the beginning.
"""

from typing import List, Optional, Dict
import re
from ..base import BaseArgumentStrategy, CotStep, AbortionMixin
from ...core.models import ArgdownStructure, ArgumentStructure, ArgumentStatementLine


class ByFeatureStrategy(AbortionMixin, BaseArgumentStrategy):
    """
    Feature-based strategy for reconstructing individual arguments.
    
    This strategy builds arguments by adding features in a specific order:
    premises first, then intermediate conclusions, then supporting elements.
    """
    
    # Explanation templates for different steps
    TITLE_EXPLANATIONS = [
        "I'll start by identifying the title and gist of the argument.",
        "Let me begin with the argument's title and main claim.",
        "First, I will note the argument's title and gist.",
        "I'll start by setting up the argument's title and core statement.",
        "Let me begin with the argument's heading and main thought."
    ]
    
    SCAFFOLD_EXPLANATIONS = [
        "Now I'll create a basic premise-conclusion scaffold with the final conclusion.",
        "Let me set up the abstract argument pattern with the main conclusion.",
        "I'll sketch the basic argument structure with the final conclusion.",
        "Now I'll create the argument scaffold showing the final conclusion.",
        "Let me build the premise-conclusion structure with the main conclusion."
    ]
    
    PREMISES_EXPLANATIONS = [
        "I'll add all the premise statements that provide the foundation for this argument.",
        "Now I'll include all the basic premises that ground the reasoning.",
        "Let me add the premises that the argument builds upon.",
        "I'll include all the premise statements that form the argument's foundation.",
        "Now I'll add the premises of the argument."
    ]
    
    INTERMEDIATE_CONCLUSIONS_EXPLANATIONS = [
        "I'll add the intermediate conclusions that bridge premises to the final conclusion.",
        "Now I'll include the intermediate steps in the reasoning chain.",
        "Let me add the conclusions derived from the premises that further support the main conclusion.",
        "I'll include the intermediate reasoning steps that connect premises to the final conclusion.",
        "Now I'll add the derived conclusions that form the middle steps of the argument."
    ]
    
    INFERENCE_EXPLANATIONS = [
        "I'll add the inference rules that show the logical connections.",
        "Now I'll include the inference information to clarify the reasoning steps.",
        "Let me add the logical rules that govern these inferences.",
        "I'll include the inference annotations to show the reasoning structure.",
        "Now I'll add the inference rules that connect premises to conclusions."
    ]
    
    YAML_EXPLANATIONS = [
        "I'll add the YAML inline data that provides additional information.",
        "Now I'll include the metadata and misc data.",
        "Let me add the YAML annotations.",
        "I'll include the inline data that adds context to the statements.",
        "Now I'll add the YAML metadata that enriches the argument."
    ]
    
    COMMENT_EXPLANATIONS = [
        "Finally, I'll add the comments that provide additional context.",
        "I'll include the explanatory comments or misc material to clarify the reasoning.",
        "Let me add the comments that provide helpful annotations.",
        "I'll include the contextual comments that explain the statements.",
        "Finally, I'll add the comments that offer additional insights."
    ]
    
    def generate(self, parsed_structure: ArgdownStructure, abortion_rate: float = 0.0) -> List[CotStep]:
        """
        Generate CoT steps using the by_feature strategy for arguments.
        
        Args:
            parsed_structure: The parsed argument structure
            abortion_rate: Probability of introducing abortion (0.0 to 1.0)
            
        Returns:
            List of CoT steps following the feature-based approach
        """
        # Only handle ArgumentStructure, not ArgumentMapStructure
        if not isinstance(parsed_structure, ArgumentStructure):
            raise ValueError(f"{self.__class__.__name__} requires an ArgumentStructure, got {type(parsed_structure).__name__}")
            
        steps = []
        
        # Step 1: Title and Gist
        title_step = self._create_title_step(parsed_structure)
        if title_step:
            steps.append(title_step)
        
        # Step 2: Scaffold with final conclusion
        scaffold_step = self._create_scaffold_step(parsed_structure)
        if scaffold_step:
            steps.append(scaffold_step)
        
        # Step 3: Add all premises
        premises_step = self._create_premises_step(parsed_structure)
        if premises_step:
            steps.append(premises_step)
        
        # Step 4: Add intermediate conclusions
        intermediate_step = self._create_intermediate_conclusions_step(parsed_structure)
        if intermediate_step:
            steps.append(intermediate_step)
        
        # Step 5: Add inference information
        inference_step = self._create_inference_step(parsed_structure, len(steps))
        if inference_step:
            steps.append(inference_step)
        
        # Step 6: Add YAML inline data
        yaml_step = self._create_yaml_step(parsed_structure, len(steps))
        if yaml_step:
            steps.append(yaml_step)
        
        # Step 7: Add comments
        comment_step = self._create_comment_step(parsed_structure, len(steps))
        if comment_step:
            steps.append(comment_step)
        
        # Apply abortion mechanism if requested
        if abortion_rate > 0.0:
            steps = self._introduce_repetitions_with_abortion(steps, abortion_rate)
        
        return steps
    
    def _create_title_step(self, structure: ArgumentStructure) -> Optional[CotStep]:
        """Create the title and gist step (v1)."""
        preamble_lines = self._get_preamble_lines(structure)
        if not preamble_lines:
            return None
            
        content = self._format_statement_line(preamble_lines[0])
        explanation = self._get_random_explanation(self.TITLE_EXPLANATIONS)
        
        return self._create_step("v1", content, explanation)
    
    def _create_scaffold_step(self, structure: ArgumentStructure) -> CotStep:
        """Create the scaffold step with final conclusion (v2)."""
        final_conclusion = structure.final_conclusion
        scaffold_content = self._create_premise_conclusion_scaffold(structure, final_conclusion)
        explanation = self._get_random_explanation(self.SCAFFOLD_EXPLANATIONS)
        
        return self._create_step("v2", scaffold_content, explanation)
    
    def _create_premises_step(self, structure: ArgumentStructure) -> Optional[CotStep]:
        """Create step that adds ALL basic premises (v3)."""
        
        classification = self._classify_statements_by_feature(structure)
        premises = classification['premises']
        
        if not premises:
            return None
        
        # Build content starting from scaffold and adding all premises
        lines = []
        
        # Add preamble
        preamble_lines = self._get_preamble_lines(structure)
        if preamble_lines:
            lines.append(self._format_statement_line(preamble_lines[0]))
            lines.append("")
        
        # Add all premises with consecutive numbering
        for i, premise in enumerate(premises, 1):
            content = self._extract_statement_content(premise)
            lines.append(f"({i}) {content}")
        
        # Add placeholder comment for intermediate steps if there are any
        if classification['intermediate']:
            lines.append("// ... intermediate conclusions to be added here")
        
        # Add separator
        lines.append("-----")
        
        # Add final conclusion
        final_conclusion = structure.final_conclusion
        if final_conclusion:
            conclusion_content = self._extract_statement_content(final_conclusion)
            # Use consecutive numbering: after all premises
            final_number = len(premises) + 1
            lines.append(f"({final_number}) {conclusion_content}")
        
        content = '\n'.join(lines)
        explanation = self._get_random_explanation(self.PREMISES_EXPLANATIONS)
        
        return self._create_step("v3", content, explanation)
    
    def _create_intermediate_conclusions_step(self, structure: ArgumentStructure) -> Optional[CotStep]:
        """Create step that adds intermediate conclusions (v4)."""
        
        classification = self._classify_statements_by_feature(structure)
        premises = classification['premises']
        intermediates = classification['intermediate']
        
        if not intermediates:
            return None
        
        # Build complete argument with premises + intermediates + final conclusion
        lines = []
        
        # Add preamble
        preamble_lines = self._get_preamble_lines(structure)
        if preamble_lines:
            lines.append(self._format_statement_line(preamble_lines[0]))
            lines.append("")
        
        statement_counter = 1
        
        # Add all premises first
        for premise in premises:
            content = self._extract_statement_content(premise)
            lines.append(f"({statement_counter}) {content}")
            statement_counter += 1
        
        # Add separator after premises
        lines.append("-----")
        
        # Add all intermediate conclusions
        for intermediate in intermediates:
            content = self._extract_statement_content(intermediate)
            lines.append(f"({statement_counter}) {content}")
            statement_counter += 1
        
        # Add separator before final conclusion
        lines.append("-----")
        
        # Add final conclusion
        final_conclusion = structure.final_conclusion
        if final_conclusion:
            conclusion_content = self._extract_statement_content(final_conclusion)
            lines.append(f"({statement_counter}) {conclusion_content}")
        
        content = '\n'.join(lines)
        explanation = self._get_random_explanation(self.INTERMEDIATE_CONCLUSIONS_EXPLANATIONS)
        
        return self._create_step("v4", content, explanation)
    
    def _classify_statements_by_feature(self, structure: ArgumentStructure) -> Dict[str, List[ArgumentStatementLine]]:
        """Classify all statements by their logical role/feature."""
        
        final_conclusion = structure.final_conclusion
        numbered_statements = self._get_numbered_statements(structure)
        
        premises: List[ArgumentStatementLine] = []
        intermediate: List[ArgumentStatementLine] = []
        
        # Get all conclusions derived by inference rules
        derived_statement_numbers = self._get_derived_statement_numbers(structure)
        
        # Sort statements by their statement number for consistent processing
        sorted_statements = sorted(
            [s for s in numbered_statements if s != final_conclusion],
            key=lambda x: x.statement_number or 0
        )
        
        for statement in sorted_statements:
            # Check if this statement number appears as a conclusion of any inference
            if statement.statement_number in derived_statement_numbers:
                intermediate.append(statement)
            else:
                premises.append(statement)
        
        return {
            'premises': premises,
            'intermediate': intermediate
        }
    
    def _get_derived_statement_numbers(self, structure: ArgumentStructure) -> set:
        """
        Get the set of statement numbers that are derived by inference rules.
        
        A statement is a conclusion iff it is the first statement to appear after an inference line.
        We allow for non-statement lines (comments, etc.) to appear between inference and conclusion.
        """
        derived_numbers = set()
        inference_rules = self._get_inference_rules(structure)
        numbered_statements = self._get_numbered_statements(structure)
        
        for rule in inference_rules:
            if not rule.line_number:
                continue
                
            # Find the first statement line that appears after this inference rule
            first_statement_after_rule = None
            min_line_number = float('inf')
            
            for statement in numbered_statements:
                if (statement.line_number and 
                    statement.line_number > rule.line_number and
                    statement.line_number < min_line_number):
                    first_statement_after_rule = statement
                    min_line_number = statement.line_number
            
            # If we found a first statement after this rule, it's a conclusion
            if first_statement_after_rule and first_statement_after_rule.statement_number:
                derived_numbers.add(first_statement_after_rule.statement_number)
        
        return derived_numbers
    
    def _is_derived_from_premises(self, structure: ArgumentStructure, statement: ArgumentStatementLine) -> bool:
        """Check if a statement is derived from other premises by looking for preceding inference rules."""
        if not statement.line_number:
            return False
            
        inference_rules = self._get_inference_rules(structure)
        
        # Look for inference rules that come just before this statement
        for rule in inference_rules:
            if (rule.line_number and rule.line_number < statement.line_number and 
                statement.line_number - rule.line_number <= 2):
                return True
        
        return False
    
    def _extract_statement_content(self, statement: ArgumentStatementLine) -> str:
        """Extract the content of a statement without the number prefix."""
        content = statement.content.strip()
        # Remove the number prefix like "(1) " from the content
        match = re.match(r'^\(\d+\)\s*(.*)$', content)
        if match:
            return match.group(1)
        return content
    
    def _create_inference_step(self, structure: ArgumentStructure, step_count: int) -> Optional[CotStep]:
        """Create the inference information step."""
        inference_rules = self._get_inference_rules(structure)
        if not inference_rules:
            return None
            
        # Build complete argument with inference rules
        content = self._format_argument_complete(structure, include_yaml=False, include_comments=False)
        explanation = self._get_random_explanation(self.INFERENCE_EXPLANATIONS)
        
        return self._create_step(f"v{step_count + 1}", content, explanation)
    
    def _create_yaml_step(self, structure: ArgumentStructure, step_count: int) -> Optional[CotStep]:
        """Create the YAML inline data step."""
        if not self._has_yaml_data(structure):
            return None
            
        # Build complete argument with YAML but no comments
        content = self._format_argument_complete(structure, include_yaml=True, include_comments=False)
        explanation = self._get_random_explanation(self.YAML_EXPLANATIONS)
        
        return self._create_step(f"v{step_count + 1}", content, explanation)
    
    def _create_comment_step(self, structure: ArgumentStructure, step_count: int) -> Optional[CotStep]:
        """Create the final comments step."""
        if not self._has_comments(structure):
            return None
            
        # Build complete argument with everything
        content = self._format_argument_complete(structure, include_yaml=True, include_comments=True)
        explanation = self._get_random_explanation(self.COMMENT_EXPLANATIONS)
        
        return self._create_step(f"v{step_count + 1}", content, explanation)
