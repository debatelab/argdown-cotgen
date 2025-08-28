"""
Rank-based strategy for individual arguments.

This strategy builds arguments by logical rank/level:
1. Title and Gist
2. Final conclusion
3. Main inference step
4. Iteratively add remaining sub arguments
5. Inference information
6. YAML inline data
7. Comments and Misc

Minimal Test Case:
=================
Input:
```
<Democracy Argument>: Democracy is the best system.

(1) Democracy respects individual rights.
(2) Individual rights are fundamental.
(3) Systems respecting fundamental values are superior.
-- from (2) and (3) --
(4) Democracy respects fundamental values. {strength: 0.8}
-- from (1) and (4) --
(5) Democracy is the best system. // Main conclusion
```

Expected Output Steps:
- v1: Title and gist: "<Democracy Argument>: Democracy is the best system."
- v2: Scaffold with final conclusion: "(1) // ... ----- (2) Democracy is the best system."
- v3: Main inference step - add all propositions used to infer main conclusion: (1), (4), (5)
- v4: Add sub-argument for (4): propositions (2), (3), (4)
- v5: Add inference information: "-- from (2) and (3) --", "-- from (1) and (4) --"
- v6: Add YAML inline data: {strength: 0.8}
- v7: Add comments: // Main conclusion

Note: Propositions rendered as premises in previous steps become conclusions in sub-arguments.
"""

from typing import List, Optional
from ..base import BaseArgumentStrategy, CotStep, AbortionMixin
from ...core.models import ArgdownStructure, ArgumentStatementLine, ArgumentStructure


