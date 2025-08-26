#!/usr/bin/env python3
"""
Processing Configuration for Dataset Processor Template

This module defines the processing function that will be applied to each item
in the dataset. Modify the process_item function below to implement your
specific processing logic using argdown-cotgen.

This file serves as a template - copy it and modify the process_item function
for your specific use case.
"""

from typing import Dict, Any
import argparse


def process_item(item: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Process a single item from the dataset.
    
    This is the main processing function that you should customize for your
    specific use case. It receives a single item from the dataset and should
    return the processed version of that item.
    
    Args:
        item: A single item from the dataset (dictionary)
        args: Command-line arguments from argparse.Namespace
              Available args include:
              - args.batch_size: Batch size for processing
              - args.dry_run: Boolean indicating if this is a dry run
              - args.debug: Boolean indicating debug mode
              - Any other custom arguments you add
    
    Returns:
        Dictionary containing the processed item
    
    Example:
        To integrate with argdown-cotgen, you might do something like:
        
        ```python
        from argdown_cotgen import Generator
        
        def process_item(item: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
            # Extract argdown text from item
            argdown_text = item.get('argdown', '')
            
            # Process with argdown-cotgen
            generator = Generator()
            processed_text = generator.process(argdown_text)
            
            # Return processed item
            return {
                **item,
                'processed_argdown': processed_text,
                'processing_metadata': {
                    'timestamp': datetime.now().isoformat()
                }
            }
        ```
    """
    # TODO: Replace this placeholder with your actual processing logic
    
    # Example placeholder processing - customize this for your needs
    processed_item = {
        **item,  # Keep all original fields
        'processed': True,
        'processing_metadata': {
            'batch_size': args.batch_size,
            'dry_run': args.dry_run,
            'debug': args.debug
        }
    }
    
    # Add your argdown-cotgen processing logic here
    # For example:
    # if 'argdown' in item:
    #     from argdown_cotgen import Generator
    #     generator = Generator()
    #     processed_item['cot_explanation'] = generator.generate_explanation(item['argdown'])
    
    return processed_item


def get_custom_arguments() -> list:
    """
    Define any custom command-line arguments specific to your processing.
    
    Returns:
        List of tuples, each containing arguments for parser.add_argument()
        Format: [('--arg-name', {'help': 'description', 'type': str, 'default': 'value'}), ...]
    
    Example:
        return [
            ('--temperature', {
                'type': float, 
                'default': 0.7, 
                'help': 'Temperature for text generation'
            }),
            ('--max-tokens', {
                'type': int, 
                'default': 100, 
                'help': 'Maximum tokens to generate'
            }),
            ('--model-name', {
                'type': str, 
                'default': 'gpt-3.5-turbo', 
                'help': 'Model name to use'
            })
        ]
    """
    # Add your custom arguments here
    return [
        # Example custom arguments - modify or remove as needed
        # ('--temperature', {
        #     'type': float, 
        #     'default': 0.7, 
        #     'help': 'Temperature for processing'
        # }),
    ]


def validate_item(item: Dict[str, Any]) -> bool:
    """
    Validate that an item has the required fields for processing.
    
    Args:
        item: A single item from the dataset
    
    Returns:
        True if item is valid, False otherwise
    
    Example:
        def validate_item(item: Dict[str, Any]) -> bool:
            # Check for required fields
            required_fields = ['argdown', 'id']
            return all(field in item for field in required_fields)
    """
    # Add your validation logic here
    # For now, accept all items
    return True


def post_process_dataset(dataset, args: argparse.Namespace) -> dict:
    """
    Perform any post-processing on the entire dataset after individual item processing.
    
    Args:
        dataset: The processed dataset
        args: Command-line arguments
    
    Returns:
        Dictionary with any additional metadata or statistics
    
    Example:
        def post_process_dataset(dataset, args):
            return {
                'total_processed': len(dataset),
                'strategy_used': args.strategy,
                'processing_summary': 'All items processed successfully'
            }
    """
    return {
        'processing_completed': True
    }
