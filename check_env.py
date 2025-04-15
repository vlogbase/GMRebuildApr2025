"""
Check environment script for the Memory-Enhanced GloriaMundo Chat Application.
This script verifies that all required environment variables are set.
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """
    Check if required environment variables are set.
    Returns True if all required variables are set, False otherwise.
    """
    # Load environment variables
    load_dotenv()
    
    # Check required variables for PostgreSQL database
    pg_vars = ['DATABASE_URL']
    missing_pg = [var for var in pg_vars if not os.environ.get(var)]
    
    # Check required variables for OpenRouter
    api_vars = ['OPENROUTER_API_KEY']
    missing_api = [var for var in api_vars if not os.environ.get(var)]
    
    # Memory system variables (not required by default)
    memory_vars = ['MONGODB_ATLAS_URI']
    missing_memory = [var for var in memory_vars if not os.environ.get(var)]
    
    # Azure OpenAI variables (optional)
    azure_vars = [
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME',
        'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'
    ]
    missing_azure = [var for var in azure_vars if not os.environ.get(var)]
    
    # Print status
    print(f"\n{'=' * 50}")
    print("ENVIRONMENT CHECK")
    print(f"{'=' * 50}")
    
    # Check PostgreSQL
    if missing_pg:
        print("\n❌ PostgreSQL Database: MISSING VARIABLES")
        print(f"  Missing: {', '.join(missing_pg)}")
    else:
        print("\n✅ PostgreSQL Database: CONFIGURED")
        print(f"  DATABASE_URL is set (starts with {os.environ.get('DATABASE_URL', '')[:15]}...)")
    
    # Check OpenRouter
    if missing_api:
        print("\n❌ OpenRouter API: MISSING VARIABLES")
        print(f"  Missing: {', '.join(missing_api)}")
    else:
        print("\n✅ OpenRouter API: CONFIGURED")
        print(f"  OPENROUTER_API_KEY is set")
    
    # Check Memory System
    if missing_memory:
        print("\n⚠️ MongoDB Memory System: NOT CONFIGURED")
        print(f"  Missing: {', '.join(missing_memory)}")
        print("  Memory features will be disabled")
    else:
        print("\n✅ MongoDB Memory System: CONFIGURED")
        print(f"  MONGODB_ATLAS_URI is set (starts with {os.environ.get('MONGODB_ATLAS_URI', '')[:15]}...)")
    
    # Check Azure OpenAI (only if MongoDB is configured)
    if not missing_memory:
        if missing_azure:
            print("\n⚠️ Azure OpenAI: NOT CONFIGURED")
            print(f"  Missing: {', '.join(missing_azure)}")
            print("  Using OpenRouter for embeddings (reduced functionality)")
        else:
            print("\n✅ Azure OpenAI: CONFIGURED")
            print(f"  Using Azure OpenAI for embeddings and memory extraction")
    
    print(f"\n{'=' * 50}")
    
    # Check for critical missing variables
    if missing_pg or missing_api:
        print("\n❌ CRITICAL VARIABLES MISSING")
        print("  The application will not function correctly without these variables.")
        return False
    
    # If memory system is enabled but missing MongoDB
    if os.environ.get('ENABLE_MEMORY_SYSTEM', 'false').lower() == 'true' and missing_memory:
        print("\n⚠️ WARNING: Memory system is enabled but MongoDB URI is missing.")
        print("  Set MONGODB_ATLAS_URI or disable memory with ENABLE_MEMORY_SYSTEM=false")
    
    print("\n✅ Environment check completed. Application can start.")
    return True

if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)