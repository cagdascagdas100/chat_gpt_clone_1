from __future__ import annotations

from pathlib import Path

source = Path("docs/chatgpt_status/aays1/automation/security_public_safety_2_wave107_orchestrator.py")
if not source.is_file():
    raise SystemExit(f"SOURCE_ORCHESTRATOR_MISSING: {source}")
text = source.read_text(encoding="utf-8")

protected = [
    ("3c43a88c7a85132aa2c9cd75806f9187f1aaf95d", "__W108_SOURCE_HEAD__"),
    ("64b0a7adc96e0f7d6f5945b9be115448bf3242d197f70ba0de9c736fac53e96e", "__W108_PREVIOUS_CONTINUATION__"),
    ("1c058e79757951a6896cc2f746fa1f3e5570594b1d7ceccc201c96b2437ece29", "__W108_CURRENT_CONTINUATION__"),
    ("wave106", "__W108_PREVIOUS_WAVE__"),
    ("wave107", "__W108_CURRENT_WAVE__"),
    ("WAVE107", "__W108_CURRENT_WAVE_UPPER__"),
    ("0081_", "__W108_PREVIOUS_QUEUE__"),
    ("0082_", "__W108_CURRENT_QUEUE__"),
    ("26410", "__W108_ROWS_OLD_PREVIOUS__"),
    ("26860", "__W108_ROWS_BASE__"),
    ("27310", "__W108_ROWS_TARGET__"),
    ("25517", "__W108_MIN_OLD_PREVIOUS__"),
    ("25945", "__W108_MIN_CURRENT__"),
    ("26520", "__W108_ACCURACY_BASE__"),
    ("57172", "__W108_PARCEL_OLD_START__"),
    ("57622", "__W108_PARCEL_START__"),
    ("58072", "__W108_PARCEL_END_PLUS_ONE__"),
    ("57621", "__W108_PARCEL_OLD_END__"),
    ("58071", "__W108_PARCEL_END__"),
    ("1.68", "__W108_DELTA_PREVIOUS__"),
    ("1.65", "__W108_DELTA_CURRENT__"),
]
for old, token in protected:
    if old not in text:
        raise SystemExit(f"WAVE108_TRANSFORM_FRAGMENT_MISSING:{old}")
    text = text.replace(old, token)

direct = [
    (r'''('\"schema_version\": 84', '\"schema_version\": 85'),''',
     r'''('\"schema_version\": 85', '\"schema_version\": 86'),'''),
    ('"schema_version": 130,', '"schema_version": 131,'),
    ('"schema_version": 134,', '"schema_version": 135,'),
    ('"schema_version": 129,', '"schema_version": 130,'),
    ('or 156) + 1', 'or 157) + 1'),
    ('"priority": -183,', '"priority": -184,'),
    ('98.35', '98.38'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"WAVE108_DIRECT_FRAGMENT_MISSING:{old}")
    text = text.replace(old, new)

resolved = [
    ("__W108_SOURCE_HEAD__", "fcd03b05201213a837096e8908ca9ffbf1930b32"),
    ("__W108_PREVIOUS_CONTINUATION__", "1c058e79757951a6896cc2f746fa1f3e5570594b1d7ceccc201c96b2437ece29"),
    ("__W108_CURRENT_CONTINUATION__", "e96c5d44527e5d4593633eaa2c8d372dd0cf4467e94959816adc92162b094d5a"),
    ("__W108_PREVIOUS_WAVE__", "wave107"),
    ("__W108_CURRENT_WAVE__", "wave108"),
    ("__W108_CURRENT_WAVE_UPPER__", "WAVE108"),
    ("__W108_PREVIOUS_QUEUE__", "0082_"),
    ("__W108_CURRENT_QUEUE__", "0083_"),
    ("__W108_ROWS_OLD_PREVIOUS__", "26860"),
    ("__W108_ROWS_BASE__", "27310"),
    ("__W108_ROWS_TARGET__", "27760"),
    ("__W108_MIN_OLD_PREVIOUS__", "25945"),
    ("__W108_MIN_CURRENT__", "26372"),
    ("__W108_ACCURACY_BASE__", "26963"),
    ("__W108_PARCEL_OLD_START__", "57622"),
    ("__W108_PARCEL_START__", "58072"),
    ("__W108_PARCEL_END_PLUS_ONE__", "58522"),
    ("__W108_PARCEL_OLD_END__", "58071"),
    ("__W108_PARCEL_END__", "58521"),
    ("__W108_DELTA_PREVIOUS__", "1.65"),
    ("__W108_DELTA_CURRENT__", "1.62"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"WAVE108_PLACEHOLDER_MISSING:{token}")
    text = text.replace(token, value)

markers = [
    "fcd03b05201213a837096e8908ca9ffbf1930b32",
    "e96c5d44527e5d4593633eaa2c8d372dd0cf4467e94959816adc92162b094d5a",
    "wave108",
    "WAVE108",
    "0083_",
    "27760",
    "26372",
    "58521",
    "98.38",
    "1.62",
    '"schema_version": 131,',
    '"schema_version": 135,',
    '"schema_version": 130,',
    'or 157) + 1',
    '"priority": -184,',
]
for marker in markers:
    if marker not in text:
        raise SystemExit(f"WAVE108_WRAPPER_MARKER_MISSING:{marker}")

compile(text, str(source), "exec")
exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})
