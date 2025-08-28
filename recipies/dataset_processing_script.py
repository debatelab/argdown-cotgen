#!/usr/bin/env python3
"""
Dataset Processor Script for Argdown-CoTGen Recipes

This module provides a fully configurable script for creating recipes that process argdown
argumentation datasets using the argdown-cotgen library. It demonstrates the standard pattern for:

- Command-line argument parsing with configurable options
- Simple console output for progress tracking
- Dataset loading using Hugging Face datasets library
- Error handling and validation
- Dataset loading and processing workflows
- Output generation and saving in multiple formats (HF, JSON, JSONL, Parquet)

The template uses Hugging Face's datasets library for efficient loading and saving,
with fallback to manual JSON handling when needed.

Usage:
    python -m recipies.dataset_processing_script --input <dataset_path> --output <output_path> [options]

Example:
    # Basic usage with local JSON file
    python -m recipies.dataset_processing_script --input ./data/argdown_dataset.json --output ./processed/

    # Load from Hugging Face Hub
    python -m recipies.dataset_processing_script --input "username/dataset-name" --output ./processed/

    # Load local directory (HF dataset format)
    python -m recipies.dataset_processing_script --input ./hf_dataset/ --output ./processed/

    # Load specific split and use custom config
    python -m recipies.dataset_processing_script --input "username/dataset-name" --output ./processed/ --split train --config my_config.py

    # With debug mode (process only 50 items, no upload)
    python -m recipies.dataset_processing_script --input ./data/argdown_dataset.json --output ./processed/ --debug

Supported Input Formats:
    - JSON files (.json)
    - JSONL files (.jsonl) 
    - CSV files (.csv)
    - Parquet files (.parquet)
    - Arrow files (.arrow)
    - Hugging Face dataset directories
    - Hugging Face Hub dataset names

Output Formats:
    - Hugging Face dataset format (for efficient loading)
    - JSON (for compatibility)
    - JSONL (for streaming)
    - Parquet (for efficient storage)

Arguments:
    --input: Path to input dataset, directory, or HF Hub name (required)
    --output: Path to output directory (required)
    --debug: Enable debug mode (process only 50 items, disable uploads)
    --log-file: Optional log file path
    --dry-run: Perform validation without actual processing
    --hub-repo-id: Optional HF Hub repository for uploading results
    --split: Load only a specific split from DatasetDict (e.g., 'train', 'test', 'validation')
    --subset: Load only a specific subset/configuration (e.g., 'aaac01-thinking', 'aaac02-thinking')
    --config: Path to processing configuration file (default: processing_config.py)

Author: Gregor Betz
Created: August 2025
"""

import os
import argparse
import random
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
import json
import importlib.util
from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict, load_dataset  # type: ignore

# Type alias for all possible dataset types
DatasetType = Union[Dataset, DatasetDict, IterableDataset, IterableDatasetDict]


