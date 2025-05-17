"""
Workflow to test the fixed price_updater.py with proper application context handling
"""
import sys
import os

def run():
    """Run the price updater test script to verify the application context fix"""
    sys.path.append('.')
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    
    # Import and run the test
    import test_price_updater_fix
    test_price_updater_fix.test_price_updater()
    
if __name__ == '__main__':
    run()