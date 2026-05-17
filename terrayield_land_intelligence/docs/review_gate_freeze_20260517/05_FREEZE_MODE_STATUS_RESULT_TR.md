# Review-Gate Freeze Mode Status Result

Generated: 2026-05-17T19:54:54
docs_written: True
backend_live: True
ui_live: True
gate_safe_not_ready_for_auto_accept: True
compile_passed: True
pytest_passed: True
production_auto_accept: NO-GO
verified_promotion: NO-GO without evidence_checked=yes and verified polygon/source

## Endpoint gates snapshot
```json
{
    "generated_at":  "2026-05-17T16:54:31.149192Z",
    "automation_gate":  "COMPLETE",
    "wide_accuracy_program_percent":  "100_automation_complete",
    "production_acceptance_gate":  "NOT_READY_FOR_AUTO_ACCEPT",
    "safe_output_gate":  "READY_FOR_HUMAN_EVIDENCE_REVIEW",
    "threshold_gate":  "DO_NOT_RELAX_THRESHOLDS",
    "evidence_checked_yes":  0,
    "accept":  0,
    "checked_yes":  0,
    "checked_total":  26,
    "final_closeout_path":  "C:\\AAYS_GITHUB_BRIDGE_CLEAN2\\ai-heartbeat\\final-closeout.md",
    "status_reason":  "no checked=yes evidence rows; manual evidence review required",
    "can_production_auto_accept":  false,
    "files":  {
                  "risk_preview":  {
                                       "key":  "risk_preview",
                                       "path":  "C:\\AAYS_GITHUB_BRIDGE_CLEAN2\\ai-results\\aays-097-risk-preview-v2-20260515_025249.csv",
                                       "exists":  true,
                                       "rows":  120,
                                       "required_columns_missing":  [

                                                                    ]
                                   },
                  "completed_labels":  {
                                           "key":  "completed_labels",
                                           "path":  "C:\\AAYS_GITHUB_BRIDGE_CLEAN2\\ai-results\\aays-103-completed_labels_auto_conservative-20260515_133839.csv",
                                           "exists":  true,
                                           "rows":  26,
                                           "required_columns_missing":  [

                                                                        ]
                                       },
                  "review_tracking":  {
                                          "key":  "review_tracking",
                                          "path":  "C:\\AAYS_GITHUB_BRIDGE_CLEAN2\\ai-results\\aays-107-review_tracking_autofilled-20260515_155052.csv",
                                          "exists":  true,
                                          "rows":  26,
                                          "required_columns_missing":  [

                                                                       ]
                                      }
              },
    "all_required_files_present":  true
}
```

