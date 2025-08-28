"""
By-objection strategy for argument maps.

This strategy builds maps by argumentative structure:
1. Roots: Show all root nodes
2. Main supporting argumentation: Show support chains
3. Objections: Add objection-like arguments against revealed nodes and their supports
4. Iterate step 3 (objections become rebuttals, rebuttals become counter-rebuttals, etc.)
5. Continue until complete
6. Add YAML and comments

The strategy treats different dialectical relations by their argumentative function:
- Support-like relations: SUPPORTS (<+)
- Objection-like relations: ATTACKS (<-), UNDERCUTS (<_), CONTRADICTORY (><)

All objection-like relations are treated uniformly as "opposing arguments against 
currently revealed nodes" and grouped together when they attack the same target.

Minimal Test Case:
=================
Input:
```
[Vegetarianism]: People should be vegetarian.
    <+ <Animal Welfare>: Animals suffer in factory farms.
        <+ <Scientific Evidence>: Studies show animal pain.
    <- <Nutrition Concern>: Vegetarian diets lack nutrients.
        <- <Modern Alternatives>: Supplements provide nutrients.
            <+ <Bioavailability>: Modern supplements work well.
        <- <Health Studies>: Vegetarians are healthier.
```

Expected Output Steps:
- v1: Main claim: "[Vegetarianism]: People should be vegetarian."
- v2: Main case: <Animal Welfare> + <Scientific Evidence> (complete support chain)
- v3: Objections: <Nutrition Concern> (attacks main claim)
- v4: Rebuttals: <Modern Alternatives> + <Bioavailability> + <Health Studies> (all attacks against Nutrition Concern)
- v5: Add YAML and comments (if any)

Note: Groups arguments by their argumentative role rather than structural position.
"""

from typing import List
from ..base import BaseArgumentMapStrategy, AbortionMixin
from ...core.models import ArgdownStructure, ArgumentMapStructure, CotStep, DialecticalType


