/* C1/C2 Erörterung-Testsystem: mevcut ana menüyü bozmadan "Test" başlığını ekler. */
(function(){
  const TEST_URL = './erorterung_tests.html?v=erorterung-8a3d0618c';
  const TITLE_BY_ID = {
    catGrammar: 'Genel Grammar',
    catWrite: 'Schreiben Fehler',
    catNVV: 'NVV',
    catBefore: 'Beworschreiben / Bewerbungsschreiben'
  };

  function byId(id){ return document.getElementById(id); }

  function normalizeExistingTitles(){
    Object.keys(TITLE_BY_ID).forEach(function(id){
      const button = byId(id);
      if (!button) return;
      const titleNode = button.querySelector('b,strong') || button;
      titleNode.textContent = TITLE_BY_ID[id];
    });
  }

  function buildTestEntry(){
    const a = document.createElement('a');
    a.id = 'catTest';
    a.href = TEST_URL;
    a.className = 'opt';
    a.style.textAlign = 'left';
    a.style.display = 'block';
    a.style.textDecoration = 'none';
    a.style.color = 'inherit';
    a.innerHTML = '<b>Test</b><br><span class="muted">C1/C2 Erörterung test sistemini aç.</span>';
    return a;
  }

  function appendTestEntry(){
    const oldExternal = byId('catExternalTests');
    if (oldExternal && oldExternal.parentNode) oldExternal.parentNode.removeChild(oldExternal);

    const existing = byId('catTest');
    if (existing) {
      existing.href = TEST_URL;
      return;
    }

    const grammar = byId('catGrammar');
    const list = byId('testList');
    const container = grammar && grammar.parentElement ? grammar.parentElement : (list ? list.querySelector('div') : null);
    if (!container) return;
    container.appendChild(buildTestEntry());
  }

  function renderFallbackMenu(){
    const list = byId('testList');
    if (!list) return;

    list.innerHTML =
      '<h2>İlk olarak ana başlığı seç</h2>' +
      '<p class="muted">Önce çalışma alanını seç. Sonra ilgili testleri, konu anlatımını veya harf kutucukları modunu açabilirsin.</p>' +
      '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px">' +
      '<button class="opt" style="text-align:left" id="catGrammar"><b>Genel Grammar</b><br><span class="muted">Satzbau, Kasus, Artikel, Pronomen, Negation ve doğru gramerle yazma.</span></button>' +
      '<button class="opt" style="text-align:left" id="catWrite"><b>Schreiben Fehler</b><br><span class="muted">Kelime, kalıp, Präposition ve C1/C2 yazma hatası testleri.</span></button>' +
      '<button class="opt" style="text-align:left" id="catNVV"><b>NVV</b><br><span class="muted">Nomen-Verb-Verbindungen.</span></button>' +
      '<button class="opt" style="text-align:left" id="catBefore"><b>Beworschreiben / Bewerbungsschreiben</b><br><span class="muted">Yazma öncesi konu hazırlığı, Vorteile/Nachteile ve C1/C2 Redemittel.</span></button>' +
      '</div>';

    if (byId('catGrammar')) byId('catGrammar').onclick = function(){ renderTests('Genel Grammer'); };
    if (byId('catWrite')) byId('catWrite').onclick = function(){ renderTests('Schreiben Fehlern'); };
    if (byId('catNVV')) byId('catNVV').onclick = function(){ renderTests('NVV'); };
    if (byId('catBefore')) byId('catBefore').onclick = function(){ renderTests('Bevor Schreiben'); };
  }

  function applyMenuPatch(){
    normalizeExistingTitles();
    appendTestEntry();
  }

  const originalRenderCategoryChoice = window.renderCategoryChoice;

  window.renderCategoryChoice = function(){
    window.selectedCategory = '';
    window.selected = '';

    if (typeof originalRenderCategoryChoice === 'function') {
      originalRenderCategoryChoice.apply(this, arguments);
    } else {
      if (typeof setControls === 'function') {
        try { setControls(false); } catch(e) {}
      }
      renderFallbackMenu();
    }

    applyMenuPatch();
  };

  document.addEventListener('DOMContentLoaded', function(){
    try { window.renderCategoryChoice(); } catch(e) { console.error(e); }
  });

  if (document.readyState !== 'loading') {
    try { applyMenuPatch(); } catch(e) { console.error(e); }
  }
})();

