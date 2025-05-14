from app import app

for rule in app.url_map.iter_rules():
    if "share" in rule.endpoint:
        print(f"Rule: {rule}, Endpoint: {rule.endpoint}")