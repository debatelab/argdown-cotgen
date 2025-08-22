# Strategy Testing Framework

This document explains the comprehensive testing framework for argument map strategies in the argdown-cotgen project.

## Overview

The testing framework provides a unified, reusable approach for testing all argument map strategies with consistent test coverage and quality standards. All strategy-related tests are organized in the `tests/strategies/` subfolder for clear separation and maintainability.

## Framework Architecture

### Core Components

1. **`tests/strategies/strategy_test_framework.py`** - The main framework module
2. **`BaseStrategyTestSuite`** - Abstract base class for strategy tests
3. **`COMMON_STRATEGY_TEST_CASES`** - Shared test cases for all strategies
4. **Strategy-specific test files** - Individual test suites for each strategy

### File Structure

```
tests/
├── strategies/                               # Strategy testing package
│   ├── __init__.py                          # Package initialization
│   ├── strategy_test_framework.py           # Main testing framework
│   ├── test_by_rank_strategy.py             # ByRankStrategy tests
│   ├── test_breadth_first_strategy.py       # BreadthFirstStrategy tests
│   └── test_strategy_comparisons.py         # Cross-strategy comparison tests
├── test_comments.py                         # Comment processing tests
├── test_cot_formatter.py                    # CoT formatter tests
├── test_parser.py                           # Parser tests
└── ... (other core tests)
```

## Usage

### Creating Tests for a New Strategy

1. **Create a new test file in `tests/strategies/`**:

```python
from typing import Type
from tests.strategies.strategy_test_framework import BaseStrategyTestSuite
from src.argdown_cotgen.strategies.argument_maps.my_strategy import MyStrategy
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy

class TestMyStrategy(BaseStrategyTestSuite):
    """Test suite for MyStrategy using the common framework."""
    
    @property
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        return MyStrategy
    
    @property  
    def strategy_name(self) -> str:
        return "MyStrategy"
```

⚠️ **Important**: Use `@property` methods, NOT `@pytest.fixture`. Fixtures will prevent the common test cases from being collected properly.
        return "MyStrategy"
```

2. **Automatic Test Coverage**: The framework automatically provides:
   - Common test cases (simple maps, YAML, comments, etc.)
   - Error handling tests (wrong structure types)
   - Quality validation (explanations, step progression)
   - Abortion functionality testing

3. **Add Strategy-Specific Tests**:

```python
def test_my_strategy_specific_behavior(self):
    """Test behavior unique to MyStrategy."""
    # Your strategy-specific test logic
    pass
```

### Framework Features

#### Common Test Cases

The framework includes these test cases for all strategies:

- **`simple_two_level`** - Basic argument map with support and attack
- **`deep_nesting`** - Multi-level hierarchical structure  
- **`with_yaml`** - YAML inline data handling
- **`with_comments`** - Comment processing
- **`yaml_and_comments`** - Combined YAML and comment handling
- **`single_claim`** - Single root claim only

#### Automatic Validations

Every strategy automatically gets tested for:

1. **Step Quality**:
   - Non-empty content and explanations
   - Proper version numbering
   - Content progression across steps

2. **Feature Support**:
   - YAML data handling
   - Comment processing
   - Root claim identification

3. **Error Handling**:
   - Rejection of non-ArgumentMap structures
   - Proper empty line handling

4. **Abortion Functionality**:
   - High abortion rate handling
   - First step always clean

5. **Content Reconstruction**:
   - Final step exactly reconstructs original input
   - No missing content from original argdown
   - No extra content beyond original
   - Proper YAML and comment formatting

#### Customization Hooks

Override these methods for strategy-specific behavior:

```python
def _validate_step_count(self, steps, test_case):
    """Override for strategy-specific step count validation."""
    # Custom validation logic
    super()._validate_step_count(steps, test_case)

def _validate_features(self, steps, structure, expected):
    """Override for strategy-specific feature validation."""
    # Custom feature validation
    super()._validate_features(steps, structure, expected)
```

## Common Pitfalls and Solutions

### ❌ Wrong Inheritance Pattern

**Problem**: Using `@pytest.fixture` instead of `@property`

```python
# WRONG - This prevents common test collection
class TestMyStrategy(BaseStrategyTestSuite):
    @pytest.fixture
    def strategy(self):
        return MyStrategy()
```

**Solution**: Use properties with proper type hints

```python
# CORRECT - This enables proper test inheritance
class TestMyStrategy(BaseStrategyTestSuite):
    @property
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        return MyStrategy
    
    @property
    def strategy_name(self) -> str:
        return "MyStrategy"
