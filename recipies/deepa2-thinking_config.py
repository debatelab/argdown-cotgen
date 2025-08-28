#!/usr/bin/env python3
"""
Processing Configuration for DeepA2-Conversations Thinking-Dataset

Input dataset: 
- DebateLabKIT/deepa2-conversations
- Subsets: aaac01-thinking, aaac02-thinking, aaac03-thinking, folly-thinking

This module defines the processing function that will be applied to each chat
item in the conversational dataset. Specifically, we target the "thinking" field
of the first assistant message and transform the first argdown code snippet that 
includes a premise conclusion structure. 

Usage:

```bash
uv run hf auth login
uv run python -m recipies.dataset_processing_script \
    --config "recipies/deepa2-thinking_config.py" \
    --input "DebateLabKIT/deepa2-conversations" \
    --subset "aaac01-thinking" \
    --output "./test_output" \
    --hub-repo-id "DebateLabKIT/argunauts-thinking" \
    --hub-config-name "deepa2-aaac01-thinking" \
    --debug \
```

Example input item:
{
    "source_id": "aaac01-thinking-0001",
    "messages":
    [
        [
            [
                "role",
                "system"
            ],
            [
                "content",
                "You are an AI expert for logical analysis of natural language argumentation. You use available tools to support your analyses."
            ],
            [
                "thinking",
                null
            ],
            [
                "tools",
                "[]"
            ]
        ],
        [
            [
                "role",
                "user"
            ],
            [
                "content",
                "Instruction: Formalize the argument and rebuild its inferential structure in Z3 to demonstrate that the premises (1) (2) (3) (5) logically entail the conclusion. You may ignore the argument's intermediate conclusions for this purpose.
                Try to create a SMT program to check global validity of all inferences from the following argumentative text:
                Ladies and gentlemen, today I'd like to talk about something that's been on everyone's minds lately: tax policies. There's been a lot of debate about whether raising corporate tax by 10 percent is a viable option, and I'd like to shed some light on that.
                
                Now, I know some of you might be thinking, \"But what about raising corporate tax rates by 40 percent? The Fed has criticized that idea.\" And yes, that's true. However, it's also important to note that raising corporate tax by 20 percent hasn't been denounced by the Center for Automotive Research. 
                
                But here's the thing: some organizations think that raising inheritance tax by 10 percent is a bad idea. The Cato Institute has criticized this policy, and the Berggruen Institute has even called it \"financially insane.\" On the other hand, the Center for National Policy and George Soros think that raising inheritance tax by 40 percent is a great idea and shouldn't be postponed.
                
                Now, back to corporate tax. The Bipartisan Policy Center thinks that raising corporate tax by 40 percent is morally required, but George Bush strongly disagrees. And if we look at income tax, the International Union of Operating Engineers thinks that raising it by 15 percent should be postponed.
                
                But what about raising corporate tax rates by 10 percent? The Fed hasn't evaluated this option recently, and the Center for American Progress hasn't criticized it. So, what does this all mean?
                
                Well, it seems that if a policy isn't supported by Bill Clinton or the International Union of Operating Engineers, it's unlikely to be criticized by the Cato Institute or evaluated by the United Auto Workers. And if the Bipartisan Policy Center thinks that raising corporate tax by 40 percent is morally obligatory, then the Fed will likely criticize it.
                
                In conclusion, raising corporate tax by 40 percent is a measure that's both morally required and strongly opposed, depending on who you ask. The Bipartisan Policy Center and George Bush have very different opinions on this matter."
            ],
            [
                "thinking",
                null
            ]
        ],
        [
            [
                "role",
                "assistant"
            ],
            [
                "content",
                "```
                (declare-sort Universal)
                (declare-fun p () Bool) ;; raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally required
                (declare-fun q () Bool) ;; raising corporate tax by 40 percent is a measure which George Bush strictly opposes
                (declare-fun r () Bool) ;; raising corporate tax by 40 percent is a policy criticized by the Fed
                (declare-fun s () Bool) ;; raising corporate tax by 10 percent is a policy option recently evaluated by the Center for Governmental Research
                (define-fun premise1 () Bool (or p q))
                (define-fun premise2 () Bool (=> p r))
                (define-fun premise3 () Bool (=> q r))
                (define-fun premise5 () Bool (=> r (not s)))
                (define-fun conclusion6 () Bool (not s))
                (define-fun argument () Bool (=> (and premise1 premise2 premise3 premise5) conclusion6))
                (assert (not argument))
                (check-sat)
                ```"
            ],
            [
                "thinking",
                "Alright, here's a preliminary plan to tackle this issue and create a SMT program to check global validity of all inferences:
                
                Step 1: Summarize the argument's gist
                Step 2: Reconstruct the argument in argdown format (premise conclusion structure)
                Step 3: Formalize the premises
                Step 4: Provide placeholder keys (substitutions)
                Step 5: Formalize the main conclusion
                Step 6: Reconstruct the argument in standard form (Argdown) with title and gist
                Step 7: Reconstruct the argument in Argdown syntax including logical formalizations
                Step 8: Create a SMT program to check global validity of all inferences
                
                ## Step 1: Summarize the argument's gist
                
                If I had one line to summarize the argument, what would I say?
                
                The argument's gist is: Raising corporate tax by 10 percent is not a policy option recently evaluated by the Center for Governmental Research.
                
                ## Step 2: Reconstruct the argument in argdown format (premise conclusion structure)
                
                I transform the argument into a well-defined, premise-conclusion structure using argdown, identifying any assumptions made.
                
                The argument can be reconstructed as follows:
                
                ```argdown
                (1) Raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally obligatory or raising corporate tax by 40 percent is a measure which George Bush strictly opposes.
                (2) If raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally obligatory, then raising corporate tax by 40 percent is criticized by the Fed.
                (3) If raising corporate tax by 40 percent is a measure which George Bush strictly opposes, then raising corporate tax by 40 percent is criticized by the Fed.
                --
                with case analysis from (1) (2) (3)
                --
                (4) Raising corporate tax by 40 percent is criticized by the Fed.
                (5) If raising corporate tax by 40 percent is criticized by the Fed, then raising corporate tax by 10 percent is not a policy option recently evaluated by the Center for Governmental Research.
                --
                with modus ponens [negation variant] from (4) (5)
                --
                (6) Raising corporate tax by 10 percent is not a policy option recently evaluated by the Center for Governmental Research.
                ```
                
                ## Step 3: Formalize the premises
                
                I will formalize the argument's sentences (1) (2) (3) (5). I'll use deepa2 syntax.
                
                The premises can be formalized as follows:
                Premise (1): p v q
                Premise (2): p -> r
                Premise (3): q -> r
                Premise (5): r -> not s
                
                ## Step 4: Provide placeholder keys (substitutions)
                
                I plan to provide a list of keys that map symbols used in logical formulae to the corresponding terms they denote. I'll include any symbols I have used so far or may need in the further logical analysis.
                
                - `p` denotes: raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally required
                - `q` denotes: raising corporate tax by 40 percent is a measure which George Bush strictly opposes
                - `r` denotes: raising corporate tax by 40 percent is a policy criticized by the Fed
                - `s` denotes: raising corporate tax by 10 percent is a policy option recently evaluated by the Center for Governmental Research
                
                ## Step 5: Formalize the main conclusion
                
                I will formalize the argument's conclusion using deepa2 syntax .
                
                Formalization of conclusion (6): not s
                
                ## Step 6: Reconstruct the argument in standard form (Argdown) with title and gist
                
                I will reformulate the argument in argdown, specifying all premises and conclusions, include the argument's title and gist, and use standard conventions to describe inferences if applicable.
                
                The argument can be reconstructed as follows:
                
                ```argdown
                <Raising corporate tax>: Raising corporate tax by 10 percent is not a policy option recently evaluated by the Center for Governmental Research.
                
                (1) Raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally obligatory or raising corporate tax by 40 percent is a measure which George Bush strictly opposes.
                (2) If raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally obligatory, then raising corporate tax by 40 percent is criticized by the Fed.
                (3) If raising corporate tax by 40 percent is a measure which George Bush strictly opposes, then raising corporate tax by 40 percent is criticized by the Fed.
                --
                with case analysis from (1) (2) (3)
                --
                (4) Raising corporate tax by 40 percent is criticized by the Fed.
                (5) If raising corporate tax by 40 percent is criticized by the Fed, then raising corporate tax by 10 percent is not a policy option recently evaluated by the Center for Governmental Research.
                --
                with modus ponens [negation variant] from (4) (5)
                --
                (6) Raising corporate tax by 10 percent is not a policy option recently evaluated by the Center for Governmental Research.
                ```
                
                ## Step 7: Reconstruct the argument in Argdown syntax including logical formalizations
                
                I plan to incorporate detailed logical formalizations into the argdown argument reconstruction by including them as inline YAML data for each proposition. I'll specify the logical formula and the placeholders used, and maintain consistent key usage when formalizing different propositions.
                
                Let me include logical formalizations and keys:
                
                ```argdown
                (1) Raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally obligatory or raising corporate tax by 40 percent is a measure which George Bush strictly opposes. {\"formalization\": \"p v q\", \"keys\": {\"p\": \"raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally required\", \"q\": \"raising corporate tax by 40 percent is a measure which George Bush strictly opposes\"}}
                (2) If raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally obligatory, then raising corporate tax by 40 percent is criticized by the Fed. {\"formalization\": \"p -> r\", \"keys\": {\"p\": \"raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally required\", \"r\": \"raising corporate tax by 40 percent is a policy criticized by the Fed\"}}
                (3) If raising corporate tax by 40 percent is a measure which George Bush strictly opposes, then raising corporate tax by 40 percent is criticized by the Fed. {\"formalization\": \"q -> r\", \"keys\": {\"q\": \"raising corporate tax by 40 percent is a measure which George Bush strictly opposes\", \"r\": \"raising corporate tax by 40 percent is a policy criticized by the Fed\"}}
                -----
                (4) Raising corporate tax by 40 percent is criticized by the Fed. {\"formalization\": \"r\", \"keys\": {}, \"follows_from\": [1, 2, 3]}
                (5) If raising corporate tax by 40 percent is criticized by the Fed, then raising corporate tax by 10 percent is not a policy option recently evaluated by the Center for Governmental Research. {\"formalization\": \"r -> not s\", \"keys\": {\"r\": \"raising corporate tax by 40 percent is a policy criticized by the Fed\", \"s\": \"raising corporate tax by 10 percent is a policy option recently evaluated by the Center for Governmental Research\"}}
                -----
                (6) Raising corporate tax by 10 percent is not a policy option recently evaluated by the Center for Governmental Research. {\"formalization\": \"not s\", \"keys\": {\"s\": \"raising corporate tax by 10 percent is a policy option recently evaluated by the Center for Governmental Research\"}, \"follows_from\": [4, 5]}
                ```
                
                ## Step 8: Create a SMT program to check global validity of all inferences
                
                I will formalize the argument and rebuild its inferential structure in Z3 to demonstrate that the premises (1) (2) (3) (5) logically entail the conclusion. I may ignore the argument's intermediate conclusions for this purpose.
                
                ```
                (declare-sort Universal)
                (declare-fun p () Bool) ;; raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally required
                (declare-fun q () Bool) ;; raising corporate tax by 40 percent is a measure which George Bush strictly opposes
                (declare-fun r () Bool) ;; raising corporate tax by 40 percent is a policy criticized by the Fed
                (declare-fun s () Bool) ;; raising corporate tax by 10 percent is a policy option recently evaluated by the Center for Governmental Research
                (define-fun premise1 () Bool (or p q))
                (define-fun premise2 () Bool (=> p r))
                (define-fun premise3 () Bool (=> q r))
                (define-fun premise5 () Bool (=> r (not s)))
                (define-fun conclusion6 () Bool (not s))
                (define-fun argument () Bool (=> (and premise1 premise2 premise3 premise5) conclusion6))
                (assert (not argument))
                (check-sat)
                ```"
            ]
        ]
    ]
}

In this example, we'd apply argdown-cotgen to the following argdown snippet:

    ```argdown
    (1) Raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally obligatory or raising corporate tax by 40 percent is a measure which George Bush strictly opposes.
    (2) If raising corporate tax by 40 percent is a measure which is, according to the Bipartisan Policy Center, morally obligatory, then raising corporate tax by 40 percent is criticized by the Fed.
    (3) If raising corporate tax by 40 percent is a measure which George Bush strictly opposes, then raising corporate tax by 40 percent is criticized by the Fed.
    --
    with case analysis from (1) (2) (3)
    --
    (4) Raising corporate tax by 40 percent is criticized by the Fed.
    (5) If raising corporate tax by 40 percent is criticized by the Fed, then raising corporate tax by 10 percent is not a policy option recently evaluated by the Center for Governmental Research.
    --
    with modus ponens [negation variant] from (4) (5)
    --
    (6) Raising corporate tax by 10 percent is not a policy option recently evaluated by the Center for Governmental Research.
    ```

    
"""

