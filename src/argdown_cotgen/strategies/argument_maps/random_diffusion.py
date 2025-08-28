"""
Random diffusion strategy for argument maps.

This strategy starts with a randomly distorted version and
incrementally removes errors to reach the final correct version.

Minimal Test Case:
=================
Input (Final Correct Version):
```
[Exercise]: Regular exercise is beneficial.
    <+ <Health Benefits>: Exercise improves health.
    <- <Time Constraints>: People lack time for exercise.
```

Expected Output Steps:
- v1: Distorted version with errors:
  ```
  Regular exercise is beneficial.  // Missing label
      -> <Health Benefits>: Exercise improves health.  // Wrong relation
  [Time Constraints]: People lack time for exercise.  // Wrong node type and relation
  ```
- v2: Fix a first error (-> should be <+):
  ```
  Regular exercise is beneficial.
      <+ <Health Benefits>: Exercise improves health.
  [Time Constraints]: People lack time for exercise.
  ```
- v3: Fix a second error (add label):
  ```
  [Exercise]: Regular exercise is beneficial.
      <+ <Health Benefits>: Exercise improves health.
  [Time Constraints]: People lack time for exercise.
  ```
- v4: Fix a third error (place in correct position):
  ```
  [Exercise]: Regular exercise is beneficial.
      <+ <Health Benefits>: Exercise improves health.
      <- [Time Constraints]: People lack time for exercise.
  ```
- v5: Fix a fourth error (make argument):
  ```
  [Exercise]: Regular exercise is beneficial.
      <+ <Health Benefits>: Exercise improves health.
      <- <Time Constraints>: People lack time for exercise.
  ```
- v6: Add YAML and comments (if any)

Note: Starts with systematic distortions (wrong relations, wrong nesting, missing labels, wrong node types etc.)
and progressively corrects them to demonstrate error-correction reasoning.
"""


import random
import copy
from abc import ABC, abstractmethod
from ..base import BaseArgumentMapStrategy, AbortionMixin
from ...core.models import ArgdownStructure, ArgumentMapLine, ArgumentMapStructure, CotStep, DialecticalType


class ErrorMechanism(ABC):
    """Abstract interface for error introduction mechanisms."""
    
    @abstractmethod
    def introduce_error(self, structure: ArgumentMapStructure) -> tuple[ArgumentMapStructure, str]:
        """Introduce one error into the structure."""
        pass
    
    @abstractmethod 
    def get_explanation(self, node_label: str) -> str:
        """Get explanation for fixing this type of error regarding node node_label."""
        pass

# Implementations of error mechanisms

class DialecticalRelationError(ErrorMechanism):
    """
    Error mechanism that introduces incorrect dialectical relations.
    """

    ADD_NOTE_PROBABILITY = 0.1  # Probability of adding note to content of corrupt line

    # Explanation templates for different types of error corrections
    DIALECTICAL_ERROR_EXPLANATIONS = [
        "I notice the dialectical relation for '{node_label}' is incorrect, let me fix it.",
        "The support/attack relation for '{node_label}' seems wrong, let me correct it.",
        "The logical relationship for '{node_label}' is off, let me adjust it.",
        "Not sure the relation type for '{node_label}' is correct, let me try to fix it."
    ]

    NOTES = [
        "// Note: relation seems off",
        "// Not sure here",
        "// NOTE: Is this correct?",
        "// needs to be revisited",
        "// might need to fix this later",
        "// Correct? Check later."
    ]

    def introduce_error(self, structure: ArgumentMapStructure) -> tuple[ArgumentMapStructure, str]:
        """
        Introduce a dialectical relation error by changing a random relation to a different one.
        
        Returns:
            Tuple of (corrupted_structure, explanation)
        """
        # Create a deep copy to avoid modifying the original
        corrupted_structure = copy.deepcopy(structure)
        
        # Find all lines that have dialectical relations
        lines_with_relations = []
        for i, line in enumerate(corrupted_structure.lines):
            if line.content.strip() and line.support_type is not None:
                lines_with_relations.append((i, line))
        
        # If no relations found, return unchanged, will trigger another attempt
        if not lines_with_relations:
            return structure, ""
        
        # Pick a random line with a relation
        line_index, selected_line = random.choice(lines_with_relations)
        
        # Get the current relation
        current_relation = selected_line.support_type
        
        # Get all possible DialecticalType values
        all_relations = list(DialecticalType) + [None]  # Include None as a possible relation
        
        # Filter out the current relation to ensure we pick a different one
        available_relations = [rel for rel in all_relations if rel != current_relation]
        
        # If somehow no different relations available (shouldn't happen), return unchanged, will trigger another attempt
        if not available_relations:
            return structure, ""
        
        # Pick a random different relation
        new_relation = random.choice(available_relations)
        
        # Update the line's support_type
        corrupted_structure.lines[line_index].support_type = new_relation

        # Add a note to the content with some probability, provided the content doesn' contain a comment already
        if (random.random() < self.ADD_NOTE_PROBABILITY and "//" not in selected_line.content):
            note = random.choice(self.NOTES)
            corrupted_structure.lines[line_index].content += " " + note

        # Get node label for explanation (use label if available, otherwise content preview)
        if selected_line.label:
            node_label = selected_line.label
        else:
            # Fallback to content preview if no label
            content_preview = selected_line.content.strip()
            node_label = content_preview[:30] + "..." if len(content_preview) > 30 else content_preview
        
        # Generate explanation
        explanation = self.get_explanation(node_label)
        
        return corrupted_structure, explanation
    
    def get_explanation(self, node_label: str) -> str:
        return random.choice(self.DIALECTICAL_ERROR_EXPLANATIONS).format(node_label=node_label)


