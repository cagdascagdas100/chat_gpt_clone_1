from __future__ import annotations

from pathlib import Path

source = Path("docs/chatgpt_status/aays1/automation/security_public_safety_2_wave108_orchestrator.py")
if not source.is_file():
    raise SystemExit(f"SOURCE_ORCHESTRATOR_MISSING: {source}")
text = source.read_text(encoding="utf-8")

protected = [
    ("fcd03b05201213a837096e8908ca9ffbf1930b32", "__W109_SOURCE_HEAD__"),
    ("1c058e79757951a6896cc2f746fa1f3e5570594b1d7ceccc201c96b2437ece29", "__W109_PREVIOUS_CONTINUATION__"),
    ("e96c5d44527e5d4593633eaa2c8d372dd0cf4467e94959816adc92162b094d5a", "__W109_CURRENT_CONTINUATION__"),
    ("wave107", "__W109_PREVIOUS_WAVE__"),
    ("wave108", "__W109_CURRENT_WAVE__"),
    ("WAVE108", "__W109_CURRENT_WAVE_UPPER__"),
    ("0082_", "__W109_PREVIOUS_QUEUE__"),
    ("0083_", "__W109_CURRENT_QUEUE__"),
    ("26860", "__W109_ROWS_OLD_PREVIOUS__"),
    ("27310", "__W109_ROWS_BASE__"),
    ("27760", "__W109_ROWS_TARGET__"),
    ("25945", "__W109_MIN_OLD_PREVIOUS__"),
    ("26372", "__W109_MIN_CURRENT__"),
    ("26963", "__W109_ACCURACY_BASE__"),
    ("57622", "__W109_PARCEL_OLD_START__"),
    ("58072", "__W109_PARCEL_START__"),
    ("58522", "__W109_PARCEL_END_PLUS_ONE__"),
    ("58071", "__W109_PARCEL_OLD_END__"),
    ("58521", "__W109_PARCEL_END__"),
    ("1.65", "__W109_DELTA_PREVIOUS__"),
    ("1.62", "__W109_DELTA_CURRENT__"),
]
for old, token in protected:
    if old not in text:
        raise SystemExit(f"WAVE109_TRANSFORM_FRAGMENT_MISSING:{old}")
    text = text.replace(old, token)

direct = [
    (r'''('\"schema_version\": 85', '\"schema_version\": 86'),''',
     r'''('\"schema_version\": 86', '\"schema_version\": 87'),'''),
    ('"schema_version": 131,', '"schema_version": 132,'),
    ('"schema_version": 135,', '"schema_version": 136,'),
    ('"schema_version": 130,', '"schema_version": 131,'),
    ('or 157) + 1', 'or 158) + 1'),
    ('"priority": -184,', '"priority": -185,'),
    ('98.38', '98.40'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"WAVE109_DIRECT_FRAGMENT_MISSING:{old}")
    text = text.replace(old, new)

resolved = [
    ("__W109_SOURCE_HEAD__", "038e803ae531a29b963e1721b137ed7e835b2cbc"),
    ("__W109_PREVIOUS_CONTINUATION__", "e96c5d44527e5d4593633eaa2c8d372dd0cf4467e94959816adc92162b094d5a"),
    ("__W109_CURRENT_CONTINUATION__", "00640c873f67283da0bcaa6f31141f332247d7197d86bf8d48f7650f49290319"),
    ("__W109_PREVIOUS_WAVE__", "wave108"),
    ("__W109_CURRENT_WAVE__", "wave109"),
    ("__W109_CURRENT_WAVE_UPPER__", "WAVE109"),
    ("__W109_PREVIOUS_QUEUE__", "0083_"),
    ("__W109_CURRENT_QUEUE__", "0084_"),
    ("__W109_ROWS_OLD_PREVIOUS__", "27310"),
    ("__W109_ROWS_BASE__", "27760"),
    ("__W109_ROWS_TARGET__", "28210"),
    ("__W109_MIN_OLD_PREVIOUS__", "26372"),
    ("__W109_MIN_CURRENT__", "26800"),
    ("__W109_ACCURACY_BASE__", "27412"),
    ("__W109_PARCEL_OLD_START__", "58072"),
    ("__W109_PARCEL_START__", "58522"),
    ("__W109_PARCEL_END_PLUS_ONE__", "58972"),
    ("__W109_PARCEL_OLD_END__", "58521"),
    ("__W109_PARCEL_END__", "58971"),
    ("__W109_DELTA_PREVIOUS__", "1.62"),
    ("__W109_DELTA_CURRENT__", "1.60"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"WAVE109_PLACEHOLDER_MISSING:{token}")
    text = text.replace(token, value)

markers = [
    "038e803ae531a29b963e1721b137ed7e835b2cbc",
    "00640c873f67283da0bcaa6f31141f332247d7197d86bf8d48f7650f49290319",
    "wave109",
    "WAVE109",
    "0084_",
    "28210",
    "26800",
    "58971",
    "98.40",
    "1.60",
    '"schema_version": 132,',
    '"schema_version": 136,',
    '"schema_version": 131,',
    'or 158) + 1',
    '"priority": -185,',
]
for marker in markers:
    if marker not in text:
        raise SystemExit(f"WAVE109_WRAPPER_MARKER_MISSING:{marker}")

compile(text, str(source), "exec")
exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})
