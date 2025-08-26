"""
Depth diffusion strategy for argument maps.

This strategy starts with a flat, randomly shuffled, and unstructured list of all 
arguments and propositions. All reasons are incrementally subsumed under their 
correct parent nodes, increasing maximum depth level by level.

Strategy Overview:
=================
The depth diffusion approach reconstructs argument maps by:

1. **Initial Flat State**: All nodes presented as a flat, shuffled list without structure
2. **Incremental Depth Construction**: Progressively organize nodes by depth levels
3. **Placeholder Relations**: Use '??' for nodes not yet properly placed
4. **Final Assembly**: Add YAML data and comments to complete reconstruction

Example Progression:
==================
Original Structure:
```
[A]: Root claim
    <+ [B]: Support for A
        <- [C]: Counter to B
    <+ [D]: Another support
        <+ [E]: Deep support for D
```

Depth Diffusion Steps:
```
v1 (flat, shuffled):
C
B
E  
D
A

v2 (depth 0-1):
A
  <+ B
  ?? C
  ?? E
  ?? D

v3 (depth 0-2):
A
  <+ B
    <- C
  <+ D
    ?? E

v4 (depth 0-3):
A
  <+ B
    <- C
  <+ D
    <+ E
```

Key Features:
============
- **Forward Construction**: Builds complexity incrementally (vs backward error correction)
- **Depth-Based Logic**: Organizes by hierarchical depth levels
- **Predictable Progression**: Systematic revelation of structure levels
- **Placeholder System**: Uses '??' to indicate pending node placement
- **Configurable Shuffling**: Reproducible randomization with optional seed

Implementation Architecture:
===========================
- **DepthDiffusionStrategy**: Main strategy class implementing BaseArgumentMapStrategy
- **DepthAnalyzer**: Analyzes target structure and determines depth relationships
- **ShuffleManager**: Handles initial randomization and flat list creation
Comparison with Other Strategies:
================================
- **vs RandomDiffusion**: Forward building vs backward error correction
- **vs ByRank**: Depth-based vs rank-based organization  
- **vs BreadthFirst**: Depth-limited vs breadth-first traversal
- **vs DepthFirst**: Incremental depth vs complete depth traversal

Technical Details:
=================
- Maintains compatibility with existing ArgumentMapStructure representation
- Integrates with AbortionMixin for abortion functionality
- Supports YAML inline data and comment preservation
- Uses configurable shuffle seeds for reproducible behavior
- Follows established testing patterns with BaseStrategyTestSuite integration

Error Handling:
==============
- Graceful handling of single-depth structures
- Robust behavior with complex branching patterns
- Fallback mechanisms for edge cases
- Validation of depth analysis accuracy

Performance Considerations:
==========================
- Efficient depth analysis algorithms
- Minimal memory overhead for intermediate structures
- Optimized placement tracking
- Scalable to large argument maps
"""

import random
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass

from src.argdown_cotgen.core.models import ArgdownStructure, ArgumentMapStructure, CotStep, INDENT_SIZE
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy, AbortionMixin


@dataclass
class NodeDepthInfo:
    """Node information for depth-based placement."""
    content: str
    label: Optional[str]
    target_depth: int
    target_parent_index: Optional[int]
    target_relation: Optional[str]
    yaml_data: Optional[str]
    comment: Optional[str]
    original_index: int


@dataclass
class DepthLevel:
    """Represents a depth level with nodes to place."""
    level: int
    nodes: List[NodeDepthInfo]
    max_nodes_to_place: int