class ByRankStrategy(AbortionMixin, BaseArgumentStrategy):
    """
    Rank-based strategy for reconstructing individual arguments.
    """
    
    # Explanation templates for different steps
    TITLE_EXPLANATIONS = [
        "I'll start by identifying the title and gist of the argument.",
        "Let me begin with the argument's title and main claim.",
        "First, I shall to establish the argument's title and central thesis.",
        "I'll start by setting up the argument's title and core statement.",
        "Let me begin with the argument's heading and main proposition."
    ]
    
    SCAFFOLD_EXPLANATIONS = [
        "Now I'll create a basic premise-conclusion scaffold with the final conclusion.",
        "Let me set up the argument structure with the main conclusion.",
        "I'll establish the final conclusion, leaving room for premises to be added later.",
        "Now I'll create the argument scaffold showing the final conclusion.",
        "Let me outline a premise-conclusion structure including the main conclusion."
    ]
    
    MAIN_INFERENCE_EXPLANATIONS = [
        "I'll add the main inference step that leads to the final conclusion.",
        "Now I'll include the propositions that directly support the main conclusion.",
        "Let me add the primary sub argument leading to the final conclusion.",
        "I'll include the premises and conclusion for the final inference step.",
        "Now I'll add the propositions that directly entail the main conclusion."
    ]
    
    SUB_ARGUMENT_EXPLANATIONS = [
        "I'll add a sub-argument for statement ({number}), which shows how it can be derived from other statements.",
        "Now I'll include the supporting reasoning for statement ({number}).",
        "Let me add the inference step that leads to statement ({number}).",
        "I'll show how statement ({number}) is derived from additional premises.",
        "Now I'll add another sub-argument that justifies statement ({number})."
    ]
    
    INFERENCE_EXPLANATIONS = [
        "I'll add inference information that explicates the logical connections.",
        "Now I'll include the inference information to clarify the reasoning steps.",
        "Let me add the logical rules that govern these inferences.",
        "I'll include the inference annotations to show how the reasoning steps work.",
        "Now I'll add inference rules used to derive conclusions from the corresponding premises."
    ]
    
    YAML_EXPLANATIONS = [
        "I'll add the YAML inline data that provides additional information.",
        "Now I'll include the metadata and axtra information.",
        "Let me add the YAML annotations with further data.",
        "I'll include the inline data that adds context to the statements.",
        "Now I'll add the YAML metadata that enriches the argument."
    ]
    
    COMMENT_EXPLANATIONS = [
        "Finally, I'll add the comments that provide additional context.",
        "I'll include the explanatory comments to put the argument in context.",
        "Let me add the comments and misc content that provides helpful annotations.",
        "I'll include the contextual comments that explain the statements.",
        "Finally, I'll add the comments that offer additional insights."
    ]

    NOTES_INTERMEDIATE_CONCLUSION = [
        "not sure here",
        "need to revisit this",
        "might be an intermediate conclusion",
        "revisit later and add supporting premises if required",
        "🤔 Is this a conclusion?"
    ]


    """
    Rank-based strategy for reconstructing individual arguments.
    """
    
    def generate(self, parsed_structure: ArgdownStructure, abortion_rate: float = 0.0) -> List[CotStep]:
        """
        Generate CoT steps using the by_rank strategy for arguments.
        
        Args:
            parsed_structure: The parsed argument structure
            abortion_rate: Probability of introducing abortion (0.0 to 1.0)
            
        Returns:
            List of CoT steps following the rank-based approach
        """
        # Only handle ArgumentStructure, not ArgumentMapStructure
        if not isinstance(parsed_structure, ArgumentStructure):
            raise ValueError(f"{self.__class__.__name__} requires an ArgumentStructure, got {type(parsed_structure).__name__}")
            
        steps = []
        
        # Step 1: Title and Gist
        title_step = self._create_title_step(parsed_structure, len(steps) + 1)
        if title_step:
            steps.append(title_step)
        
        # Step 2: Scaffold with final conclusion
        scaffold_step = self._create_scaffold_step(parsed_structure, len(steps) + 1)
        if scaffold_step:
            steps.append(scaffold_step)
        
        # Step 3: Main inference step
        main_inference_step, last_added_intermediate_conclusion = self._create_main_inference_step(parsed_structure, len(steps) + 1)
        if main_inference_step:
            steps.append(main_inference_step)
        
        # Step 4: Add sub-arguments iteratively by rank
        sub_argument_steps = self._create_sub_argument_steps(parsed_structure, len(steps), last_added_intermediate_conclusion)
        steps.extend(sub_argument_steps)
        
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
    
    def _create_title_step(self, structure: ArgumentStructure, step_num: int) -> Optional[CotStep]:
        """Create the title and gist step."""
        preamble_lines = self._get_preamble_lines(structure)
        if not preamble_lines:
            return None
            
        content = self._format_statement_line(preamble_lines[0])
        explanation = self._get_random_explanation(self.TITLE_EXPLANATIONS)
        
        return self._create_step(f"v{step_num}", content, explanation)
    
    def _create_scaffold_step(self, structure: ArgumentStructure, step_num: int) -> CotStep:
        """Create the scaffold step with final conclusion."""
        final_conclusion = structure.final_conclusion
        scaffold_content = self._create_premise_conclusion_scaffold(structure, final_conclusion)
        explanation = self._get_random_explanation(self.SCAFFOLD_EXPLANATIONS)
        
        return self._create_step(f"v{step_num}", scaffold_content, explanation)
    
    def _create_main_inference_step(self, structure: ArgumentStructure, step_num: int) -> tuple[Optional[CotStep], Optional[int]]:
        """Create the main inference step."""
        # Find the final conclusion and its direct premises
        final_conclusion = structure.final_conclusion
        if not final_conclusion:
            return None, None
            
        # Get the main inference step by finding premises that directly support the final conclusion
        main_premises = self._find_direct_premises_for_conclusion(structure, final_conclusion)
        
        # Build content with preamble, main premises (renumbered), and final conclusion
        lines = []
        last_added_intermediate_conclusion: int | None = None
        
        # Add preamble if present
        preamble_lines = self._get_preamble_lines(structure)
        if preamble_lines:
            lines.append(self._format_statement_line(preamble_lines[0]))
            lines.append("")
        
        # Add main premises with consecutive numbering starting from 1
        for i, premise in enumerate(main_premises, 1):
            content = self._extract_statement_content(premise)
            # if premise is in fact an intermediate conclusion, add a note
            if self._is_intermediate_conclusion(structure, premise):
                note = self._get_random_explanation(self.NOTES_INTERMEDIATE_CONCLUSION)
                content += f" // {note}"
                last_added_intermediate_conclusion = i
            lines.append(f"({i}) {content}")
        
        # Add separator
        lines.append("-----")
        
        # Add final conclusion with next consecutive number
        conclusion_content = self._extract_statement_content(final_conclusion)
        conclusion_number = len(main_premises) + 1
        lines.append(f"({conclusion_number}) {conclusion_content}")
        
        content = '\n'.join(lines)
        explanation = self._get_random_explanation(self.MAIN_INFERENCE_EXPLANATIONS)
        
        return self._create_step(f"v{step_num}", content, explanation), last_added_intermediate_conclusion
    
    def _create_sub_argument_steps(self, structure: ArgumentStructure, step_count: int, last_added_intermediate_conclusion: int | None) -> List[CotStep]:
        """Create sub-argument steps (v4+)."""
        steps: List[CotStep] = []
        final_conclusion = structure.final_conclusion
        if not final_conclusion:
            return steps

        # Find ALL intermediate conclusions, not just those that are main premises
        all_intermediate_conclusions = []
        for statement in structure.numbered_statements:
            if self._is_intermediate_conclusion(structure, statement):
                all_intermediate_conclusions.append(statement)
        if not all_intermediate_conclusions:
            return steps    
        
        # Sort by statement number to ensure consistent ordering
        all_intermediate_conclusions.sort(key=lambda x: x.statement_number or 0, reverse=True)

        # Target label for explanations
        target_label = last_added_intermediate_conclusion

        # Create step with intermediate conclusions (i1) (i1,i2) (i1,i2,i3) etc 
        for i in range(len(all_intermediate_conclusions)):
            step_version = f"v{step_count + i + 1}"
            assert target_label is not None, "target_label should be provided if there are intermediate conclusions to expand."
            sub_arg_content, next_target_label = self._build_sub_argument_content(structure, all_intermediate_conclusions, i+1)
            
            explanation = self._get_random_explanation(
                self.SUB_ARGUMENT_EXPLANATIONS, 
                number=target_label
            )
            steps.append(self._create_step(step_version, sub_arg_content, explanation))
            target_label = next_target_label
        
        return steps
    
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
    
    def _find_direct_premises_for_conclusion(self, structure: ArgumentStructure, conclusion: ArgumentStatementLine | None):
        """Find premises that directly support a given conclusion by looking at inference rules."""
        if not conclusion or not conclusion.statement_number:
            return []
            
        numbered_statements = self._get_numbered_statements(structure)
        conclusion_num = conclusion.statement_number
        
        # Look for inference rules
        inference_rules = self._get_inference_rules(structure)
        premises_for_conclusion = []
        
        for rule in inference_rules:
            # Check if this rule is followed by our conclusion
            rule_line_num = rule.line_number
            conclusion_line_num = conclusion.line_number
            
            # If the conclusion comes right after this inference rule
            if conclusion_line_num > rule_line_num and conclusion_line_num - rule_line_num <= 2:
                # Parse the inference rule to extract premise numbers
                # Look for patterns like:
                # - "from (1) and (2)" or "from (2), (3)" - parenthetical format
                # - "-- from [1,2,3] --" or "-- uses: [1,2] --" - bracket format
                import re
                premise_nums = []
                
                # Try parenthetical format first: (1), (2), etc.
                parenthetical_numbers = re.findall(r'\((\d+)\)', rule.content)
                premise_nums.extend([int(num) for num in parenthetical_numbers])
                
                # Try bracket format: [1,2,3] or [1, 2, 3]
                bracket_matches = re.findall(r'\[([0-9,\s]+)\]', rule.content)
                for match in bracket_matches:
                    # Split by comma and extract numbers
                    numbers_in_brackets = re.findall(r'(\d+)', match)
                    premise_nums.extend([int(num) for num in numbers_in_brackets])
                
                # Remove duplicates while preserving order
                seen = set()
                unique_premise_nums = []
                for num in premise_nums:
                    if num not in seen:
                        seen.add(num)
                        unique_premise_nums.append(num)
                premise_nums = unique_premise_nums
                
                # Find the actual statements with these numbers
                for stmt in numbered_statements:
                    if stmt.statement_number in premise_nums:
                        premises_for_conclusion.append(stmt)
        
        # If no inference rules found, use simple heuristic
        if not premises_for_conclusion:
            # Find statements numbered just before this conclusion
            candidates = [stmt for stmt in numbered_statements 
                         if stmt.statement_number and stmt.statement_number < conclusion_num]
            # Take all preceeding statements up to previous inference line (if any) as likely premises
            premises_for_conclusion: List[ArgumentStatementLine] = []
            for line in reversed(structure.lines[:conclusion.line_number - 1]):
                if premises_for_conclusion and (line.is_inference_rule or line.is_separator):
                    break
                if line in candidates:
                    premises_for_conclusion.append(line)

            # Reverse to maintain original order
            premises_for_conclusion.reverse()
        
        return premises_for_conclusion
    
    def _build_sub_argument_content(self, structure: ArgumentStructure, intermediate_conclusions: List[ArgumentStatementLine], num_intermediate_conclusions_to_show: int) -> tuple[str, int | None]:
        """Build content for a sub-argument by expanding from the main inference step."""

        # TODO: rewrite 
        # Go through the structure line by line, counting statements that have been added
        # If LINE is either 
        # - the final conclusion
        # - a direct premise for the final conclusion
        # - an intermediate conclusion in the list or
        # - a direct premise for any of the intermediate conclusions in the list
        # then add it to the sub-argument, renumbering as we go
        # If LINE is a conclusion (final or intermediate), add a separator line before it

        final_conclusion = structure.final_conclusion
        assert final_conclusion is not None, "Final conclusion is required to build sub-argument content."
        revealed_intermediate_conclusions = intermediate_conclusions[:num_intermediate_conclusions_to_show]


        revealed_statements: List[ArgumentStatementLine] = []
        for concl in revealed_intermediate_conclusions + [final_conclusion]:
            revealed_statements.extend(self._find_direct_premises_for_conclusion(structure, concl))
        revealed_statements.extend(revealed_intermediate_conclusions)
        revealed_statements.append(final_conclusion)
        revealed_statements = [s for e, s in enumerate(revealed_statements) if revealed_statements.index(s) == e]  # remove duplicates

        lines: List[str] = []

        # Add preamble if present
        preamble_lines = self._get_preamble_lines(structure)
        if preamble_lines:
            lines.append(self._format_statement_line(preamble_lines[0]))
            lines.append("")
        
        label_counter = 1
        label_of_last_added_intermediate_conclusion: int | None = None

        for line in structure.lines:
            if not line.is_numbered_statement:
                continue
            if line in revealed_intermediate_conclusions or line == final_conclusion:
                lines.append("-----")
            if line in revealed_statements:
                if line in intermediate_conclusions[num_intermediate_conclusions_to_show:]:
                    note = "  // " + self._get_random_explanation(self.NOTES_INTERMEDIATE_CONCLUSION)
                    label_of_last_added_intermediate_conclusion = label_counter
                else:
                    note = ""
                content = self._extract_statement_content(line)
                lines.append(f"({label_counter}) {content}{note}")
                label_counter += 1

        return '\n'.join(lines), label_of_last_added_intermediate_conclusion

    
    def _extract_statement_content(self, statement: ArgumentStatementLine):
        """Extract the content of a statement without the number prefix."""
        content = statement.content.strip()
        # Remove the number prefix like "(1) " from the content
        import re
        match = re.match(r'^\(\d+\)\s*(.*)$', content)
        if match:
            return match.group(1)
        return content
    
    def _find_inference_rule_for_statement(self, structure: ArgumentStructure, statement):
        """Find the inference rule that leads to a specific statement."""
        if not statement or not statement.line_number:
            return None
            
        inference_rules = self._get_inference_rules(structure)
        
        # Look for an inference rule that comes just before this statement
        for rule in inference_rules:
            if (rule.line_number < statement.line_number and 
                statement.line_number - rule.line_number <= 2):
                return rule
        
        return None
    
    def _renumber_inference_rule(self, rule_content: str, premises):
        """Renumber an inference rule to match new premise numbering."""
        # Create mapping from original numbers to new consecutive numbers
        new_rule = rule_content
        for i, premise in enumerate(premises, 1):
            if premise.statement_number:
                old_ref = f"({premise.statement_number})"
                new_ref = f"({i})"
                new_rule = new_rule.replace(old_ref, new_ref)
        
        return new_rule
    
    def _find_renumbered_position(self, statement, main_premises):
        """Find the renumbered position of a statement in the main premises list."""
        for i, premise in enumerate(main_premises, 1):
            if premise.statement_number == statement.statement_number:
                return i
        return statement.statement_number  # fallback to original number
    
    def _is_intermediate_conclusion(self, structure: ArgumentStructure, statement):
        """
        Check if a statement is an intermediate conclusion.
        
        A statement is an intermediate conclusion if:
        1. It is derived by an inference rule (first statement after an inference line)
        2. It is not the final conclusion
        """
        if not statement or not statement.statement_number:
            return False
            
        # Check if it's the final conclusion
        final_conclusion = structure.final_conclusion
        if final_conclusion and statement.statement_number == final_conclusion.statement_number:
            return False
            
        # Check if it's derived by an inference rule
        return self._is_derived_by_inference(structure, statement)
    
    def _is_derived_by_inference(self, structure: ArgumentStructure, statement):
        """
        Check if a statement is derived by an inference rule.
        
        A statement is derived if it's the first statement to appear after an inference line (i.e., inference_rule OR separator line).
        """
        if not statement.line_number:
            return False
            
        # Get both inference rules and separator lines
        inference_rules = self._get_inference_rules(structure)
        separator_lines = [line for line in structure.lines if line.is_separator]
        all_rule_lines = inference_rules + separator_lines
        
        numbered_statements = self._get_numbered_statements(structure)
        
        for rule in all_rule_lines:
            if not rule.line_number:
                continue
                
            # Find the first statement line that appears after this inference rule or separator
            first_statement_after_rule = None
            min_line_number = float('inf')
            
            for stmt in numbered_statements:
                if (stmt.line_number and 
                    stmt.line_number > rule.line_number and
                    stmt.line_number < min_line_number):
                    first_statement_after_rule = stmt
                    min_line_number = stmt.line_number
            
            # If this statement is the first after this rule, it's derived
            if (first_statement_after_rule and 
                first_statement_after_rule.statement_number == statement.statement_number):
                return True
        
        return False
