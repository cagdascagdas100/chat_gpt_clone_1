(function(){
  var REQUIRED = [
    'parcel_id','security_score','security_level','security_level_label','security_color_category','security_color_hex',
    'source_name','source_url','source_date','evidence','matching_method','calculation_explanation','confidence_score','accuracy_rating'
  ];
  var ALIASES = {
    parcel_id:['parcel_id','security_parcel_id','id','parcelId'],
    security_score:['security_score','safety_score','score'],
    security_level:['security_level','safety_level','level'],
    security_level_label:['security_level_label','safety_level_label','confidence_label'],
    security_color_category:['security_color_category','color_category','safety_color_category'],
    security_color_hex:['security_color_hex','color_hex','safety_color_hex'],
    source_name:['source_name','source','dataset_name'],
    source_url:['source_url','url','dataset_url'],
    source_date:['source_date','date','dataset_date'],
    evidence:['evidence','confidence_flags','evidence_text'],
    matching_method:['matching_method','match_method'],
    calculation_explanation:['calculation_explanation','explanation'],
    confidence_score:['confidence_score','confidence'],
    accuracy_rating:['accuracy_rating','accuracy']
  };
  function val(p, keys){ for(var i=0;i<keys.length;i++){ var v=p && p[keys[i]]; if(v !== undefined && v !== null && v !== '') return v; } return null; }
  function normalize(p){
    p = p || {};
    var out = Object.assign({}, p);
    REQUIRED.forEach(function(k){ if(out[k] === undefined || out[k] === null || out[k] === '') out[k] = val(p, ALIASES[k] || [k]); });
    out.__missing_security_contract_fields = REQUIRED.filter(function(k){ return out[k] === undefined || out[k] === null || out[k] === ''; });
    return out;
  }
  function esc(v){ return String(v === undefined || v === null || v === '' ? 'missing' : v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];}); }
  function html(p){
    var n = normalize(p);
    return '<div class="aays-security-contract" data-contract-missing="'+esc(n.__missing_security_contract_fields.join(','))+'">' +
      REQUIRED.map(function(k){ return '<div class="aays-security-contract-row"><strong>'+esc(k)+':</strong> '+esc(n[k])+'</div>'; }).join('') +
      (n.__missing_security_contract_fields.length ? '<div class="aays-security-contract-blocker">Missing canonical fields: '+esc(n.__missing_security_contract_fields.join(', '))+'</div>' : '') +
      '</div>';
  }
  window.AAYSSecurityContractBridge = { requiredFields: REQUIRED.slice(), normalize: normalize, renderHtml: html };
})();
