# argdown-cotgen

Takes arbitrary argdown snippets and creates reasoning traces that mimic step by step reconstruction processes

## Usage Examples

```python
from argdown_cotgen import CotGenerator

argdown_snippet = """
[Main claim]: This is the main claim.
    <+ <Argument 1>: The first reason.
    <+ <Argument 2>: The second reason.
    <- <Objection>: An objection to the main claim.
        <- <Rebuttal>: The objection can be rebutted. 
"""

# instantiate pipeline
pipeline = CotGenerator(pipe_type="by_rank")
# call pipeline
cot = pipeline(argdown_snippet)
# print result
print(cot)

#> Let me build the Argdown code snippet step by step.
#> 
#> ```argdown {version='v1'}
#> [Main claim]: This is the main claim.
#> // Arguments need to be added here.
#> ```
#> 
#> I'll add all first-order reasons and arguments.
#> 
#> ```argdown {version='v2'}
#> [Main claim]: This is the main claim.
#>     <+ <Argument 1>: The first reason.
#>     <+ <Argument 2>: The second reason.
#>     <- <Objection>: An objection to the main claim.
#>     // More arguments might need to be added here.
#> ```
#> 
#> Next, I'll add all second-order arguments.
#> 
#> ```argdown {version='v3'}
#> [Main claim]: This is the main claim.
#>     <+ <Argument 1>: The first reason.
#>     <+ <Argument 2>: The second reason.
#>     <- <Objection>: An objection to the main claim.
#>         <- <Rebuttal>: The objection can be rebutted. 
#> ```
#> 
#> That looks good. I've created the Argdown code snippet and may submit version='v3'.
```

```python
from argdown_cotgen import CotGenerator

argdown_snippet = """
<Argument title>: Gist of the argument.

(1) Premise 1.
(2) Premise 2.
-- inference rule --
(3) Intermediary conclusion 1.
(4) Premise 3.
-- inference rule --
(5) Final conclusion.
"""

# instantiate pipeline
pipeline = CotGenerator(pipe_type="by_rank")
# call pipeline
cot = pipeline(argdown_snippet)
# print result
print(cot)

#> Let me build the Argdown code snippet step by step.
#> 
#> I'll start by identifying the conclusion.
#> 
#> ```argdown {version='v1'}
#> // Premises will be added later
#> -----
#> (??) Final conclusion.
#> ```
#> 
#> Let me next add premises.
#> 
#> ```argdown {version='v2'}
#> (1) Premise 1.
#> (2) Premise 2.
#> (3) Premise 3.
#> -----
#> (4) Final conclusion.
#> ```
#> 
#> The inference can be broken down into multiple sub arguments.
#> 
#> ```argdown {version='v3'}
#> (1) Premise 1.
#> (2) Premise 2.
#> -----
#> (3) Intermediary conclusion 1.
#> (4) Premise 3.
#> -----
#> (5) Final conclusion.
#> ```
#> 
#> I can now add additional info for each inference step.
#> 
#> ```argdown {version='v4'}
#> (1) Premise 1.
#> (2) Premise 2.
#> -- inference rule --
#> (3) Intermediary conclusion 1.
#> (4) Premise 3.
#> -- inference rule --
#> (5) Final conclusion.
#> ```
#> 
#> Let me finally add title and gist.
#> 
#> ```argdown {version='v5'}
#> <Argument title>: Gist of the argument.
#> 
#> (1) Premise 1.
#> (2) Premise 2.
#> -- inference rule --
#> (3) Intermediary conclusion 1.
#> (4) Premise 3.
#> -- inference rule --
#> (5) Final conclusion.
#> ```
#> 
#> That looks good. I've created the Argdown code snippet and may submit version='v5'.
```

## CoT Strategies for Incremental Argumentation Reconstructions

### CoT Strategies for Individual Arguments

#### Strategy `by_feature`

1. Step **Title and Gist**: Show title and gist (preamble), otherwise empty.
2. Step **Final conclusion**: Add premise-conclusion scaffold with final conclusion (no yaml, no comments).
3. Step **Premises**: Add all premises (no yaml, no comments).
4. Step **Intermediate Conclusions**: Add all intermediate steps (no yaml, no comments).
5. Step **Inference information**: Add any available inference information in inference steps.
6. Step **YAML inline data**: Add yaml inline data to all propositions.
7. Step **Comments and Misc**: Add all comments and remaining misc lines present in original argdown snippet. 

Notes:

* In each step, propositions are enumerated consecutively.
* Each step may contain specific (preliminary) comments inserted to document, clarify, evaluate and guide the reconstruction process. E.g., "// inference data needs to be added here", "// this has been premise (3) in previous argument"
* Variants: Add **title and gist** only at the very end, rather than at the beginning.


#### Strategy `by_rank`

1. Step **Title and Gist**: Show title and gist (preamble), otherwise empty.
2. Step **Final conclusion**: Add premise-conclusion scaffold with final conclusion (no yaml, no comments).
3. Step **main inference step**: Add all propositions that are "used" to infer the main conclusion.
4. Step **iteratively add all remaining sub arguments**:
    - Propositions rendered as premises in previous steps will become conclusions. 
5. Step **Inference information**: Add any available inference information in inference steps.
6. Step **YAML inline data**: Add yaml inline data to all propositions.
7. Step **Comments and Misc**: Add all comments and remaining misc lines present in original argdown snippet. 

Example:

<code>

```argdown {version="v1"}
<Title>: Argument's key point.
```

```argdown {version="v2"}
<Title>: Argument's key point.