class LabelError(ErrorMechanism):
    """
    Error mechanism that introduces missing or incorrect labels.
    """

    ADD_NOTE_PROBABILITY = 0.1  # Probability of adding note to content

    LABEL_ERROR_EXPLANATIONS = [
        "The statement '{node_label}' is missing proper labeling, let me add it.",
        "The node labeling for {node_label} is incorrect, let me fix it.",
        "'{node_label}' needs a proper label format, let me correct it.",
        "Let me fix the missing or wrong label for '{node_label}'."
    ]

    NOTES = [
        "// missing label?",
        "// needs proper labeling",
        "// label format unclear",
        "// should this have a label?",
        "// labeling issue here",
        "// fix later"
    ]

    def introduce_error(self, structure: ArgumentMapStructure) -> tuple[ArgumentMapStructure, str]:
        """
        Introduce a label error by removing or corrupting labels.
        
        Returns:
            Tuple of (corrupted_structure, explanation)
        """
        # Create a deep copy to avoid modifying the original
        corrupted_structure = copy.deepcopy(structure)
        
        # Find all lines that have labels
        lines_with_labels = []
        for i, line in enumerate(corrupted_structure.lines):
            if line.content.strip() and line.label:
                lines_with_labels.append((i, line))
        
        # If no labels found, return unchanged, will trigger another attempt
        if not lines_with_labels:
            return structure, ""
        
        # Pick a random line with a label
        line_index, selected_line = random.choice(lines_with_labels)
        
        # Store the original label for the explanation
        original_label = selected_line.label
        assert original_label is not None  # For type checker
        
        # Remove the label by setting it to None
        corrupted_structure.lines[line_index].label = None
        
        # Add a note to the content with some probability
        if (random.random() < self.ADD_NOTE_PROBABILITY and "//" not in selected_line.content):
            note = random.choice(self.NOTES)
            corrupted_structure.lines[line_index].content += " " + note
        
        # Generate explanation using the original label
        explanation = self.get_explanation(original_label)
        
        return corrupted_structure, explanation
    
    def get_explanation(self, node_label: str) -> str:
        return random.choice(self.LABEL_ERROR_EXPLANATIONS).format(node_label=node_label)
    

