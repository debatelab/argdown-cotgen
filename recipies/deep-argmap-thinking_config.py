#!/usr/bin/env python3
"""
Processing Configuration for Deep-Argmap-Conversations Dataset

Input dataset: 
- DebateLabKIT/deep-argmap-conversations
- Subsets: synthetic_corpus-001

This module defines the processing function that will be applied to each chat
item in the conversational dataset. Specifically, we target the last assistant 
message in the chat which contains an Argdown snippet. Per default, we will extract
the first argdown snippet from that message and assume that it contains an argument 
map. This map will be processed with one of the following strategies: "by_rank", 
"breadth_first", "depth_first", "by_objection", "random_diffusion", "depth_diffusion".
The resulting CoT trace will be used as thinking field of the assistant message in
the processed chat item.

However, two tasks need special attention:

* `ExtractArgumentTask`: The argdown snippet in the assistant message is an Argument
  (premise-conclusion structure). We will extract it and transform it with one of
  "by_rank", "by_feature".
* `ReconstructAllArgumentsTask`: The last assistant message contains two Argdown snippets
  (with metadata after code identifier). We assume: The first snippet is an argument map, 
  the second one contains argument reconstructions. To construct the thinking field of 
  the assistant message, we (a) transform the argument map with one of "by_rank", 
  "breadth_first", "depth_first", "by_objection", "random_diffusion", "depth_diffusion";
  (b) add finally the complete 2nd snippet with all the reconstructed arguments.

Usage:

```bash
uv run hf auth login
uv run python -m recipies.dataset_processing_script \
    --config "recipies/deep-argmap-thinking_config.py" \
    --input "DebateLabKIT/deep-argmap-conversations" \
    --subset "synthetic_corpus-001" \
    --output "./test_output" \
    --hub-repo-id "DebateLabKIT/argunauts-thinking" \
    --hub-config-name "deep-argmap-synthetic_corpus-001-thinking" \
    --debug \

uv run python -m recipies.dataset_processing_script \
    --config "recipies/deep-argmap-thinking_config.py" \
    --input "DebateLabKIT/deep-argmap-conversations" \
    --subset "synthetic_corpus-001" \
    --output "./test_output" \
    --dry-run \
    --debug
```

Example input item:
[
  {
    "content": "Please reconfigure the provided list of opposing reasons into a visual argument map, utilizing the Argdown syntax to facilitate a clearer representation of the arguments and their dialectic relations.

    pros and cons:
    ```argdown    
    [AI Stifles Young Minds]: Implementing artificial intelligence in education undermines critical thinking and creativity.    
      + [Automated Insights]: Relying on artificial intelligence in education can lead to students memorizing automated responses rather than developing their own critical thinking skills.    
      - [Tech for Exploration]: Artificial intelligence in education can be used to create interactive and immersive learning experiences that foster student-led inquiry and discovery, rather than merely providing automated responses.    
      <- [Contextual Learning]: AI-powered educational tools can offer context-dependent guidance and feedback that encourages students to think creatively and develop problem-solving skills, rather than merely relying on automated responses.    
      - [Simulated Realities]: Artificial intelligence can create simulated environments that mimic real-world situations, allowing students to explore and interact with complex concepts in a controlled and safe space.    
      - [Future-Proofing the Workforce:]: Developing problem-solving skills in students is crucial for preparing them to tackle the complex, dynamic challenges of the 21st-century job market.    
    ```",
    "role": "user"
  },
  {
    "content": "
    ```argdown    
    [AI Stifles Young Minds]: Implementing artificial intelligence in education undermines critical thinking and creativity.    
      <+ [Automated Insights]: Relying on artificial intelligence in education can lead to students memorizing automated responses rather than developing their own critical thinking skills.    
        <- [Tech for Exploration]: Artificial intelligence in education can be used to create interactive and immersive learning experiences that foster student-led inquiry and discovery, rather than merely providing automated responses.    
          <+ [Simulated Realities]: Artificial intelligence can create simulated environments that mimic real-world situations, allowing students to explore and interact with complex concepts in a controlled and safe space.    
        <- [Contextual Learning]: AI-powered educational tools can offer context-dependent guidance and feedback that encourages students to think creatively and develop problem-solving skills, rather than merely relying on automated responses.    
          <+ [Future-Proofing the Workforce:]: Developing problem-solving skills in students is crucial for preparing them to tackle the complex, dynamic challenges of the 21st-century job market.    
    ```",
    "role": "assistant"
  }
]

In this example, we'd apply argdown-cotgen to the following argdown snippet:

    ```argdown    
    [AI Stifles Young Minds]: Implementing artificial intelligence in education undermines critical thinking and creativity.    
      <+ [Automated Insights]: Relying on artificial intelligence in education can lead to students memorizing automated responses rather than developing their own critical thinking skills.    
        <- [Tech for Exploration]: Artificial intelligence in education can be used to create interactive and immersive learning experiences that foster student-led inquiry and discovery, rather than merely providing automated responses.    
          <+ [Simulated Realities]: Artificial intelligence can create simulated environments that mimic real-world situations, allowing students to explore and interact with complex concepts in a controlled and safe space.    
        <- [Contextual Learning]: AI-powered educational tools can offer context-dependent guidance and feedback that encourages students to think creatively and develop problem-solving skills, rather than merely relying on automated responses.    
          <+ [Future-Proofing the Workforce:]: Developing problem-solving skills in students is crucial for preparing them to tackle the complex, dynamic challenges of the 21st-century job market.    
    ```
    
"""

