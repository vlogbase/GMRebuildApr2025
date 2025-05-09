"""
Simple script to test Jinja template rendering
"""

import logging
from flask import Flask, render_template_string

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.template_folder = 'templates'
app.config['SERVER_NAME'] = 'example.com'

def test_namespace_pattern():
    """Test if namespace pattern works in Jinja templates"""
    with app.app_context(), app.test_request_context():
        template = '''
        {% set active_affiliates = namespace(count=0, ids=[]) %}
        {% for i in range(3) %}
            {% if i > 0 %}
                {% set active_affiliates.count = active_affiliates.count + 1 %}
                {% set _ = active_affiliates.ids.append(i) %}
            {% endif %}
        {% endfor %}
        Count: {{ active_affiliates.count }}
        '''
        
        try:
            result = render_template_string(template)
            print("Template rendered successfully!")
            print(f"Result: {result.strip()}")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

if __name__ == "__main__":
    test_namespace_pattern()