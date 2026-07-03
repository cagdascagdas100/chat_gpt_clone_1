(function(){
  var REQUIRED_FIELDS = ['emission_percent','level','risk_color','confidence','source','source_date','matching_method','calculation_explanation'];
  function ensureLegend(){
    var d=document.getElementById('gas-emissions-legend-20260703');
    if(!d){d=document.createElement('div');d.id='gas-emissions-legend-20260703';d.style.cssText='position:absolute;right:18px;bottom:18px;z-index:99999;background:white;padding:10px;border:1px solid #777;border-radius:6px;font:12px Arial';d.innerHTML='<b>Gas Emissions</b><br>emission_percent green to red legend<br><span style="color:green">Low</span> â†’ <span style="color:red">High</span>';document.body.appendChild(d);}
  }
  function panelData(row){
    row=row||{};
    return {
      emission_percent: row.emission_percent ?? 'No Data',
      level: row.level ?? row.gas_emission_level ?? 'No Data',
      risk_color: row.risk_color ?? 'No Data',
      confidence: row.confidence ?? row.confidence_percent ?? 'No Data',
      source: row.source ?? 'No Data',
      source_date: row.source_date ?? 'No Data',
      matching_method: row.matching_method ?? 'No Data',
      calculation_explanation: row.calculation_explanation ?? 'No Data'
    };
  }
  function htmlFor(f){return '<b>Gas Emissions parcel details</b>'+REQUIRED_FIELDS.map(function(k){return '<br><b>'+k+'</b>: '+(f[k] ?? 'No Data');}).join('');}
  function showPanel(f){var p=document.getElementById('gas-emissions-right-panel-20260703');if(!p){p=document.createElement('div');p.id='gas-emissions-right-panel-20260703';p.style.cssText='position:absolute;top:80px;right:18px;z-index:99999;background:white;max-width:420px;padding:12px;border:1px solid #777;border-radius:6px;font:13px Arial';document.body.appendChild(p);}p.innerHTML=htmlFor(f);}
  async function loadRows(){
    var urls=['gas_emissions_updates/latest_changes.json','outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/latest_changes.json','../outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/latest_changes.json'];
    for(var i=0;i<urls.length;i++){try{var r=await fetch(urls[i],{cache:'no-store'});if(!r.ok)continue;var j=await r.json();return Array.isArray(j.changes)?j.changes:[];}catch(e){}}
    return [];
  }
  function color(p){var n=Number(p);if(!isFinite(n))return '#9ca3af';var h=Math.round(120-(120*Math.max(0,Math.min(100,n))/100));return 'hsl('+h+',80%,45%)';}
  function tryStyle(row){try{document.querySelectorAll('[data-emission-percent],[data-emission_percent]').forEach(function(el){var v=el.getAttribute('data-emission-percent')||el.getAttribute('data-emission_percent');el.style.fill=color(v);el.style.backgroundColor=color(v);});}catch(e){}}
  async function activate(){var rows=await loadRows();ensureLegend();showPanel(panelData(rows[0]||{}));tryStyle(rows[0]);document.body.setAttribute('data-gas-emissions-layer-active','true');return true;}
  document.addEventListener('click',function(ev){var el=ev.target,hay='';while(el&&el!==document.body){hay+=' '+((el.getAttribute&&((el.getAttribute('src')||'')+' '+(el.getAttribute('alt')||'')+' '+(el.getAttribute('title')||'')))||'')+' '+(el.textContent||'');el=el.parentElement;}hay=hay.toLowerCase();if(hay.includes('air.png')||hay.includes('gas emissions')||hay.includes('gas emission'))setTimeout(activate,150);},true);
  window.__gasEmissionsActivate20260703=activate;
})();
