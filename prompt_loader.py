# prompt_loader.py
import yaml
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

_PROMPTS: Dict[str, Any] = {}
_PROMPTS_LOADED = False

def load_prompts(prompt_file_path: str = "prompts.yml") -> Dict[str, Any]:
    global _PROMPTS, _PROMPTS_LOADED
    if _PROMPTS_LOADED:
        return _PROMPTS

    logger.info(f"Initializing Prompts from {prompt_file_path}...")
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        abs_prompt_file_path = os.path.join(base_dir, prompt_file_path)

        if not os.path.exists(abs_prompt_file_path):
            logger.error(f"Prompts configuration file not found: {abs_prompt_file_path}")
            raise FileNotFoundError(f"Prompts configuration file not found: {abs_prompt_file_path}")

        with open(abs_prompt_file_path, 'r', encoding='utf-8') as f: # Added encoding
            loaded_prompts = yaml.safe_load(f)

        if not loaded_prompts:
            logger.error(f"Prompts configuration file '{abs_prompt_file_path}' is empty or invalid.")
            raise ValueError(f"Prompts configuration file '{abs_prompt_file_path}' is empty or invalid.")

        _PROMPTS = loaded_prompts
        _PROMPTS_LOADED = True
        logger.info("Prompts initialized successfully.")
        return _PROMPTS

    except FileNotFoundError:
        logger.critical(f"CRITICAL: Prompts configuration file '{prompt_file_path}' not found. Application may not function correctly.", exc_info=True)
        raise
    except yaml.YAMLError as e:
        logger.critical(f"Error parsing YAML prompts file '{prompt_file_path}': {e}", exc_info=True)
        raise
    except Exception as e:
        logger.critical(f"An unexpected error occurred during Prompts initialization: {e}", exc_info=True)
        raise

def get_prompt(key: str) -> str:
    if not _PROMPTS_LOADED:
        load_prompts() # Load if not already loaded
    
    prompt_template = _PROMPTS.get(key)
    if prompt_template is None:
        logger.error(f"Prompt key '{key}' not found in loaded prompts.")
        raise KeyError(f"Prompt key '{key}' not found. Available keys: {list(_PROMPTS.keys())}")
    return prompt_template

# Load prompts when the module is imported for the first time
if not _PROMPTS_LOADED:
    try:
        load_prompts()
    except Exception as e:
        logger.warning(f"Initial prompt loading failed (will retry on first get_prompt call): {e}")
