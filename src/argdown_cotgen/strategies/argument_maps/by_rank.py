"""
Rank-based strategy for argument maps.

This strategy builds argument maps by hierarchical rank/level:
1. Roots: Show all root nodes
2. First order reasons: Add direct children
3. Higher order reasons: Iteratively add deeper levels
4. Add YAML and comments

Minimal Test Case:
=================
Input:
```
[Climate Action]: We should act on climate change.
    <+ <Scientific Evidence>: Science supports action. {confidence: 0.95}
    <- <Economic Cost>: Action is too expensive. // Common objection
        <- <Long-term Benefits>: Benefits outweigh costs.
            <+ <Health Savings>: Prevents health costs.
```

Expected Output Steps:
- v1: Root only: "[Climate Action]: We should act on climate change."
- v2: First order (rank 1): Add <Scientific Evidence> and <Economic Cost>
- v3: Second order (rank 2): Add <Long-term Benefits>
- v4: Third order (rank 3): Add <Health Savings>
- v5: Add YAML inline data: {confidence: 0.95}
- v6: Add comments: // Common objection

Note: Each step shows all nodes up to that rank level with proper indentation.
"""

from typing import List
from ..base import BaseStrategy, AbortionMixin
from ...core.models import ArgdownStructure, ArgumentMapStructure, ArgumentMapLine, CotStep, INDENT_SIZE


