from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")


def replace_required(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)


# Replace the generic 590 target before fixing resulting queue/date paths.
replace_required("590", "6610")
replace_required(
    "0007_security_public_safety_2_priority_6610row_incremental_evidence_expansion_20260729.v3.task.json",
    "0035_security_public_safety_2_priority_6610row_incremental_evidence_expansion_20260730.v3.task.json",
)
replace_required(
    "2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae",
    "6757d62b9226dc562217fd84b23f7b9ef2f9fda4d7362c745ede1abbc8e84947",
)
replace_required("wave32", "wave60")
replace_required("range(30762, 31352)", "range(30762, 37372)")
replace_required("parcel_31351", "parcel_37371")
replace_required("MIN_QUALITY = 561", "MIN_QUALITY = 6280")
replace_required('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 5.30')
replace_required('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 6260')
replace_required('"incremental_rows_target": 70', '"incremental_rows_target": 350')
replace_required('"incremental_rows_completed": 70', '"incremental_rows_completed": 350')
replace_required(
    "security_public_safety_2_priority_6610row_incremental_evidence_expansion_20260729",
    "security_public_safety_2_priority_6610row_incremental_evidence_expansion_20260730",
)
replace_required(
    "priority_6610row_browser_acceptance_wave60_receipt_20260729.json",
    "priority_6610row_browser_acceptance_wave60_receipt_20260730.json",
)
replace_required(
    "priority_6610row_targeted_retry_wave60_diagnostic_20260729.json",
    "priority_6610row_targeted_retry_wave60_diagnostic_20260730.json",
)

old_gate = '    if any(gate.get("state") != "PASS" for gate in gates[:12]):\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
new_gate = '    failed_gates = [gate for gate in gates[:12] if gate.get("state") != "PASS"]\n    if failed_gates:\n        print("PRE_BROWSER_FAILED_GATES=" + __import__("json").dumps(failed_gates, ensure_ascii=False, sort_keys=True))\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
replace_required(old_gate, new_gate)

old_html_write = '    WEB_HTML.write_text(generate_html(payload, rows, sources, gates, accuracy, police, len(recovered_ids)), encoding="utf-8")'
new_html_write = '''    compact_source_rows = "".join(
        f"<tr><td>{index} | {html.escape(str(source.get('name') or '-'))} | publisher={html.escape(str(source.get('publisher') or '-'))} | accuracy={html.escape(str(source.get('accuracy_percent') or 0))}% | status={html.escape(str(source.get('status') or '-'))} | http={html.escape(str((source.get('probe') or {}).get('http_status') or '-'))} | sha256={html.escape(str((source.get('probe') or {}).get('sha256') or '-'))}</td></tr>"
        for index, source in enumerate(sources, 1)
    )
    compact_row_rows = "".join(
        f"<tr><td>{html.escape(str(row.get('parcel_id') or '-'))} | lon={html.escape(str(row.get('longitude', '-')))} | lat={html.escape(str(row.get('latitude', '-')))} | ons_lsoa={html.escape(str(row.get('ons_lsoa_code') or '-'))} | crime_rank={html.escape(str((row.get('iod_2025') or {}).get('crime_rank') or '-'))} | crime_decile={html.escape(str((row.get('iod_2025') or {}).get('crime_decile') or '-'))} | candidate={html.escape(str(row.get('relative_security_candidate_percent')))} | accuracy={html.escape(str(row.get('candidate_accuracy_percent') or 0))}% | police_records={html.escape(str((row.get('police_query') or {}).get('crime_record_count')))} | police_sha256={html.escape(str((row.get('police_query') or {}).get('sha256') or '-'))} | business_score=null</td></tr>"
        for row in rows
    )
    compact_gate_rows = "".join(
        f"<tr><td>{index} | {html.escape(str(gate.get('gate') or '-'))} | state={html.escape(str(gate.get('state') or '-'))} | evidence={html.escape(str(gate.get('evidence', '')))}</td></tr>"
        for index, gate in enumerate(gates, 1)
    )
    compact_html = f"""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>security_public_safety_2 — {len(rows)} satır</title><style>body{{font-family:Arial,sans-serif;margin:20px;background:#f5f7fa;color:#17202a}}.cards{{display:flex;gap:10px;flex-wrap:wrap}}.card{{background:#fff;border:1px solid #cfd8dc;padding:10px;min-width:145px}}table{{border-collapse:collapse;width:100%;background:#fff;font-size:11px;margin:14px 0}}td{{border:1px solid #cfd8dc;padding:6px;text-align:left;vertical-align:top;word-break:break-word}}.notice{{padding:12px;background:#fff3cd;border:1px solid #ffe69c}}</style></head><body><h1>security_public_safety_2 — {len(rows)} satır aday kanıtı</h1><div class='notice'>Her satır resmî ONS, IoD 2025 ve Police.uk kanıt zinciriyle gösterilir. Değerler adaydır; business skoru yükseltilmemiştir.</div><div class='cards'><div class='card'>Genel ilerleme<br><b>100.0%</b></div><div class='card'>İşlem<br><b>14/14</b></div><div class='card'>Kaynak<br><b>{promoted}/{len(sources)}</b></div><div class='card'>Aday satır<br><b>{len(rows)}/{len(rows)}</b></div><div class='card'>≥95 satır kanıtı<br><b>{accuracy}</b></div><div class='card'>Police SHA256<br><b>{police}</b></div><div class='card'>Targeted retry<br><b>{len(recovered_ids)}</b></div><div class='card'>Business satır<br><b>0</b></div></div><h2>Resmî kaynaklar</h2><table><tbody>{compact_source_rows}</tbody></table><h2>{len(rows)} örnek satır</h2><table><tbody>{compact_row_rows}</tbody></table><h2>Kabul kapıları</h2><table><tbody>{compact_gate_rows}</tbody></table><p><b>final_ready:</b> remote readback pending</p></body></html>"""
    WEB_HTML.write_text(compact_html, encoding="utf-8")'''
replace_required(old_html_write, new_html_write)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
