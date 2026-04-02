from app import app
import sys
rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
for rule in rules:
    sys.stdout.write(rule.endpoint + ' ' + rule.rule + '\n')