(1) // ...
-----
(2) Main conclusion.
```

```argdown {version="v3"}
<Title>: Argument's key point.

(1) Proposition A
(2) Proposition B
-- {uses: [1,2]} --
(3) Main conclusion.
```

```argdown {version="v4"}
<Title>: Argument's key point.

(1) Proposition A
(2) Proposition C
(3) Proposition D
-- {uses: [2,3]} --
(4) Proposition B
-- {uses: [1,4]} --
(5) Main conclusion.
```

```argdown {version="v5"}
<Title>: Argument's key point.

(1) Proposition A
(2) Proposition C
(3) Proposition D
-- with rule1 --
(4) Proposition B
-- with rule2 from 1 and 4 --
(5) Main conclusion.
```
</code>


### CoT Strategies for Argument Maps 

#### Strategy `by_rank`

1. Step **Roots**: Show all root nodes of map (no comments or inline yaml)
2. Step **First order reasons**: Add all args / claims directly related to any root.
3. Step **Higher order reasons**: For all ranks _r>1_:
    - Show all nodes up to rank _r_.
4. Add yaml and comments.

#### Strategy `breadth_first`

1. Reveal all child nodes "breadth_first"
2. Add yaml and comments.

#### Strategy `depth_first`

1. Reveal all child nodes "depth_first"
2. Add yaml and comments.


#### Strategy `by_objection`

1. Step **Roots**: Show all root nodes of map (no comments or inline yaml)
2. Step **Main supporting argumentation**: Show all nodes that are connected to any root via a directed path of support edges.
3. Step **Objections**: Add any reasons that are directly attacking any nodes added so far, plus all their supporting nodes.
4. Step **Rebuttals**: Add any nodes that are directly attacking any nodes added so far, plus all their supporting nodes.
5. Iterate until all nodes have been added.
6. Add yaml and comments.


#### Strategy `random_diffusion`

Here the reconstruction process starts with a randomly distorted and heavily erroneous version of the correct and final argument map. All errors are incrementally removed to reach the final and correct version.

#### Strategy `depth_diffusion`

Here the reconstruction process starts with a flat and unstructured list of all arguments and propositions. All reasons are subsumed unter their correct parent node, increasing max depth incrementally.

Example:

<code>

```argdown {version="v1"}
C
B
E
D
A
```

```argdown {version="v2"}
A
  <+ B
  ?? C
  ?? E
  ?? D
```

```argdown {version="v3"}
A
  <+ B
    <- C
    ?? E
    <+ D
```

```argdown {version="v3"}
A
  <+ B
    <- C
    <+ D 
        <+ E
```

</code>


### General Remarks

#### Comments

* Use comments with '✅' to earmark lines as correct
* Use comments with other emojis like '🤔' or '❌' to indicate uncertainty, flaws


#### Abortion

Mimic fatal (block-) repetitions and abort creating argdown snippet in such cases.

Example:

<code>

```argdown {version='v3'}
(1) Climate change causes suffering. {certainty: 0.9}
(2) We have a duty to prevent suffering. // Kantian principle
(3) We have a duty to prevent suffering. // Kantian principle
// Oh no! This is just exactly what I've written before. Better ABORT and DISCARD this, and start anew.   
```

I ignore the above Argdown snippet and will try again.

```argdown {version='v3'}
(1) Climate change causes suffering. {certainty: 0.9}
(2) We have a duty to prevent suffering. // Kantian principle
-- modus ponens --
// ...
```

</code>


