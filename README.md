# argdown-cotgen

Takes arbitrary argdown snippets and creates reasoning traces that mimic step by step reconstruction processes

## Usage examples

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