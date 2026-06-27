(function(){
'use strict';
window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
window.DEUTSCH_LONG_SOURCE_PATCH_DISABLED=true;
window.DEUTSCH_LONG_SOURCE_PATCH_NOTE='Generic 1500-word lesson generator disabled. Long lessons must come from source-based lesson files only.';
if(!window.DEUTSCH_SOURCE_PATCH_ACE3AB_LOADED){window.DEUTSCH_SOURCE_PATCH_ACE3AB_LOADED=true;document.write('<script src="https://rawcdn.githack.com/cagdascagdas100/chat_gpt_clone_1/ace3ab0a1c1b0bbc47f024d92a0a110980d580df/deutsch_tests_1/bevor_long_1500_patch.js"><\/script>');}
function relock(k,title,doc,w,flag){
  var T=window.DEUTSCH_TESTS[k]=window.DEUTSCH_TESTS[k]||{};
  T.category='Bevor Schreiben';
  T.title=T.title||title;
  T.source=doc;
  var L=window.DEUTSCH_LESSONS[k]=window.DEUTSCH_LESSONS[k]||{};
  L.source=doc;
  L.longSourceDocx=doc;
  L.longSourceWordCount=w;
  L.longSourceVerified=true;
  L.sourceRelock='stable-live direct metadata relock after invalid legacy ref audit';
  window[flag]=true;
}
relock('t23','E-Books – Nachteile · C1/C2 Nachteilsabsatz','E_Books_Nachteile_C1_C2_Konuanlatimi.docx',1790,'EBOOKS_NACHTEILE_SOURCE_RELOCK_OK');
relock('t24','Selbstfahrende Autos – Nachteile · C1/C2 Nachteilsabsatz','Selbstfahrende_Autos_Nachteile_C1_C2_Konuanlatimi.docx',1509,'SELBSTFAHRENDE_AUTOS_NACHTEILE_SOURCE_RELOCK_OK');
relock('t25','Studium im Ausland – Nachteile · C1/C2 Nachteilsabsatz','Studium_im_Ausland_Nachteile_C1_C2_Konuanlatimi.docx',1567,'STUDIUM_AUSLAND_NACHTEILE_SOURCE_RELOCK_OK');
relock('t26','Mehrsprachiges Aufwachsen – Nachteile · C1/C2 Nachteilsabsatz','Mehrsprachiges_Aufwachsen_Nachteile_C1_C2_Konuanlatimi.docx',2048,'MEHRSPRACHIGES_AUFWACHSEN_NACHTEILE_SOURCE_RELOCK_OK');
window.DEUTSCH_T23_T26_METADATA_RELOCK_OK=true;
})();