class DepthAnalyzer:
    """Analyzes structures to determine depth relationships and placement order."""
    
    def __init__(self):
        self.analyzed_structure = None
        self.depth_map: Dict[int, int] = {}
        self.parent_map: Dict[int, Optional[int]] = {}
        self.children_map: Dict[int, List[int]] = {}
        self.max_depth = 0
    
    def analyze_structure(self, structure: ArgumentMapStructure) -> Dict[str, Any]:
        """Analyze target structure to determine depth relationships."""
        self.analyzed_structure = structure
        self.depth_map.clear()
        self.parent_map.clear()
        self.children_map.clear()
        
        # Build maps for all non-empty lines
        for i, line in enumerate(structure.lines):
            if not line.content.strip():
                continue
                
            # Map line index to its depth
            self.depth_map[i] = line.indent_level
            
            # Find parent (previous line with lower indent level)
            parent_index = self._find_parent_index(structure, i)
            self.parent_map[i] = parent_index
            
            # Initialize children list
            if i not in self.children_map:
                self.children_map[i] = []
                
            # Add this node to parent's children list
            if parent_index is not None:
                if parent_index not in self.children_map:
                    self.children_map[parent_index] = []
                self.children_map[parent_index].append(i)
        
        # Calculate maximum depth
        self.max_depth = structure.max_depth
        
        return {
            'depth_map': self.depth_map,
            'parent_map': self.parent_map,
            'children_map': self.children_map,
            'max_depth': self.max_depth
        }
    
    def _find_parent_index(self, structure: ArgumentMapStructure, node_index: int) -> Optional[int]:
        """Find the parent node index by looking backwards for a line with lower indent."""
        current_line = structure.lines[node_index]
        current_indent = current_line.indent_level
        
        # Root nodes have no parent
        if current_indent == 0:
            return None
            
        # Look backwards to find parent
        for i in range(node_index - 1, -1, -1):
            line = structure.lines[i]
            if line.content.strip() and line.indent_level < current_indent:
                return i
                
        return None
    
    def get_nodes_at_depth(self, depth: int) -> List[NodeDepthInfo]:
        """Get all nodes at the specified depth level."""
        if not self.analyzed_structure:
            return []
            
        nodes = []
        for i, line in enumerate(self.analyzed_structure.lines):
            if not line.content.strip():
                continue
                
            if line.indent_level == depth:
                # Create NodeDepthInfo for this node
                parent_index = self.parent_map.get(i)
                
                # Determine target relation from line properties
                relation = None
                if line.support_type:
                    relation = self._get_relation_symbol(line.support_type)
                
                node_info = NodeDepthInfo(
                    content=line.content.strip(),
                    label=line.label,
                    target_depth=depth,
                    target_parent_index=parent_index,
                    target_relation=relation,
                    yaml_data=line.yaml_inline_data,
                    comment=line.comment_content if line.has_comment else None,
                    original_index=i
                )
                nodes.append(node_info)
                
        return nodes
    
    def _get_relation_symbol(self, support_type) -> str:
        """Convert DialecticalType to relation symbol."""
        # Import here to avoid circular imports
        from src.argdown_cotgen.core.models import DialecticalType
        
        if support_type == DialecticalType.SUPPORTS:
            return "<+"
        elif support_type == DialecticalType.ATTACKS:
            return "<-"
        elif support_type == DialecticalType.UNDERCUTS:
            return "<_"
        elif support_type == DialecticalType.CONTRADICTORY:
            return "><"
        elif support_type == DialecticalType.IS_SUPPORTED_BY:
            return "+>"
        elif support_type == DialecticalType.IS_ATTACKED_BY:
            return "->"
        elif support_type == DialecticalType.IS_UNDERCUT_BY:
            return "_>"
        else:
            return "<+"  # Default to support
    
    def get_depth_levels(self) -> List[DepthLevel]:
        """Get organized depth levels for incremental construction."""
        if not self.analyzed_structure:
            return []
            
        levels = []
        for depth in range(self.max_depth + 1):
            nodes = self.get_nodes_at_depth(depth)
            if nodes:  # Only include levels that have nodes
                level = DepthLevel(
                    level=depth,
                    nodes=nodes,
                    max_nodes_to_place=len(nodes)  # For now, place all nodes at each level
                )
                levels.append(level)
                
        return levels
    
    def calculate_node_depth(self, structure: ArgumentMapStructure, node_index: int) -> int:
        """Calculate the depth of a specific node in the argument map."""
        if node_index >= len(structure.lines):
            return 0
            
        line = structure.lines[node_index]
        return line.indent_level


