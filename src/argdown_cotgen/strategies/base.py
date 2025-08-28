"""
Base strategy interface for generating Chain-of-Thought reasoning traces.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import random
from ..core.models import ArgdownStructure, CotStep, ArgumentStructure, ArgumentMapStructure, ArgumentMapLine, ArgumentStatementLine, INDENT_SIZE


class AbortionMixin:
    """
    Mixin class that provides abortion functionality for CoT strategies.
    
    This mixin allows strategies to introduce realistic AI reconstruction errors
    with repetitions followed by abortion and retry attempts.
    
    Note: This mixin assumes the class it's mixed into has:
    - _create_step method (provided by BaseStrategy)
    - _get_random_explanation method (provided by BaseStrategy)
    """
    
    # Universal abortion and retry comments with emoji support
    ABORTION_COMMENTS = [
        "Oh no! This is just exactly what I've written before. Better ABORT and DISCARD this, and start anew.",
        "Oops! I just repeated myself. Let me discard this and try again.",
        "Fatal block repetition detected! Aborting this version and starting over.",
        "Detected fatal repetitions. Let me abort this step now and start afresh.",
        "Wait, I'm repeating content! Let me abort and redo this step.",
        "Error: Duplicate content found. Discarding this attempt and trying again.",
        "🚨 ABORT! I'm duplicating content here. Let me start over.",
        "❌ Fatal repetition error! Discarding this attempt and trying again.",
        "🛑 Wait, this is exactly what I wrote before! Better abort and restart.",
        "🚨 Repetition detected! Let me abort this version and try fresh.",
        "‼️ Oops! Duplicate content alert. Aborting and starting anew.",
        "⚠️ Error: I'm repeating myself. Time to abort and redo this step."
    ]
    
    RETRY_COMMENTS = [
        "🚮 I ignore the above Argdown snippet and will try again.",
        "Let me start over with this step.",
        "🚮 I'll discard the previous attempt and redo this step.",
        "Starting fresh with this reconstruction step.",
        "Let me try this step again without the repetitions.",
        "🔄 Let me restart this step from scratch.",
        "✨ Starting fresh with a clean slate for this step.",
        "🆕 Ignoring the previous attempt, let me try again.",
        "🔄 Let me focus and redo this step properly.",
        "🧹 Clearing the slate and reconstructing this step anew.",
        "🆕 Fresh start! Let me rebuild this step correctly."
    ]
    
    def _introduce_repetitions_with_abortion(self, steps: List[CotStep], 
                                           abortion_rate: float = 0.1) -> List[CotStep]:
        """
        Post-process steps to introduce repetitions and abortion comments.
        
        Args:
            steps: List of CoT steps to process
            abortion_rate: Probability of introducing abortion (0.0 to 1.0)
            
        Returns:
            List of steps with some potentially having abortion and retry
        """
        if abortion_rate <= 0.0:
            return steps
            
        processed_steps = []
        
        for step in steps:
            # Randomly decide if this step should have abortion
            if random.random() < abortion_rate and len(step.content.split('\n')) >= 3:
                # Create the aborted version with repetitions
                aborted_step = self._create_aborted_version(step)
                processed_steps.append(aborted_step)
                
                # Create the retry version (clean original)
                retry_explanation = self._get_random_explanation(self.RETRY_COMMENTS)  # type: ignore
                # This relies on the mixed-in class having _create_step method
                retry_step = self._create_step(  # type: ignore
                    step.version,  # Same version number
                    step.content,  # Original clean content
                    retry_explanation
                )
                processed_steps.append(retry_step)
            else:
                # Keep the original step
                processed_steps.append(step)
                
        return processed_steps
    
    def _create_aborted_version(self, step: CotStep) -> CotStep:
        """
        Create an aborted version of a step by introducing repetitions.
        
        Args:
            step: Original step to create aborted version from
            
        Returns:
            New step with repetitions and abortion comment
        """
        lines = step.content.split('\n')
        non_empty_lines = [i for i, line in enumerate(lines) if line.strip() and not line.strip().startswith('//')]
        
        if len(non_empty_lines) < 2:
            return step  # Can't create meaningful repetition
            
        # Choose repetition size (1, 2, or 3 lines)
        repetition_size = random.choice([1, 2, 3])
        
        # Find a suitable starting point for repetition (early in the content)
        max_start = min(len(non_empty_lines) - repetition_size, len(non_empty_lines) // 2)
        if max_start < 0:
            repetition_size = 1
            max_start = len(non_empty_lines) - 1
            
        if max_start >= 0:
            start_idx = random.randint(0, max_start)
            
            # Get the lines to repeat (in original line indices)
            lines_to_repeat_indices = non_empty_lines[start_idx:start_idx + repetition_size]
            lines_to_repeat = [lines[i] for i in lines_to_repeat_indices]
            
            # Insert the repetition after the original block
            insertion_point = lines_to_repeat_indices[-1] + 1
            
            # Create the distorted content - but STOP after the repetition point
            # Include content up to the insertion point, then add repetition, then ABORT
            distorted_lines = lines[:insertion_point] + lines_to_repeat
            
            # Add abortion comment immediately after the repetition
            if not hasattr(self, '_get_random_explanation'):
                raise NotImplementedError("AbortionMixin can only be used with classes that implement _get_random_explanation method.")
            abortion_comment = f"// {self._get_random_explanation(self.ABORTION_COMMENTS)}"  # type: ignore
            distorted_lines.append(abortion_comment)
            
            distorted_content = '\n'.join(distorted_lines)
            
            # This relies on the mixed-in class having _create_step method
            if not hasattr(self, '_create_step'):
                raise NotImplementedError("AbortionMixin can only be used with classes that implement _create_step method.")
            return self._create_step(  # type: ignore
                step.version,
                distorted_content,
                step.explanation
            )
        
        return step


class BaseStrategy(ABC):
    """
    Abstract base class for all CoT generation strategies.
    """
    
    @abstractmethod
    def generate(self, parsed_structure: ArgdownStructure, abortion_rate: float = 0.0) -> List[CotStep]:
        """
        Generate a sequence of CoT steps from a parsed Argdown structure.
        
        Args:
            parsed_structure: The parsed Argdown structure
            abortion_rate: Probability of introducing abortion (0.0 to 1.0)
            
        Returns:
            A list of CotStep objects representing the reasoning trace
        """
        pass
    
    def _create_step(self, version: str, content: str, explanation: str = "") -> CotStep:
        """Helper method to create a CoT step."""
        return CotStep(version, content, explanation)
    
    def _get_random_explanation(self, explanation_list: List[str], **format_kwargs) -> str:
        """
        Randomly select and format an explanation from the given list.
        
        Args:
            explanation_list: List of explanation templates
            **format_kwargs: Keyword arguments for string formatting
            
        Returns:
            Randomly selected and formatted explanation
        """
        template = random.choice(explanation_list)
        return template.format(**format_kwargs) if format_kwargs else template
    
    def _has_yaml_data(self, structure: ArgumentStructure | ArgumentMapStructure) -> bool:
        """Check if any lines have YAML inline data."""
        return any(line.yaml_inline_data for line in structure.lines)
    
    def _has_comments(self, structure: ArgumentStructure | ArgumentMapStructure) -> bool:
        """Check if any lines have comments."""
        return any(line.has_comment for line in structure.lines)
    

class BaseArgumentMapStrategy(BaseStrategy):
    """
    Abstract base class for all CoT argument map generation strategies.
    """    

    def _format_line(self, line: ArgumentMapLine, include_yaml: bool = False, 
                    include_comments: bool = False) -> str:
        """
        Convert an ArgumentMapLine back to proper Argdown syntax.
        
        Args:
            line: The ArgumentMapLine to format
            include_yaml: Whether to include YAML inline data
            include_comments: Whether to include comments
            
        Returns:
            Formatted Argdown line as string
        """
        # Handle standalone comments (empty content but has comment)
        if not line.content.strip() and include_comments and line.has_comment:
            indent = " " * (line.indent_level * line.indent_size)
            return f"{indent}// {line.comment_content}"
        
        # Skip empty lines
        if not line.content.strip():
            return ""
        
        # Build the line with proper indentation
        indent = " " * (line.indent_level * line.indent_size)
        
        # Add dialectical relation if present
        relation_part = ""
        if line.support_type and line.indent_level > 0:
            relation_part = f"{line.support_type.value} "
        
        # Build the main content
        content = line.content
        
        # Add YAML inline data if requested and present
        if include_yaml and line.yaml_inline_data:
            # Remove trailing spaces from content before adding YAML to avoid double spaces
            content = content.rstrip() + f" {line.yaml_inline_data}"
        
        # Add comment if requested and present
        if include_comments and line.has_comment and line.content.strip():
            content += f" // {line.comment_content}"
        
        return f"{indent}{relation_part}{content}"


class BaseArgumentStrategy(BaseStrategy):
    """
    Abstract base class for all CoT argument generation strategies.
    """

    def _format_statement_line(self, line: ArgumentStatementLine, include_yaml: bool = False, 
                              include_comments: bool = False) -> str:
        """
        Convert an ArgumentStatementLine back to proper Argdown syntax.
        
        Args:
            line: The ArgumentStatementLine to format
            include_yaml: Whether to include YAML inline data
            include_comments: Whether to include comments
            
        Returns:
            Formatted Argdown line as string
        """
        # Handle standalone comments (empty content but has comment)
        if not line.content.strip() and include_comments and line.has_comment:
            return f"// {line.comment_content}"
        
        # Skip empty lines
        if not line.content.strip():
            return ""
        
        # Handle different line types
        content = line.content.strip()
        
        # Handle inference rules (like "-- modus ponens --")
        if line.is_inference_rule:
            return content
        
        # Handle separators (like "-----")
        if line.is_separator:
            return content
        
        # Handle preamble (title and gist)
        if line.is_preamble:
            formatted_content = content
            # Add YAML inline data if requested and present
            if include_yaml and line.yaml_inline_data:
                formatted_content = formatted_content.rstrip() + f" {line.yaml_inline_data}"
            # Add comment if requested and present
            if include_comments and line.has_comment:
                formatted_content += f" // {line.comment_content}"
            return formatted_content
        
        # Handle numbered statements - content already includes the number
        # so we don't need to add it again
        formatted_content = content
        
        # Add YAML inline data if requested and present
        if include_yaml and line.yaml_inline_data:
            formatted_content = formatted_content.rstrip() + f" {line.yaml_inline_data}"
        
        # Add comment if requested and present
        if include_comments and line.has_comment:
            formatted_content += f" // {line.comment_content}"
        
        return formatted_content
    
    def _get_premises(self, structure: ArgumentStructure) -> List[ArgumentStatementLine]:
        """Get all premise statements from the argument structure."""
        return structure.premises
    
    def _get_conclusions(self, structure: ArgumentStructure) -> List[ArgumentStatementLine]:
        """Get all conclusion statements from the argument structure."""
        return structure.conclusions
    
    def _get_inference_rules(self, structure: ArgumentStructure) -> List[ArgumentStatementLine]:
        """Get all inference rule lines from the argument structure."""
        return [line for line in structure.lines if line.is_inference_rule]
    
    def _get_numbered_statements(self, structure: ArgumentStructure) -> List[ArgumentStatementLine]:
        """Get all numbered statements from the argument structure."""
        return structure.numbered_statements
    
    def _get_preamble_lines(self, structure: ArgumentStructure) -> List[ArgumentStatementLine]:
        """Get all preamble lines (title and gist) from the argument structure."""
        return [line for line in structure.lines if line.is_preamble]
    
    def _build_inference_step(self, premises: List[ArgumentStatementLine], 
                             conclusion: ArgumentStatementLine,
                             inference_rule: Optional[ArgumentStatementLine] = None,
                             include_yaml: bool = False,
                             include_comments: bool = False) -> str:
        """
        Build a complete inference step with premises, rule, and conclusion.
        
        Args:
            premises: List of premise statements
            conclusion: The conclusion statement
            inference_rule: Optional inference rule line
            include_yaml: Whether to include YAML inline data
            include_comments: Whether to include comments
            
        Returns:
            Formatted inference step as string
        """
        lines = []
        
        # Add premises
        for premise in premises:
            lines.append(self._format_statement_line(premise, include_yaml, include_comments))
        
        # Add inference rule if present
        if inference_rule:
            lines.append(self._format_statement_line(inference_rule, include_yaml, include_comments))
        
        # Add conclusion
        lines.append(self._format_statement_line(conclusion, include_yaml, include_comments))
        
        return '\n'.join(line for line in lines if line.strip())
    
    def _create_premise_conclusion_scaffold(self, structure: ArgumentStructure,
                                          main_conclusion: Optional[ArgumentStatementLine] = None) -> str:
        """
        Create a basic premise-conclusion scaffold structure.
        
        Args:
            structure: The argument structure
            main_conclusion: Optional specific conclusion to highlight
            
        Returns:
            Scaffold structure as string
        """
        lines = []
        
        # Add preamble if present
        preamble_lines = self._get_preamble_lines(structure)
        for line in preamble_lines:
            lines.append(self._format_statement_line(line))
        
        if preamble_lines:
            lines.append("")  # Empty line after preamble
        
        # Add placeholder for premises
        lines.append("(1) // ... premises to be added here")
        
        # Add separator
        lines.append("-----")
        
        # Add main conclusion or placeholder
        if main_conclusion:
            # Renumber the conclusion to (2) for consecutive numbering
            # Extract the content without the original statement number
            import re
            content_match = re.match(r'^\(\d+\)\s*(.*)$', main_conclusion.content.strip())
            if content_match:
                conclusion_text = content_match.group(1)
                lines.append(f"(2) {conclusion_text}")
            else:
                # Fallback if the content doesn't match expected format
                lines.append(f"(2) {main_conclusion.content.strip()}")
        else:
            lines.append("(2) // ... main conclusion to be added here")
        
        return '\n'.join(lines)
    
    def _format_argument_complete(self, structure: ArgumentStructure,
                                 include_yaml: bool = True,
                                 include_comments: bool = True) -> str:
        """
        Format the complete argument structure.
        
        Args:
            structure: The argument structure to format
            include_yaml: Whether to include YAML inline data
            include_comments: Whether to include comments
            
        Returns:
            Complete formatted argument as string
        """
        lines = []
        
        for line in structure.non_empty_lines:
            formatted_line = self._format_statement_line(line, include_yaml, include_comments)
            if formatted_line.strip():
                lines.append(formatted_line)
        
        return '\n'.join(lines)
    
