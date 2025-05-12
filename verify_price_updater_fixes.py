"""
Script to verify fixes in price_updater.py.
"""
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_file(file_path):
    """Read the contents of a file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def verify_logger_initialization():
    """
    Verify that logger is initialized correctly and before it's used.
    """
    content = read_file('price_updater.py')
    if content is None:
        return False
    
    # Check if logger is defined before any usage
    logger_def_match = re.search(r'logger\s*=\s*logging\.getLogger\(__name__\)', content)
    if not logger_def_match:
        logger.error("Logger definition not found")
        return False
    
    # Find the first logger usage
    logger_use_match = re.search(r'logger\.(debug|info|warning|error|critical)', content)
    if not logger_use_match:
        logger.error("No logger usage found")
        return False
    
    # Check if definition comes before usage
    if logger_def_match.start() > logger_use_match.start():
        logger.error("Logger is used before it's defined")
        return False
    
    logger.info("✅ Logger is correctly initialized before usage")
    return True

def verify_app_context_usage():
    """
    Verify that database operations are wrapped in application context.
    """
    content = read_file('price_updater.py')
    if content is None:
        return False
    
    # Check if OpenRouterModel.query is always inside app.app_context()
    query_matches = re.finditer(r'OpenRouterModel\.query', content)
    app_context_matches = re.finditer(r'with\s+app\.app_context\(\):', content)
    
    # Convert matches to positions
    query_positions = [match.start() for match in query_matches]
    app_context_starts = [match.end() for match in app_context_matches]
    
    # For each app_context block, find its end
    app_context_blocks = []
    for start in app_context_starts:
        # Find the indentation level of the with statement
        indent_match = re.search(r'^\s*', content[start:].split('\n')[0])
        base_indent = indent_match.group(0) if indent_match else ''
        
        # Find where this indentation level ends (or file ends)
        lines = content[start:].split('\n')
        end_line = 0
        for i, line in enumerate(lines[1:], 1):  # Skip the first line (the with statement)
            if line.strip() and not line.startswith(base_indent + ' '):
                end_line = i
                break
        
        if end_line == 0:
            end_line = len(lines)
        
        block_end = start + sum(len(line) + 1 for line in lines[:end_line])
        app_context_blocks.append((start, block_end))
    
    # Check if each query is inside an app_context block
    for query_pos in query_positions:
        inside_context = any(start <= query_pos <= end for start, end in app_context_blocks)
        if not inside_context:
            logger.error(f"Query at position {query_pos} is not inside app.app_context()")
            return False
    
    logger.info("✅ All database queries are inside application context")
    
    # Check if db.session.commit is inside app_context
    commit_matches = re.finditer(r'db\.session\.commit\(\)', content)
    commit_positions = [match.start() for match in commit_matches]
    
    for commit_pos in commit_positions:
        inside_context = any(start <= commit_pos <= end for start, end in app_context_blocks)
        if not inside_context:
            logger.error(f"Commit at position {commit_pos} is not inside app.app_context()")
            return False
    
    logger.info("✅ All database commits are inside application context")
    
    # Check for db.session.rollback
    rollback_matches = re.finditer(r'db\.session\.rollback\(\)', content)
    rollback_positions = [match.start() for match in rollback_matches]
    
    for rollback_pos in rollback_positions:
        inside_context = any(start <= rollback_pos <= end for start, end in app_context_blocks)
        if not inside_context:
            logger.error(f"Rollback at position {rollback_pos} is not inside app.app_context()")
            return False
    
    logger.info("✅ All database rollbacks are inside application context")
    
    return True

def verify_import_app_before_db():
    """
    Verify that app is imported before any database operations.
    """
    content = read_file('price_updater.py')
    if content is None:
        return False
    
    # Check for the import of app
    app_import_match = re.search(r'from\s+app\s+import\s+app', content)
    if not app_import_match:
        logger.error("Import of app not found")
        return False
    
    # Check for the first database usage
    db_usage_match = re.search(r'db\.session|OpenRouterModel\.query', content)
    if not db_usage_match:
        logger.error("No database usage found")
        return False
    
    # Check if import comes before usage
    if app_import_match.start() > db_usage_match.start():
        logger.error("Database is used before app is imported")
        return False
    
    logger.info("✅ App is imported before database operations")
    return True

def main():
    """Run all verification checks."""
    logger.info("Verifying fixes in price_updater.py...")
    
    logger_init_ok = verify_logger_initialization()
    app_context_ok = verify_app_context_usage()
    import_order_ok = verify_import_app_before_db()
    
    if logger_init_ok and app_context_ok and import_order_ok:
        logger.info("✅ All checks passed! price_updater.py should work correctly now.")
        return 0
    else:
        logger.error("❌ Some checks failed. price_updater.py still has issues.")
        return 1

if __name__ == "__main__":
    exit(main())