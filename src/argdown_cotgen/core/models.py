"""Data models for argdown-cotgen library."""

from dataclasses import dataclass
from typing import List, Optional, Union
from enum import Enum


class SnippetType(Enum):
    """Type of argdown snippet."""
    ARGUMENT_MAP = "argument_map"
    ARGUMENT = "argument"


class DialecticalType(Enum):
    """Type of dialectical relationship in argument maps of child to parent."""
    SUPPORTS = "<+"
    ATTACKS = "<-"
    UNDERCUTS = "<_"
    CONTRADICTORY = "><"
    IS_SUPPORTED_BY = "+>"
    IS_ATTACKED_BY = "->"
    IS_UNDERCUT_BY = "_>"

@dataclass
class ArgumentLine:
    """Represents a single line in an argdown snippet."""
    content: str
    indent_level: int
    line_number: int
    original_line: str
    has_comment: bool = False
    comment_content: Optional[str] = None


@dataclass
class ArgumentMapLine(ArgumentLine):
    """Line in an argument map (hierarchical claim structure)."""
    support_type: Optional[DialecticalType] = None
    label: Optional[str] = None
    is_claim: bool = False
    
    @property
    def is_statement(self) -> bool:
        """Check if this line contains a statement (claim or argument)."""
        return self.label is not None or self.is_claim


@dataclass
class ArgumentStatementLine(ArgumentLine):
    """Line in an argument (premise-conclusion structure)."""
    statement_number: Optional[int] = None
    is_premise: bool = False
    is_conclusion: bool = False
    is_inference_rule: bool = False
    is_separator: bool = False
    is_preamble: bool = False
    
    @property
    def is_numbered_statement(self) -> bool:
        """Check if this line is a numbered statement."""
        return self.statement_number is not None


class ArgumentMapStructure:
    """Represents the structure of an argument map."""
    
    def __init__(self, lines: List[ArgumentMapLine]):
        self.lines = lines
        self.snippet_type = SnippetType.ARGUMENT_MAP
    
    @property
    def max_depth(self) -> int:
        """Maximum indentation depth in the argument map."""
        if not self.lines:
            return 0
        return max(line.indent_level for line in self.lines)
    
    @property
    def statement_lines(self) -> List[ArgumentMapLine]:
        """Get only the lines that contain statements."""
        return [line for line in self.lines if line.is_statement]
    
    @property
    def non_empty_lines(self) -> List[ArgumentMapLine]:
        """Get only non-empty lines."""
        return [line for line in self.lines if line.content.strip()]
    
    def get_lines_at_depth(self, depth: int) -> List[ArgumentMapLine]:
        """Get all statement lines at a specific indentation depth."""
        return [line for line in self.statement_lines if line.indent_level == depth]
    
    @property
    def main_claim(self) -> Optional[ArgumentMapLine]:
        """Get the main claim (first statement at depth 0)."""
        depth_0_lines = self.get_lines_at_depth(0)
        return depth_0_lines[0] if depth_0_lines else None


class ArgumentStructure:
    """Represents the structure of an argument (premise-conclusion)."""
    
    def __init__(self, lines: List[ArgumentStatementLine]):
        self.lines = lines
        self.snippet_type = SnippetType.ARGUMENT
    
    @property
    def numbered_statements(self) -> List[ArgumentStatementLine]:
        """Get all numbered statements."""
        return [line for line in self.lines if line.is_numbered_statement]
    
    @property
    def non_empty_lines(self) -> List[ArgumentStatementLine]:
        """Get only non-empty lines."""
        return [line for line in self.lines if line.content.strip()]
    
    @property
    def premises(self) -> List[ArgumentStatementLine]:
        """Get all premise statements."""
        return [line for line in self.lines if line.is_premise]
    
    @property
    def conclusions(self) -> List[ArgumentStatementLine]:
        """Get all conclusion statements."""
        return [line for line in self.lines if line.is_conclusion]
    
    @property
    def inference_rules(self) -> List[ArgumentStatementLine]:
        """Get all inference rule lines."""
        return [line for line in self.lines if line.is_inference_rule]
    
    @property
    def title_line(self) -> Optional[ArgumentStatementLine]:
        """Get the title line if present."""
        title_lines = [line for line in self.lines if line.is_preamble]
        return title_lines[0] if title_lines else None
    
    @property
    def final_conclusion(self) -> Optional[ArgumentStatementLine]:
        """Get the final conclusion (highest numbered conclusion)."""
        conclusions = self.conclusions
        if not conclusions:
            return None
        return max(conclusions, key=lambda x: x.statement_number or 0)


# Union type for either structure
ArgdownStructure = Union[ArgumentMapStructure, ArgumentStructure]


@dataclass
class CotStep:
    """Represents a single step in a chain of thought generation."""
    version: str
    description: str
    argdown_content: str
