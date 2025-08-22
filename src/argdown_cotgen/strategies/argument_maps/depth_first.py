"""
Depth-first strategy for argument maps.

This strategy reveals all child nodes depth-first:
1. Reveal nodes by following paths to maximum depth
2. Add YAML and comments

Minimal Test Case:
=================
Input:
```
[Main-1]: Central claim 1.
    <+ <Support A>: First supporter.
        <+ <Sub A1>: Support for A.
        <- <Sub A2>: Attack on A.
    <- <Attack B>: Main attacker.
        <+ <Sub B1>: Support for B.
[Main-2]: Central claim 2.
    <+ <Support C>: First supporter.
        <+ <Sub C1>: Support for C.
        <- <Sub C2>: Attack on C.
```

Expected Output Steps:
- v1: "[Main-1]: Central claim 1. [Main-2]: Central claim 2."
- v2: Add all childs of [Main-1]: <Support A>, <Attack B>
- v3: Add all childs of <Support A>: <Sub A1>, <Sub A2>
- v4: Add all childs of <Attack B>: <Sub B1>
- v5: Add all childs of [Main-2]: <Support C>
- v6: Add all childs of <Support C>: <Sub C1>, <Sub C2>
- v7: Add YAML and comments (if any)

Note: Complete entire branches before moving to siblings.
This differs from breadth-first which would add all level 1 nodes before level 2.
"""

from typing import List
from ..base import BaseStrategy, CotStep
from ...core.models import ArgdownStructure


class DepthFirstStrategy(BaseStrategy):
    """
    Depth-first strategy for reconstructing argument maps.
    """
    
    def generate(self, parsed_structure: ArgdownStructure, abortion_rate: float = 0.0) -> List[CotStep]:
        """
        Generate CoT steps using depth-first traversal.
        
        Args:
            parsed_structure: The parsed argument map structure
            
        Returns:
            List of CoT steps following depth-first approach
        """
        # TODO: Implement depth-first strategy
        steps = []
        
        steps.append(self._create_step(
            "v1", 
            "// Depth-first placeholder",
            "I'll explore the argument map depth-first."
        ))
        
        return steps