class NodeTypeError(ErrorMechanism):
    """
    Error mechanism that introduces incorrect node types (claim vs argument).
    """

    ADD_NOTE_PROBABILITY = 0.1  # Probability of adding note to content

    NODE_TYPE_ERROR_EXPLANATIONS = [
        "The node type for '{node_label}' is wrong, let me correct it.",
        "The brackets are incorrect for '{node_label}', let me fix them.",
        "'{node_label}' should be formatted differently, let me adjust the node type.",
        "Let me correct the node type for {node_label}."
    ]

    NOTES = [
        "// claim or argument?",
        "// bracket type unclear",
        "// [claim] vs <argument>?",
        "// unsure here",
        "// might need to be fixed later",
        "// check node type",
        "// wrong brackets?"
    ]

    def introduce_error(self, structure: ArgumentMapStructure) -> tuple[ArgumentMapStructure, str]:
        """
        Introduce a node type error by changing claim/argument formatting.
        
        Returns:
            Tuple of (corrupted_structure, explanation)
        """
        # Create a deep copy to avoid modifying the original
        corrupted_structure = copy.deepcopy(structure)
        
        # Find all lines that have labels (since we need labels to change their type)
        lines_with_labels: list[tuple[int, ArgumentMapLine]] = []
        for i, line in enumerate(corrupted_structure.lines):
            if line.content.strip() and line.label:
                lines_with_labels.append((i, line))
        
        # If no labels found, return unchanged, will trigger another attempt
        if not lines_with_labels:
            return structure, ""
        
        # Pick a random line with a label
        line_index, selected_line = random.choice(lines_with_labels)
        
        # Store the original label for the explanation
        original_label = selected_line.label
        assert original_label is not None  # For type checker
        
        # Flip the node type (claim <-> argument)
        corrupted_structure.lines[line_index].is_claim = not selected_line.is_claim
        
        # Add a note to the content with some probability
        if (random.random() < self.ADD_NOTE_PROBABILITY and "//" not in selected_line.content):
            note = random.choice(self.NOTES)
            corrupted_structure.lines[line_index].content += " " + note
        
        # Generate explanation using the original label
        explanation = self.get_explanation(original_label)
        
        return corrupted_structure, explanation
    
    def get_explanation(self, node_label: str) -> str:
        return random.choice(self.NODE_TYPE_ERROR_EXPLANATIONS).format(node_label=node_label)