from typing import Dict, Any, List, Optional, Tuple
import argparse
import logging
import re
import random

from src.argdown_cotgen import CotGenerator

# Type alias
CodeSnippetRecord = Tuple[str, int, int, bool]

MAP_STRATEGY_WEIGHTS = {
    "by_rank": 1.0,
    "breadth_first": 0.5,
    "depth_first": 0.5,
    "by_objection": 1.0,
    "random_diffusion": 1.0,
    "depth_diffusion": 1.0,
}
ARGUMENT_STRATEGY_WEIGHTS = {
    "by_rank": 1.0,
    "by_feature": 1.0,
}

logger = logging.getLogger(__name__)


def _extract_all_argdown_snippets(input_text: str) -> List[CodeSnippetRecord]:
    """
    Extract all argdown code snippets and classify as containing premise-conclusion structure
    (with numbered propositions like (1), (2), (3), etc.) or not.

    Args:
        input_text: The text content of the "thinking" field

    Returns:
        List of tuples of (argdown_snippet, start_pos, end_pos, contains_premise_conclusion_structure)
    """
    if not input_text:
        logger.debug("No thinking text provided")
        return []

    logger.debug(f"Analyzing input text: {len(input_text)} characters")

    # Pattern to find argdown code blocks, allowing for optional metadata
    # such as ```argdown {file="myfile.ad"}
    argdown_pattern = r"```argdown(?:\s*\{.*?\})?\s*\n(.*?)\n```"

    # Find all argdown code blocks
    matches = list(re.finditer(argdown_pattern, input_text, re.DOTALL))
    logger.debug(f"Found {len(matches)} argdown code blocks")

    results: List[CodeSnippetRecord] = []

    for i, match in enumerate(matches):
        argdown_content = match.group(1).strip()
        logger.debug(f"Argdown block {i}: {len(argdown_content)} chars")
        contains_premises_conclusion = False  # default assumption

        # Check if this argdown snippet contains numbered propositions (premise-conclusion structure)
        # Look for patterns like (1), (2), (3), etc. at the beginning of lines
        # and ensure it contains at least (1) and (2)
        numbered_prop_pattern = r"^\s*\(\d+\)"
        numbered_props = re.findall(
            numbered_prop_pattern, argdown_content, re.MULTILINE
        )
        logger.debug(f"Found numbered props: {numbered_props}")

        if numbered_props:
            # Extract the numbers to check if we have at least (1) and (2)
            numbers = []
            for prop in numbered_props:
                match_num = re.search(r"\((\d+)\)", prop)
                if match_num:
                    numbers.append(int(match_num.group(1)))

            logger.debug(f"Extracted numbers: {numbers}")

            # Check if we have at least propositions (1) and (2)
            if 1 in numbers and 2 in numbers:
                logger.debug(
                    f"Found valid premise-conclusion structure with numbers: {numbers}"
                )
                contains_premises_conclusion = True
            else:
                logger.debug(
                    f"Insufficient numbered propositions - need (1) and (2), got: {numbers}"
                )

        results.append(
            (argdown_content, match.start(), match.end(), contains_premises_conclusion)
        )

    logger.debug(f"Identified: {len(results)} argdown code block(s). contains_premises_conclusion: {[c for _,_,_,c in results]}")

    return results


