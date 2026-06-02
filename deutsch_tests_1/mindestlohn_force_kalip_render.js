(function(){
  function isMindestlohn(){
    var checked=document.querySelector('input[name="tc"]:checked');
    if(checked&&checked.value==='t27')return true;
    try{return typeof selected!=='undefined'&&selected==='t27'}catch(e){return false}
  }
  function safe(v){return String(v||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]});}
  var extra=`
<h4>8. C1/C2-Kalıp Bankası: Nachteil Einleiten</h4>
<ul>
<li>Ein zentraler Nachteil des Mindestlohns liegt darin, dass ...</li>
<li>Ein problematischer Aspekt besteht darin, dass ...</li>
<li>Aus wirtschaftlicher Sicht ist kritisch zu sehen, dass ...</li>
<li>Besonders problematisch erscheint, dass ...</li>
<li>Ein häufig übersehener Nachteil betrifft ...</li>
<li>Nicht zu unterschätzen ist außerdem, dass ...</li>
<li>Vor allem für kleine Betriebe kann sich als problematisch erweisen, dass ...</li>
<li>Aus arbeitsmarktpolitischer Perspektive besteht die Gefahr, dass ...</li>
</ul>
<h4>9. C1/C2-Kalıp Bankası: Begründung</h4>
<ul>
<li>Dies lässt sich damit begründen, dass kleine Unternehmen häufig nur über geringe finanzielle Reserven verfügen.</li>
<li>Der Grund dafür liegt darin, dass Personalkosten in arbeitsintensiven Branchen einen erheblichen Teil der Gesamtkosten ausmachen.</li>
<li>Dieses Problem verschärft sich insbesondere dann, wenn Betriebe höhere Kosten nicht an Kunden weitergeben können.</li>
<li>Hinzu kommt, dass Berufsanfänger oft eine längere Einarbeitungszeit benötigen.</li>
<li>Zu berücksichtigen ist außerdem, dass steigende Preise die reale Kaufkraft begrenzen können.</li>
<li>Dies ist vor allem deshalb problematisch, weil Haushalte mit geringem Einkommen einen großen Teil ihres Budgets für alltägliche Ausgaben verwenden.</li>
</ul>
<h4>10. C1/C2-Kalıp Bankası: Folgen ausdrücken</h4>
<ul>
<li>Dies kann dazu führen, dass Betriebe auf Neueinstellungen verzichten.</li>
<li>Infolgedessen könnten einfache Einstiegsmöglichkeiten seltener werden.</li>
<li>Dadurch kann der wirtschaftliche Handlungsspielraum kleiner Unternehmen eingeschränkt werden.</li>
<li>Langfristig besteht die Gefahr, dass die lokale Wirtschaftsstruktur geschwächt wird.</li>
<li>Dies kann wiederum zur Folge haben, dass Verbraucherpreise steigen.</li>
<li>Auf lange Sicht könnte der Mindestlohn somit unbeabsichtigte Nebenwirkungen auf dem Arbeitsmarkt haben.</li>
</ul>
<h4>11. Nachteil 1 İçin Örnek Cümleler: Kleine Betriebe</h4>
<ul>
<li>Gerade kleine Betriebe können durch einen höheren Mindestlohn unter wirtschaftlichen Druck geraten.</li>
<li>In Betrieben mit geringen Gewinnspannen stellt jede zusätzliche Lohnerhöhung eine spürbare finanzielle Mehrbelastung dar.</li>
<li>Ein Familienbetrieb kann steigende Personalkosten oft nicht so leicht ausgleichen wie ein großer Konzern.</li>
<li>Wenn die Einnahmen unverändert bleiben, können höhere Lohnkosten die Kostenstruktur erheblich verändern.</li>
<li>Die Folge könnte sein, dass ein kleines Café seine Öffnungszeiten reduziert oder weniger Aushilfen beschäftigt.</li>
<li>Auch Investitionen in Renovierung, Digitalisierung oder Ausbildung könnten verschoben werden.</li>
<li>Langfristig kann dies die Wettbewerbsfähigkeit kleiner Betriebe schwächen.</li>
<li>Dadurch könnte die Vielfalt der lokalen Wirtschaft gefährdet werden.</li>
</ul>
<h4>12. Nachteil 2 İçin Örnek Cümleler: Geringqualifizierte</h4>
<ul>
<li>Ein höherer Mindestlohn kann dazu führen, dass Arbeitgeber bei Neueinstellungen selektiver vorgehen.</li>
<li>Geringqualifizierte Bewerber könnten benachteiligt werden, wenn Unternehmen stärker auf Erfahrung und Produktivität achten.</li>
<li>Gerade Berufsanfänger sind jedoch auf niedrigschwellige Einstiegsmöglichkeiten angewiesen.</li>
<li>Wenn einfache Tätigkeiten weniger angeboten werden, wird der Berufseinstieg zusätzlich erschwert.</li>
<li>Menschen ohne abgeschlossene Ausbildung benötigen häufig Zeit, um Berufserfahrung zu sammeln.</li>
<li>Bei höheren Lohnkosten könnte diese Einarbeitungszeit aus Sicht der Arbeitgeber zu teuer erscheinen.</li>
<li>Der Mindestlohn schützt somit zwar Beschäftigte, kann aber Arbeitssuchenden am Rand des Arbeitsmarktes den Einstieg erschweren.</li>
<li>Dadurch kann soziale Ungleichheit unbeabsichtigt verstärkt werden.</li>
</ul>
<h4>13. Nachteil 3 İçin Örnek Cümleler: Preise und Kaufkraft</h4>
<ul>
<li>Unternehmen können höhere Personalkosten teilweise an die Kundschaft weitergeben.</li>
<li>Besonders in arbeitsintensiven Dienstleistungen können steigende Löhne zu höheren Verbraucherpreisen führen.</li>
<li>Wenn Restaurants, Friseursalons oder Lieferdienste ihre Preise erhöhen, werden alltägliche Dienstleistungen teurer.</li>
<li>Dadurch kann der finanzielle Vorteil eines höheren Mindestlohns teilweise relativiert werden.</li>
<li>Für Haushalte mit geringem Einkommen ist dies besonders problematisch.</li>
<li>Steigende Preise können die reale Kaufkraft begrenzen.</li>
<li>Wenn die Nachfrage sinkt, können Betriebe erneut unter Druck geraten.</li>
<li>Somit kann ein höherer Mindestlohn indirekt auch Verbraucher und kleine Unternehmen belasten.</li>
</ul>
<h4>14. Nachteil 4 İçin Örnek Cümleler: Bürokratie</h4>
<ul>
<li>Der Mindestlohn erfordert eine genaue Dokumentation der Arbeitszeiten.</li>
<li>Kleine Betriebe müssen Lohnabrechnungen, Arbeitsstunden und betriebliche Abläufe sorgfältig kontrollieren.</li>
<li>Diese Dokumentationspflichten können zusätzlichen Verwaltungsaufwand verursachen.</li>
<li>Gerade kleine Unternehmen verfügen oft nicht über eigene Personalabteilungen.</li>
<li>Für sie kann die Umsetzung gesetzlicher Vorgaben daher besonders zeitaufwendig sein.</li>
<li>Fehlerhafte Arbeitszeiterfassung kann zu rechtlicher Unsicherheit führen.</li>
<li>Kontrollen sind notwendig, erhöhen aber zugleich die organisatorische Belastung.</li>
<li>Damit entsteht ein Spannungsverhältnis zwischen Arbeitnehmerschutz und betrieblicher Umsetzbarkeit.</li>
</ul>
<h4>15. Kopyalanabilir C1/C2 Musterformulierungen</h4>
<table style="width:100%;border-collapse:collapse">
<tr><td><b>Einleitung</b></td><td>Ein zentraler Nachteil des Mindestlohns besteht darin, dass er insbesondere kleine Betriebe finanziell belasten kann.</td></tr>
<tr><td><b>Begründung</b></td><td>Dies ist darauf zurückzuführen, dass Personalkosten in arbeitsintensiven Branchen einen erheblichen Teil der Gesamtkosten ausmachen.</td></tr>
<tr><td><b>Beispiel</b></td><td>Ein kleines Café könnte gezwungen sein, Preise anzuheben, Öffnungszeiten zu verkürzen oder weniger Aushilfen einzustellen.</td></tr>
<tr><td><b>Folge</b></td><td>Infolgedessen kann der wirtschaftliche Handlungsspielraum kleiner Unternehmen eingeschränkt werden.</td></tr>
<tr><td><b>Differenzierung</b></td><td>Dies gilt jedoch nicht für alle Unternehmen gleichermaßen, sondern vor allem für Betriebe mit geringen Gewinnspannen.</td></tr>
<tr><td><b>Bewertung</b></td><td>Langfristig betrachtet kann der Mindestlohn daher unbeabsichtigte Nebenwirkungen haben, obwohl sein sozialpolitisches Ziel nachvollziehbar ist.</td></tr>
</table>
<h4>16. Ezber İçin 12 Hazır Satzstarter</h4>
<ul>
<li>Ein wesentlicher Nachteil liegt darin, dass ...</li>
<li>Besonders betroffen sind ...</li>
<li>Dies zeigt sich vor allem daran, dass ...</li>
<li>Ein konkretes Beispiel hierfür wäre ...</li>
<li>Problematisch wird dies, wenn ...</li>
<li>Dadurch entsteht die Gefahr, dass ...</li>
<li>Hinzu kommt, dass ...</li>
<li>Aus Sicht kleiner Unternehmen bedeutet dies, dass ...</li>
<li>Aus arbeitsmarktpolitischer Perspektive ist kritisch, dass ...</li>
<li>Für Verbraucher kann dies zur Folge haben, dass ...</li>
<li>Im Ergebnis kann ...</li>
<li>Diese Entwicklung sollte jedoch differenziert betrachtet werden, weil ...</li>
</ul>`;
  function render(){
    var tests=window.DEUTSCH_TESTS||{};
    var lessons=window.DEUTSCH_LESSONS||{};
    var test=tests.t27||{};
    var base=(lessons.t27&&lessons.t27.long)||'<h3>Mindestlohn – Nachteile · Lang</h3>';
    if(base.indexOf('C1/C2-Kalıp Bankası')<0)base+=extra;
    if(typeof hide==='function')hide();
    document.getElementById('lesson').classList.remove('hide');
    document.getElementById('lessonTitle').textContent='Konu anlatımı: '+(test.title||'Mindestlohn – Nachteile · C1/C2 Nachteilsabsatz');
    document.getElementById('lessonMeta').textContent='Seviye: Uzun · Kalıp bankası ve örnek cümleler genişletilmiş';
    var words=(test.words||[]).slice(0,30).map(function(w){return '<li>'+safe(w)+'</li>';}).join('');
    document.getElementById('lessonContent').innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>1. Genel bakış</h2><p><b>Thema:</b> '+safe(test.topic||'Mindestlohn – Nachteile')+'</p>'+(words?'<h3>Öncelikli kavramlar</h3><ul>'+words+'</ul>':'')+'</section><section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>2. Konu açıklaması</h2>'+base+'</section>';
    document.getElementById('lesson').scrollIntoView({behavior:'smooth'});
  }
  function bind(){
    var btn=document.getElementById('btnLessonLong');
    if(!btn||btn.dataset.mindestlohnForceKalip==='1')return;
    btn.dataset.mindestlohnForceKalip='1';
    btn.addEventListener('click',function(ev){
      if(!isMindestlohn())return;
      ev.preventDefault();
      ev.stopImmediatePropagation();
      render();
      return false;
    },true);
  }
  document.addEventListener('DOMContentLoaded',bind);
  setInterval(bind,500);
})();