class ByObjectionStrategy(AbortionMixin, BaseArgumentMapStrategy):
    """
    By-objection strategy for reconstructing argument maps.
    
    This strategy organizes revelation by argumentative role:
    1. Main claims (roots)
    2. Supporting evidence chains  
    3. Attacking arguments against revealed nodes (objections/rebuttals/counter-rebuttals)
    4. Continue step 3 until complete
    
    The strategy treats objections, rebuttals, and counter-rebuttals uniformly as 
    "attacking arguments against currently revealed nodes" and groups all attacks 
    against the same target together.
    """
    
    @staticmethod
    def _is_primary_support(dialectical_type: DialecticalType) -> bool:
        """Primary support relations (child supports parent)."""
        return dialectical_type == DialecticalType.SUPPORTS

    @staticmethod
    def _is_primary_objection(dialectical_type: DialecticalType) -> bool:
        """Primary objection relations (child objects to parent)."""
        return dialectical_type in {
            DialecticalType.ATTACKS,
            DialecticalType.UNDERCUTS, 
            DialecticalType.CONTRADICTORY
        }

    @staticmethod
    def _is_inverse_relation(dialectical_type: DialecticalType) -> bool:
        """Inverse relations (parent is supported/attacked/undercut by child)."""
        return dialectical_type in {
            DialecticalType.IS_SUPPORTED_BY,    # +>
            DialecticalType.IS_ATTACKED_BY,     # ->
            DialecticalType.IS_UNDERCUT_BY      # _>
        }
    
    # Explanation templates for different argumentative roles
    INITIAL_ROOT_EXPLANATIONS = [
        "Let me begin with adding a main claim.",
        "I'll first try to identify a central proposition.",
        "First, let me establish a core claim.",
        "I'll start with a root node.",
        "I'll start with a primary proposition.",
        "Let me begin by identifying a key claim."
    ]
    
    ROOT_EXPLANATIONS = [
        "Let me add another main claim.",
        "I'll try to identify a further central proposition.",
        "Let me establish another core claim.",
        "I'll continue with another root node.",
        "I'll continue with an additional primary proposition.",
        "Let me further identify another key claim."
    ]
    
    MAIN_CASE_EXPLANATIONS = [
        "Now I'll build the main supporting case.",
        "Let me add the primary argumentation.",
        "I'll establish the main argumentative support.",
        "How is the main claim supported? Let me sketch the central line of argumentation.",
        "Now I'll outline the core supporting arguments.",
        "Let me add the main arguments supporting the root claim."
        "What are the main arguments in favour of the key claim? Let me show them.",
    ]
    
    OBJECTION_EXPLANATIONS = [
        "Now let me add objections against the arguments and claims sketched so far.",
        "I shall next add objections and their respective supporting arguments.",
        "Are there any objections challenging the key claims directly or indirectly?",
        "Now I'll present further critical arguments opposing the key claims.",
        "Let me consider and add objections."
    ]
    
    REBUTTAL_EXPLANATIONS = [
        "Now I'll address rebuttals to these objections.",
        "Let me see whether I can add any counterarguments to these objections.",
        "I should consider arguments that defend the key claims against these objections.",
        "Now I'll present counter-responses to the previously added objections.",
        "Is there an argumentative responses to these challenges? Let me try to add it."
    ]
    
    IMPLICATION_EXPLANATIONS = [
        "Let me now consider what follows from the arguments presented in the Argdown map.",
        "I should add what these arguments imply or entail.",
        "Let me now reveal the implications of the arguments sketched so far.",
        "What follows from the arguments? Let me show the implications.",
        "Let me now add the logical consequences of the argumentation outline so far."
    ]
    
    REMAINING_EXPLANATIONS = [
        "Let me complete the remaining argumentation.",
        "I should add any remaining arguments.",
        "Let me fill in the remaining parts of the argument map.",
        "Finally, let me add the remaining argumentative content.",
        "Let me complete the argument map with the remaining material."
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
        Generate CoT steps using by-objection strategy.
        
        Args:
            parsed_structure: The parsed argument map structure
            abortion_rate: Probability of introducing abortion (0.0 to 1.0)
            
        Returns:
            List of CoT steps following by-objection approach
        """
        if not isinstance(parsed_structure, ArgumentMapStructure):
            raise ValueError("ByObjectionStrategy requires an ArgumentMapStructure")
        
        steps = []
        
        # Get all root nodes
        root_nodes = self._get_root_nodes(parsed_structure)
        revealed_nodes = set()
        version_counter = 1
        total_nodes = len([line for line in parsed_structure.lines if line.content.strip()])
        
        # Process each root claim sequentially
        for root_counter, root_node in enumerate(root_nodes):
            # Step: Reveal this root claim (if not already revealed)
            if root_node not in revealed_nodes:
                revealed_nodes.add(root_node)
                root_content = self._build_content_with_nodes(parsed_structure, revealed_nodes)
                steps.append(self._create_step(
                    f"v{version_counter}",
                    root_content,
                    self._get_random_explanation(self.ROOT_EXPLANATIONS if root_counter > 0 else self.INITIAL_ROOT_EXPLANATIONS)
                ))
                version_counter += 1
            
            # Build complete argumentation for this root claim
            # Step: Add all primary supporting evidence chains for this root
            support_chains = self._get_primary_support_group(parsed_structure, revealed_nodes)
            if support_chains:
                revealed_nodes.update(support_chains)
                content = self._build_content_with_nodes(parsed_structure, revealed_nodes)
                steps.append(self._create_step(
                    f"v{version_counter}",
                    content,
                    self._get_random_explanation(self.MAIN_CASE_EXPLANATIONS)
                ))
                version_counter += 1
            
            # Phase 1: Build core argument tree with primary objection relations for this root
            phase1_complete = False
            revealing_rebuttals = False  # We start with objections, not rebuttals, and switch between them 
            while len(revealed_nodes) < total_nodes and not phase1_complete:
                progress_made = False
                
                # Try to add primary objections/rebuttals with their supporting evidence
                objection_group = self._get_next_primary_objection_group(parsed_structure, revealed_nodes)
                if objection_group:
                    revealed_nodes.update(objection_group)
                    content = self._build_content_with_nodes(parsed_structure, revealed_nodes)
                    steps.append(self._create_step(
                        f"v{version_counter}",
                        content,
                        self._get_random_explanation(self.REBUTTAL_EXPLANATIONS if revealing_rebuttals else self.OBJECTION_EXPLANATIONS)
                    ))
                    version_counter += 1
                    progress_made = True
                    
                    # Switch rebuttals / objections after adding a group
                    revealing_rebuttals = not revealing_rebuttals
                    continue

                # If no primary relations found, phase 1 is complete for this root
                if not progress_made:
                    phase1_complete = True
            
            # Phase 2: Add implications (inverse relations) for this root
            implication_progress = True
            while len(revealed_nodes) < total_nodes and implication_progress:
                implication_group = self._get_next_implication_group(parsed_structure, revealed_nodes)
                if implication_group:
                    revealed_nodes.update(implication_group)
                    content = self._build_content_with_nodes(parsed_structure, revealed_nodes)
                    steps.append(self._create_step(
                        f"v{version_counter}",
                        content,
                        self._get_random_explanation(self.IMPLICATION_EXPLANATIONS)
                    ))
                    version_counter += 1
                else:
                    implication_progress = False
        
        # Handle any remaining unrevealed nodes (cleanup)
        while len(revealed_nodes) < total_nodes:
            unrevealed = self._get_unrevealed_nodes(parsed_structure, revealed_nodes)
            if unrevealed:
                revealed_nodes.update(unrevealed[:1])  # Add one node at a time
                content = self._build_content_with_nodes(parsed_structure, revealed_nodes)
                steps.append(self._create_step(
                    f"v{version_counter}",
                    content,
                    self._get_random_explanation(self.REMAINING_EXPLANATIONS)
                ))
                version_counter += 1
            else:
                break  # All nodes revealed
        
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
    
    def _get_primary_support_group(self, structure: ArgumentMapStructure, revealed_nodes: set) -> List[int]:
        """
        Get all primary support chains for already revealed nodes.
        
        Collects ALL primary support arguments and their descendants that support 
        nodes already in revealed_nodes. This groups all supporting evidence together
        by argumentative role rather than revealing chains one by one.
        """
        support_chains = []
        
        for revealed_node in revealed_nodes:
            # Find direct children that are primary supports
            children = self._get_immediate_children(structure, revealed_node)
            for child in children:
                if child not in revealed_nodes:
                    line = structure.lines[child]
                    # Check if it's a primary support-like argument
                    if line.support_type and self._is_primary_support(line.support_type):
                        # Add this support and its primary support descendant chain
                        support_chains.append(child)
                        primary_descendants = self._get_primary_support_descendants(structure, child, revealed_nodes)
                        support_chains.extend(primary_descendants)
        
        return support_chains
    
    def _get_next_primary_objection_group(self, structure: ArgumentMapStructure, revealed_nodes: set) -> List[int]:
        """
        Get the next primary objection group (all primary objection-like relations against the same revealed nodes) with supporting evidence.
        
        A primary objection group consists of all primary objection-like arguments (attacks, undercuts, contradictory) 
        against the same revealed nodes, along with their supporting descendants.
        """
        objections: list[int] = []

        # Look at each revealed node that has unrevealed primary objection-like children
        for revealed_node in revealed_nodes:
            children = self._get_immediate_children(structure, revealed_node)
            
            # Collect ALL primary objection-like children of this revealed node
            for child in children:
                if child not in revealed_nodes:
                    line = structure.lines[child]
                    if line.support_type and self._is_primary_objection(line.support_type):
                        # Add this objection and its supporting evidence
                        objections.append(child)
                        # Add supporting evidence for this objection
                        support_chain = self._get_primary_support_descendants(structure, child, revealed_nodes)
                        objections.extend(support_chain)
            
        # Delete duplicates
        objections = list(set(objections))
        
        return objections
    
    def _get_unrevealed_nodes(self, structure: ArgumentMapStructure, revealed_nodes: set) -> List[int]:
        """Get all nodes that haven't been revealed yet."""
        unrevealed = []
        for i, line in enumerate(structure.lines):
            if line.content.strip() and i not in revealed_nodes:
                unrevealed.append(i)
        return unrevealed
    
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
    
    def _get_complete_descendant_chain(self, structure: ArgumentMapStructure, 
                                     root_index: int, revealed_nodes: set) -> List[int]:
        """Get all unrevealed descendants of a node."""
        descendants = []
        if root_index not in revealed_nodes:
            descendants.append(root_index)
        
        children = self._get_immediate_children(structure, root_index)
        for child in children:
            if child not in revealed_nodes:
                descendants.extend(self._get_complete_descendant_chain(structure, child, revealed_nodes))
        
        return descendants

    def _get_next_implication_group(self, structure: ArgumentMapStructure, revealed_nodes: set) -> List[int]:
        """
        Get the next implication group (all inverse relation nodes that can be revealed based on revealed nodes).
        
        An implication group consists of all nodes with inverse relations (IS_SUPPORTED_BY, IS_ATTACKED_BY, IS_UNDERCUT_BY)
        where the source node is already revealed.
        """
        implication_group = []
        
        # Look for all revealed nodes to see what inverse relations they imply
        for revealed_node in revealed_nodes:
            children = self._get_immediate_children(structure, revealed_node)
            
            # Collect inverse relation children of this revealed node
            for child in children:
                if child not in revealed_nodes:
                    line = structure.lines[child]
                    if line.support_type and self._is_inverse_relation(line.support_type):
                        implication_group.append(child)
        
        return implication_group
        
    def _get_primary_support_descendants(self, structure: ArgumentMapStructure, start_node: int, revealed_nodes: set) -> List[int]:
        """
        Get all supporting descendants of a node using only primary support relations.
        
        This includes all descendants connected via primary SUPPORTS relations.
        """
        descendants = []
        queue = [start_node]
        visited = set()
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            children = self._get_immediate_children(structure, current)
            for child in children:
                if child not in revealed_nodes and child not in visited:
                    line = structure.lines[child]
                    if line.support_type and self._is_primary_support(line.support_type):
                        descendants.append(child)
                        queue.append(child)
        
        return descendants