class ShuffleManager:
    """Manages initial randomization and flat list creation for depth diffusion."""
    
    def __init__(self, shuffle_seed: Optional[int] = None):
        self.shuffle_seed = shuffle_seed
        if shuffle_seed is not None:
            random.seed(shuffle_seed)
    
    def create_flat_shuffled_list(self, structure: ArgumentMapStructure) -> List[str]:
        """Create a flat, randomly shuffled list of all node contents."""
        # Extract content from all non-empty lines (content is already clean)
        contents = []
        for line in structure.lines:
            if line.content.strip():
                contents.append(line.content.strip())
        
        # Reset seed for reproducibility before shuffling
        if self.shuffle_seed is not None:
            random.seed(self.shuffle_seed)
        
        # Shuffle the list
        random.shuffle(contents)
        return contents
    
    def format_flat_content(self, content_list: List[str]) -> str:
        """Format the flat content list as a proper Argdown string."""
        if not content_list:
            return ""
        
        # Simply join with newlines - no indentation or relations
        return "\n".join(content_list)


class DepthDiffusionStrategy(AbortionMixin, BaseArgumentMapStrategy):
    """Depth diffusion strategy for reconstructing argument maps using incremental depth-based construction."""
    
    # Standard explanation templates for different phases
    INITIAL_EXPLANATIONS = [
        "Let me start by laying out all the arguments and claims in a flat list.",
        "I'll begin with an unstructured list of all the components.",
        "First, let me list all the arguments and propositions without structure.",
        "I'll start by gathering all the elements in a simple list.",
    ]
    
    DEPTH_EXPLANATIONS = [
        "Now I'll organize the arguments by adding the next level of structure.",
        "Let me add the next layer of hierarchical organization.",
        "I'll now organize arguments at the next depth level.",
        "Next, I'll organize arguments into the next level of the hierarchy.",
        "Let me add another level of structural organization.",
    ]
    
    YAML_EXPLANATIONS = [
        "Now I'll add the YAML inline data.",
        "Let me include the YAML metadata.",
        "I'll add the structured metadata annotations.",
        "Next, I'll include the inline YAML information.",
    ]
    
    COMMENTS_EXPLANATIONS = [
        "Finally, I'll add the clarifying comments.",
        "Last, I'll include the explanatory comments.",
        "To finish, I'll add the commentary and additional notes.",
        "Finally, let me add the remaining comments.",
    ]
    
    def __init__(self, shuffle_seed: Optional[int] = None):
        """Initialize the DepthDiffusionStrategy."""
        super().__init__()
        self.shuffle_seed = shuffle_seed
        self.depth_analyzer = DepthAnalyzer()
        self.shuffle_manager = ShuffleManager(shuffle_seed)
    
    def generate(self, parsed_structure: ArgdownStructure, abortion_rate: float = 0.0) -> List[CotStep]:
        """Generate CoT steps using depth diffusion strategy."""
        if not isinstance(parsed_structure, ArgumentMapStructure):
            raise ValueError("DepthDiffusionStrategy requires an ArgumentMapStructure")
        
        steps: List[CotStep] = []
        
        # Step 1: Analyze the target structure to determine depth relationships
        self.depth_analyzer.analyze_structure(parsed_structure)
        max_depth = parsed_structure.max_depth
        
        # Step 2: Create flat shuffled initial state
        flat_step = self._create_flat_initial_step(parsed_structure)
        steps.append(flat_step)
        
        # Step 3: Generate incremental depth construction steps
        version_counter = 2
        for current_max_depth in range(max_depth + 1):
            depth_step = self._create_depth_increment_step(
                parsed_structure, 
                current_max_depth, 
                version_counter
            )
            steps.append(depth_step)
            version_counter += 1
        
        # Step 4: Add YAML inline data if present
        if self._has_yaml_data(parsed_structure):
            content_with_yaml = self._build_content_with_nodes(
                parsed_structure, 
                include_yaml=True, 
                include_comments=False
            )
            steps.append(self._create_step(
                f"v{version_counter}",
                content_with_yaml,
                self._get_random_explanation(self.YAML_EXPLANATIONS)
            ))
            version_counter += 1
        
        # Step 5: Add comments if present
        if self._has_comments(parsed_structure):
            final_content = self._build_content_with_nodes(
                parsed_structure, 
                include_yaml=True, 
                include_comments=True
            )
            steps.append(self._create_step(
                f"v{version_counter}",
                final_content,
                self._get_random_explanation(self.COMMENTS_EXPLANATIONS)
            ))
        
        # Step 6: Apply abortion post-processing
        steps = self._introduce_repetitions_with_abortion(steps, abortion_rate)
        
        return steps
    
    def _create_flat_initial_step(self, structure: ArgumentMapStructure) -> CotStep:
        """Create the initial step with flat, shuffled content."""
        # Use shuffle manager to create flat list
        flat_content_list = self.shuffle_manager.create_flat_shuffled_list(structure)
        content = self.shuffle_manager.format_flat_content(flat_content_list)
        
        # Get random explanation for initial step
        explanation = self._get_random_explanation(self.INITIAL_EXPLANATIONS)
        
        return self._create_step("v1", content, explanation)
    
    def _create_depth_increment_step(
        self, 
        structure: ArgumentMapStructure, 
        max_depth: int, 
        step_number: int
    ) -> CotStep:
        """Create a step that adds nodes up to the specified maximum depth."""
        # Build the partial structure with nodes up to max_depth
        partial_nodes = self._get_nodes_up_to_depth(structure, max_depth)
        content = self._build_content_with_partial_placement(structure, partial_nodes, max_depth)
        
        # Get appropriate explanation
        explanation = self._get_random_explanation(self.DEPTH_EXPLANATIONS)
        
        return self._create_step(f"v{step_number}", content, explanation)
    
    def _get_nodes_up_to_depth(self, structure: ArgumentMapStructure, max_depth: int) -> Set[int]:
        """Get all node indices that should be included up to the specified depth."""
        nodes = set()
        
        for i, line in enumerate(structure.lines):
            # Include all non-empty statement lines up to max_depth
            if line.content.strip() and line.indent_level <= max_depth:
                nodes.add(i)
        
        return nodes
    
    def _build_content_with_partial_placement(
        self, 
        structure: ArgumentMapStructure, 
        included_nodes: Set[int], 
        max_depth: int
    ) -> str:
        """Build content with correct placement up to max_depth and placeholders for deeper nodes."""
        lines = []
        siblings_at_max_depth = []  # Track siblings to shuffle
        current_parent_signature = None
        
        for i, line in enumerate(structure.lines):
            # Skip empty lines
            if not line.content.strip():
                continue
            
            # Include nodes up to max_depth with correct relations
            if i in included_nodes and line.indent_level <= max_depth:
                formatted_line = self._format_line(line, include_yaml=False, include_comments=False)
                if formatted_line.strip():
                    # Check if this line is at max_depth and should be shuffled
                    if line.indent_level == max_depth:
                        parent_sig = self._get_parent_signature(lines)
                        if parent_sig != current_parent_signature:
                            # New parent - shuffle and add previous siblings
                            if siblings_at_max_depth:
                                random.shuffle(siblings_at_max_depth)
                                lines.extend(siblings_at_max_depth)
                                siblings_at_max_depth = []
                            current_parent_signature = parent_sig
                        siblings_at_max_depth.append(formatted_line)
                    else:
                        # Not at max_depth - add directly and flush any pending siblings
                        if siblings_at_max_depth:
                            random.shuffle(siblings_at_max_depth)
                            lines.extend(siblings_at_max_depth)
                            siblings_at_max_depth = []
                        lines.append(formatted_line)
            
            # Add placeholder entries for nodes that exist at deeper levels
            elif line.content.strip() and line.indent_level > max_depth:
                # Check if this node has a parent that's already placed
                parent_placed = self._has_placed_parent(structure, i, included_nodes, max_depth)
                if parent_placed:
                    # Create placeholder entry at the deepest placed level
                    placeholder_line = self._create_placeholder_line(structure, i, max_depth)
                    if placeholder_line and placeholder_line not in lines:
                        # Placeholders are always at max_depth + 1, but treat as max_depth for shuffling
                        parent_sig = self._get_parent_signature(lines)
                        if parent_sig != current_parent_signature:
                            if siblings_at_max_depth:
                                random.shuffle(siblings_at_max_depth)
                                lines.extend(siblings_at_max_depth)
                                siblings_at_max_depth = []
                            current_parent_signature = parent_sig
                        siblings_at_max_depth.append(placeholder_line)
        
        # Flush any remaining siblings
        if siblings_at_max_depth:
            random.shuffle(siblings_at_max_depth)
            lines.extend(siblings_at_max_depth)

        return "\n".join(lines)
    
    def _has_placed_parent(
        self, 
        structure: ArgumentMapStructure, 
        node_index: int, 
        placed_nodes: Set[int], 
        max_depth: int
    ) -> bool:
        """Check if a node has a parent that's already been placed."""
        current_line = structure.lines[node_index]
        current_indent = current_line.indent_level
        
        # Look backwards to find the parent
        for i in range(node_index - 1, -1, -1):
            line = structure.lines[i]
            
            # Found a potential parent (less indented and non-empty)
            if line.content.strip() and line.indent_level < current_indent:
                # Check if this parent is placed and within max_depth
                if i in placed_nodes and line.indent_level <= max_depth:
                    return True
                # If we found a parent but it's not placed, stop looking
                break
        
        return False
    
    def _create_placeholder_line(
        self, 
        structure: ArgumentMapStructure, 
        node_index: int, 
        max_depth: int
    ) -> Optional[str]:
        """Create a placeholder line for a node that's not yet properly placed."""
        current_line = structure.lines[node_index]
        
        # Find the appropriate indentation level (at max_depth + 1)
        placeholder_indent = min(max_depth + 1, current_line.indent_level)
        indent = " " * (placeholder_indent * INDENT_SIZE)
        
        # Extract just the content without labels or relations
        content = current_line.content.strip()
        
        # Remove label brackets if present
        if content.startswith('[') and ']:' in content:
            # For claims like "[A]: Content" -> "A"
            end_bracket = content.find(']:')
            content = content[1:end_bracket]
        elif content.startswith('<') and '>:' in content:
            # For arguments like "<Arg>: Content" -> "Arg"  
            end_bracket = content.find('>:')
            content = content[1:end_bracket]
        else:
            # Take first few words for other content
            words = content.split()[:3]
            content = ' '.join(words)
        
        # Create placeholder with ?? relation
        return f"{indent}?? {content}"
    
    def _get_parent_signature(self, lines: List[str]) -> str:
        """Get a signature representing the current parent context for sibling grouping."""
        if not lines:
            return "root"
        
        # Use the last line's indentation and content as parent signature
        last_line = lines[-1]
        indent_level = len(last_line) - len(last_line.lstrip())
        
        # For grouping siblings, we care about the parent context
        # If last line could be our parent, use it; otherwise use line count
        return f"parent_{indent_level}_{len(lines)}"
    
    def _build_content_with_nodes(self, structure: ArgumentMapStructure, 
                                node_indices: Optional[Set[int]] = None, include_yaml: bool = False, 
                                include_comments: bool = False) -> str:
        """Build Argdown content including only the specified nodes (or all nodes if None)."""
        # If no specific nodes provided, include all nodes
        if node_indices is None:
            node_indices = set(range(len(structure.lines)))
            
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
