/* C1/C2 Erörterung-Testsystem: ana menüye kalıcı "Test" başlığı ekler.
   Bu dosya test.html içinde en altta yüklenmelidir. */
(function(){
  const TEST_URL = './erorterung_tests.html?v=stable1';

  function byId(id){ return document.getElementById(id); }
  function esc(s){
    return String(s || '').replace(/[&<>"]/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
    });
  }

  function cardButton(id, title, desc){
    return '<button id="'+id+'" class="ghost" style="text-align:left;width:100%;min-height:116px;border-radius:16px;padding:16px;line-height:1.35;background:#fff;color:#183642;border:1px solid #ddd6ca;box-shadow:0 6px 16px #00000010;">'
      + '<strong style="display:block;font-size:19px;margin-bottom:7px;">'+esc(title)+'</strong>'
      + '<span style="font:14px Arial;color:#4b5563;">'+esc(desc)+'</span>'
      + '</button>';
  }

  function linkCard(title, desc){
    return '<a id="catExternalTests" href="'+TEST_URL+'" style="display:block;text-decoration:none;min-height:116px;border-radius:16px;padding:16px;line-height:1.35;background:#183642;color:#fff;border:1px solid #183642;box-shadow:0 6px 16px #00000018;">'
      + '<strong style="display:block;font-size:19px;margin-bottom:7px;">'+esc(title)+'</strong>'
      + '<span style="font:14px Arial;color:#e5e7eb;">'+esc(desc)+'</span>'
      + '<span style="display:inline-block;margin-top:12px;background:#c4a484;color:#183642;border-radius:999px;padding:5px 10px;font:13px Arial;font-weight:bold;">Testsystem öffnen</span>'
      + '</a>';
  }

  window.renderCategoryChoice = function(){
    window.selectedCategory = '';
    window.selected = '';

    if (typeof setControls === 'function') {
      try { setControls(false); } catch(e) {}
    }

    const list = byId('testList');
    if (!list) return;

    list.innerHTML =
      '<h2>İlk olarak ana başlığı seç</h2>'
      + '<p class="muted">Önce çalışma alanını seç. Sonra ilgili testleri, konu anlatımını veya harf kutucukları modunu açabilirsin.</p>'
      + '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-top:12px;">'
      + cardButton('catGrammar','Genel Grammar','Satzbau, Kasus, Artikel, Pronomen, Negation und korrektes Schreiben.')
      + cardButton('catWrite','Schreiben Fehler','Wortschatz, Präpositionen, Kollokationen und typische C1/C2-Schreibfehler.')
      + cardButton('catNVV','NVV','Nomen-Verb-Verbindungen zu Wirtschaft, Gesellschaft, Medien, Bildung, Umwelt und Argumentation.')
      + cardButton('catBefore','Beworschreiben / Bewerbungsschreiben','Schreibvorbereitung: Vorteile, Nachteile, Redemittel und Erörterungsthemen.')
      + linkCard('Test','C1/C2-Erörterungstests zu Deklination, Possessivartikeln, Pronomen, Indefinitpronomen, Negationswörtern, Satzstellung und Redemitteln.')
      + '</div>';

    const grammar = byId('catGrammar');
    const write = byId('catWrite');
    const nvv = byId('catNVV');
    const before = byId('catBefore');

    if (grammar) grammar.onclick = function(){ renderTests('Genel Grammer'); };
    if (write) write.onclick = function(){ renderTests('Schreiben Fehlern'); };
    if (nvv) nvv.onclick = function(){ renderTests('NVV'); };
    if (before) before.onclick = function(){ renderTests('Bevor Schreiben'); };
  };

  document.addEventListener('DOMContentLoaded', function(){
    try { window.renderCategoryChoice(); } catch(e) { console.error(e); }
  });
})();
