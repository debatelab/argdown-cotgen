# Configurable Dataset Processor Template

This enhanced template allows you to define custom processing logic in separate configuration files, making the template truly reusable for different argdown-cotgen use cases.

## Files Overview

- `dataset_processing_script.py` - Main configurable script
- `processing_config.py` - Basic configuration template

## How to Use

### 1. Basic Usage with Default Config

```bash
# Uses processing_config.py by default
python -m recipies.dataset_processing_script --input dataset.json --output ./processed/
```

### 2. Using Custom Configuration

```bash
# Use a custom configuration file
python -m recipies.dataset_processing_script \
    --input dataset.json \
    --output ./processed/ \
    --config my_custom_config.py
```

### 3. With Custom Arguments

When you create custom configurations that add arguments:

```bash
python -m recipies.dataset_processing_script \
    --input dataset.json \
    --output ./processed/ \
    --config my_custom_config.py \
    --my-custom-param value
```

## Creating Your Own Configuration

### Step 1: Copy the Template

```bash
cp processing_config.py my_custom_config.py
```

### Step 2: Implement Required Functions

Your configuration file must define:

```python
def process_item(item: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """Process a single dataset item - REQUIRED"""
    # Your processing logic here
    pass
```

### Step 3: Optional Functions

You can also define these optional functions:

```python
def get_custom_arguments() -> list:
    """Define custom command-line arguments"""
    return [
        ('--my-param', {'type': str, 'help': 'My custom parameter'}),
    ]

def validate_item(item: Dict[str, Any]) -> bool:
    """Validate items before processing"""
    return True  # or your validation logic

def post_process_dataset(dataset, args: argparse.Namespace) -> dict:
    """Post-process the entire dataset after processing"""
    return {'status': 'completed'}
```

## Configuration Function Reference

### `process_item(item, args)` - **Required**

The main processing function that transforms each dataset item.

**Parameters:**
- `item`: Dictionary containing a single dataset item
- `args`: Namespace with all command-line arguments

**Returns:** Processed item as dictionary

### `get_custom_arguments()` - Optional

Define additional command-line arguments specific to your processing.

**Returns:** List of tuples: `[('--arg-name', {'type': str, 'help': 'description'}), ...]`

### `validate_item(item)` - Optional

Validate items before processing. Invalid items are skipped with a warning.

**Parameters:**
- `item`: Dictionary containing a single dataset item

**Returns:** Boolean indicating if item is valid

### `post_process_dataset(dataset, args)` - Optional

Perform analysis or cleanup after all items are processed.

**Parameters:**
- `dataset`: The complete processed dataset
- `args`: Command-line arguments

**Returns:** Dictionary with metadata/statistics

## Integration with argdown-cotgen

You can create configurations that integrate with the argdown-cotgen library by implementing the `process_item` function to use argdown-cotgen's processing capabilities. Here's a basic example structure:

```python
# my_argdown_config.py
from argdown_cotgen import Generator

def process_item(item, args):
    argdown_text = item.get('argdown', '')
    generator = Generator(strategy=args.strategy)
    
    return {
        **item,
        'cot_explanation': generator.generate_explanation(argdown_text),
        'strategy': args.strategy
    }

def get_custom_arguments():
    return [
        ('--max-tokens', {'type': int, 'default': 500}),
        ('--temperature', {'type': float, 'default': 0.7}),
    ]
```

## Examples

### Simple Text Processing

```python
# simple_config.py
def process_item(item, args):
    text = item.get('text', '')
    return {
        **item,
        'word_count': len(text.split()),
        'processed': True
    }
```

### Argdown Chain-of-Thought Generation

```python
# cot_config.py
from argdown_cotgen import Generator

def process_item(item, args):
    argdown_text = item.get('argdown', '')
    generator = Generator(strategy=args.strategy)
    
    return {
        **item,
        'cot_explanation': generator.generate_explanation(argdown_text),
        'strategy': args.strategy
    }

def get_custom_arguments():
    return [
        ('--max-tokens', {'type': int, 'default': 500}),
        ('--temperature', {'type': float, 'default': 0.7}),
    ]
```

## Error Handling

The template includes robust error handling:

- Configuration loading errors are reported clearly
- Invalid items are skipped with warnings
- Processing errors are caught and logged
- Failed items can include error information in output

## Performance Tips

- Use appropriate `--batch-size` for your processing
- Enable `--debug` for detailed logging during development
- Use `--dry-run` to test configuration without processing
- Consider memory usage with large datasets

## Output Formats

The template supports multiple output formats:
- JSONL (default, efficient for large datasets)
- Hub upload (with `--hub-repo-id`)
- Split-aware naming for DatasetDict inputs

## Next Steps

1. Copy and customize a configuration file for your use case
2. Test with `--dry-run` and small datasets first
3. Add custom validation and error handling as needed
4. Scale up to full datasets once testing is complete