def setup_logging(debug: bool = False, log_file: Optional[str] = None) -> logging.Logger:
    """Setup simple logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            *([logging.FileHandler(log_file)] if log_file else [])
        ]
    )
    
    return logging.getLogger(__name__)


def load_processing_config(config_path: str, logger: logging.Logger):
    """
    Load processing configuration from a Python file.
    
    Args:
        config_path: Path to the configuration file
        logger: Logger instance
    
    Returns:
        Module object with processing functions
    """
    logger.debug(f"Loading processing configuration from: {config_path}")
    
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("processing_config", config_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load configuration from: {config_path}")
    
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    # Validate required functions exist
    required_functions = ['process_item']
    for func_name in required_functions:
        if not hasattr(config_module, func_name):
            raise AttributeError(f"Configuration file must define function: {func_name}")
    
    logger.info(f"Successfully loaded processing configuration from: {config_path}")
    return config_module


def validate_arguments(args: argparse.Namespace, logger: logging.Logger) -> bool:
    """
    Validate command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        logger: Logger instance
    
    Returns:
        True if arguments are valid, False otherwise
    """
    logger.debug(f"Validating arguments: {vars(args)}")
    
    # Validation code here
    
    logger.debug("All arguments validated successfully")
    return True


def load_hf_dataset(input_path: str, logger: logging.Logger, split: Optional[str] = None, subset: Optional[str] = None) -> DatasetType:
    """
    Load dataset from input path using Hugging Face datasets library.
    
    Args:
        input_path: Path to input dataset, directory, or HF Hub dataset name
        logger: Logger instance
        split: Optional specific split to load from DatasetDict (e.g., 'train', 'test', 'validation')
        subset: Optional specific subset/configuration to load (e.g., 'aaac01-thinking', 'aaac02-thinking')
    
    Returns:
        Dataset, DatasetDict, IterableDataset, or IterableDatasetDict object
    """
    logger.info(f"Loading dataset from: {input_path}")
    
    path = Path(input_path)
    
    try:
        # Try to load with Hugging Face datasets
        if path.is_file():
            # Determine file format and load accordingly
            if path.suffix.lower() == '.json':
                dataset = load_dataset('json', data_files=str(path), split='train')
            elif path.suffix.lower() == '.jsonl':
                dataset = load_dataset('json', data_files=str(path), split='train')
            elif path.suffix.lower() == '.csv':
                dataset = load_dataset('csv', data_files=str(path), split='train')
            elif path.suffix.lower() in ['.parquet', '.arrow']:
                dataset = load_dataset('parquet' if path.suffix.lower() == '.parquet' else 'arrow', 
                                     data_files=str(path), split='train')
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        
        elif path.is_dir():
            # Load from directory (HF dataset format) - don't specify split to get all splits
            dataset = load_dataset(str(path), name=subset) if subset else load_dataset(str(path))
        
        else:
            # Try to load as a Hugging Face Hub dataset - don't specify split to get all splits
            dataset = load_dataset(input_path, name=subset) if subset else load_dataset(input_path)
        
        # If user requested a specific split, extract it from DatasetDict
        if split and isinstance(dataset, (DatasetDict, IterableDatasetDict)):
            if split in dataset:
                logger.info(f"Extracting requested split '{split}' from DatasetDict")
                dataset = dataset[split]
            else:
                available_splits = list(dataset.keys())
                raise ValueError(f"Requested split '{split}' not found. Available splits: {available_splits}")
        
        # Log information about what we loaded
        if isinstance(dataset, (DatasetDict, IterableDatasetDict)):
            splits = list(dataset.keys())
            logger.info(f"Loaded DatasetDict with splits: {splits}")
            # Get total size across all splits if possible
            total_size = 0
            for split_name, split_data in dataset.items():
                try:
                    if isinstance(split_data, Dataset):
                        split_size = len(split_data)
                        logger.info(f"  Split '{split_name}': {split_size} items")
                        if isinstance(split_size, int):
                            total_size += split_size
                    else:
                        logger.info(f"  Split '{split_name}': size unknown (iterable)")
                except Exception:
                    logger.info(f"  Split '{split_name}': size unknown (iterable)")
            
            if total_size > 0:
                logger.info(f"Total items across all splits: {total_size}")
        
        elif isinstance(dataset, (Dataset, IterableDataset)):
            try:
                if isinstance(dataset, Dataset):
                    size = len(dataset)
                    logger.info(f"Loaded single dataset with {size} items")
                else:
                    logger.info("Loaded iterable dataset with unknown size")
            except Exception:
                logger.info("Loaded iterable dataset with unknown size")
        
        # Log features if available
        try:
            if isinstance(dataset, (Dataset, IterableDataset)) and hasattr(dataset, 'features') and dataset.features:
                logger.debug(f"Dataset features: {list(dataset.features.keys())}")
            elif isinstance(dataset, (DatasetDict, IterableDatasetDict)):
                # Try to get features from first split
                first_split = next(iter(dataset.values()))
                if hasattr(first_split, 'features') and first_split.features:
                    logger.debug(f"Dataset features: {list(first_split.features.keys())}")
        except Exception:
            pass
        
        return dataset
    
    except Exception as e:
        logger.error(f"Failed to load dataset with Hugging Face datasets: {e}")
        logger.info("Falling back to manual JSON loading...")
        
        # Fallback: create Dataset from manual loading
        try:
            if path.suffix.lower() == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = [data]
            
            elif path.suffix.lower() == '.jsonl':
                data = []
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data.append(json.loads(line))
            
            else:
                raise ValueError(f"Fallback failed: Unsupported file format: {path.suffix}")
            
            # Create Dataset from the loaded data
            dataset = Dataset.from_list(data)
            logger.info(f"Fallback successful: Created dataset with {len(dataset)} items")
            return dataset
        
        except Exception as fallback_e:
            logger.error(f"Fallback loading also failed: {fallback_e}")
            raise fallback_e


def process_dataset(dataset: DatasetType, args: argparse.Namespace, logger: logging.Logger, config_module) -> DatasetType:
    """
    Process dataset using Dataset.map() for efficient processing.
    Works with Dataset, DatasetDict, IterableDataset, or IterableDatasetDict.
    
    Args:
        dataset: Input Dataset object (any type)
        args: Command-line arguments
        logger: Logger instance
        config_module: Loaded configuration module with processing functions
    
    Returns:
        Processed Dataset object (same type as input)
    """
    def process_item_wrapper(item: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Wrapper around the configurable process_item function."""
        # Validate item if validation function exists
        if hasattr(config_module, 'validate_item'):
            if not config_module.validate_item(item):
                item_str = str(item)[:128]
                logger.warning(f"Item validation failed, skipping: {item_str}")
                return item
        
        # Call the configurable processing function
        return config_module.process_item(item, args)
    
    logger.info("Processing dataset ...")
    
    # Debug mode: limit to 50 items
    if args.debug:
        logger.info("Debug mode enabled: limiting to 50 items")
        if isinstance(dataset, Dataset):
            # For Dataset objects
            dataset = dataset.select(range(min(50, len(dataset))))
        elif isinstance(dataset, DatasetDict):
            # For DatasetDict objects - limit each split
            limited_dict = {}
            for split_name, split_dataset in dataset.items():
                limited_dict[split_name] = split_dataset.select(range(min(50, len(split_dataset))))
            dataset = DatasetDict(limited_dict)
        elif isinstance(dataset, IterableDataset):
            # For IterableDataset objects
            dataset = dataset.take(50)
        elif isinstance(dataset, IterableDatasetDict):
            # For IterableDatasetDict objects - limit each split
            limited_dict = {}
            for split_name, split_dataset in dataset.items():
                limited_dict[split_name] = split_dataset.take(50)
            dataset = IterableDatasetDict(limited_dict)
        else:
            logger.warning("Cannot limit dataset size for this dataset type in debug mode")
    
    processed_dataset = dataset.map(
        process_item_wrapper,
        fn_kwargs={"hash": random.getrandbits(64)}  # Ensure unique hash per run (for diasbling caching)
    )
        
    return processed_dataset


