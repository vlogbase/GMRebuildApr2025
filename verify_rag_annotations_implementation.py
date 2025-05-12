"""
Script to verify the RAG annotations implementation
This script inspects the code changes to confirm proper annotation processing.
"""
import os
import sys
import re
import ast
import inspect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_file_content(file_path, patterns, all_must_match=True):
    """
    Check if a file contains specific patterns.
    
    Args:
        file_path: Path to the file to check
        patterns: List of regex patterns to search for
        all_must_match: If True, all patterns must match; if False, at least one pattern must match
        
    Returns:
        bool: Whether the patterns match according to the criteria
    """
    if not os.path.exists(file_path):
        logger.error(f"File {file_path} does not exist")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        matched_patterns = []
        for pattern in patterns:
            if re.search(pattern, content, re.MULTILINE):
                matched_patterns.append(pattern)
                logger.info(f"Pattern matched: {pattern}")
            else:
                logger.warning(f"Pattern not matched: {pattern}")
        
        if all_must_match:
            return len(matched_patterns) == len(patterns)
        else:
            return len(matched_patterns) > 0
    
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return False

def verify_models_annotations_field():
    """
    Verify that the Message model has the annotations field.
    """
    logger.info("Verifying Message model has annotations field...")
    patterns = [
        r"annotations\s*=\s*db\.Column\(db\.JSON,\s*nullable=True\)",  # JSON field
    ]
    return check_file_content('models.py', patterns)

def verify_capture_annotations():
    """
    Verify that the code captures annotations from responses.
    """
    logger.info("Verifying code captures annotations from responses...")
    patterns = [
        r"if\s+'annotations'\s+in\s+json_data",  # Check for annotations in response
        r"generate\.captured_annotations\s*=\s*json_data\.get\('annotations'\)",  # Store annotations
    ]
    return check_file_content('app.py', patterns)

def verify_save_annotations():
    """
    Verify that annotations are saved to the Message instance.
    """
    logger.info("Verifying annotations are saved to Message instance...")
    patterns = [
        r"annotations\s*=\s*getattr\(generate,\s*'captured_annotations',\s*None\)",  # Get annotations from generate
        r"annotations=annotations",  # Pass annotations to Message constructor
    ]
    return check_file_content('app.py', patterns)

def verify_include_annotations():
    """
    Verify that previous annotations are included in subsequent requests.
    """
    logger.info("Verifying previous annotations are included in subsequent requests...")
    patterns = [
        r"last_annotations\s*=\s*None",  # Initialize last_annotations
        r"last_assistant_msg\s*=\s*Message\.query\.filter_by\(",  # Query for last assistant message
        r"if\s+last_assistant_msg\s+and\s+last_assistant_msg\.annotations:",  # Check if annotations exist
        r"last_annotations\s*=\s*last_assistant_msg\.annotations",  # Get annotations from last message
        r"payload\['annotations'\]\s*=\s*last_annotations",  # Add annotations to payload
    ]
    return check_file_content('app.py', patterns)

def verify_migration_script():
    """
    Verify that the migration script adds the annotations column.
    """
    logger.info("Verifying migration script adds annotations column...")
    patterns = [
        r"ALTER\s+TABLE\s+message\s+ADD\s+COLUMN\s+annotations\s+JSONB",  # Add annotations column
    ]
    return check_file_content('migrations_annotations.py', patterns)

def run_verification():
    """
    Run all verification checks.
    """
    results = {
        "Message model has annotations field": verify_models_annotations_field(),
        "Code captures annotations from responses": verify_capture_annotations(),
        "Annotations are saved to Message instance": verify_save_annotations(),
        "Previous annotations are included in requests": verify_include_annotations(),
        "Migration script adds annotations column": verify_migration_script()
    }
    
    logger.info("\n=== Verification Results ===")
    all_passed = True
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    logger.info("Verifying RAG annotations implementation...")
    success = run_verification()
    if success:
        logger.info("\n✅ All verification checks passed. The RAG annotations implementation is correct.")
        sys.exit(0)
    else:
        logger.error("\n❌ Some verification checks failed. Please review the implementation.")
        sys.exit(1)