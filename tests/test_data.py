"""Test data and fixtures for argdown parser tests."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from src.argdown_cotgen.core import SnippetType


@dataclass
class SnippetTestCase:
    """Test case for an argdown snippet."""
    name: str
    snippet: str
    expected_type: SnippetType
    description: str
    expected_properties: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.expected_properties is None:
            self.expected_properties = {}


# Collection of argdown test snippets
ARGUMENT_MAP_SNIPPETS = [
    SnippetTestCase(
        name="basic_support_attack",
        snippet="""
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.
    <+ <Argument 2>: The second reason.
    <- <Objection>: An objection to the main claim.
        <- <Rebuttal>: The objection can be rebutted.
""",
        expected_type=SnippetType.ARGUMENT_MAP,
        description="Basic argument map with support and attack relations",
        expected_properties={
            "max_depth": 2,
            "main_claim_content": "Main claim",
            "first_level_count": 3,
            "second_level_count": 1
        }
    ),

    SnippetTestCase(
        name="basic_support_attack_with_comments",
        snippet="""
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.  // This is a comment
    <+ <Argument 2>: The second reason.
    // Another comment
    <- <Objection>: An objection to the main claim.
        <- <Rebuttal>: The objection can be rebutted.
    /* And a final
    multiline
    comment */
""",
        expected_type=SnippetType.ARGUMENT_MAP,
        description="Basic argument map with support and attack relations",
        expected_properties={
            "max_depth": 2,
            "main_claim_content": "Main claim",
            "first_level_count": 3,
            "second_level_count": 1
        }
    ),

    SnippetTestCase(
        name="basic_support_attack_with_yaml",
        snippet="""
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason. {key1: "value1"}
    <+ <Argument 2>: The second reason.
    <- <Objection>: An objection to the main claim.  {key1: "value2"}  // comment here
        <- <Rebuttal>: The objection can be rebutted.
""",
        expected_type=SnippetType.ARGUMENT_MAP,
        description="Basic argument map with support and attack relations",
        expected_properties={
            "max_depth": 2,
            "main_claim_content": "Main claim",
            "first_level_count": 3,
            "second_level_count": 1
        }
    ),

    SnippetTestCase(
        name="inverse_support_attack",
        snippet="""
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.
    +> <Argument 2>: The second reason.
        -> <Objection>: An objection to Argument 2.
            <- <Rebuttal>: The objection can be rebutted.
""",
        expected_type=SnippetType.ARGUMENT_MAP,
        description="Basic argument map with support and attack relations",
        expected_properties={
            "max_depth": 3,
            "main_claim_content": "Main claim",
            "first_level_count": 2,
            "second_level_count": 1
        }
    ),


    SnippetTestCase(
        name="complex_multilevel",
        snippet="""
[Climate change is real]: Human activities are causing climate change.
    <+ <Scientific consensus>: 97% of climate scientists agree.
        <+ <Multiple studies>: Numerous peer-reviewed studies support this.
        <- <Funding bias>: Climate scientists are biased by funding.
            <- <Independent verification>: Results verified independently.
    <- <Natural variation>: Climate has always varied naturally.
        <- <Unprecedented rate>: Current rate of change is unprecedented.
    <+ <Physical evidence>: Ice cores show CO2 correlation.
""",
        expected_type=SnippetType.ARGUMENT_MAP,
        description="Complex multi-level argument map",
        expected_properties={
            "max_depth": 3,
            "depth_0_count": 1,
            "depth_1_count": 3,
            "depth_2_count": 3,
            "depth_3_count": 1
        }
    ),
    
    SnippetTestCase(
        name="single_claim",
        snippet="[Single claim]: Just one claim.",
        expected_type=SnippetType.ARGUMENT_MAP,
        description="Single claim without arguments",
        expected_properties={
            "max_depth": 0,
            "main_claim_exists": True
        }
    ),
    
    SnippetTestCase(
        name="undercut_relations",
        snippet="""
[Main position]: The main position.
    <+ <Support>: Supporting argument.
        <_ <Undercut>: This undercuts the support.
""",
        expected_type=SnippetType.ARGUMENT_MAP,
        description="Argument map with undercut relations",
        expected_properties={
            "has_undercuts": True,
            "max_depth": 2
        }
    ),
]

ARGUMENT_SNIPPETS = [
    SnippetTestCase(
        name="basic_premise_conclusion",
        snippet="""