def _extract_argdown_from_chat(
    item: Dict[str, Any],
) -> Tuple[List[CodeSnippetRecord], Optional[Dict[str, Any]]]:
    """
    Extract all argdown code snippets to target from the last assistant message.

    Args:
        item: Dataset item with messages field containing a chat history

    Returns:
        Tuple of [List[CodeSnippets], source_assistant_msg]
    """
    # TODO: needs to be revised

    messages: List[Dict[str, Any]] = item.get("messages", [])
    task = item.get("task", "unknown")

    logger.debug(f"[{task}] Processing {len(messages)} messages")

    for message in reversed(messages):
        # Check if this is an assistant message with thinking
        role = message.get("role", "")
        content = message.get("content", "")

        if role == "assistant" and content:
            argdown_records = _extract_all_argdown_snippets(content)
            if argdown_records:
                return argdown_records, message

    logger.debug(f"[{task}] No argdown code found in any assistant msg")
    return [], None


def _process_item_default_task(
    processed_item: Dict[str, Any],
    args: argparse.Namespace,
    argdown_records: List[CodeSnippetRecord],
    target_ass_msg: Dict[str, Any],
) -> Dict[str, Any]:
    argdown_snippet = next(
        (snippet for snippet, _, _, has_pc in argdown_records if not has_pc), None
    )
    if not argdown_snippet:
        logger.debug(
            f"No argdown snippet found in item: {processed_item.get('task', 'unknown')}. Returning unprocessed item."
        )
        return processed_item

    try:
        # Randomly select strategy for each item

        strategies, weights = zip(*MAP_STRATEGY_WEIGHTS.items())
        selected_strategy = random.choices(strategies, weights=weights, k=1)[0]

        # Create generator with selected strategy
        generator = CotGenerator(pipe_type=selected_strategy)

        # Process the argdown snippet
        argdown_cot = generator(argdown_snippet, abortion_rate=args.abortion_rate)

        # Update the thinking field in the processed item
        updated_item = _update_thinking_in_assistant_message(
            processed_item, target_ass_msg, argdown_cot
        )

        if args.debug:
            logger.info(
                f"Successfully processed item {processed_item.get('task', 'unknown')} with strategy {selected_strategy}"
            )
            logger.debug(f"CoT preview: {argdown_cot[:128]}")

        return updated_item

    except Exception as e:
        logger.warning(
            f"Error processing item with {processed_item.get('task', 'unknown')}: {str(e)}"
        )
        logger.debug("Returning unprocessed item.")
        # Return original item if processing fails
        return processed_item


def _process_item_extract_argument_task(
    processed_item: Dict[str, Any],
    args: argparse.Namespace,
    argdown_records: List[CodeSnippetRecord],
    target_ass_msg: Dict[str, Any],
) -> Dict[str, Any]:
    argdown_snippet = next(
        (snippet for snippet, _, _, has_pc in argdown_records if has_pc), None
    )
    if not argdown_snippet:
        logger.debug(
            f"No premise-conclusion argdown found in item: {processed_item.get('task', 'unknown')}. Returning unprocessed item."
        )
        return processed_item

    try:
        # Randomly select strategy for each item

        strategies, weights = zip(*ARGUMENT_STRATEGY_WEIGHTS.items())
        selected_strategy = random.choices(strategies, weights=weights, k=1)[0]

        # Create generator with selected strategy
        generator = CotGenerator(pipe_type=selected_strategy)

        # Process the argdown snippet
        argdown_cot = generator(argdown_snippet, abortion_rate=args.abortion_rate)

        # Update the thinking field in the processed item
        updated_item = _update_thinking_in_assistant_message(
            processed_item, target_ass_msg, argdown_cot
        )

        if args.debug:
            logger.info(
                f"Successfully processed item {processed_item.get('task', 'unknown')} with strategy {selected_strategy}"
            )
            logger.debug(f"CoT preview: {argdown_cot[:128]}")

        return updated_item

    except Exception as e:
        logger.warning(
            f"Error processing item with {processed_item.get('task', 'unknown')}: {str(e)}"
        )
        logger.debug("Returning unprocessed item.")
        # Return original item if processing fails
        return processed_item