class PlacementError(ErrorMechanism):
    """
    Error mechanism that introduces incorrect placement in hierarchy.
    """

    ADD_NOTE_PROBABILITY = 0.1  # Probability of adding note to content

    PLACEMENT_ERROR_EXPLANATIONS = [
        "The argument '{node_label}' appears to be in the wrong place, let me move it (including its descendants).",
        "The structure for {node_label} looks off, let me reorganize.",
        "'{node_label}' needs to be repositioned, let me fix the hierarchy.",
        "The placement of {node_label} is incorrect, let me correct it."
    ]

    NOTES = [
        "// wrong place?",
        "// should this be elsewhere?",
        "// placement unclear",
        "// reorganize structure",
        "// hierarchy issue",
        "// move this?"
    ]

    def introduce_error(self, structure: ArgumentMapStructure) -> tuple[ArgumentMapStructure, str]:
        """
        Introduce a placement error by moving a block to a different location.
        
        Returns:
            Tuple of (corrupted_structure, explanation)
        """
        # Create a deep copy to avoid modifying the original
        corrupted_structure = copy.deepcopy(structure)
        
        # Find all potential blocks (any node with content)
        content_nodes = []
        for i, line in enumerate(corrupted_structure.lines):
            if line.content.strip():
                content_nodes.append(i)
        
        # Need at least 2 content nodes to move one
        if len(content_nodes) < 2:
            return structure, ""
        
        # Pick a random node to move
        block_root_index = random.choice(content_nodes)
        block_root = corrupted_structure.lines[block_root_index]
        
        # Get all descendants of this block
        block_nodes = self._get_all_descendants(corrupted_structure, block_root_index)
        block_nodes.insert(0, block_root_index)  # Include the root itself
        
        # Ensure there are nodes outside this block
        external_nodes = [i for i in content_nodes if i not in block_nodes]
        if not external_nodes:
            return structure, ""
        
        # Find valid target parents (including None for root)
        valid_parents = self._find_valid_target_parents(corrupted_structure, block_root_index, block_nodes)
        if not valid_parents:
            return structure, ""
        
        # Choose a random valid parent
        new_parent_index = random.choice(valid_parents)
        
        # Move the block to the new parent
        self._move_block_to_parent(corrupted_structure, block_nodes, new_parent_index)
        
        # Add a note to the original block root with some probability
        # Note: We need to find the moved block's new position
        moved_block_root = None
        for line in corrupted_structure.lines:
            if (line.label == block_root.label and 
                line.content.strip() == block_root.content.strip()):
                moved_block_root = line
                break
        
        if (moved_block_root and random.random() < self.ADD_NOTE_PROBABILITY and 
            "//" not in moved_block_root.content):
            note = random.choice(self.NOTES)
            moved_block_root.content += " " + note
        
        # Get node label for explanation
        node_label = block_root.label if block_root.label else block_root.content.strip()[:20] + "..."
        
        # Generate explanation
        explanation = self.get_explanation(node_label)
        
        return corrupted_structure, explanation

    def _get_immediate_children(self, structure: ArgumentMapStructure, parent_index: int) -> list[int]:
        """Get the indices of immediate children of the given node."""
        parent_line = structure.lines[parent_index]
        parent_indent = parent_line.indent_level
        children = []
        
        # Look for immediate children (indent_level = parent_indent + 1)
        for i in range(parent_index + 1, len(structure.lines)):
            line = structure.lines[i]
            
            # Stop if we've left this parent's subtree
            if line.content.strip() and line.indent_level <= parent_indent:
                break
                
            # Add immediate children
            if line.content.strip() and line.indent_level == parent_indent + 1:
                children.append(i)
        
        return children

    def _get_all_descendants(self, structure: ArgumentMapStructure, node_index: int) -> list[int]:
        """Get all descendants of a node (recursive)."""
        descendants = []
        children = self._get_immediate_children(structure, node_index)
        
        for child in children:
            descendants.append(child)
            descendants.extend(self._get_all_descendants(structure, child))
        
        return descendants

    def _find_valid_target_parents(self, structure: ArgumentMapStructure, block_root: int, block_nodes: list[int]) -> list[int | None]:
        """Find valid parents where the block can be moved."""
        valid_parents: list[int | None] = []
        
        # Get current parent of the block
        current_parent = self._get_parent_index(structure, block_root)
        
        # Add None as option for making it a root node ONLY if it's not already root
        if current_parent is not None:  # Only add None if node is NOT already root
            valid_parents.append(None)
        
        # Find all content nodes
        for i, line in enumerate(structure.lines):
            if not line.content.strip():
                continue
                
            # Can't move block inside itself
            if i in block_nodes:
                continue
                
            # Can't move to current parent (no change)
            if i == current_parent:
                continue
                
            # This is a valid target parent
            valid_parents.append(i)
        
        return valid_parents

    def _get_parent_index(self, structure: ArgumentMapStructure, node_index: int) -> int | None:
        """Get the parent index of a node, or None if it's a root."""
        node_line = structure.lines[node_index]
        node_indent = node_line.indent_level
        
        # If it's at indent 0, it's a root node
        if node_indent == 0:
            return None
        
        # Look backwards for a node at the parent indent level
        target_indent = node_indent - 1
        for i in range(node_index - 1, -1, -1):
            line = structure.lines[i]
            if line.content.strip() and line.indent_level == target_indent:
                return i
        
        return None

    def _move_block_to_parent(self, structure: ArgumentMapStructure, block_nodes: list[int], new_parent_index: int | None) -> None:
        """Move a block to be under a new parent."""
        # Extract the block lines
        block_lines = [structure.lines[i] for i in block_nodes]
        
        # Calculate new indentation
        if new_parent_index is None:
            # Moving to root level
            new_base_indent = 0
            
            # Remove support_type from the block root when making it a root node
            if block_lines:
                block_lines[0].support_type = None  # Root nodes cannot have dialectical relations
        else:
            # Moving under a parent
            parent_indent = structure.lines[new_parent_index].indent_level
            new_base_indent = parent_indent + 1
        
        # Adjust indentation for the block
        original_base_indent = block_lines[0].indent_level
        indent_adjustment = new_base_indent - original_base_indent
        
        for line in block_lines:
            line.indent_level = max(0, line.indent_level + indent_adjustment)
        
        # Remove block from original position (reverse order to maintain indices)
        for i in reversed(sorted(block_nodes)):
            del structure.lines[i]
        
        # Find insertion point
        if new_parent_index is None:
            # Insert at the end of root nodes
            insertion_point = 0
            for i, line in enumerate(structure.lines):
                if line.content.strip() and line.indent_level == 0:
                    insertion_point = i + 1
            
            # Adjust insertion point if we removed lines before it
            removed_before = len([i for i in block_nodes if i < insertion_point])
            insertion_point -= removed_before
        else:
            # Adjust parent index if we removed lines before it
            adjusted_parent_index = new_parent_index
            removed_before = len([i for i in block_nodes if i <= new_parent_index])
            adjusted_parent_index -= removed_before
            
            # Find insertion point after this parent's existing children
            parent_indent = structure.lines[adjusted_parent_index].indent_level
            insertion_point = adjusted_parent_index + 1
            
            # Skip past existing children
            while (insertion_point < len(structure.lines) and 
                   structure.lines[insertion_point].content.strip() and
                   structure.lines[insertion_point].indent_level > parent_indent):
                insertion_point += 1
        
        # Insert the block at the new location
        for i, line in enumerate(block_lines):
            structure.lines.insert(insertion_point + i, line)

    def get_explanation(self, node_label: str) -> str:
        return random.choice(self.PLACEMENT_ERROR_EXPLANATIONS).format(node_label=node_label)


