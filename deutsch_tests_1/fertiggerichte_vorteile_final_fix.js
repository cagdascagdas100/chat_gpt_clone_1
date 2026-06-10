(function(){
  var KEY='t33';
  function safe(v){return String(v||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]});}
  window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
  window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};

  var W=['das Fertiggericht','die vorbereitete Mahlzeit','die Zeitersparnis','die Alltagserleichterung','die Entlastung','der Zeitdruck','die Vereinbarkeit','die Flexibilität','der Zubereitungsaufwand','die Erholungszeit','die Alltagsorganisation','die schnelle Verfügbarkeit','die Arbeitserleichterung','die praktische Lösung','Zeit sparen','den Alltag erleichtern','eine Entlastung darstellen','den Aufwand reduzieren','unter Zeitdruck stehen','die Zubereitungszeit verkürzen','Flexibilität ermöglichen','Stress abbauen','zur Alltagsorganisation beitragen','die einfache Zubereitung','die Verfügbarkeit','die Lagerfähigkeit','die Portionierung','die Selbstständigkeit','die Kochkenntnisse','die Zugänglichkeit','die Essensplanung','die Versorgung','leicht zuzubereiten sein','keine Kochkenntnisse voraussetzen','jederzeit verfügbar sein','Mahlzeiten bereitstellen','Selbstständigkeit ermöglichen','als Reserve dienen','die Selbstversorgung','die Alltagshilfe','die Unterstützung','die Zielgruppe','die Lebenssituation','die körperliche Einschränkung','die Schichtarbeit','regelmäßige Mahlzeiten sichern','Unabhängigkeit fördern','die Planbarkeit','die Lebensmittelverschwendung','die Haltbarkeit','die Vorratshaltung','die Kostenkontrolle','die Restevermeidung','Lebensmittelverschwendung reduzieren','Reste vermeiden','Kosten überblicken','Vorräte anlegen'];

  window.DEUTSCH_TESTS[KEY]={
    category:'Bevor Schreiben',
    slug:'fertiggerichte_vorteile_c1_c2',
    title:'Fertiggerichte – Vorteile · C1/C2 Vorteilsabsatz',
    topic:'Erörterung · Vorteile von Fertiggerichten · Zeitersparnis · einfache Zubereitung · Selbstständigkeit · Planbarkeit · weniger Lebensmittelverschwendung',
    words:W,
    fill:[
      ['Fertiggerichte können im modernen Alltag eine sinnvolle ____ darstellen.','Entlastung','Grundthese'],
      ['Sie sparen Zeit, sind leicht verfügbar und ermöglichen eine schnelle ____.','Versorgung','Grundthese'],
      ['Ein wesentlicher Vorteil liegt in der deutlichen ____.','Zeitersparnis','Vorteil 1'],
      ['Fertiggerichte können die Zubereitungszeit deutlich ____.','verkürzen','NVV'],
      ['Der Vorteil liegt nicht nur in der Geschwindigkeit, sondern auch in der mentalen ____.','Entlastung','Vorteil 1'],
      ['Ein weiterer Vorteil besteht in der einfachen ____ und praktischen Verfügbarkeit.','Zubereitung','Vorteil 2'],
      ['Fertiggerichte setzen keine besonderen Kochkenntnisse ____.','voraus','Vorteil 2'],
      ['Fertiggerichte können bestimmten Personengruppen mehr ____ ermöglichen.','Selbstständigkeit','Vorteil 3'],
      ['Sie erleichtern die Selbstversorgung, wenn Kochen körperlich, zeitlich oder organisatorisch ____ ist.','schwierig','Vorteil 3'],
      ['Ein zusätzlicher Vorteil liegt in der besseren ____.','Planbarkeit','Vorteil 4'],
      ['Fertiggerichte sind häufig portioniert und länger ____.','haltbar','Vorteil 4'],
      ['Portionierte Mahlzeiten können Lebensmittelverschwendung ____.','reduzieren','NVV']
    ],
    mc:[
      ['Welche Grundthese passt am besten?',['Fertiggerichte können im modernen Alltag eine sinnvolle Entlastung darstellen, weil sie Zeit sparen, leicht verfügbar sind, eine schnelle Versorgung ermöglichen und bestimmten Personengruppen mehr Selbstständigkeit geben.','Fertiggerichte sind immer schlecht.','Fertiggerichte ersetzen grundsätzlich jede frische Mahlzeit.','Fertiggerichte betreffen nur Restaurants.'],0,'Grundthese'],
      ['Welche vier Vorteile gehören zu diesem Modul?',['Zeitersparnis, einfache Zubereitung, Unterstützung bestimmter Gruppen, Planbarkeit und weniger Lebensmittelverschwendung','Manipulation, Konsumdruck, Reizüberflutung, digitale Kontrolle','Konflikte, Trittbrettfahrer, Zeitverlust, Verantwortungsdiffusion','Egoismus, Vergleichsdruck, Anpassungsprobleme, soziale Isolation'],0,'Gliederung'],
      ['Welche Formulierung ist C1/C2-gerecht?',['Ein wesentlicher Vorteil von Fertiggerichten liegt in der deutlichen Zeitersparnis, da Einkauf, Vorbereitung und Abwasch reduziert werden.','Fertiggerichte sind halt schnell.','Kochen ist immer sinnlos.','Fertiggerichte machen alles perfekt.'],0,'Stil'],
      ['Was beschreibt die mentale Entlastung?',['Man muss weniger planen, einkaufen, vorbereiten und aufräumen, wodurch der Alltag organisatorisch leichter wird.','Man braucht nie wieder gesunde Ernährung.','Man bekommt automatisch mehr Geld.','Man muss keine Mahlzeiten mehr essen.'],0,'Vorteil 1'],
      ['Welche Aussage passt zu einfacher Zubereitung?',['Fertiggerichte setzen meist keine besonderen Kochkenntnisse voraus und sind klar beschrieben.','Fertiggerichte sind nur für Profiköche geeignet.','Fertiggerichte erfordern immer umfangreiche Kochtechniken.','Fertiggerichte sind nie verfügbar.'],0,'Vorteil 2'],
      ['Welche Personengruppe passt zu Vorteil 3?',['Senioren, Studierende, Alleinerziehende, Schichtarbeiter und Menschen mit körperlichen Einschränkungen','Nur professionelle Köche','Nur Menschen, die täglich drei Stunden kochen','Nur Menschen ohne Wohnung'],0,'Vorteil 3'],
      ['Welche Aussage passt zu Planbarkeit?',['Portionierte und länger haltbare Fertiggerichte können Essensplanung erleichtern und Reste verringern.','Portionierung führt immer zu mehr Abfällen.','Fertiggerichte können niemals als Reserve dienen.','Tiefkühlprodukte verderben immer sofort.'],0,'Vorteil 4'],
      ['Welche NVV ist korrekt?',['Lebensmittelverschwendung reduzieren','Lebensmittelverschwendung schlafen','Lebensmittelverschwendung wohnen','Lebensmittelverschwendung besitzen'],0,'NVV']
    ],
    tf:[
      ['Fertiggerichte können Zeit sparen und dadurch den Alltag entlasten.',true,'Vorteil 1'],
      ['In einer C1/C2-Erörterung reicht der Satz „Fertiggerichte sind schnell“ völlig aus.',false,'Prüfungsstrategie'],
      ['Fertiggerichte können den Planungsaufwand reduzieren, weil Zutaten bereits vorbereitet sind.',true,'Vorteil 1'],
      ['Einfache Zubereitung bedeutet, dass immer umfangreiche Kochkenntnisse nötig sind.',false,'Vorteil 2'],
      ['Fertiggerichte können Menschen mit wenig Kocherfahrung mehr Selbstständigkeit ermöglichen.',true,'Vorteil 2'],
      ['Fertiggerichte können für Senioren, Schichtarbeiter, Studierende und Alleinerziehende eine Alltagshilfe sein.',true,'Vorteil 3'],
      ['Portionierte Fertiggerichte können in manchen Haushalten Reste verringern.',true,'Vorteil 4'],
      ['Fertiggerichte können niemals als Reserve genutzt werden.',false,'Vorteil 4']
    ],
    wordMatch:[['die Zeitersparnis','Vorteil, dass weniger Zeit benötigt wird'],['die Entlastung','Verringerung von Druck, Aufwand oder Belastung'],['der Zubereitungsaufwand','Zeit und Arbeit, die für Vorbereiten und Kochen nötig sind'],['die einfache Zubereitung','unkomplizierte Herstellung oder Erwärmung einer Mahlzeit'],['die Selbstversorgung','Fähigkeit, sich selbst mit Essen zu versorgen'],['die Lebensmittelverschwendung','Wegwerfen von Lebensmitteln, die noch hätten genutzt werden können']],
    phraseMatch:[['Zeit','sparen'],['den Alltag','erleichtern'],['eine Entlastung','darstellen'],['den Aufwand','reduzieren'],['unter Zeitdruck','stehen'],['die Zubereitungszeit','verkürzen'],['Flexibilität','ermöglichen'],['Selbstständigkeit','ermöglichen'],['Lebensmittelverschwendung','reduzieren'],['Reste','vermeiden']],
    prep:[['Ein wesentlicher Vorteil liegt ___ der deutlichen Zeitersparnis.','in','liegen in + Dativ'],['Viele Menschen stehen im Alltag ___ erheblichem Zeitdruck.','unter','unter + Dativ'],['Fertiggerichte können ___ einer besseren Alltagsorganisation beitragen.','zu','beitragen zu + Dativ'],['Sie dienen ___ Reserve für stressige Tage.','als','dienen als + Nomen'],['Ältere Menschen sind dadurch weniger ___ Hilfe angewiesen.','auf','angewiesen sein auf + Akkusativ'],['Portionierte Produkte helfen ___ der Restevermeidung.','bei','helfen bei + Dativ']],
    hang:['Fertiggerichte Vorteile','Zeitersparnis und Entlastung im Alltag','die Zubereitungszeit verkürzen','eine spürbare Entlastung darstellen','einfache Zubereitung und praktische Verfügbarkeit','keine Kochkenntnisse voraussetzen','Mahlzeiten schnell bereitstellen','Selbstständigkeit ermöglichen','Unterstützung bestimmter Personengruppen','Selbstversorgung ermöglichen','regelmäßige Mahlzeiten sichern','Schichtarbeiter und Alleinerziehende','Planbarkeit und Portionierung','weniger Lebensmittelverschwendung','als Reserve aufbewahren','Reste vermeiden','Kosten überblicken','pragmatische Ergänzung im Alltag','Endgültiger Mini Merksatz Fertiggerichte']
  };

  var SHORT='<h3>Fertiggerichte – Vorteile · Kurz</h3><p><b>Grundthese:</b> Fertiggerichte können im modernen Alltag eine sinnvolle Entlastung darstellen, weil sie Zeit sparen, leicht verfügbar sind, eine schnelle Versorgung ermöglichen und bestimmten Personengruppen mehr Selbstständigkeit geben.</p><ul><li>Zeitersparnis und Entlastung</li><li>Einfache Zubereitung und Verfügbarkeit</li><li>Unterstützung bestimmter Personengruppen</li><li>Planbarkeit und weniger Lebensmittelverschwendung</li></ul>';
  var MEDIUM='<h3>Fertiggerichte – Vorteile · Mittel</h3><h4>1. Grundidee</h4><p>Fertiggerichte sind vorbereitete Mahlzeiten, die man meistens nur noch erwärmen, kurz anbraten oder mit wenigen Handgriffen fertigstellen muss. Im modernen Alltag können sie eine praktische Rolle spielen, weil viele Menschen unter Zeitdruck stehen, lange arbeiten, lernen, pendeln oder familiäre Verpflichtungen haben.</p><h4>2. Zeitersparnis und Entlastung</h4><p>Ein wesentlicher Vorteil besteht darin, dass Fertiggerichte die Zubereitungszeit verkürzen. Einkauf, Vorbereitung und Abwasch werden reduziert. Dadurch bleibt mehr Zeit für Erholung, Familie, Arbeit oder Lernen.</p><h4>3. Einfache Zubereitung</h4><p>Fertiggerichte sind meist klar beschrieben, schnell erwärmt und vielerorts erhältlich. Sie setzen keine umfangreichen Kochkenntnisse voraus.</p><h4>4. Unterstützung und Planbarkeit</h4><p>Studierende, Berufstätige, Senioren, Alleinerziehende und Schichtarbeiter können Fertiggerichte als konkrete Alltagshilfe nutzen. Portionierung und Haltbarkeit können außerdem die Haushaltsplanung erleichtern.</p>';
  var LONG='<h3>Fertiggerichte – Vorteile · C1/C2 Konu Anlatımı · Erörterungsvorbereitung · Vollständige Word-Version</h3><p>Die vollständige Word-Version wird über <b>fertiggerichte_vorteile_word_full_override.js</b> geladen. Enthalten sind Ziel, Grundidee, Grundthese, vier Vorteile, Beobachtungen, detaillierte Erklärungen, Beispiele, Ergebnisse, Chancen, Anwendungsbereiche, Kurz- und Langzeitwirkungen, C1/C2-Kopiervorlage, Satzbausteine, Musterabsätze, Übungen, Prüfungsstrategie und endgültiger Mini-Merksatz.</p>';
  window.DEUTSCH_LESSONS[KEY]=window.DEUTSCH_LESSONS[KEY]||{};
  window.DEUTSCH_LESSONS[KEY].short=SHORT;
  window.DEUTSCH_LESSONS[KEY].medium=MEDIUM;
  if(!window.DEUTSCH_LESSONS[KEY].long||window.DEUTSCH_LESSONS[KEY].long.length<3000)window.DEUTSCH_LESSONS[KEY].long=LONG;

  function currentKey(){var c=document.querySelector('input[name="tc"]:checked');if(c&&c.value)return c.value;try{if(typeof selected!=='undefined')return selected}catch(e){}return '';}
  function levelFromButton(el){if(!el)return null;var id=el.id||'';if(id==='btnLessonShort')return 'short';if(id==='btnLessonMedium')return 'medium';if(id==='btnLessonLong')return 'long';return null;}
  function render(level){var test=window.DEUTSCH_TESTS[KEY];var lesson=(window.DEUTSCH_LESSONS[KEY]&&window.DEUTSCH_LESSONS[KEY][level])||LONG;if(typeof window.forceFertiggerichteVorteileWordFull==='function'&&level==='long')return window.forceFertiggerichteVorteileWordFull('long'),true;if(typeof hide==='function')hide();document.getElementById('lesson').classList.remove('hide');document.getElementById('lessonTitle').textContent='Konu anlatımı: '+test.title;document.getElementById('lessonMeta').textContent='Seviye: '+(level==='short'?'Kısa':level==='medium'?'Orta':'Uzun')+' · Word dosyasına göre tam Vorteile konusu';var list=(test.words||[]).slice(0,level==='short'?8:level==='medium'?24:70).map(function(w){return '<li>'+safe(w)+'</li>';}).join('');document.getElementById('lessonContent').innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>1. Genel bakış</h2><p><b>Thema:</b> '+safe(test.topic)+'</p>'+(list?'<h3>Öncelikli kavramlar</h3><ul>'+list+'</ul>':'')+'</section><section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>2. Konu açıklaması</h2>'+lesson+'</section>';document.getElementById('lesson').scrollIntoView({behavior:'smooth'});return true;}
  document.addEventListener('click',function(ev){var b=ev.target&&ev.target.closest&&ev.target.closest('#btnLessonShort,#btnLessonMedium,#btnLessonLong');var level=levelFromButton(b);if(!level||currentKey()!==KEY)return;ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();setTimeout(function(){render(level);},0);return false;},true);
  window.forceFertiggerichteVorteileLessonFinal=render;
})();