<Argument title>: Gist of the argument.

(1) Premise 1.
(2) Premise 2.
-- inference rule --
(3) Intermediary conclusion 1.
(4) Premise 3.
-- inference rule --
(5) Final conclusion.
""",
        expected_type=SnippetType.ARGUMENT,
        description="Basic argument with premises, inference rules, and conclusions",
        expected_properties={
            "numbered_statements": 5,
            "inference_rules": 2,
            "has_title": True,
            "final_conclusion_number": 5
        }
    ),
    
    SnippetTestCase(
        name="simple_syllogism",
        snippet="""
(1) All humans are mortal.
(2) Socrates is human.
-----
(3) Therefore, Socrates is mortal.
""",
        expected_type=SnippetType.ARGUMENT,
        description="Simple syllogism with separator",
        expected_properties={
            "numbered_statements": 3,
            "has_separator": True,
            "conclusions": 1
        }
    ),
    
    SnippetTestCase(
        name="argument_no_title",
        snippet="""
(1) First premise.
(2) Second premise.
(3) Conclusion follows.
""",
        expected_type=SnippetType.ARGUMENT,
        description="Argument without title or inference rules",
        expected_properties={
            "numbered_statements": 3,
            "has_title": False,
            "inference_rules": 0
        }
    ),
    
    SnippetTestCase(
        name="multi_step_argument",
        snippet="""
<Complex argument>: Multi-step reasoning.

(1) Initial premise.
(2) Second premise.
-- modus ponens --
(3) Intermediate conclusion.
(4) Additional premise.
(5) Another premise.
-- disjunctive syllogism --
(6) Another intermediate conclusion.
(7) Final premise.
-- modus tollens --
(8) Final conclusion.
""",
        expected_type=SnippetType.ARGUMENT,
        description="Multi-step argument with multiple inference rules",
        expected_properties={
            "numbered_statements": 8,
            "inference_rules": 3,
            "has_title": True
        }
    ),
]

# Edge cases and special scenarios
EDGE_CASE_SNIPPETS = [
    SnippetTestCase(
        name="empty_lines_mixed",
        snippet="""
[Main claim]: This is the main claim.

    <+ <Argument 1>: The first reason.
    
    <+ <Argument 2>: The second reason.

""",
        expected_type=SnippetType.ARGUMENT_MAP,
        description="Snippet with empty lines interspersed",
        expected_properties={
            "preserves_empty_lines": True,
            "non_empty_content_lines": 3
        }
    ),
    
    SnippetTestCase(
        name="mixed_indentation",
        snippet="""
[Main]: Main claim.
  <+ <Arg1>: Argument 1 (2 spaces).
      <+ <Arg2>: Argument 2 (6 spaces).
    <- <Obj>: Objection (4 spaces).
""",
        expected_type=SnippetType.ARGUMENT_MAP,
        description="Mixed indentation levels",
        expected_properties={
            "handles_mixed_indentation": True,
            "max_depth": 1
        }
    ),
    
    SnippetTestCase(
        name="contradictory_relations",
        snippet="""
[Position A]: First position.
    >< [Position B]: Contradictory position.
""",
        expected_type=SnippetType.ARGUMENT_MAP,
        description="Contradictory relations between claims",
        expected_properties={
            "has_contradictory": True
        }
    ),
]

# All test cases combined
ALL_SNIPPETS = ARGUMENT_MAP_SNIPPETS + ARGUMENT_SNIPPETS + EDGE_CASE_SNIPPETS

# Helper functions for test data
def get_snippets_by_type(snippet_type: SnippetType) -> List[SnippetTestCase]:
    """Get all snippets of a specific type."""
    return [s for s in ALL_SNIPPETS if s.expected_type == snippet_type]

def get_snippet_by_name(name: str) -> SnippetTestCase:
    """Get a specific snippet by name."""
    for snippet in ALL_SNIPPETS:
        if snippet.name == name:
            return snippet
    raise ValueError(f"Snippet '{name}' not found")

def get_snippet_names_by_type(snippet_type: SnippetType) -> List[str]:
    """Get names of all snippets of a specific type."""
    return [s.name for s in get_snippets_by_type(snippet_type)]