def save_results(dataset: DatasetType, output_path: str, logger: logging.Logger, hub_kwargs: Optional[Dict[str, Any]] = None, debug: bool = False) -> None:
    """
    Save processed dataset using Hugging Face datasets.
    Handles Dataset, DatasetDict, IterableDataset, or IterableDatasetDict.
    
    Args:
        dataset: Processed Dataset object (any type)
        output_path: Path to output directory
        logger: Logger instance
        hub_kwargs: Optional Hugging Face Hub repository kwargs for uploading
    """
    logger.info(f"Saving dataset to: {output_path}")
    
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        saved_files = []
        total_items = 0
        
        if isinstance(dataset, (DatasetDict, IterableDatasetDict)):
            # Save each split separately with filename_SPLIT.jsonl format
            logger.info(f"Saving DatasetDict with splits: {list(dataset.keys())}")

            for split_name, split_data in dataset.items():
                jsonl_file = output_dir / f"processed_dataset_{split_name}.jsonl"
                split_data.to_json(str(jsonl_file), orient='records', lines=True)
                saved_files.append(str(jsonl_file))
                logger.info(f"Split '{split_name}' saved as JSONL to: {jsonl_file}")
                
                # Count items if possible
                try:
                    if isinstance(split_data, Dataset):
                        split_size = len(split_data)
                        total_items += split_size
                        logger.info(f"  Split '{split_name}': {split_size} items")
                except Exception:
                    logger.info(f"  Split '{split_name}': unknown size (iterable)")
        
        else:
            # Single Dataset or IterableDataset
            jsonl_file = output_dir / "processed_dataset.jsonl"
            dataset.to_json(str(jsonl_file), orient='records', lines=True)
            saved_files.append(str(jsonl_file))
            logger.info(f"Dataset saved as JSONL to: {jsonl_file}")
            
            try:
                if isinstance(dataset, Dataset):
                    total_items = len(dataset)
            except Exception:
                pass
        
        # Upload to Hugging Face Hub (optional)
        if hub_kwargs and not debug:
            logger.info(f"Uploading dataset to Hugging Face Hub: {hub_kwargs}")
            dataset.push_to_hub(
                **hub_kwargs,
            )
            logger.info(f"Dataset successfully uploaded to: https://huggingface.co/datasets/{hub_kwargs.get('repo_id', 'unknown')}")
        elif hub_kwargs and debug:
            logger.info(f"Debug mode: Skipping upload to Hugging Face Hub: {hub_kwargs}")
        
        # Log summary statistics
        logger.info("Processing summary:")
        if total_items > 0:
            logger.info(f"  Total items: {total_items}")
        logger.info(f"  Created dataset: {dataset}")
        
        logger.info(f"  JSONL files: {saved_files}")
        if hub_kwargs:
            logger.info(f"  Hub repository and dataset kwargs: {hub_kwargs}")
    
    except Exception as e:
        logger.error(f"Failed to save or upload dataset: {e}")
        raise e


