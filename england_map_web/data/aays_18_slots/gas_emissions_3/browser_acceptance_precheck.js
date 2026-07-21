(()=>{
  'use strict';
  const byId=id=>document.getElementById(id);
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const has=(o,k)=>Object.prototype.hasOwnProperty.call(o,k)&&o[k]!==null&&o[k]!=='';
  const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  async function getJson(path,ts){
    const response=await fetch(path+'?ts='+ts,{cache:'no-store'});
    if(!response.ok) throw new Error(path+' HTTP '+response.status);
    return response.json();
  }
  async function run(){
    const ts=Date.now();
    const [manifest,summary]=await Promise.all([
      getJson('./browser_acceptance_precheck_manifest.json',ts),
      getJson('./summary_latest.json',ts)
    ]);
    const docs=await Promise.all(manifest.inputs.row_documents.map(path=>getJson('./'+path,ts)));
    const rows=docs.flatMap(doc=>Array.isArray(doc.rows)?doc.rows:[]);
    const required=manifest.checks.required_row_fields;
    const allowed=new Set(manifest.checks.allowed_decisions);
    const counts=new Map();
    rows.forEach(row=>counts.set(row.row_id,(counts.get(row.row_id)||0)+1));
    const duplicateIds=[...counts.entries()].filter(([,count])=>count>1).map(([id])=>id);
    const sourceUrls=[summary?.source?.old_preview_url,summary?.source?.new_preview_url];
    const sourceUrlsValid=sourceUrls.every(url=>{try{return new URL(url).hostname===manifest.checks.official_source_host}catch{return false}});
    const checkedRows=rows.map((row,index)=>{
      const missing=required.filter(field=>!has(row,field));
      const numericValid=['old_value','new_value','change_percent','confidence'].every(field=>finite(row[field]));
      const confidenceValid=finite(row.confidence)&&row.confidence>=manifest.checks.minimum_source_confidence_percent;
      const decisionValid=allowed.has(row.decision);
      const unique=counts.get(row.row_id)===1;
      const passed=missing.length===0&&numericValid&&confidenceValid&&decisionValid&&unique;
      return {index:index+1,row,missing,numericValid,confidenceValid,decisionValid,unique,passed};
    });
    const failed=checkedRows.filter(item=>!item.passed);
    const result={
      status:'PRECHECK_BLOCKED',
      slot_id:manifest.slot_id,
      document_count:docs.length,
      row_count:rows.length,
      unique_row_count:counts.size,
      duplicate_row_ids:duplicateIds,
      failed_row_count:failed.length,
      minimum_confidence:rows.length?Math.min(...rows.map(r=>r.confidence)):null,
      official_source_urls_valid:sourceUrlsValid,
      known_remote_browser_rows:summary.metrics.browser_verified_rows,
      target_browser_rows:summary.metrics.browser_target_rows,
      browser_acceptance_passed:false,
      parcel_binding_passed:false,
      final_ready:false
    };
    const precheckPassed=
      docs.length===manifest.checks.expected_document_count&&
      rows.length===manifest.checks.expected_row_count&&
      counts.size===manifest.checks.expected_unique_row_id_count&&
      duplicateIds.length===0&&failed.length===0&&sourceUrlsValid;
    result.status=precheckPassed?'PRECHECK_PASS_NOT_BROWSER_ACCEPTANCE':'PRECHECK_FAIL';
    window.__gasEmissions3Precheck=result;
    byId('meta').textContent=`SLOT_ID=${manifest.slot_id} | Ön-kabul=${result.status} | Satır=${result.row_count} | Benzersiz=${result.unique_row_count}`;
    const cards=[
      ['Ön-kabul',result.status],
      ['Belgeler',result.document_count+' / '+manifest.checks.expected_document_count],
      ['Satırlar',result.row_count+' / '+manifest.checks.expected_row_count],
      ['Benzersiz',result.unique_row_count+' / '+manifest.checks.expected_unique_row_id_count],
      ['Başarısız satır',result.failed_row_count],
      ['En düşük güven',result.minimum_confidence+'%'],
      ['Resmî URL',result.official_source_urls_valid?'PASS':'FAIL'],
      ['Gerçek browser',result.known_remote_browser_rows+' / '+result.target_browser_rows]
    ];
    byId('cards').innerHTML=cards.map(([label,value])=>`<div class="card"><div class="muted">${esc(label)}</div><div class="value">${esc(value)}</div></div>`).join('');
    byId('notice').textContent=precheckPassed
      ?'100 kaynak adayı statik ön-kabulden geçti. Bu sonuç gerçek 100/100 browser/DOM kabulü değildir; canonical F shared runner testi hâlâ gereklidir.'
      :'Ön-kabul hatası bulundu. Hatalı satırlar aşağıda gösteriliyor.';
    byId('rows').innerHTML=checkedRows.map(item=>{
      const r=item.row;
      const checks=[item.unique?'UNIQUE':'DUPLICATE',item.missing.length?'MISSING:'+item.missing.join(','):'FIELDS_OK',item.numericValid?'NUMERIC_OK':'NUMERIC_FAIL',item.confidenceValid?'CONFIDENCE_OK':'CONFIDENCE_FAIL',item.decisionValid?'DECISION_OK':'DECISION_FAIL'].join(' | ');
      return `<tr class="${item.passed?'pass':'fail'}"><td>${item.index}</td><td>${esc(r.row_id)}</td><td>${esc(r.calendar_year??'—')}</td><td>${esc(r.sector)}</td><td>${esc(r.sub_sector)}</td><td>${esc(r.gas)}</td><td>${esc(r.confidence)}%</td><td>${esc(r.decision)}</td><td>${esc(checks)}</td><td>${item.passed?'PASS':'FAIL'}</td></tr>`;
    }).join('');
    byId('machine').textContent=JSON.stringify(result,null,2);
  }
  run().catch(error=>{
    const result={status:'PRECHECK_RUNTIME_ERROR',error:String(error),browser_acceptance_passed:false,final_ready:false};
    window.__gasEmissions3Precheck=result;
    byId('meta').textContent='Ön-kabul çalıştırılamadı';
    byId('notice').textContent=String(error);
    byId('machine').textContent=JSON.stringify(result,null,2);
  });
})();
