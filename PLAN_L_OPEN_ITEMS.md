# Plan L Open Items

Final delivery is accepted by manifest and evidence pack.

Confirmed:
- rows: 34864
- features: 34864
- rows match features: true
- final closure: 100/100
- read-only delivery: preserved

Open technical items:
- ZIP packaging remains unreliable on the runner.
- Confidence is still uniform at score 3.
- QA scripts expect both old and new column names.

Recommended next step:
- Add a small compatibility layer that writes both column families in the CSV and GeoJSON outputs.
- Then rerun deep QA.

NEXT_COMMAND=devam et
