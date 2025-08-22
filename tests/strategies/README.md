# Strategy Testing - Quick Start

🚀 **Need to test a new strategy? Start here!**

📚 **For complete documentation**: See [`docs/STRATEGY_TESTING_FRAMEWORK.md`](../../docs/STRATEGY_TESTING_FRAMEWORK.md)

## Template

Create `tests/strategies/test_your_strategy.py`:

```python
from typing import Type
from src.argdown_cotgen.strategies.argument_maps.your_strategy import YourStrategy
from src.argdown_cotgen.strategies.base import BaseArgumentMapStrategy
from .strategy_test_framework import BaseStrategyTestSuite

class TestYourStrategy(BaseStrategyTestSuite):
    """Test suite for YourStrategy using the common framework."""
    
    @property
    def strategy_class(self) -> Type[BaseArgumentMapStrategy]:
        return YourStrategy
    
    @property
    def strategy_name(self) -> str:
        return "YourStrategy"
```

## Critical Rules

⚠️ **Use `@property` NOT `@pytest.fixture`** - fixtures break test collection!

✅ **Must inherit from `BaseStrategyTestSuite`**

✅ **Must implement both `strategy_class` and `strategy_name` properties**

## You Get Automatically

- **14 comprehensive tests** (10 common cases + 4 framework tests)
- **Content reconstruction validation** (final step = original input)
- **Quality assurance** (explanations, versions, step progression)

## Examples

- **Working reference**: [`test_breadth_first_strategy.py`](test_breadth_first_strategy.py)
- **All strategy tests**: Run `uv run python -m pytest tests/strategies/ -v`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Tests not collected | Check you're using `@property` not `@pytest.fixture` |
| Content reconstruction fails | Usually YAML spacing bugs - check `_format_line()` method |
| Import errors | Verify all required imports and inheritance |

---
💡 **Need more details?** See the complete guide: [`docs/STRATEGY_TESTING_FRAMEWORK.md`](../../docs/STRATEGY_TESTING_FRAMEWORK.md)