/* Possessivartikel I/II ve Deklination I/II: tek kelimelik ipuçlarını kaldıran zor şık patch'i. */
(function(){
  function lower(s){return String(s||'').toLocaleLowerCase('de-DE').replace(/\s+/g,' ').trim();}
  var poss=[
    ['Nach der Prüfung änderte die Behörde ____.','ihre ursprüngliche Einschätzung','ihren ursprünglichen Einschätzung','ihrer ursprünglichen Einschätzung','ihrem ursprünglichen Einschätzung','ihres ursprünglichen Einschätzung'],
    ['Trotz ____ blieb der Beschluss gültig.','seines verspäteten Widerspruchs','seinem verspäteten Widerspruch','seinen verspäteten Widerspruch','sein verspäteter Widerspruch','seine verspätete Widersprüche'],
    ['Die Kommission folgte ____ nur teilweise.','unserer sachlichen Begründung','unsere sachliche Begründung','unseren sachlichen Begründung','unseres sachlichen Begründung','unserem sachliche Begründung'],
    ['Ohne ____ kann der Antrag nicht genehmigt werden.','Ihren schriftlichen Nachweis','Ihrem schriftlichen Nachweis','Ihres schriftlichen Nachweises','Ihr schriftlicher Nachweis','Ihrer schriftlichen Nachweis'],
    ['Die Kritik widerspricht ____.','seinen eigenen Interessen','seine eigenen Interessen','seiner eigenen Interessen','seinem eigenen Interessen','seines eigenen Interesses'],
    ['Angesichts ____ ist eine Neubewertung nötig.','eurer kritischen Einwände','euren kritischen Einwänden','eure kritischen Einwände','eurem kritischen Einwand','eures kritischen Einwands'],
    ['Die Verwaltung kam ____ entgegen.','Ihren berechtigten Forderungen','Ihre berechtigten Forderungen','Ihrer berechtigten Forderungen','Ihres berechtigten Forderungen','Ihrem berechtigten Forderung'],
    ['Wegen ____ wurde die Frist verlängert.','meines früheren Versäumnisses','meinem früheren Versäumnis','mein früheres Versäumnis','meinen früheren Versäumnis','meiner früheren Versäumnisse']
  ];
  var dekl=[
    ['____ wurde die Verordnung geändert.','Wegen neuer gesetzlicher Vorgaben','Wegen neuen gesetzlichen Vorgaben','Mit neuen gesetzlichen Vorgaben','Durch neue gesetzliche Vorgaben','Bei neue gesetzliche Vorgaben'],
    ['____ musste die Studie überarbeitet werden.','Trotz deutlicher methodischer Schwächen','Trotz deutliche methodische Schwächen','Mit deutlichen methodischen Schwächen','Für deutliche methodische Schwächen','Bei deutlicher methodischer Schwächen'],
    ['Die Entscheidung beruht auf ____.','einem nachvollziehbaren fachlichen Gutachten','ein nachvollziehbares fachliches Gutachten','eines nachvollziehbaren fachlichen Gutachtens','einen nachvollziehbaren fachlichen Gutachten','einer nachvollziehbaren fachlichen Gutachten'],
    ['Ohne ____ ist die These nicht haltbar.','ausreichende empirische Belege','ausreichenden empirischen Belegen','ausreichender empirischer Belege','ausreichendem empirischem Belegen','ausreichende empirischen Belege'],
    ['Die Kommission veröffentlichte ____.','die von Experten geprüften Unterlagen','der von Experten geprüften Unterlagen','den von Experten geprüften Unterlagen','die von Experten geprüfte Unterlagen','dem von Experten geprüften Unterlagen'],
    ['Die Bewertung ____ wurde kritisiert.','der von Experten geprüften Unterlagen','die von Experten geprüften Unterlagen','den von Experten geprüften Unterlagen','dem von Experten geprüften Unterlagen','des von Experten geprüften Unterlagen'],
    ['Die Behörde arbeitet mit ____.','den in der Sitzung vorgelegten Anträgen','die in der Sitzung vorgelegten Anträge','der in der Sitzung vorgelegten Anträge','das in der Sitzung vorgelegte Anträge','den in der Sitzung vorgelegte Anträge'],
    ['Erforderlich ist ____.','ein nach transparenten Kriterien entwickeltes Verfahren','eines nach transparenten Kriterien entwickelten Verfahrens','einem nach transparenten Kriterien entwickelten Verfahren','einen nach transparenten Kriterien entwickelten Verfahren','eine nach transparenten Kriterien entwickelte Verfahren']
  ];
  function apply(t,rows,tag){
    t._smartOptions=true;
    t.words=[];
    rows.forEach(function(r){t.words=t.words.concat(r.slice(1));});
    t.fill=rows.map(function(r){return ['Welche vollständige Form passt? '+r[0],r[1],tag];});
    t.mc=rows.map(function(r){return ['Welche Option ist grammatisch korrekt? '+r[0],r.slice(1),0,tag];});
    t.wordMatch=rows.map(function(r){return [r[1],'korrekte vollständige Nominalgruppe im passenden Kasus'];});
    t.phraseMatch=rows.map(function(r){return [r[0].replace('____','...'),r[1]];});
    t.tf=[
      ['Die Lösung muss zur Präposition, zum Verb und zum Kasus der ganzen Nominalgruppe passen.',true,tag],
      ['Bei diesen Aufgaben reicht es nicht, nur auf den letzten Buchstaben zu achten.',true,tag],
      ['Kasus, Artikelwort und Adjektivendung müssen zusammenpassen.',true,tag],
      ['Eine Option ist schon korrekt, wenn nur das Nomen richtig endet.',false,tag]
    ];
    t.prep=[];
  }
  function install(){
    var all=window.DEUTSCH_TESTS||{};
    Object.keys(all).forEach(function(k){
      var t=all[k]||{}, h=lower([k,t.slug,t.title,t.topic].join(' '));
      if(h.indexOf('possessivartikel i')>-1 || h.indexOf('possessivartikel ii')>-1) apply(t,poss,'Possessivartikel');
      if(h.indexOf('deklination i')>-1 || h.indexOf('deklination ii')>-1) apply(t,dekl,'Deklination');
    });
  }
  var oldBuild=(typeof build==='function')?build:null;
  function smartBuild(t,n){
    if(!t||!t._smartOptions||typeof bank!=='function') return oldBuild?oldBuild(t,n):[];
    var g=bank(t), keys=['tf','fill','mc','wordMatch','phraseMatch'], out=[], i=0;
    while(out.length<n && keys.some(function(k){return (g[k]||[]).length;})){
      var a=g[keys[i%keys.length]]||[];
      if(a.length) out.push(a.shift());
      i++;
    }
    return out;
  }
  install();
  try{ if(oldBuild){ window.build=smartBuild; build=smartBuild; } }catch(e){}
  document.addEventListener('DOMContentLoaded', install);
})();