class SyntaxErrorMechanism(ErrorMechanism):
    """
    Error mechanism that introduces syntax errors.
    """

    ADD_NOTE_PROBABILITY = 0.1  # Probability of adding note to content

    SYNTAX_ERROR_EXPLANATIONS = [
        "There are syntax issues with '{node_label}', let me clean them up.",
        "The formatting for '{node_label}' needs correction, let me fix it.",
        "I need to fix the indentation and syntax for {node_label}.",
        "Let me correct the formatting problems with '{node_label}'."
    ]

    NOTES = [
        "// formatting issue",
        "// syntax error here?",
        "// might need to be fixed",
        "// cleanup needed",
        "// parsing problem",
        "// format unclear"
    ]

    def introduce_error(self, structure: ArgumentMapStructure) -> tuple[ArgumentMapStructure, str]:
        """
        Introduce a syntax error by corrupting formatting, indentation, or symbols.
        
        Returns:
            Tuple of (corrupted_structure, explanation)
        """
        # Create a deep copy to avoid modifying the original
        corrupted_structure = copy.deepcopy(structure)
        
        # Find all lines with content
        lines_with_content = []
        for i, line in enumerate(corrupted_structure.lines):
            if line.content.strip():
                lines_with_content.append((i, line))
        
        # If no content lines found, return unchanged
        if not lines_with_content:
            return structure, ""
        
        # Pick a random line with content
        line_index, selected_line = random.choice(lines_with_content)
        
        node_label = selected_line.label if selected_line.label else f"'{selected_line.content.strip()[:10]}...'"
        
        # Try different error types until we successfully apply one
        error_applied = False
        
        # Attempt 1: Wrong indent (most likely to succeed)
        if not error_applied:
            # Ensure we actually change the indent level
            indent_changes = [-3, -2, -1, 1, 2, 3]
            for indent_change in indent_changes:
                new_indent = max(0, selected_line.indent_level + indent_change)
                if new_indent != selected_line.indent_level:
                    corrupted_structure.lines[line_index].indent_level = new_indent
                    error_applied = True
                    break
        
        # Attempt 2: Wrong label syntax (if line has a label and indent didn't change)
        if not error_applied and selected_line.label:
            # Try removing colon from content
            content = selected_line.content
            if ": " in content:
                corrupted_structure.lines[line_index].content = content.replace(": ", " ", 1)
                error_applied = True
            elif selected_line.label.endswith((">", "]")):
                # Try removing closing bracket from label
                corrupted_structure.lines[line_index].label = selected_line.label[:-1]
                error_applied = True
        
        # Attempt 3: Illegal relation symbol (if line has a relation)
        if not error_applied and selected_line.support_type is not None:
            illegal_symbols = ["++", "--", "~>", "=>", "<", ">", ">>", "<<", "<~", "#", "*", "@"]
            illegal_symbol = random.choice(illegal_symbols)
            
            # Set support_type to None and modify content to include the illegal symbol
            corrupted_structure.lines[line_index].support_type = None
            
            # Prepend the illegal symbol to the content
            original_content = selected_line.content.strip()
            new_content = f"{illegal_symbol} {original_content}"
            corrupted_structure.lines[line_index].content = new_content
            error_applied = True
        
        # Attempt 4: Force content change if nothing else worked
        if not error_applied:
            # Add extra whitespace or modify content directly
            original_content = selected_line.content
            
            # Try adding extra spaces at the beginning
            if not original_content.startswith("  "):
                corrupted_structure.lines[line_index].content = "  " + original_content
                error_applied = True
            else:
                # If already has leading spaces, add a syntax error marker
                corrupted_structure.lines[line_index].content = original_content + " !"
                error_applied = True
        
        # Add a note to the content with some probability (after applying the syntax error)
        if (random.random() < self.ADD_NOTE_PROBABILITY and 
            "//" not in corrupted_structure.lines[line_index].content):
            note = random.choice(self.NOTES)
            corrupted_structure.lines[line_index].content += " " + note
        
        # Generate explanation
        explanation = self.get_explanation(node_label)
        
        return corrupted_structure, explanation
    
    def get_explanation(self, node_label: str) -> str:
        return random.choice(self.SYNTAX_ERROR_EXPLANATIONS).format(node_label=node_label)


