(function(){
  function esc(v){return String(v==null?'':v).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  async function json(url){var r=await fetch(url); if(!r.ok) throw new Error('HTTP '+r.status); return await r.json();}
  function firstProps(fc){return (fc.features&&fc.features[0]&&fc.features[0].properties)||{};}
  function renderPanel(p, meta){
    return '<h2>Nearby Planned Developments</h2>'+
      '<div data-testid="planned-data-present">DATA_PRESENT='+esc(!!(meta&&meta.data_present))+'</div>'+
      '<div>planned building value: '+esc(p.planned_building_1_value)+'</div>'+
      '<div>probability: '+esc(p.planned_building_1_probability)+'</div>'+
      '<div>completion month: '+esc(p.planned_building_1_completion_month)+'</div>'+
      '<div>source: '+esc(p.source_name)+'</div>'+
      '<div>source date: '+esc(p.source_date)+'</div>'+
      '<div>confidence: '+esc(p.match_confidence_score||p.confidence_score)+'</div>'+
      '<div>relation type: '+esc(p.relation_type)+'</div>'+
      '<div>explanation: '+esc(p.calculation_explanation||p.evidence_summary)+'</div>';
  }
  async function load(){
    var status=document.getElementById('plannedBuildingsStatus');
    var panel=document.getElementById('plannedBuildingsPanel');
    status.textContent='Loading planned layer...';
    try{
      var fc=await json('/planned-assets/parcel-layer?bbox=-0.2,51.4,0.2,51.7&limit=10');
      var count=(fc.features||[]).length;
      status.textContent='planned layer loaded: '+count+' matched parcels';
      status.setAttribute('data-feature-count', String(count));
      panel.innerHTML=renderPanel(firstProps(fc), fc.metadata||{});
    }catch(e){status.textContent='planned layer error: '+e.message; panel.textContent='planned layer unavailable';}
  }
  document.addEventListener('DOMContentLoaded', function(){
    var root=document.getElementById('app')||document.body;
    var wrap=document.createElement('section');
    wrap.id='plannedBuildingsSmoke';
    wrap.innerHTML='<button id="showPlannedBuildings" data-icon-src="./assets/icons/terrayield_icons/planed_buildings.png" type="button">Nearby Planned Developments</button><div id="plannedBuildingsStatus">planned layer idle</div><div id="plannedBuildingsPanel"></div>';
    root.appendChild(wrap);
    document.getElementById('showPlannedBuildings').addEventListener('click', load);
  });
})();