from typing import Dict, Any, List, Optional, Tuple
import argparse
import logging
import re
import random

from src.argdown_cotgen import CotGenerator

logger = logging.getLogger(__name__)


def extract_first_premise_conclusion_argdown(
    thinking_text: str,
) -> Optional[Tuple[str, int, int]]:
    """
    Extract the first argdown code snippet that contains a premise-conclusion structure
    (with numbered propositions like (1), (2), (3), etc.).

    Args:
        thinking_text: The text content of the "thinking" field

    Returns:
        Tuple of (argdown_snippet, start_pos, end_pos) if found, None otherwise
    """
    if not thinking_text:
        logger.debug("No thinking text provided")
        return None

    logger.debug(f"Analyzing thinking text: {len(thinking_text)} characters")

    # Pattern to find argdown code blocks
    argdown_pattern = r"```argdown\s*\n(.*?)\n```"

    # Find all argdown code blocks
    matches = list(re.finditer(argdown_pattern, thinking_text, re.DOTALL))
    logger.debug(f"Found {len(matches)} argdown code blocks")

    for i, match in enumerate(matches):
        argdown_content = match.group(1).strip()
        logger.debug(f"Argdown block {i}: {len(argdown_content)} chars")

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
                return (argdown_content, match.start(), match.end())
            else:
                logger.debug(
                    f"Insufficient numbered propositions - need (1) and (2), got: {numbers}"
                )
        else:
            logger.debug(f"No numbered propositions found in block {i}")

    logger.debug("No valid premise-conclusion argdown found")
    return None