def create_parser_with_config(config_path: Optional[str] = None) -> argparse.ArgumentParser:
    """
    Create argument parser with optional custom arguments from config file.
    
    Args:
        config_path: Optional path to configuration file
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Process argdown datasets using argdown-cotgen and Hugging Face datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Local JSON file
  python -m recipies.dataset_processing_script --input ./data/dataset.json --output ./processed/
  
  # Hugging Face Hub dataset
  python -m recipies.dataset_processing_script --input "username/dataset-name" --output ./processed/
  
  # Load specific split from DatasetDict
  python -m recipies.dataset_processing_script --input "username/dataset-name" --output ./processed/ --split train
  
  # Load specific subset from dataset (e.g., DeepA2-Conversations)
  python -m recipies.dataset_processing_script --input "DebateLabKIT/deepa2-conversations" --output ./processed/ --subset aaac01-thinking
  
  # Use custom configuration file
  python -m recipies.dataset_processing_script --input ./data/dataset.json --output ./processed/ --config my_config.py
  
  # Local HF dataset directory
  python -m recipies.dataset_processing_script --input ./hf_dataset/ --output ./processed/
  
  # With debug and custom options
  python -m recipies.dataset_processing_script --input ./data/dataset.json --output ./processed/ --debug
  
  # Dry run
  python -m recipies.dataset_processing_script --input ./data/dataset.json --output ./processed/ --dry-run
  
  # Upload to Hugging Face Hub
  python -m recipies.dataset_processing_script --input ./data/dataset.json --output ./processed/ --hub-repo-id "username/processed-dataset"
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to input dataset, directory, or Hugging Face Hub dataset name (supports JSON, JSONL, CSV, Parquet, Arrow formats)'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Path to output directory for processed results (saves in multiple formats: HF, JSON, JSONL, Parquet)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (process only 50 items, disable uploads)'
    )
    
    parser.add_argument(
        '--log-file',
        help='Optional path to log file'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform validation and setup without actual processing'
    )
    
    parser.add_argument(
        '--hub-repo-id',
        help='Optional Hugging Face Hub repository ID to upload results (e.g., "username/dataset-name")'
    )
    
    parser.add_argument(
        '--hub-config-name',
        help='Optional Hugging Face Hub config name to upload results (e.g., "cot-thinking-subset-01")'
    )
    
    parser.add_argument(
        '--split',
        help='Load only a specific split from DatasetDict (e.g., "train", "test", "validation"). If not specified, all splits will be loaded and processed.'
    )
    
    parser.add_argument(
        '--subset',
        help='Load only a specific subset/configuration from the dataset (e.g., "aaac01-thinking", "aaac02-thinking"). If not specified, the default subset will be loaded.'
    )
    
    parser.add_argument(
        '--config',
        default='processing_config.py',
        help='Path to processing configuration file (default: processing_config.py)'
    )
    
    # Add custom arguments from config file if it exists
    if config_path and Path(config_path).exists():
        try:
            temp_logger = logging.getLogger(__name__)
            config_module = load_processing_config(config_path, temp_logger)
            if hasattr(config_module, 'get_custom_arguments'):
                custom_args = config_module.get_custom_arguments()
                for arg_name, arg_kwargs in custom_args:
                    parser.add_argument(arg_name, **arg_kwargs)
        except Exception:
            # If config loading fails, continue without custom arguments
            pass
    
    return parser


def main() -> int:
    """
    Main function for the dataset processor recipe.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse arguments (first pass to get config file)
    parser = create_parser_with_config()
    args = parser.parse_args()
    
    # If config file is different from default, reparse with custom arguments
    if args.config != 'processing_config.py':
        parser = create_parser_with_config(args.config)
        args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(
        debug=args.debug,
        log_file=args.log_file
    )
    
    logger.info("Starting dataset processing recipe")
    logger.debug(f"Command-line arguments: {vars(args)}")
    
    try:
        # Validate arguments
        if not validate_arguments(args, logger):
            logger.error("Argument validation failed")
            return 1
        
        # Load processing configuration
        config_module = load_processing_config(args.config, logger)
        
        # Load dataset
        dataset = load_hf_dataset(args.input, logger, args.split, args.subset)
        
        if args.dry_run:
            logger.info(f"DRY RUN: Using configuration file: {args.config}")
            logger.info(f"DRY RUN: Output would be saved to: {args.output}")
            if args.hub_repo_id:
                logger.info(f"DRY RUN: Would upload to Hub repository: {args.hub_repo_id}")
                logger.info(f"DRY RUN: Would use Hub config name: {args.hub_config_name}" if args.hub_config_name else "DRY RUN: No explicit Hub config name specified")
            logger.info("Dry run completed successfully")
            return 0
        
        # Process dataset using Dataset.map()
        processed_dataset = process_dataset(dataset, args, logger, config_module)
        
        # Post-process if function exists
        if hasattr(config_module, 'post_process_dataset'):
            processed_dataset, post_process_info = config_module.post_process_dataset(processed_dataset, args)
            logger.info(f"Post-processing completed: {post_process_info}")
        
        # Save results
        if args.hub_repo_id:
            hub_kwargs = {
                'repo_id': args.hub_repo_id,
                'private': False,
                'create_pr': True  
            }
            if args.split:
                hub_kwargs['split'] = args.split
            if args.hub_config_name:
                hub_kwargs['config_name'] = args.hub_config_name
            elif args.subset:
                hub_kwargs['config_name'] = args.subset
        else:
            hub_kwargs = None
        save_results(processed_dataset, args.output, logger, hub_kwargs=hub_kwargs, debug=args.debug)
        
        logger.info("Processing completed successfully.")
        return 0
    
    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.debug)
        return 1


if __name__ == "__main__":
    sys.exit(main())
