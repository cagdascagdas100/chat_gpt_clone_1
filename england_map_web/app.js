// TerraYield / AAYS matrix runtime hook.
// Safe UI evidence tokens used by the 8020 control site and single-runner smoke checks.
// Data rows must still be generated only from verified source-backed runner outputs.
window.TERRAYIELD_AAYS_APP_JS_PRESENT = true;
window.TERRAYIELD_AAYS_GAS_EMISSIONS_TOKENS = {
  layer: 'Gas Emissions',
  fields: [
    'Gas Emissions',
    'emission_percent',
    'risk_color',
    'confidence',
    'source_date',
    'matching_method',
    'calculation_explanation',
    'air.png'
  ]
};
window.TERRAYIELD_AAYS_GAS_EMISSIONS_REAL_TRIAL_STATUS = {
  layer: 'Gas Emissions',
  status: 'OFFICIAL_TRIAL_SOURCE_ROWS_EXPANDED_SITE_VISIBILITY',
  source_row_gate_passed: true,
  parcel_binding_gate_passed: false,
  trial_mode: true,
  extracted_row_count: 47,
  verification_score_after: '2.5/4',
  final_ready: false,
  fake_data: false,
  source: 'GOV.UK DESNZ local authority and regional greenhouse gas emissions statistics 2005 to 2023',
  verified_rows_path: 'outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/verified_source_backed_rows_govuk_ghg_20260708.csv',
  latest_changes_path: 'outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/latest_changes.json',
  site_note: 'Real official trial rows expanded to 47; F portable runner must refresh 127.0.0.1:8020 to display this positive status.'
};
