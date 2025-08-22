"""
Depth-first strategy for argument maps.

This strategy reveals nodes using depth-first traversal:
1. Start with all root nodes
2. Process nodes in stack order, following branches to maximum depth
3. Each step shows the children of one processed node
4. Complete entire branches before moving to siblings
5. Add YAML and comments at the end

Minimal Test Case:
=================
Input:
```
[Climate Action]: We should act on climate change.
    <+ <Scientific Evidence>: Science supports climate action.
        <+ <IPCC Reports>: International scientific consensus.
        <+ <Temperature Data>: Rising global temperatures.
    <- <Economic Costs>: Action is too expensive.
        <- <Long-term Benefits>: Benefits outweigh costs.
            <+ <Health Savings>: Reduced healthcare costs.
```

Expected Output Steps:
- v1: Show root: "[Climate Action]: We should act on climate change."
- v2: Process [Climate Action] - add its children: <Scientific Evidence>, <Economic Costs>
- v3: Process <Scientific Evidence> - add its children: <IPCC Reports>, <Temperature Data>
- v4: Process <Economic Costs> - add its children: <Long-term Benefits>
- v5: Process <Long-term Benefits> - add its children: <Health Savings>
- v6: Add YAML and comments (if any)

Note: Each step processes one node from the stack and shows its immediate children.
This follows true depth-first search traversal order - complete branches before siblings.
This differs from breadth-first which would process all level 1 nodes before level 2.
"""

from typing import List
from ..base import BaseArgumentMapStrategy, AbortionMixin
from ...core.models import ArgdownStructure, ArgumentMapStructure, CotStep


class DepthFirstStrategy(AbortionMixin, BaseArgumentMapStrategy):
    """
    Depth-first strategy for reconstructing argument maps.
    """
    
    # Explanation templates for different types of steps
    ROOT_EXPLANATIONS = [
        "Let me start by identifying the root claims.",
        "I'll begin with the main claims.",
        "First, I need to establish the primary claims.",
        "Let me start with the central arguments and propositions.",
        "I'll begin by showing the root-level claims."
    ]
    
    PROCESSING_EXPLANATIONS = [
        "Now I'll check '{node}' and show any arguments or claims directly related to it.",
        "Let me consider '{node}' and add its direct children.",
        "I'll now examine '{node}' and reveal any supporting and or attacking reasons.",
        "Processing '{node}' - I'll add immediate reasons and objections.",
        "Let me next expand '{node}'."
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
        "Lastly, I'll include the comments and additional content.",
        "To finish, I'll add the explanatory comments.",
        "Finally, let me add the commentary.",
        "Last, I'll include the additional comments."
    ]

    def generate(self, parsed_structure: ArgdownStructure, abortion_rate: float = 0.0) -> List[CotStep]:
        """
        Generate CoT steps using depth-first traversal.
        
        Args:
            parsed_structure: The parsed argument map structure
            abortion_rate: Probability of introducing abortion (0.0 to 1.0)
            
        Returns:
            List of CoT steps following depth-first approach
        """
        if not isinstance(parsed_structure, ArgumentMapStructure):
            raise ValueError("DepthFirstStrategy requires an ArgumentMapStructure")
        
        steps = []
        
        # Step 1: Show all root nodes
        root_nodes = self._get_root_nodes(parsed_structure)
        if root_nodes:
            root_content = self._build_content_with_nodes(parsed_structure, set(root_nodes))
            steps.append(self._create_step(
                "v1",
                root_content,
                self._get_random_explanation(self.ROOT_EXPLANATIONS)
            ))
        
        # Initialize depth-first stack with root nodes (in reverse order for proper processing)
        stack = list(reversed(root_nodes))
        revealed_nodes = set(root_nodes)  # Track which nodes we've revealed
        version_counter = 2
        
        # Process nodes depth-first
        while stack:
            current_node = stack.pop()  # LIFO - depth-first
            children = self._get_immediate_children(parsed_structure, current_node)
            
            # Only create a step if this node has children we haven't revealed yet
            new_children = [child for child in children if child not in revealed_nodes]
            if new_children:
                # Add new children to revealed set and stack (in reverse order for left-to-right processing)
                revealed_nodes.update(new_children)
                stack.extend(reversed(new_children))
                
                # Create step showing the expanded structure
                content = self._build_content_with_nodes(parsed_structure, revealed_nodes)
                node_name = self._extract_node_name(current_node, parsed_structure)
                explanation = self._get_random_explanation(
                    self.PROCESSING_EXPLANATIONS, 
                    node=node_name
                )
                
                steps.append(self._create_step(
                    f"v{version_counter}",
                    content,
                    explanation
                ))
                version_counter += 1
        
        # Add YAML inline data if present
        if self._has_yaml_data(parsed_structure):
            content_with_yaml = self._build_content_with_nodes(
                parsed_structure, revealed_nodes, include_yaml=True
            )
            steps.append(self._create_step(
                f"v{version_counter}",
                content_with_yaml,
                self._get_random_explanation(self.YAML_EXPLANATIONS)
            ))
            version_counter += 1
        
        # Add comments if present
        if self._has_comments(parsed_structure):
            final_content = self._build_content_with_nodes(
                parsed_structure, revealed_nodes, include_yaml=True, include_comments=True
            )
            steps.append(self._create_step(
                f"v{version_counter}",
                final_content,
                self._get_random_explanation(self.COMMENTS_EXPLANATIONS)
            ))
        
        # Apply abortion post-processing
        steps = self._introduce_repetitions_with_abortion(steps, abortion_rate)
        
        return steps
    
    def _get_root_nodes(self, structure: ArgumentMapStructure) -> List[int]:
        """Get the indices of all root nodes (indent_level = 0)."""
        return [i for i, line in enumerate(structure.lines) 
                if line.content.strip() and line.indent_level == 0]
    
    def _get_immediate_children(self, structure: ArgumentMapStructure, parent_index: int) -> List[int]:
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
    
    def _build_content_with_nodes(self, structure: ArgumentMapStructure, 
                                node_indices: set, include_yaml: bool = False, 
                                include_comments: bool = False) -> str:
        """Build Argdown content including only the specified nodes."""
        lines = []
        
        for i, line in enumerate(structure.lines):
            # Skip empty lines that are not standalone comments
            if not line.content.strip() and not (include_comments and line.has_comment):
                continue
                
            # Include only nodes that are in our revealed set
            if i in node_indices:
                formatted_line = self._format_line(line, include_yaml, include_comments)
                if formatted_line.strip():  # Only add non-empty lines
                    lines.append(formatted_line)
        
        return "\n".join(lines)
    
    def _extract_node_name(self, node_index: int, structure: ArgumentMapStructure) -> str:
        """Extract a displayable name from a node for explanations."""
        line = structure.lines[node_index]
        content = line.content.strip()
        
        # Extract claim/argument name from content
        if content.startswith('[') and ']:' in content:
            # Claim format: [Name]: description
            end_bracket = content.find(']:')
            return content[1:end_bracket]
        elif content.startswith('<') and '>:' in content:
            # Argument format: <Name>: description  
            end_bracket = content.find('>:')
            return content[1:end_bracket]
        else:
            # Fallback to first few words
            words = content.split()[:4]
            return ' '.join(words) + ('...' if len(content.split()) > 4 else '')
