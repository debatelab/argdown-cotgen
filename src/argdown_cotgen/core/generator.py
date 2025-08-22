"""
Main CotGenerator class that orchestrates the creation of Chain-of-Thought 
reasoning traces from Argdown snippets.
"""

from .parser import ArgdownParser
from .models import SnippetType, CotResult
from ..formatters.output import CotFormatter
from ..strategies.argument_maps.by_rank import ByRankStrategy


class CotGenerator:
    """
    Main generator class that creates Chain-of-Thought reasoning traces
    from Argdown snippets using various strategies.
    """
    
    def __init__(self, pipe_type: str = "by_rank"):
        """
        Initialize the CoT generator.
        
        Args:
            pipe_type: Strategy to use for generating CoT traces.
                      Options: "by_rank", "by_feature", "breadth_first", 
                      "depth_first", "by_objection", "random_diffusion", 
                      "depth_diffusion"
        """
        self.pipe_type = pipe_type
        self.parser = ArgdownParser()
    
    def generate(self, argdown_snippet: str, abortion_rate: float = 0.0) -> CotResult:
        """
        Generate a Chain-of-Thought reasoning trace from an Argdown snippet.
        
        Args:
            argdown_snippet: The input Argdown code snippet
            abortion_rate: Probability of introducing abortion (0.0 to 1.0)
            
        Returns:
            CotResult with steps, input type, and strategy name
        """
        # Parse the snippet
        parsed_structure = self.parser.parse(argdown_snippet)
        
        # Determine strategy based on snippet type and pipe_type
        strategy = self._get_strategy(parsed_structure.snippet_type)
        
        # Generate the CoT trace
        trace_steps = strategy.generate(parsed_structure, abortion_rate=abortion_rate)
        
        return CotResult(
            steps=trace_steps,
            input_type=parsed_structure.snippet_type.name,
            strategy_name=self.pipe_type
        )
    
    def __call__(self, argdown_snippet: str, abortion_rate: float = 0.0) -> str:
        """
        Generate a Chain-of-Thought reasoning trace from an Argdown snippet.
        
        Args:
            argdown_snippet: The input Argdown code snippet
            abortion_rate: Probability of introducing abortion (0.0 to 1.0)
            
        Returns:
            A formatted Chain-of-Thought reasoning trace as a string
        """
        result = self.generate(argdown_snippet, abortion_rate=abortion_rate)
        
        formatter = CotFormatter()
        formatted_output = formatter.format(result)

        return formatted_output

    
    def _get_strategy(self, snippet_type: SnippetType):
        """Get the appropriate strategy based on snippet type and pipe_type."""
        if snippet_type == SnippetType.ARGUMENT_MAP:
            if self.pipe_type == "by_rank":
                return ByRankStrategy()
            else:
                raise NotImplementedError(f"Strategy '{self.pipe_type}' not yet implemented for argument maps")
        elif snippet_type == SnippetType.ARGUMENT:
            raise NotImplementedError("Argument strategies not yet implemented")
        else:
            raise ValueError(f"Unknown snippet type: {snippet_type}")