## Listing snapshot
```json
{
    "status":  "ok",
    "verification_id":  "L4-00001-OTM-16748769",
    "listing_id":  "OTM-16748769",
    "automation_gate":  "COMPLETE",
    "production_acceptance_gate":  "NOT_READY_FOR_AUTO_ACCEPT",
    "safe_output_gate":  "READY_FOR_HUMAN_EVIDENCE_REVIEW",
    "threshold_gate":  "DO_NOT_RELAX_THRESHOLDS",
    "can_production_auto_accept":  false,
    "flags":  [
                  "evidence_not_checked",
                  "missing_verified_polygon",
                  "needs_source"
              ],
    "file_status":  {
                        "risk_preview":  {
                                             "path":  "C:\\AAYS_GITHUB_BRIDGE_CLEAN2\\ai-results\\aays-097-risk-preview-v2-20260515_025249.csv",
                                             "exists":  true,
                                             "row_count":  120,
                                             "required_columns_missing":  [

                                                                          ]
                                         },
                        "completed_labels":  {
                                                 "path":  "C:\\AAYS_GITHUB_BRIDGE_CLEAN2\\ai-results\\aays-103-completed_labels_auto_conservative-20260515_133839.csv",
                                                 "exists":  true,
                                                 "row_count":  26,
                                                 "required_columns_missing":  [

                                                                              ]
                                             },
                        "review_tracking":  {
                                                "path":  "C:\\AAYS_GITHUB_BRIDGE_CLEAN2\\ai-results\\aays-107-review_tracking_autofilled-20260515_155052.csv",
                                                "exists":  true,
                                                "row_count":  26,
                                                "required_columns_missing":  [

                                                                             ]
                                            }
                    },
    "duplicates":  {
                       "risk_preview":  {
                                            "verification_id":  0
                                        },
                       "completed_labels":  {
                                                "verification_id":  0
                                            },
                       "review_tracking":  {
                                               "verification_id":  0
                                           }
                   },
    "review_tracking":  {
                            "case_id":  "VS-001",
                            "geometry_verdict":  "derived_multi_signal",
                            "current_label":  "needs_source",
                            "current_issue":  "missing_source",
                            "check_url":  "manual_source_url_required",
                            "url_status":  "unchecked",
                            "postcode_status":  "unchecked",
                            "authority_status":  "unchecked",
                            "polygon_status":  "unchecked",
                            "checked":  "no",
                            "final_decision":  "needs_source",
                            "notes":  "AUTO_CONSERVATIVE_FILL: evidence not checked by human; keep production auto-accept disabled; collect canonical source URL and georeferenced polygon before promotion."
                        },
    "completed_labels":  {
                             "validation_case_id":  "VS-001",
                             "reviewer_label":  "needs_source",
                             "reviewer_confidence":  "low",
                             "evidence_checked":  "no",
                             "issue_type":  "missing_source",
                             "reviewer_notes":  "AUTO_CONSERVATIVE_PRELABEL: not human verified; do not use to auto-accept; keep production acceptance blocked until evidence is checked.",
                             "label_source":  "auto_conservative_prelabelling"
                         },
    "risk_preview":  {
                         "risk_label_v2":  "high",
                         "acceptance_status_strict":  "manual_review",
                         "policy_reason_v2":  "no_verified_polygon;area_above_25000;price_above_3000000;ppm_above_5000;multi_signal_candidate",
                         "decision_reason":  "Non-rectangular candidate with multiple independent sale signals. Not verified boundary.",
                         "geometry_verdict":  "derived_multi_signal",
                         "source_polygon_original_site_status":  "unknown_not_verified",
                         "has_source_url":  true,
                         "has_verified_polygon_geojson":  false,
                         "source_urls_json":  [
                                                  "https://www.onthemarket.com/details/16748769/"
                                              ],
                         "field_confidence_json":  {
                                                       "area_m2":  {
                                                                       "reason":  "Area m2 value available.",
                                                                       "status":  "high"
                                                                   },
                                                       "ask_price":  {
                                                                         "reason":  "Numeric ask price parsed.",
                                                                         "status":  "high"
                                                                     },
                                                       "listing_url":  {
                                                                           "reason":  "Canonical HTTPS listing URL available.",
                                                                           "status":  "high"
                                                                       },
                                                       "location":  {
                                                                        "reason":  "Postcode present.",
                                                                        "status":  "high"
                                                                    },
                                                       "parcel_geometry":  {
                                                                               "reason":  "Geometry verdict is derived_multi_signal.",
                                                                               "status":  "medium"
                                                                           },
                                                       "price_per_m2":  {
                                                                            "reason":  "Computed from ask_price and area_m2.",
                                                                            "status":  "high"
                                                                        },
                                                       "sale_year":  {
                                                                         "reason":  "Sale year not available in current open listing feed fields.",
                                                                         "status":  "no_data"
                                                                     },
                                                       "sales_region":  {
                                                                            "reason":  "Local authority present.",
                                                                            "status":  "high"
                                                                        }
                                                   },
                         "side_lengths_m_json":  [
                                                     14.268,
                                                     8.983,
                                                     16.226,
                                                     8.983,
                                                     14.268,
                                                     8.983,
                                                     16.226,
                                                     8.983
                                                 ],
                         "verified_polygon_geojson_present":  false
                     },
    "warnings":  [

                 ]
}
```
