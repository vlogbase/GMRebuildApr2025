import app
from flask import url_for

with app.app.app_context():
    print("Share URL:", url_for('view_shared_conversation', share_id='test_share_id', _external=False))