def _process_item_reconstruct_all_arguments_task(
    processed_item: Dict[str, Any],
    args: argparse.Namespace,
    argdown_records: List[CodeSnippetRecord],
    target_ass_msg: Dict[str, Any],
) -> Dict[str, Any]:
    argdown_snippet_map = next(
        (snippet for snippet, _, _, has_pc in argdown_records if not has_pc), None
    )
    if not argdown_snippet_map:
        logger.debug(
            f"No premise-conclusion argdown found in item: {processed_item.get('task', 'unknown')}. Returning unprocessed item."
        )
        return processed_item
    argdown_snippet_pcs = next(
        (snippet for snippet, _, _, has_pc in argdown_records if has_pc), None
    )
    if not argdown_snippet_pcs:
        logger.debug(
            f"No premise-conclusion argdown found in item: {processed_item.get('task', 'unknown')}. Returning unprocessed item."
        )
        return processed_item

    try:
        # Randomly select strategy for each item

        strategies, weights = zip(*MAP_STRATEGY_WEIGHTS.items())
        selected_strategy = random.choices(strategies, weights=weights, k=1)[0]

        # Create generator with selected strategy
        generator = CotGenerator(pipe_type=selected_strategy)

        # Process the argdown map snippet
        argdown_cot = generator(argdown_snippet_map, abortion_rate=args.abortion_rate)

        # Finally append the reconstruction
        explanation = random.choice(
            [
                "So I can finally do:",
                "I am now ready to analyse the arguments.",
                "I will now reconstruct the arguments.",
                "Let us consider the individual arguments now.",
                "To complete the assignemnt, let me finally consider:",
            ]
        )
        argdown_cot = (
            f"{argdown_cot}\n\n{explanation}\n\n```argdown{argdown_snippet_pcs}```"
        )

        # Update the thinking field in the processed item
        updated_item = _update_thinking_in_assistant_message(
            processed_item, target_ass_msg, argdown_cot
        )

        if args.debug:
            logger.info(
                f"Successfully processed item {processed_item.get('task', 'unknown')} with strategy {selected_strategy}"
            )
            logger.debug(f"CoT preview: {argdown_cot[:128]}")

        return updated_item

    except Exception as e:
        logger.warning(
            f"Error processing item with {processed_item.get('task', 'unknown')}: {str(e)}"
        )
        logger.debug("Returning unprocessed item.")
        # Return original item if processing fails
        return processed_item