```

### ❌ Missing Type Imports

**Problem**: Missing required imports for type hints

```python
# WRONG - Missing imports
from tests.strategies.strategy_test_framework import BaseStrategyTestSuite
```

**Solution**: Include all required imports

```python
# CORRECT - All imports included
from typing import Type
from tests.strategies.strategy_test_framework import BaseStrategyTestSuite
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy
```

### ❌ Content Reconstruction Issues

**Problem**: Strategy doesn't properly reconstruct original content (YAML spacing, missing content)

The framework automatically validates that `steps[-1].content` exactly matches the original input. Common issues:
- Extra spaces before YAML data
- Missing YAML or comments in final step
- Incorrect indentation or formatting

**Solution**: Ensure your strategy's `_format_line()` method properly handles spacing and reconstruction.

## Content Reconstruction Validation

The framework automatically validates that the final generated step exactly reconstructs the original argdown input. This ensures:

1. **No Lost Content**: Every line from the original is present in the final step
2. **No Extra Content**: Final step doesn't add content not in the original  
3. **Exact Formatting**: YAML, comments, and indentation match precisely

This validation catches common bugs like:
- YAML spacing issues (`content += f" {yaml}"` → `content.rstrip() + f" {yaml}"`)
- Missing content in final reconstruction
- Incorrect formatting or line ordering

## Testing Different Strategies Together

### Comparison Testing

Use `tests/strategies/test_strategy_comparisons.py` to test that different strategies produce different but valid results:

```python
def test_strategies_produce_different_results(self, test_case):
    results = run_strategy_comparison(self.strategies, test_case)
    assert_strategies_differ(results)
```

### Utility Functions

- **`run_strategy_comparison()`** - Run multiple strategies on same input
- **`assert_strategies_differ()`** - Verify strategies produce different outputs

## Benefits

### 1. **Organized Structure**
- Strategy tests clearly separated in `tests/strategies/` subfolder
- Core framework and all strategy tests in one logical location
- Clean separation from parser, formatter, and other core tests

### 2. **Consistency**
- All strategies tested with same quality standards
- Uniform test structure across implementations

### 3. **Comprehensive Coverage**
- Automatic testing of common functionality
- Edge cases covered systematically  

### 4. **Maintainability**
- Add new test cases in one place (affects all strategies)
- Strategy-specific tests clearly separated in organized structure

### 5. **Quality Assurance**
- Validates explanation quality and variety
- Ensures proper content progression
- Tests abortion functionality consistently

### 6. **Easy Extension**
- New strategies get comprehensive testing automatically
- Framework grows with new test cases
- Clear location for adding new strategy tests

## Test Examples

### Basic Strategy Test

```python
# Automatically tests with all common cases
@pytest.mark.parametrize("test_case", COMMON_STRATEGY_TEST_CASES)
def test_common_cases(self, test_case):
    # Framework handles this automatically
    pass
```

### Strategy-Specific Test

```python
def test_breadth_first_ordering(self):
    """Test breadth-first specific ordering behavior."""
    argdown_text = """[Root]: Main.
    <+ <A>: Support A.
        <+ <A1>: Deep A.
    <+ <B>: Support B."""
    
    structure = self.parser.parse(argdown_text)
    steps = self.strategy.generate(structure)
    
    # Test that A and B appear before A1 (breadth-first order)
    # ... specific validation logic
```

## Running Tests

```bash
# Run all strategy tests
uv run python -m pytest tests/strategies/ -v

# Run specific strategy tests  
uv run python -m pytest tests/strategies/test_breadth_first_strategy.py -v

# Run comparison tests
uv run python -m pytest tests/strategies/test_strategy_comparisons.py -v

# Run framework tests
uv run python -m pytest tests/strategies/strategy_test_framework.py -v

# Run all tests (including non-strategy tests)
uv run python -m pytest tests/ -v
```

## Test Statistics

Current test coverage (163 total tests, 96 strategy-specific):

- **Strategy Framework Tests**: 96 comprehensive tests across all strategies
  - **BreadthFirstStrategy**: 20 tests (14 common + 6 specific)
  - **ByRankStrategy**: 20 tests (14 common + 6 specific) 
  - **ByObjectionStrategy**: 23 tests (14 common + 9 specific)
  - **DepthFirstStrategy**: 20 tests (14 common + 6 specific)
  - **Comparison Tests**: 13 cross-strategy tests
- **Core Tests**: 67 tests for parser, formatter, and other components

### Common Tests Per Strategy (14 each)
- 10 parametrized common test cases (simple_two_level, with_yaml, etc.)
- 4 framework tests (wrong_structure_type, empty_lines_handling, etc.)
- Content reconstruction validation for all tests
- Quality assurance for explanations and step progression

The organized framework in `tests/strategies/` ensures comprehensive, consistent, and maintainable testing for all current and future argument map strategies.