class ByRankStrategy(AbortionMixin, BaseStrategy):
    """
    Rank-based strategy for reconstructing argument maps.
    """
    
    # Alternative explanation phrasings for different types of steps
    ROOT_EXPLANATIONS = [
        "Let me start by identifying the main claims.",
        "I'll begin by finding the primary claims.",
        "First, I need to identify the core claims.",
        "Let me first locate the main arguments.",
        "I'll start with the root-level claims."
    ]
    
    FIRST_ORDER_EXPLANATIONS = [
        "I'll add all first-order reasons and arguments.",
        "Now I'll include the direct supporting and opposing arguments.",
        "Next, I'll add the immediate reasons for each claim.",
        "Let me include all level 1 arguments.",
        "I'll now add the first-tier supporting evidence."
    ]
    
    INTERMEDIATE_EXPLANATIONS = [
        "Next, I'll add all level {depth} arguments.",
        "Now I'll include the level {depth} supporting details.",
        "Let me add the {depth}-tier arguments.",
        "I'll continue with level {depth} reasoning.",
        "Next, I'll include all depth {depth} arguments."
    ]
    
    FINAL_DEPTH_EXPLANATIONS = [
        "Finally, I'll add the deepest level arguments (level {depth}).",
        "Lastly, I'll include the most detailed arguments (level {depth}).",
        "To complete the structure, I'll add the final level {depth} arguments.",
        "Finally, I'll add the bottom-tier arguments (level {depth}).",
        "Let me finish by adding the deepest reasoning (level {depth})."
    ]
    
    YAML_EXPLANATIONS = [
        "Now I'll add the YAML inline data.",
        "Let me include the YAML metadata.",
        "I'll now add the inline YAML annotations.",
        "Next, I'll include the YAML inline information.",
        "Let me add the structured metadata."
    ]
    
    COMMENTS_EXPLANATIONS = [
        "Finally, I'll add clarifying comments and misc material.",
        "Lastly, I'll include the comments and, if applicable, additional content.",
        "To finish, I'll add the explanatory comments.",
        "Finally, let me add the commentary.",
        "Last, I'll include the additional comments."
    ]
    
    PLACEHOLDER_COMMENTS = [
        "🤔 Missing arguments here?",
        "More arguments might need to be added here.",
        "Need to check: Missing argument?",
        "I might add further arguments here in future steps.",
        "To consider: Add more content at this level."
    ]
    
    def generate(self, parsed_structure: ArgdownStructure, abortion_rate: float = 0.1) -> List[CotStep]:
        """
        Generate CoT steps using the by_rank strategy for argument maps.
        
        Args:
            parsed_structure: The parsed argument map structure
            abortion_rate: Probability of introducing abortion (0.0 to 1.0)
            
        Returns:
            List of CoT steps following the rank-based approach
        """
        if not isinstance(parsed_structure, ArgumentMapStructure):
            raise ValueError("ByRankStrategy requires an ArgumentMapStructure")
        
        steps = []
        max_depth = parsed_structure.max_depth
        
        # Step 1: Show only root nodes (depth 0)
        root_content = self._build_content_up_to_depth(parsed_structure, 0)
        steps.append(self._create_step(
            "v1",
            root_content,
            self._get_random_explanation(self.ROOT_EXPLANATIONS)
        ))
        
        # Steps 2+: Add each depth level progressively
        for depth in range(1, max_depth + 1):
            content = self._build_content_up_to_depth(parsed_structure, depth)
            explanation = self._get_explanation_for_depth(depth, max_depth)
            steps.append(self._create_step(
                f"v{depth + 1}",
                content,
                explanation
            ))
        
        # Add YAML inline data if present
        if self._has_yaml_data(parsed_structure):
            content_with_yaml = self._build_content_up_to_depth(
                parsed_structure, max_depth, include_yaml=True
            )
            steps.append(self._create_step(
                f"v{len(steps) + 1}",
                content_with_yaml,
                self._get_random_explanation(self.YAML_EXPLANATIONS)
            ))
        
        # Add comments if present
        if self._has_comments(parsed_structure):
            final_content = self._build_content_up_to_depth(
                parsed_structure, max_depth, include_yaml=True, include_comments=True
            )
            steps.append(self._create_step(
                f"v{len(steps) + 1}",
                final_content,
                self._get_random_explanation(self.COMMENTS_EXPLANATIONS)
            ))
        
        # Apply abortion post-processing
        steps = self._introduce_repetitions_with_abortion(steps, abortion_rate)
        
        return steps
    
    def _build_content_up_to_depth(self, structure: ArgumentMapStructure, 
                                 max_depth: int, include_yaml: bool = False, 
                                 include_comments: bool = False) -> str:
        """
        Build Argdown content including all lines up to the specified depth.
        
        Args:
            structure: The argument map structure
            max_depth: Maximum depth to include
            include_yaml: Whether to include YAML inline data
            include_comments: Whether to include comments
            
        Returns:
            Formatted Argdown content as string
        """
        lines = []
        
        for i, line in enumerate(structure.lines):
            # Skip empty lines that are not standalone comments
            if not line.content.strip() and not (include_comments and line.has_comment):
                continue
                
            # Include lines up to max_depth
            if line.indent_level <= max_depth:
                formatted_line = self._format_line(line, include_yaml, include_comments)
                if formatted_line.strip():  # Only add non-empty lines
                    lines.append(formatted_line)
                    
                    # Check if this line has children beyond max_depth and add placeholder if needed
                    if (not include_comments and 
                        line.content.strip() and 
                        self._line_has_children_beyond_depth(structure, i, max_depth)):
                        # Add placeholder comment at the appropriate indentation
                        placeholder_indent = " " * ((line.indent_level + 1) * INDENT_SIZE)
                        placeholder_text = self._get_random_explanation(self.PLACEHOLDER_COMMENTS)
                        lines.append(f"{placeholder_indent}// {placeholder_text}")
        
        return "\n".join(lines)
    
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
            indent = " " * (line.indent_level * INDENT_SIZE)
            return f"{indent}// {line.comment_content}"
        
        # Skip empty lines
        if not line.content.strip():
            return ""
        
        # Build the line with proper indentation
        indent = " " * (line.indent_level * INDENT_SIZE)
        
        # Add dialectical relation if present
        relation_part = ""
        if line.support_type and line.indent_level > 0:
            relation_part = f"{line.support_type.value} "
        
        # Build the main content
        content = line.content
        
        # Add YAML inline data if requested and present
        if include_yaml and line.yaml_inline_data:
            content += f" {line.yaml_inline_data}"
        
        # Add comment if requested and present
        if include_comments and line.has_comment and line.content.strip():
            content += f" // {line.comment_content}"
        
        return f"{indent}{relation_part}{content}"
    
    def _get_explanation_for_depth(self, depth: int, max_depth: int) -> str:
        """
        Get appropriate natural language explanation for each depth level.
        
        Args:
            depth: Current depth being added
            max_depth: Maximum depth in the structure
            
        Returns:
            Randomly selected explanation string for this step
        """
        if depth == 1:
            return self._get_random_explanation(self.FIRST_ORDER_EXPLANATIONS)
        elif depth == max_depth:
            return self._get_random_explanation(self.FINAL_DEPTH_EXPLANATIONS, depth=depth)
        else:
            return self._get_random_explanation(self.INTERMEDIATE_EXPLANATIONS, depth=depth)
    
    def _has_yaml_data(self, structure: ArgumentMapStructure) -> bool:
        """Check if any lines have YAML inline data."""
        return any(line.yaml_inline_data for line in structure.lines)
    
    def _has_comments(self, structure: ArgumentMapStructure) -> bool:
        """Check if any lines have comments."""
        return any(line.has_comment for line in structure.lines)
    
    def _has_content_beyond_depth(self, structure: ArgumentMapStructure, max_depth: int) -> bool:
        """Check if there are any content lines beyond the max_depth."""
        return any(line.content.strip() and line.indent_level > max_depth for line in structure.lines)
    
    def _line_has_children_beyond_depth(self, structure: ArgumentMapStructure, line_index: int, max_depth: int) -> bool:
        """Check if a specific line has children beyond the max_depth."""
        current_line = structure.lines[line_index]
        current_indent = current_line.indent_level
        
        # Look for subsequent lines that are children of this line and beyond max_depth
        for i in range(line_index + 1, len(structure.lines)):
            next_line = structure.lines[i]
            
            # If we reach a line at the same or lower level, we've left this line's subtree
            if next_line.content.strip() and next_line.indent_level <= current_indent:
                break
                
            # If we find a child line beyond max_depth, this line has children beyond depth
            if (next_line.content.strip() and 
                next_line.indent_level > current_indent and 
                next_line.indent_level > max_depth):
                return True
                
        return False
