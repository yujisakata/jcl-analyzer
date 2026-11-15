"""Reproduce CD2-R02: correct parser span, undetected corruption in generic checker."""
import json
from dataclasses import replace
from jclprof.parser import parse_text
from jclprof.harness.hierarchy import check_hierarchy

text = '//J JOB\n//S EXEC PGM=X\n//IN DD *,DLM=AA\n D\n//OTHER DD DUMMY\nAA\n'
parsed = parse_text(text, jes='UNKNOWN')
assert parsed.jobs[0].span == (1, 6)
bad = replace(parsed, jobs=(replace(parsed.jobs[0], span=(1, 3)),))
violations = check_hierarchy(bad)
print(json.dumps({'correct_span': parsed.jobs[0].span, 'corrupted_span': bad.jobs[0].span,
                  'violation_codes': [v.code for v in violations],
                  'corruption_detected': bool(violations)}, indent=2))