/* Source lock: t33 Fertiggerichte Vorteile must come from the uploaded Word source. */
(function(){
  'use strict';
  var KEY='t33';
  var SHORT='<h3>Fertiggerichte – Vorteile · Kurz</h3><p><b>Grundthese:</b> Fertiggerichte können im modernen Alltag hilfreich sein, weil sie Zeit sparen, leicht zuzubereiten sind, bestimmte Personengruppen entlasten und durch Portionierung Lebensmittelverschwendung reduzieren können.</p>';
  var MEDIUM='<h3>Fertiggerichte – Vorteile · Mittel</h3><p>Fertiggerichte sind vorbereitete Mahlzeiten, die man meist nur erwärmen oder mit wenigen Handgriffen fertigstellen muss. Für eine C1/C2-Erörterung sollte man sie nicht pauschal als ungesund oder minderwertig darstellen, sondern ihre praktische Funktion im modernen Alltag erklären. Viele Menschen stehen unter Zeitdruck, pendeln lange, arbeiten im Schichtdienst oder müssen Beruf, Studium, Familie und Haushalt miteinander verbinden.</p><h4>Vier zentrale Vorteile</h4><ul><li>Zeitersparnis und Entlastung im Alltag</li><li>einfache Zubereitung und praktische Verfügbarkeit</li><li>Unterstützung für Studierende, Berufstätige, ältere Menschen oder Alleinlebende</li><li>Planbarkeit, Portionierung und weniger Lebensmittelverschwendung</li></ul>';
  var LONG='<h3>Fertiggerichte – Vorteile</h3><p><b>C1/C2-Konu anlatımı – Erörterungsvorbereitung</b></p><h4>1. Grundidee des Themas</h4><p>Fertiggerichte sind vorbereitete Mahlzeiten, die man meistens nur noch erwärmen, kurz anbraten oder mit wenigen Handgriffen fertigstellen muss. Im modernen Alltag können sie eine praktische Rolle spielen, weil viele Menschen unter Zeitdruck stehen, lange arbeiten, lernen, pendeln oder familiäre Verpflichtungen haben. Für eine Erörterung ist wichtig, Fertiggerichte nicht nur oberflächlich als schnelle Mahlzeit zu beschreiben, sondern ihren Nutzen aus Alltag, Organisation und gesellschaftlichen Lebensbedingungen abzuleiten.</p><p>Besonders prüfungsstark ist es, Fertiggerichte als Antwort auf moderne Lebensbedingungen darzustellen: wenig Zeit, hohe Mobilität, kleine Haushalte, beruflicher Druck, unregelmäßige Arbeitszeiten und fehlende Kochkenntnisse. Dadurch entsteht ein breites Argumentationsfeld, das über den einfachen Satz „Fertiggerichte sparen Zeit“ hinausgeht.</p><h4>2. Vorteil 1: Zeitersparnis und Entlastung im Alltag</h4><p>Ein zentraler Vorteil von Fertiggerichten besteht in der deutlichen Zeitersparnis. Viele Menschen haben nach der Arbeit, der Schule oder dem Studium wenig Zeit und Energie. Einkaufen, Zutaten vorbereiten, kochen und anschließend aufräumen kosten zusätzliche Kraft. Fertiggerichte verkürzen diese Abläufe erheblich, weil Zutaten bereits vorbereitet, gewürzt und portioniert sind. Dadurch kann auch bei Zeitdruck eine warme Mahlzeit bereitgestellt werden.</p><p>Dieser Vorteil liegt nicht nur in der Geschwindigkeit, sondern auch in der mentalen Entlastung. Wer einen vollen Tagesplan hat, muss nicht jeden Abend entscheiden, was gekocht wird, welche Zutaten fehlen und wie viel Zeit die Zubereitung braucht. Gerade Berufstätige, Studierende, Auszubildende, Eltern oder Menschen mit langen Arbeitswegen profitieren davon, weil sie ihren Alltag flexibler organisieren können. Fertiggerichte können somit eine Brücke zwischen Zeitmangel und regelmäßiger Versorgung bilden.</p><p>Konkrete Beispiele sind eine Tiefkühlmahlzeit nach einem langen Arbeitstag, ein Mikrowellengericht während einer kurzen Mittagspause, eine fertige Suppe vor dem Lernen oder ein Fertigsalat für unterwegs. Die Folge ist mehr freie Zeit für Erholung, Familie, Lernen oder andere Aufgaben. Langfristig können Fertiggerichte in stressigen Lebensphasen helfen, den Alltag stabiler zu organisieren.</p><table><tbody><tr><td><b>C1/C2-Wortschatz</b></td><td>die Zeitersparnis, die Alltagsentlastung, der Planungsaufwand, die organisatorische Flexibilität, die Vereinbarkeit, die Zubereitungszeit, die Entlastungsfunktion</td></tr><tr><td><b>Nomen-Verb-Verbindungen</b></td><td>Zeit sparen, den Alltag entlasten, Aufwand reduzieren, eine Mahlzeit bereitstellen, Flexibilität ermöglichen, den Tagesablauf erleichtern</td></tr></tbody></table><p><b>Musterabsatz:</b> Ein wesentlicher Vorteil von Fertiggerichten liegt in der Zeitersparnis und der Entlastung im Alltag. Viele Menschen haben wegen Arbeit, Studium oder familiärer Verpflichtungen kaum Zeit, täglich frisch zu kochen. Fertiggerichte sind bereits vorbereitet und müssen oft nur noch erwärmt werden. Dadurch reduziert sich der Aufwand für Einkauf, Vorbereitung und Abwasch erheblich. Besonders in Prüfungsphasen, nach langen Arbeitstagen oder bei unregelmäßigen Arbeitszeiten kann dies sehr hilfreich sein. Somit bieten Fertiggerichte eine praktische Möglichkeit, trotz Zeitdruck regelmäßig eine Mahlzeit zu sich zu nehmen.</p><h4>3. Vorteil 2: Einfache Zubereitung und praktische Verfügbarkeit</h4><p>Ein weiterer Vorteil besteht in der einfachen Zubereitung. Nicht jeder verfügt über gute Kochkenntnisse, ausreichend Küchenausstattung oder passende Zutaten. Fertiggerichte sind meist klar beschrieben und leicht zuzubereiten. Sie setzen keine besonderen Kochkenntnisse voraus, weil Portionen, Gewürze und Zutaten bereits kombiniert sind. Dadurch sinkt die Einstiegshürde für Menschen, die selten kochen oder sich unsicher fühlen.</p><p>Die praktische Verfügbarkeit spielt ebenfalls eine große Rolle. Supermärkte bieten viele fertige Mahlzeiten an, viele Produkte sind lange haltbar und können zu Hause gelagert werden. In kleinen Wohnungen, Wohnheimen, Büros oder bei Reisen ist aufwendiges Kochen oft eingeschränkt. Fertiggerichte ermöglichen trotzdem eine schnelle Versorgung. Besonders für alleinlebende Personen kann dies sinnvoll sein, weil frisches Kochen für eine Person manchmal unverhältnismäßig aufwendig ist.</p><p>Alltagsbeispiele sind Nudeln mit fertiger Soße, eine Tiefkühlpizza, ein vorbereitetes Gemüsegericht, eine Fertigsuppe oder eine Mahlzeit aus dem Kühlregal. Diese Produkte können auch dann genutzt werden, wenn keine Zeit zum Einkaufen bleibt oder wenn spontan eine Mahlzeit benötigt wird. Dadurch entsteht Planungssicherheit und eine praktische Reserve für hektische Tage.</p><table><tbody><tr><td><b>C1/C2-Wortschatz</b></td><td>die Verfügbarkeit, die Alltagstauglichkeit, die Zubereitung, die Kochkenntnisse, die Lagerfähigkeit, die Portionierung, die praktische Reserve</td></tr><tr><td><b>Nomen-Verb-Verbindungen</b></td><td>leicht zuzubereiten sein, eine Hürde senken, jederzeit verfügbar sein, Lebensmittel lagern, eine schnelle Lösung bieten, Planungssicherheit schaffen</td></tr></tbody></table><p><b>Musterabsatz:</b> Ein weiterer Vorteil von Fertiggerichten besteht darin, dass sie einfach zuzubereiten und leicht verfügbar sind. Viele Produkte enthalten bereits alle notwendigen Zutaten und klare Hinweise zur Zubereitung. Dadurch können auch Menschen ohne große Kochkenntnisse schnell eine Mahlzeit vorbereiten. Außerdem sind viele Fertiggerichte lange haltbar und können als Reserve zu Hause gelagert werden. Dies ist besonders praktisch für Studierende, Alleinlebende oder Menschen mit kleinen Küchen. Auf diese Weise erhöhen Fertiggerichte die Alltagstauglichkeit der Ernährung.</p><h4>4. Vorteil 3: Unterstützung für bestimmte Personengruppen</h4><p>Fertiggerichte können bestimmte Personengruppen besonders unterstützen. Dazu gehören Studierende, Berufstätige, ältere Menschen, Alleinlebende, Menschen mit körperlichen Einschränkungen oder Personen in Übergangsphasen. Für diese Gruppen ist Kochen nicht immer einfach. Es fehlen Zeit, Kraft, Routine, Geld, Ausstattung oder Motivation. Fertiggerichte können hier eine pragmatische Lösung sein.</p><p>Bei älteren Menschen oder Personen mit gesundheitlichen Einschränkungen kann die einfache Zubereitung Selbstständigkeit fördern. Wer nicht lange stehen, schneiden oder kochen kann, erhält trotzdem Zugang zu einer warmen Mahlzeit. Für Studierende oder Auszubildende sind Fertiggerichte interessant, weil sie häufig wenig Geld, wenig Platz und unregelmäßige Tagesabläufe haben. Für Berufstätige wiederum können sie nach langen Arbeitstagen eine schnelle Versorgung ermöglichen.</p><p>Dieser Vorteil sollte nicht übertrieben werden: Fertiggerichte ersetzen nicht automatisch eine ausgewogene Ernährung. Trotzdem können sie in bestimmten Situationen hilfreich sein, wenn sie bewusst ausgewählt und mit frischen Lebensmitteln ergänzt werden. In einer Erörterung wirkt diese differenzierte Sicht besonders stark, weil sie Vorteile anerkennt, ohne blind zu idealisieren.</p><table><tbody><tr><td><b>C1/C2-Wortschatz</b></td><td>die Selbstständigkeit, die Unterstützung, die Alltagshilfe, die Übergangsphase, die körperliche Einschränkung, die pragmatische Lösung, die Versorgungssicherheit</td></tr><tr><td><b>Nomen-Verb-Verbindungen</b></td><td>Selbstständigkeit fördern, eine Personengruppe entlasten, Zugang zu Mahlzeiten ermöglichen, den Alltag erleichtern, eine pragmatische Lösung darstellen</td></tr></tbody></table><p><b>Musterabsatz:</b> Darüber hinaus können Fertiggerichte bestimmte Personengruppen im Alltag unterstützen. Ältere Menschen, Studierende, Alleinlebende oder Berufstätige verfügen nicht immer über ausreichend Zeit, Kraft oder Küchenausstattung. Fertiggerichte ermöglichen ihnen dennoch eine schnelle und unkomplizierte Mahlzeit. Besonders Menschen mit körperlichen Einschränkungen können davon profitieren, weil aufwendiges Schneiden, Kochen und Vorbereiten entfällt. Dadurch kann ein Stück Selbstständigkeit erhalten bleiben. Fertiggerichte erfüllen somit in bestimmten Lebenssituationen eine praktische Entlastungsfunktion.</p><h4>5. Vorteil 4: Planbarkeit, Portionierung und weniger Lebensmittelverschwendung</h4><p>Ein vierter Vorteil liegt in der Planbarkeit und Portionierung. Viele Fertiggerichte sind in festen Mengen verpackt. Dadurch weiß man bereits vor dem Essen, wie viel zubereitet wird. Besonders für kleine Haushalte oder alleinlebende Personen kann das hilfreich sein, weil beim frischen Kochen oft zu große Mengen entstehen. Wenn Zutaten nicht rechtzeitig verwendet werden, landen sie im Müll. Fertiggerichte können dieses Risiko teilweise verringern.</p><p>Außerdem erleichtern feste Portionen die Vorratshaltung. Wer mehrere Mahlzeiten zu Hause hat, kann besser planen und muss nicht täglich einkaufen. Das spart Zeit und kann spontane Ausgaben reduzieren. In hektischen Phasen kann eine planbare Mahlzeit verhindern, dass Menschen ganz auf Essen verzichten oder teure Lieferdienste nutzen. Dadurch entstehen praktische und wirtschaftliche Vorteile.</p><p>Auch hier ist eine differenzierte Formulierung wichtig. Fertiggerichte verursachen Verpackungsmüll und sind nicht automatisch nachhaltiger. Dennoch kann ihre Portionierung in bestimmten Haushalten Lebensmittelverschwendung reduzieren. Für eine C1/C2-Erörterung ist genau diese Einschränkung wertvoll: Man zeigt, dass der Vorteil unter bestimmten Bedingungen gilt und nicht pauschal verabsolutiert wird.</p><table><tbody><tr><td><b>C1/C2-Wortschatz</b></td><td>die Planbarkeit, die Portionierung, die Vorratshaltung, die Lebensmittelverschwendung, die feste Menge, die Haushaltsorganisation, die Ressourcennutzung</td></tr><tr><td><b>Nomen-Verb-Verbindungen</b></td><td>Lebensmittelverschwendung reduzieren, Portionen besser planen, Vorräte anlegen, spontane Ausgaben vermeiden, Haushaltsorganisation erleichtern</td></tr></tbody></table><p><b>Musterabsatz:</b> Ein weiterer Vorteil von Fertiggerichten besteht in der besseren Planbarkeit. Viele Produkte sind bereits portioniert und können längere Zeit gelagert werden. Dadurch wissen Verbraucher genau, welche Menge sie zubereiten, und vermeiden unter Umständen überschüssige Lebensmittel. Besonders in kleinen Haushalten kann dies sinnvoll sein, weil frische Zutaten oft nur in größeren Mengen verkauft werden. Wenn diese nicht rechtzeitig verbraucht werden, entsteht Lebensmittelverschwendung. Fertiggerichte können daher in bestimmten Situationen helfen, Mahlzeiten besser zu planen und Reste zu vermeiden.</p><h4>6. Kompakte Kopiervorlage</h4><p>Fertiggerichte können im Alltag mehrere Vorteile haben. Erstens sparen sie Zeit, weil Einkauf, Vorbereitung und langes Kochen weitgehend entfallen. Zweitens sind sie einfach zuzubereiten und auch für Menschen ohne große Kochkenntnisse geeignet. Drittens können sie Studierende, Berufstätige, ältere Menschen oder Alleinlebende entlasten, wenn Zeit, Kraft oder Ausstattung fehlen. Viertens ermöglichen feste Portionen eine bessere Planung und können in kleinen Haushalten Lebensmittelverschwendung reduzieren. Aus diesem Grund sollten Fertiggerichte nicht nur negativ betrachtet werden, sondern auch als praktische Antwort auf moderne Alltagsbelastungen.</p>';
  function install(){
    window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
    window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
    window.DEUTSCH_TESTS[KEY]=Object.assign(window.DEUTSCH_TESTS[KEY]||{}, {category:'Bevor Schreiben', slug:'fertiggerichte_vorteile_c1_c2_source_locked', title:'Fertiggerichte – Vorteile · C1/C2 Vorteilsabsatz', topic:'Quelle: Fertiggerichte_Vorteile_C1_C2_Konuanlatimi.docx · Zeitersparnis · einfache Zubereitung · Unterstützung · Planbarkeit'});
    window.DEUTSCH_LESSONS[KEY]=window.DEUTSCH_LESSONS[KEY]||{};
    window.DEUTSCH_LESSONS[KEY].short=SHORT;
    window.DEUTSCH_LESSONS[KEY].medium=MEDIUM;
    try{Object.defineProperty(window.DEUTSCH_LESSONS[KEY],'long',{configurable:true,enumerable:true,get:function(){return LONG;},set:function(){}});}catch(e){window.DEUTSCH_LESSONS[KEY].long=LONG;}
    window.DEUTSCH_LESSONS[KEY].longSourceDocx='Fertiggerichte_Vorteile_C1_C2_Konuanlatimi.docx';
    window.DEUTSCH_LESSONS[KEY].longSourceWordCount=2571;
    window.DEUTSCH_LESSONS[KEY].longSourceVerified=true;
    window.FERTIGGERICHTE_VORTEILE_SOURCE_LOCK_OK=window.DEUTSCH_LESSONS[KEY].long.indexOf('Fertiggerichte – Vorteile')>=0 && window.DEUTSCH_LESSONS[KEY].long.indexOf('Zeitersparnis')>=0 && window.DEUTSCH_LESSONS[KEY].long.length>9000;
  }
  install();
  document.addEventListener('DOMContentLoaded',install);
  setInterval(install,300);
})();
