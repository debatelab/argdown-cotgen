"""Parser for argdown snippets using indentation-based analysis."""

import re
from typing import List, Optional
from .models import (
    ArgumentMapLine, 
    ArgumentStatementLine, 
    ArgumentMapStructure, 
    ArgumentStructure,
    ArgdownStructure,
    SnippetType,
    DialecticalType,
    INDENT_SIZE
)


class ArgdownParser:
    """Parser that uses indentation and line patterns to parse argdown snippets."""
    
    # Patterns for argument maps
    DIALECTICAL_PATTERN = re.compile(r'^(\s*)(<[+\-_]|><|\+>|\->|_>|[+\-])\s*')
    DIALECTICAL_WITH_ARG_PATTERN = re.compile(r'^(\s*)(<[+\-_]|><|\+>|\->|_>|[+\-])\s*<([^>]+)>:\s*(.+)$')
    CLAIM_PATTERN = re.compile(r'^(\s*)\[([^\]]+)\]:\s*(.+)$')
    ARGUMENT_PATTERN = re.compile(r'^(\s*)<([^>]+)>:\s*(.+)$')
    
    # Comment patterns
    INLINE_COMMENT_PATTERN = re.compile(r'^(.+?)//\s*(.*)$')
    STANDALONE_COMMENT_PATTERN = re.compile(r'^(\s*)//\s*(.*)$')
    MULTILINE_COMMENT_PATTERN = re.compile(r'/\*.*?\*/', re.DOTALL)
    # YAML inline data pattern (matches {...} at end of line, before optional comment)
    # Uses a more sophisticated pattern to handle nested braces
    YAML_INLINE_PATTERN = re.compile(r'\{(?:[^{}]|{[^}]*})*\}(?=\s*(//|$))')
    def _extract_yaml_and_comment(self, line: str) -> tuple[str, Optional[str], bool, Optional[str]]:
        """Extract YAML inline data and comment from line.
        Returns (cleaned_line, yaml_inline_data, has_comment, comment_content)
        """
        yaml_inline_data = None
        # Extract YAML inline data first
        yaml_match = self.YAML_INLINE_PATTERN.search(line)
        if yaml_match:
            yaml_inline_data = yaml_match.group(0)
            # Remove YAML from line
            line = line[:yaml_match.start()] + line[yaml_match.end():]
        # Now extract comment
        inline_match = self.INLINE_COMMENT_PATTERN.match(line)
        if inline_match:
            cleaned_line = inline_match.group(1).rstrip()
            comment_content = inline_match.group(2).strip()
            return cleaned_line, yaml_inline_data, True, comment_content
        # Check for standalone comments
        standalone_match = self.STANDALONE_COMMENT_PATTERN.match(line)
        if standalone_match:
            comment_content = standalone_match.group(2).strip()
            return "", yaml_inline_data, True, comment_content
        # No comment found
        return line, yaml_inline_data, False, None
    
    # Patterns for arguments  
    NUMBERED_STATEMENT_PATTERN = re.compile(r'^(\s*)\((\d+)\)\s*(.+)$')
    INFERENCE_RULE_PATTERN = re.compile(r'^(\s*)--\s*(.+)\s*--\s*$')
    SEPARATOR_PATTERN = re.compile(r'^(\s*)-----?\s*$')
    PREAMBLE_PATTERN = re.compile(r'^(\s*)<([^>]+)>:\s*(.+)$')
    
    def __init__(self):
        pass
    
    def parse(self, argdown_snippet: str) -> ArgdownStructure:
        """Parse an argdown snippet and return the appropriate structure."""
        lines = argdown_snippet.strip().split('\n')
        
        # First pass: determine snippet type
        snippet_type = self._detect_snippet_type(lines)
        
        if snippet_type == SnippetType.ARGUMENT_MAP:
            return self._parse_argument_map(lines)
        else:
            return self._parse_argument(lines)
    
    def _detect_snippet_type(self, lines: List[str]) -> SnippetType:
        """Detect whether this is an argument map or an argument."""
        has_dialectical_relations = False
        has_numbered_statements = False
        has_separators = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for dialectical relations
            if self.DIALECTICAL_PATTERN.match(line):
                has_dialectical_relations = True
            
            # Check for numbered statements
            if self.NUMBERED_STATEMENT_PATTERN.match(line):
                has_numbered_statements = True
            
            # Check for separators
            if self.SEPARATOR_PATTERN.match(line):
                has_separators = True
        
        # If we have numbered statements or separators, it's likely an argument
        if has_numbered_statements or has_separators:
            return SnippetType.ARGUMENT
        
        # If we have dialectical relations, it's likely an argument map
        if has_dialectical_relations:
            return SnippetType.ARGUMENT_MAP
        
        # Default to argument map if unclear
        return SnippetType.ARGUMENT_MAP
    
    def _parse_argument_map(self, lines: List[str]) -> ArgumentMapStructure:
        """Parse an argument map structure."""
        parsed_lines = []
        for i, line in enumerate(lines):
            # Extract YAML and comments first
            cleaned_line, yaml_inline_data, has_comment, comment_content = self._extract_yaml_and_comment(line)
            indent_level = self._calculate_indent_level(cleaned_line)
            content = cleaned_line.strip()
            # Handle empty lines (including standalone comments)
            if not content:
                parsed_line = ArgumentMapLine(
                    content="",
                    indent_level=0,
                    line_number=i + 1,
                    original_line=line,
                    support_type=None,
                    label=None,
                    is_claim=False,
                    has_comment=has_comment,
                    comment_content=comment_content,
                    yaml_inline_data=yaml_inline_data
                )
                parsed_lines.append(parsed_line)
                continue
            # Check for dialectical relations with arguments: +> <Arg>: content
            dialectical_arg_match = self.DIALECTICAL_WITH_ARG_PATTERN.match(cleaned_line)
            support_type = None
            if dialectical_arg_match:
                support_symbol = dialectical_arg_match.group(2)
                support_type = self._parse_dialectical_type(support_symbol)
                label = dialectical_arg_match.group(3)
                is_claim = False
                content = f"<{label}>: {dialectical_arg_match.group(4)}"
                indent_level = self._calculate_indent_level(dialectical_arg_match.group(1))
            else:
                # Check for dialectical relations: +> content
                dialectical_match = self.DIALECTICAL_PATTERN.match(cleaned_line)
                if dialectical_match:
                    support_symbol = dialectical_match.group(2)
                    support_type = self._parse_dialectical_type(support_symbol)
                    content = cleaned_line[dialectical_match.end():].strip()
                # Check for claims [Claim]: content
                claim_match = self.CLAIM_PATTERN.match(cleaned_line)
                if claim_match:
                    label = None
                    is_claim = True
                    content = f"[{claim_match.group(2)}]: {claim_match.group(3)}"
                    indent_level = self._calculate_indent_level(claim_match.group(1))
                else:
                    # Check for arguments <Argument>: content  
                    arg_match = self.ARGUMENT_PATTERN.match(cleaned_line)
                    if arg_match:
                        label = arg_match.group(2)
                        is_claim = False
                        content = f"<{label}>: {arg_match.group(3)}"
                        if not support_type:  # Only update indent if no dialectical relation
                            indent_level = self._calculate_indent_level(arg_match.group(1))
                    else:
                        label = None
                        is_claim = False
            parsed_line = ArgumentMapLine(
                content=content,
                indent_level=indent_level,
                line_number=i + 1,
                original_line=line,
                support_type=support_type,
                label=label,
                is_claim=is_claim,
                has_comment=has_comment,
                comment_content=comment_content,
                yaml_inline_data=yaml_inline_data
            )
            parsed_lines.append(parsed_line)
        return ArgumentMapStructure(parsed_lines)
    
    def _parse_argument(self, lines: List[str]) -> ArgumentStructure:
        """Parse an argument structure."""
        parsed_lines = []
        for i, line in enumerate(lines):
            # Extract YAML and comments first
            cleaned_line, yaml_inline_data, has_comment, comment_content = self._extract_yaml_and_comment(line)
            indent_level = self._calculate_indent_level(cleaned_line)
            content = cleaned_line.strip()
            # Handle empty lines (including standalone comments)
            if not content:
                parsed_line = ArgumentStatementLine(
                    content="",
                    indent_level=0,
                    line_number=i + 1,
                    original_line=line,
                    statement_number=None,
                    is_premise=False,
                    is_conclusion=False,
                    is_inference_rule=False,
                    is_separator=False,
                    is_preamble=False,
                    has_comment=has_comment,
                    comment_content=comment_content,
                    yaml_inline_data=yaml_inline_data
                )
                parsed_lines.append(parsed_line)
                continue
            # Check for numbered statements
            numbered_match = self.NUMBERED_STATEMENT_PATTERN.match(cleaned_line)
            statement_number = None
            is_premise = False
            is_conclusion = False
            if numbered_match:
                statement_number = int(numbered_match.group(2))
                content = f"({statement_number}) {numbered_match.group(3)}"
                is_premise = True  # Will be refined later
            # Check for inference rules
            is_inference_rule = bool(self.INFERENCE_RULE_PATTERN.match(cleaned_line))
            # Check for separators
            is_separator = bool(self.SEPARATOR_PATTERN.match(cleaned_line))
            # Check for preamble (title and gist)
            is_preamble = False
            preamble_match = self.PREAMBLE_PATTERN.match(cleaned_line)
            if preamble_match and not numbered_match:
                is_preamble = True
                content = f"<{preamble_match.group(2)}>: {preamble_match.group(3)}"
            parsed_line = ArgumentStatementLine(
                content=content,
                indent_level=indent_level,
                line_number=i + 1,
                original_line=line,
                statement_number=statement_number,
                is_premise=is_premise,
                is_conclusion=is_conclusion,
                is_inference_rule=is_inference_rule,
                is_separator=is_separator,
                is_preamble=is_preamble,
                has_comment=has_comment,
                comment_content=comment_content,
                yaml_inline_data=yaml_inline_data
            )
            parsed_lines.append(parsed_line)
        # Post-process to identify final conclusion
        self._identify_conclusions(parsed_lines)
        return ArgumentStructure(parsed_lines)
    
    def _calculate_indent_level(self, line: str) -> int:
        """Calculate indentation level (number of INDENT_SIZE-space units)."""
        leading_spaces = len(line) - len(line.lstrip())
        return leading_spaces // INDENT_SIZE
    
    def _parse_dialectical_type(self, symbol: str) -> DialecticalType:
        """Parse dialectical relation symbol into DialecticalType."""
        symbol_map = {
            '<+': DialecticalType.SUPPORTS,
            '<-': DialecticalType.ATTACKS,
            '+': DialecticalType.SUPPORTS,
            '-': DialecticalType.ATTACKS,
            '<_': DialecticalType.UNDERCUTS,
            '><': DialecticalType.CONTRADICTORY,
            '+>': DialecticalType.IS_SUPPORTED_BY,
            '->': DialecticalType.IS_ATTACKED_BY,
            '_>': DialecticalType.IS_UNDERCUT_BY,
        }
        return symbol_map.get(symbol, DialecticalType.SUPPORTS)
    
    def _identify_conclusions(self, lines: List[ArgumentStatementLine]) -> None:
        """Identify which numbered statements are conclusions vs premises."""
        numbered_lines = [line for line in lines if line.is_numbered_statement]
        
        if not numbered_lines:
            return
        
        # Simple heuristic: the last numbered statement is typically the final conclusion
        # More sophisticated logic could be added based on separators and context
        if numbered_lines:
            numbered_lines[-1].is_conclusion = True
            numbered_lines[-1].is_premise = False
        
        # Additional logic: statements after separators are often conclusions
        for i, line in enumerate(lines):
            if line.is_separator and i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.is_numbered_statement:
                    next_line.is_conclusion = True
                    next_line.is_premise = False

    def _extract_comment(self, line: str) -> tuple[str, bool, Optional[str]]:
        """Extract comment from line and return (cleaned_line, has_comment, comment_content)."""
        # Check for inline comments
        inline_match = self.INLINE_COMMENT_PATTERN.match(line)
        if inline_match:
            cleaned_line = inline_match.group(1).rstrip()
            comment_content = inline_match.group(2).strip()
            return cleaned_line, True, comment_content
        
        # Check for standalone comments
        standalone_match = self.STANDALONE_COMMENT_PATTERN.match(line)
        if standalone_match:
            # For standalone comments, we'll treat them as empty content lines
            # but preserve the comment information
            comment_content = standalone_match.group(2).strip()
            return "", True, comment_content
        
        # No comment found
        return line, False, None