def process_item(item: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Process a single item from the dataset.

    This function:
    1. Extracts all argdown code snippets, classified as map/arg, from assistant msg
    2. Builds a thinking trace, depending on task type (default / `ExtractArgumentTask` /
       `ReconstructAllArgumentsTask`)
    4. Add the generated CoT chain as thinking field to target assistant message.

    Args:
        item: A single item from the dataset (dictionary)
        args: Command-line arguments from argparse.Namespace
              Available args include:
              - args.dry_run: Boolean indicating if this is a dry run
              - args.debug: Boolean indicating debug mode
              - args.abortion_rate: Rate for introducing abortions (0.0 to 1.0)

    Returns:
        Dictionary containing the processed item
    """
    # Create a copy of the original item
    processed_item = {**item}

    # Extract argdown snippets and target assistant msg from chat
    argdown_records, target_ass_msg = _extract_argdown_from_chat(item)

    if not argdown_records:
        logger.debug(
            f"No argdown snippets found in item: {item.get('task', 'unknown')}"
        )
        return processed_item
    if target_ass_msg is None:
        logger.debug(
            f"Failed to identify target ass msg in item: {item.get('task', 'unknown')}"
        )
        return processed_item

    task = item.get("task")

    if args.dry_run:
        logger.info(
            f"Would process {len(argdown_records)} argdown snippets in item with task {task}"
        )
        return processed_item

    if task == "ExtractArgumentTask":
        return _process_item_extract_argument_task(
            processed_item, args, argdown_records, target_ass_msg
        )
    elif task == "ReconstructAllArgumentsTask":
        return _process_item_reconstruct_all_arguments_task(
            processed_item, args, argdown_records, target_ass_msg
        )

    # default
    return _process_item_default_task(
        processed_item, args, argdown_records, target_ass_msg
    )


def _update_thinking_in_assistant_message(
    item: Dict[str, Any], target_ass_msg: Dict[str, Any], new_thinking_text: str
) -> Dict[str, Any]:
    """
    Update the "thinking" field in the first assistant message.

    Args:
        item: Dataset item with messages structure
        new_thinking_text: New content for the thinking field

    Returns:
        Updated dataset item
    """
    messages: list = item.get("messages", [])

    if target_ass_msg not in messages:
        logger.warning(
            "Target assistant msg not in chat history. Cannot update thinking field."
        )
        logger.debug(f"chat: {messages}, ass_msg: {target_ass_msg}")

    target_idx = messages.index(target_ass_msg)
    message = messages[target_idx]
    if isinstance(message, dict):
        if message.get("role") == "assistant":
            # Create a copy and update
            item["messages"][target_idx] = {**message, "thinking": new_thinking_text}
            return item
    else:
        logger.warning(f"Invalid msg format: {message}. Cannot update thinking field.")

    return item


def get_custom_arguments() -> list:
    """
    Define any custom command-line arguments specific to your processing.

    Returns:
        List of tuples, each containing arguments for parser.add_argument()
        Format: [('--arg-name', {'help': 'description', 'type': str, 'default': 'value'}), ...]
    """
    return [
        (
            "--abortion-rate",
            {
                "type": float,
                "default": 0.03,
                "help": "Rate for introducing abortions/errors in processing (0.0 to 1.0)",
            },
        )
    ]


def validate_item(item: Dict[str, Any]) -> bool:
    """
    Validate that an item has the required fields for processing.

    Args:
        item: A single item from the dataset

    Returns:
        True if item is valid, False otherwise
    """
    # Check for required fields
    if "task" not in item:
        return False

    # Check for required fields
    if "messages" not in item:
        return False

    messages = item["messages"]

    # Check that messages is a list
    if not isinstance(messages, list):
        return False

    # Check that all messages are dicts
    if not all(isinstance(msg, Dict) for msg in messages):
        return False

    # Check that there are no thiking fields
    # (we will build them from scratch and don't mean to overwrite any)
    if any(msg.get("thinking") for msg in messages):
        return False

    return True


def post_process_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post-process a single item from the dataset.

    This function converts all messages in the item to dictionary format.

    Args:
        item: A single item from the dataset (dictionary)

    Returns:
        Dictionary containing the processed item
    """
    processed_item = {**item}

    # TODO: remove
    # messages = item.get('messages', [])
    # processed_messages = [message_to_dict(msg) for msg in messages]
    #
    # processed_item['messages'] = processed_messages

    return processed_item


def post_process_dataset(dataset, args: argparse.Namespace) -> Tuple[Any, dict]:
    """
    Perform any post-processing on the entire dataset after individual item processing.

    See also: https://huggingface.co/docs/transformers/main/chat_templating_writing#writing-a-chat-template

    Args:
        dataset: The processed dataset
        args: Command-line arguments

    Returns:
        Dataset ready for chat templates, Dictionary with any additional metadata or statistics
    """

    # # apply post_process_item to each item
    # if not hasattr(dataset, "map"):
    #     raise ValueError("Dataset does not support 'map' method")
    # dataset = dataset.map(post_process_item)

    # Calculate statistics
    total_items = len(dataset)
    processed_items = sum(1 for item in dataset if "processing_metadata" in item)

    strategies_used: Dict[str, int] = {}
    if processed_items > 0:
        for item in dataset:
            if "processing_metadata" in item:
                strategy = item["processing_metadata"].get("strategy_used", "unknown")
                strategies_used[strategy] = strategies_used.get(strategy, 0) + 1

    return dataset, {
        "total_items": total_items,
        "processed_items": processed_items,
        "skipped_items": total_items - processed_items,
        "processing_rate": processed_items / total_items if total_items > 0 else 0.0,
        "strategies_used": strategies_used,
        "config_used": {"debug": args.debug, "dry_run": args.dry_run},
    }
