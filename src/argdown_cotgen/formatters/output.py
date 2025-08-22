"""
Output formatter for Chain-of-Thought reasoning traces.
"""

from ..core.models import CotResult


class CotFormatter:
    """
    Formatter for converting CoT steps into readable output.
    """
    
    def format(self, cot_result: CotResult) -> str:
        """
        Format a list of CoT steps into a readable string.
        
        Args:
            cot_result: The result containing CoT steps, input type, and strategy name
            
        Returns:
            Formatted CoT trace as a string
        """
        output_lines = []
        
        for step in cot_result.steps:
            if step.explanation:
                output_lines.append(step.explanation)
                output_lines.append("")  # Empty line
            
            # Format the Argdown content with version
            if step.content.strip():
                output_lines.append(f"```argdown {{version='{step.version}'}}")
                output_lines.append(step.content)
                output_lines.append("```")
                output_lines.append("")  # Empty line
        
        return "\n".join(output_lines).strip()