class RandomDiffusionStrategy(AbortionMixin, BaseArgumentMapStrategy):
    """
    Random diffusion strategy for reconstructing argument maps.
    
    This strategy works backwards from the correct final version,
    introducing errors and then 'fixing' them step by step.
    """
                        
    INITIAL_EXPLANATIONS = [
        "Let me draft a complete argument map and gradually improve it.",
        "I'll sketch an initial map and fix any issues later.",
        "I shall start with a quick and dirty draft, progressively correcting it in later steps.",
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
    
    def __init__(self, mechanism_weights: dict[str, float] | None = None):
        super().__init__()
        self.error_mechanisms = [
            DialecticalRelationError(),
            LabelError(),
            NodeTypeError(), 
            PlacementError(),
            SyntaxErrorMechanism()
        ]
        
        # Default weights - can be customized via mechanism_weights parameter
        default_weights = {
            'DialecticalRelationError': 1.0,
            'LabelError': 0.6,
            'NodeTypeError': 0.6,
            'PlacementError': 1.0,
            'SyntaxErrorMechanism': 0.4
        }
        
        # Allow customization of weights
        self.mechanism_weights = mechanism_weights or default_weights
        
        # Validate weights
        for mechanism in self.error_mechanisms:
            mechanism_name = mechanism.__class__.__name__
            if mechanism_name not in self.mechanism_weights:
                self.mechanism_weights[mechanism_name] = 1.0  # Default weight
    
    def generate(self, parsed_structure: ArgdownStructure, abortion_rate: float = 0.0) -> list[CotStep]:
        """
        Generate CoT steps using random diffusion strategy.

        We work backwards from the correct final version, introducing errors progressively.
                
        Args:
            parsed_structure: The parsed argument map structure
            abortion_rate: Probability of introducing abortion (0.0 to 1.0)
            
        Returns:
            List of CoT steps following random diffusion approach
        """
        if not isinstance(parsed_structure, ArgumentMapStructure):
            raise ValueError("RandomDiffusionStrategy requires an ArgumentMapStructure")
        
        num_steps = self._sample_step_count(parsed_structure)
        
        current_map = copy.deepcopy(parsed_structure)
        steps: list[CotStep] = []
        
        for step_number in range(num_steps, 0, -1):

            if step_number > 1:

                while True:

                    # Randomly choose error-introduction mechanism
                    mechanism = self._choose_error_mechanism()
                    
                    # Apply error-introduction mechanism to current map
                    corrupted_map, explanation = mechanism.introduce_error(current_map)

                    if corrupted_map != current_map:
                        break
                else:
                    # Fallback: use a simple explanation and current map
                    corrupted_map = current_map
                    explanation = "Let me refine this structure."

            else:

                # This is the initial step
                corrupted_map = current_map
                explanation = random.choice(self.INITIAL_EXPLANATIONS)

            # NOTE: Step generation logic:
            # We work backwards from the correct final version, introducing errors progressively.
            # 
            # Loop order: step_number goes from num_steps down to 1 (e.g., 5,4,3,2,1)
            # - step_number=5: corrupted_map has 1 error, current_map is correct → creates step v5
            # - step_number=4: corrupted_map has 2 errors, current_map has 1 error → creates step v4  
            # - step_number=3: corrupted_map has 3 errors, current_map has 2 errors → creates step v3
            # - step_number=2: corrupted_map has 4 errors, current_map has 3 errors → creates step v2
            # - step_number=1: corrupted_map not used, current_map has 4 errors → creates step v1
            #
            # Each CotStep(explanation, content) contains:
            # - explanation: Plan to fix the error that current_map contains
            # - content: The current_map state (showing the error to be fixed)
            #
            # Result: v1 shows most errors, v2 shows fewer errors, ..., v5 shows fewest errors
            # This creates the illusion of progressive error correction.

            content = self._format_map(current_map, include_yaml=False, include_comments=False)
            step = self._create_step(f"v{step_number}", content, explanation)
            steps.insert(0, step)  # Insert at beginning to maintain order
            current_map = corrupted_map
        
        # Add YAML inline data if present
        if self._has_yaml_data(parsed_structure):
            content_with_yaml = self._format_map(parsed_structure, include_yaml=True, include_comments=False)
            steps.append(self._create_step(
                f"v{len(steps) + 1}",
                content_with_yaml,
                self._get_random_explanation(self.YAML_EXPLANATIONS)
            ))
        
        # Add comments if present
        if self._has_comments(parsed_structure):
            final_content = self._format_map(parsed_structure, include_yaml=True, include_comments=True)
            steps.append(self._create_step(
                f"v{len(steps) + 1}",
                final_content,
                self._get_random_explanation(self.COMMENTS_EXPLANATIONS)
            ))
        
        # Apply abortion post-processing
        steps = self._introduce_repetitions_with_abortion(steps, abortion_rate)
        
        return steps
    
    def _sample_step_count(self, structure: ArgumentMapStructure) -> int:
        """
        Sample the number of error correction steps to perform.
        
        Args:
            structure: The argument map structure
            
        Returns:
            Number of steps (errors to introduce)
        """
        # Base the number of steps on structure complexity
        num_lines = len([line for line in structure.lines if line.content.strip()])
        
        # Scale based on number of content lines
        return random.randint(2, min(14, num_lines+1))  # Cap max steps to avoid excessive length
    
    def _choose_error_mechanism(self) -> ErrorMechanism:
        """
        Choose a random error introduction mechanism based on configured weights.
        
        Returns:
            Selected error mechanism
        """
        # Create weighted list based on mechanism weights
        mechanisms = []
        weights = []
        
        for mechanism in self.error_mechanisms:
            mechanism_name = mechanism.__class__.__name__
            weight = self.mechanism_weights.get(mechanism_name, 1.0)
            if weight > 0:  # Only include mechanisms with positive weights
                mechanisms.append(mechanism)
                weights.append(weight)
        
        if not mechanisms:
            # Fallback to uniform selection if all weights are zero
            return random.choice(self.error_mechanisms)
        
        # Use weighted random selection
        return random.choices(mechanisms, weights=weights, k=1)[0]
        
    def _format_map(self, structure: ArgumentMapStructure, include_yaml: bool = False, include_comments: bool = False) -> str:
        """
        Format argument map structure back to Argdown text.
        
        Args:
            structure: The argument map structure (may contain errors)
            include_yaml: Whether to include YAML inline data
            include_comments: Whether to include comments
            
        Returns:
            Formatted Argdown content as string
        """
        lines = []
        
        for line in structure.lines:
            # Skip empty lines without comments unless we're including comments
            if not line.content.strip() and not line.has_comment:
                if not include_comments:
                    continue
            
            # Format each line with specified options using inherited _format_line
            formatted_line = self._format_line(line, include_yaml=include_yaml, include_comments=include_comments)
            
            # Include line if it has content or if we're including comments and it has a comment
            if formatted_line.strip() or (include_comments and line.has_comment):
                lines.append(formatted_line)
        
        return "\n".join(lines)