def message_to_dict(message: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """
    Convert a message from list of [key, value] pairs to a dictionary.

    Args:
        message: Message in list format containing [key, value] pairs

    Returns:
        Dictionary representation of the message
    """
    if isinstance(message, dict):
        return message
    elif isinstance(message, list):
        result: Dict[str, Any] = {}

        # Each message is a list of [key, value] pairs
        # e.g., [["role", "system"], ["content", "You are an AI..."], ["thinking", null]]
        for pair in message:
            if isinstance(pair, list) and len(pair) == 2:
                key, value = pair
                result[key] = value
            else:
                logger.debug(f"Skipping non-pair item: {pair}")

        return result
    else:
        logger.warning(f"Unexpected message format: {type(message)}")
        return {}


def extract_thinking_from_assistant_message(item: Dict[str, Any]) -> Optional[str]:
    """
    Extract the "thinking" field from the first assistant message.

    Args:
        item: Dataset item with messages structure

    Returns:
        Content of thinking field if found, None otherwise
    """
    messages = item.get("messages", [])
    source_id = item.get("source_id", "unknown")

    logger.debug(f"[{source_id}] Processing {len(messages)} messages")

    for i, message in enumerate(messages):
        logger.debug(f"[{source_id}] Message {i}: type={type(message)}")

        # Convert message to dict using helper function
        msg_dict = message_to_dict(message)
        logger.debug(f"[{source_id}] Converted message keys: {list(msg_dict.keys())}")

        # Check if this is an assistant message with thinking
        role = msg_dict.get("role", "")
        thinking = msg_dict.get("thinking", None)

        logger.debug(
            f"[{source_id}] Role: {role}, Has thinking: {thinking is not None}"
        )

        if role == "assistant" and thinking is not None:
            logger.debug(
                f"[{source_id}] Found assistant thinking: {len(str(thinking))} chars"
            )
            return str(thinking) if thinking else None

    logger.debug(f"[{source_id}] No assistant thinking found")
    return None


def process_item(item: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Process a single item from the dataset.

    This function:
    1. Extracts the "thinking" field from the first assistant message
    2. Identifies and extracts the first argdown code snippet that includes
       a premise-conclusion structure (numbered propositions).
    3. Processes the extracted argdown snippet with argdown-cotgen using
       randomly selected argument strategies (by_feature or by_rank).
    4. Replaces the original argdown snippet with the generated chain.

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

    # Extract thinking field from first assistant message
    thinking_text = extract_thinking_from_assistant_message(item)

    if not thinking_text:
        logger.debug(
            f"No thinking field found in item: {item.get('source_id', 'unknown')}"
        )
        return processed_item

    # Extract the first premise-conclusion argdown snippet
    argdown_result = extract_first_premise_conclusion_argdown(thinking_text)

    if not argdown_result:
        logger.debug(
            f"No premise-conclusion argdown found in item: {item.get('source_id', 'unknown')}"
        )
        return processed_item

    argdown_snippet, start_pos, end_pos = argdown_result

    if args.dry_run:
        logger.info(
            f"Would process argdown snippet in item {item.get('source_id', 'unknown')}"
        )
        logger.info(f"Snippet preview: {argdown_snippet[:100]}...")
        return processed_item

    try:
        # Randomly select strategy for each item
        selected_strategy = random.choice(["by_feature", "by_rank"])

        # Create generator with selected strategy
        generator = CotGenerator(pipe_type=selected_strategy)

        # Process the argdown snippet
        processed_argdown = generator(argdown_snippet, abortion_rate=args.abortion_rate)

        # Replace the original argdown snippet with the processed one
        # We need to reconstruct the thinking text with the new snippet
        new_thinking_text = (
            thinking_text[:start_pos] + processed_argdown + thinking_text[end_pos:]
        )

        # Update the thinking field in the processed item
        updated_item = update_thinking_in_assistant_message(
            processed_item, new_thinking_text
        )

        if args.debug:
            logger.info(
                f"Successfully processed item {item.get('source_id', 'unknown')} with strategy {selected_strategy}"
            )

        return updated_item

    except Exception as e:
        logger.warning(
            f"Error processing item {item.get('source_id', 'unknown')}: {str(e)}"
        )
        # Return original item if processing fails
        return processed_item


def update_thinking_in_assistant_message(
    item: Dict[str, Any], new_thinking_text: str
) -> Dict[str, Any]:
    """
    Update the "thinking" field in the first assistant message.

    Args:
        item: Dataset item with messages structure
        new_thinking_text: New content for the thinking field

    Returns:
        Updated item
    """
    messages = item.get("messages", [])

    for i, message in enumerate(messages):
        # Handle both dict and list-of-lists format
        if isinstance(message, dict):
            if message.get("role") == "assistant" and "thinking" in message:
                # Create a copy and update
                item["messages"][i] = {**message, "thinking": new_thinking_text}
                return item
        elif isinstance(message, list):
            # List of [key, value] pairs format
            role = None
            thinking_index = None

            for j, pair in enumerate(message):
                if isinstance(pair, list) and len(pair) == 2:
                    key, value = pair
                    if key == "role" and value == "assistant":
                        role = "assistant"
                    elif key == "thinking":
                        thinking_index = j

            if role == "assistant" and thinking_index is not None:
                # Create a copy and update
                new_message = [list(pair) for pair in message]
                new_message[thinking_index][1] = new_thinking_text
                item["messages"][i] = new_message
                return item

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
    if "messages" not in item:
        return False

    # Check if messages is a list
    if not isinstance(item["messages"], list):
        return False

    # Check if there's at least one assistant message with a thinking field
    thinking_text = extract_thinking_from_assistant_message(item)
    return thinking_text is not None


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

    messages = item.get("messages", [])
    processed_messages = [message_to_dict(msg) for msg in messages]

    processed_item["messages"] = processed_messages

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

    # apply post_process_item to each item
    if not hasattr(dataset, "map"):
        raise ValueError("Dataset does not support 'map' method")
    dataset = dataset.map(post_process_item)

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
