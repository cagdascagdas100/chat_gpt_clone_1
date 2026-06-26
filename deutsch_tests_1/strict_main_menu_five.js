/* Strict main menu: only 5 main headings are shown on the start page.
   Topic buttons stay inside their real category, especially Bevor Schreiben / Bewerbungsschreiben. */
(function(){
  'use strict';

  var MAIN_CARDS = [
    {id:'catTest',kind:'link',href:'./erorterung_tests.html?v=stable1',title:'Test',desc:'C1/C2 Erörterung test sistemini aç.'},
    {id:'catGrammar',cat:'Genel Grammer',title:'Genel Grammar',desc:'Satzbau, Kasus, Artikel, Pronomen, Negation ve doğru gramerle yazma.'},
    {id:'catWrite',cat:'Schreiben Fehlern',title:'Schreiben Fehler',desc:'Kelime, kalıp, Präposition ve C1/C2 yazma hatası testleri.'},
    {id:'catNVV',cat:'NVV',title:'NVV',desc:'Nomen-Verb-Verbindungen ve akademik yazma kalıpları.'},
    {id:'catBefore',cat:'Bevor Schreiben',title:'Bevor Schreiben / Bewerbungsschreiben',desc:'Selbstfahrende Autos: C1/C2 Vorteilsabsatz, Redemittel, NVV ve yazma hazırlığı dahil tüm Vorteile/Nachteile konu anlatımları burada.'}
  ];
  var MAIN_IDS = {catTest:1,catGrammar:1,catWrite:1,catNVV:1,catBefore:1};
  var observerInstalled = false;

  function esc(s){return String(s==null?'':s).replace(/[&<>']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;'}[c];});}
  function el(id){return document.getElementById(id);}
  function isHidden(node){return !node || node.classList.contains('hide');}
  function showOnlyStart(){return isHidden(el('quiz')) && isHidden(el('lesson')) && isHidden(el('hang'));}
  function setModeControls(show){var c=el('modeControls'); if(c)c.classList.toggle('hide',!show);}
  function cardHtml(card){
    var inner='<b>'+esc(card.title)+'</b><br><span class="muted">'+esc(card.desc)+'</span>';
    if(card.kind==='link')return '<a class="opt" id="'+esc(card.id)+'" href="'+esc(card.href)+'" style="text-align:left;display:block;text-decoration:none;color:inherit">'+inner+'</a>';
    return '<button class="opt" style="text-align:left" id="'+esc(card.id)+'">'+inner+'</button>';
  }
  function bindMainCardClicks(){
    MAIN_CARDS.forEach(function(card){
      if(!card.cat)return;
      var b=el(card.id);
      if(b)b.onclick=function(){
        window.__strictMainMenuActive=false;
        if(typeof window.renderTests==='function')window.renderTests(card.cat);
        else if(typeof renderTests==='function')renderTests(card.cat);
      };
    });
  }
  function renderStrictMainMenu(){
    var list=el('testList'); if(!list)return;
    window.__strictMainMenuActive=true;
    try{window.selectedCategory='';window.selected='';}catch(e){}
    try{if(typeof window.setControls==='function')window.setControls(false);else if(typeof setControls==='function')setControls(false);else setModeControls(false);}catch(e){setModeControls(false);}
    list.innerHTML='<h2>İlk olarak ana başlığı seç</h2>'+'<p class="muted">Ana menüde sadece 5 ana başlık gösterilir. Alt konu başlıkları kendi ana bölümünün içine girince görünür.</p>'+'<div id="strictMainGrid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px">'+MAIN_CARDS.map(cardHtml).join('')+'</div>';
    bindMainCardClicks();
  }
  function gridIsDirty(grid){
    if(!grid)return true;
    var nodes=Array.prototype.slice.call(grid.children).filter(function(n){return n&&n.id;});
    if(nodes.length!==5)return true;
    for(var i=0;i<nodes.length;i++){if(!MAIN_IDS[nodes[i].id])return true;}
    var before=el('catBefore');
    if(!before || before.textContent.indexOf('Selbstfahrende Autos: C1/C2 Vorteilsabsatz')===-1)return true;
    return false;
  }
  function sanitizeStartMenu(){
    var list=el('testList'); if(!list || !showOnlyStart())return;
    if(window.__strictMainMenuActive===false)return;
    var grid=el('strictMainGrid');
    if(gridIsDirty(grid))renderStrictMainMenu(); else bindMainCardClicks();
  }
  window.renderCategoryChoice=function(){renderStrictMainMenu();};
  function installObserver(){
    if(observerInstalled)return;
    var list=el('testList'); if(!list || !window.MutationObserver)return;
    observerInstalled=true;
    var obs=new MutationObserver(function(){if(window.__strictMainMenuActive!==false)setTimeout(sanitizeStartMenu,0);});
    obs.observe(list,{childList:true,subtree:true,characterData:true});
  }
  document.addEventListener('DOMContentLoaded',function(){renderStrictMainMenu();installObserver();[50,150,300,700,1200,2000].forEach(function(ms){setTimeout(sanitizeStartMenu,ms);});});
  if(document.readyState!=='loading'){renderStrictMainMenu();installObserver();[50,150,300,700,1200,2000].forEach(function(ms){setTimeout(sanitizeStartMenu,ms);});}
  setInterval(function(){if(window.__strictMainMenuActive!==false)sanitizeStartMenu();},1200);
})();

/* Source lock: t31 must stay Werbung-Nachteile and must not be overwritten by Medien t32 runtime fixes. */
(function(){
  'use strict';

  var WERBUNG_SHORT = `<h3>Werbung – Nachteile · Kurz</h3><p><b>Grundthese:</b> Werbung kann zwar über Produkte informieren, führt jedoch häufig zu Manipulation, Konsumdruck, unrealistischen Erwartungen, Reizüberflutung und Datenschutzproblemen.</p><ul><li>Manipulation und künstliche Bedürfnisse</li><li>Konsumdruck und finanzielle Belastung</li><li>Unrealistische Ideale und Vergleichsdruck</li><li>Reizüberflutung und digitale Kontrolle</li></ul>`;

  var WERBUNG_MEDIUM = `<h3>Werbung – Nachteile · Mittel</h3><p>Werbung ist heute fast überall präsent: im Fernsehen, im Internet, in sozialen Medien, in Apps, auf Plakaten und in Suchergebnissen. Für eine C1/C2-Erörterung ist entscheidend, Werbung nicht nur als neutrale Produktinformation zu betrachten, sondern als gezielte Beeinflussung von Wahrnehmung, Wünschen und Kaufentscheidungen.</p><h4>1. Manipulation</h4><p>Werbung arbeitet mit Bildern, Musik, Emotionen, Statussymbolen und psychologischen Reizen. Dadurch können Bedürfnisse entstehen, die ohne Werbung gar nicht vorhanden gewesen wären.</p><h4>2. Konsumdruck</h4><p>Rabatte, Influencer, Marken und Trends können dazu führen, dass Menschen mehr kaufen, als sie eigentlich brauchen. Daraus können finanzielle Belastung und materialistisches Denken entstehen.</p><h4>3. Unrealistische Ideale</h4><p>Werbung zeigt häufig perfekte Körper, ideale Lebensstile und scheinbaren Erfolg. Besonders Jugendliche können dadurch unter Vergleichsdruck geraten und ihr Selbstwertgefühl verlieren.</p><h4>4. Reizüberflutung und Daten</h4><p>Digitale Werbung unterbricht Lernen, Lesen und Arbeiten. Personalisierte Anzeigen nutzen Nutzerdaten und werfen Fragen nach Datenschutz, Privatsphäre und digitaler Kontrolle auf.</p>`;

  var WERBUNG_LONG = `<h3>Werbung – Nachteile</h3><p><b>C1/C2-Konu anlatımı ve Prüfungsvorbereitung</b></p><h4>1. Kurze Einordnung des Themas</h4><p>Werbung ist heute fast überall präsent: im Fernsehen, im Internet, auf sozialen Medien, in Apps, auf Plakaten und sogar in Suchergebnissen. Für eine Erörterung über die Nachteile ist wichtig, Werbung nicht nur als einfache Produktinformation zu betrachten. Auf C1/C2-Niveau sollte man zeigen, dass Werbung Gefühle, Wünsche, Unsicherheiten und Kaufentscheidungen beeinflussen kann.</p><p>Eine starke Grundthese kann lauten: Werbung kann zwar über Produkte informieren, führt jedoch häufig zu Manipulation, Konsumdruck, unrealistischen Erwartungen, Reizüberflutung und Datenschutzproblemen. Entscheidend ist dabei, dass man nicht pauschal sagt, Werbung sei schlecht. Besser ist eine differenzierte Argumentation: Werbung wird problematisch, wenn sie Menschen emotional steuert, künstliche Bedürfnisse erzeugt, gesellschaftliche Ideale verzerrt oder digitale Daten ausnutzt.</p><h4>2. Nachteil 1: Manipulation und künstliche Bedürfnisse</h4><p>Ein zentraler Nachteil der Werbung liegt in ihrer manipulativen Wirkung. Werbung informiert nicht nur sachlich über ein Produkt, sondern versucht häufig, Wünsche und Bedürfnisse zu erzeugen. Dafür nutzt sie emotionale Bilder, Musik, attraktive Personen, Statussymbole, Humor, Angst oder das Versprechen von Anerkennung. Der Verbraucher soll nicht nur wissen, dass ein Produkt existiert, sondern das Gefühl bekommen, dieses Produkt unbedingt zu brauchen.</p><p>Problematisch ist, dass Kaufentscheidungen dadurch weniger rational werden. Menschen kaufen nicht mehr nur, weil sie ein Produkt tatsächlich benötigen, sondern weil Werbung ein bestimmtes Lebensgefühl verspricht. Ein Parfüm steht plötzlich für Attraktivität, ein Auto für Erfolg, ein Smartphone für Zugehörigkeit und eine bestimmte Kleidung für sozialen Status. Dadurch wird Konsum mit Identität verknüpft. Wer etwas nicht besitzt, kann den Eindruck bekommen, weniger modern, weniger erfolgreich oder weniger anerkannt zu sein.</p><p>Besonders deutlich wird dies bei emotionaler Werbung. Ein Produkt wird mit Glück, Liebe, Freiheit oder Selbstverwirklichung verbunden, obwohl diese Gefühle nicht wirklich im Produkt selbst liegen. Auch Rabattaktionen und zeitlich begrenzte Angebote verstärken die Manipulation, weil sie künstliche Dringlichkeit erzeugen. Der Satz nur heute verfügbar kann Menschen dazu bringen, schneller und weniger überlegt zu kaufen.</p><table><tbody><tr><td><b>C1/C2-Wortschatz</b></td><td>die Manipulation, die Bedürfnisweckung, das Kaufverhalten, die Kaufentscheidung, die emotionale Beeinflussung, der Werbereiz, das Statussymbol, die Anerkennungssuche</td></tr><tr><td><b>Nomen-Verb-Verbindungen</b></td><td>Kaufentscheidungen beeinflussen, künstliche Bedürfnisse erzeugen, Emotionen gezielt ansprechen, kritisches Denken schwächen, Konsum mit Identität verknüpfen</td></tr></tbody></table><p><b>Musterabsatz:</b> Ein wesentlicher Nachteil der Werbung besteht darin, dass sie Kaufentscheidungen manipulieren kann. Werbung informiert nicht nur über Produkte, sondern arbeitet häufig mit Emotionen, Statussymbolen und idealisierten Bildern. Dadurch entsteht bei vielen Menschen der Eindruck, ein bestimmtes Produkt sei für Glück, Erfolg oder Anerkennung notwendig. Besonders problematisch ist, dass künstliche Bedürfnisse erzeugt werden, die vorher gar nicht vorhanden waren. Infolgedessen treffen Verbraucher ihre Entscheidungen weniger rational und kaufen Dinge, die sie eigentlich nicht benötigen. Langfristig kann Werbung somit kritisches Denken schwächen und ein konsumorientiertes Weltbild fördern.</p><h4>3. Nachteil 2: Konsumdruck und finanzielle Belastung</h4><p>Ein weiterer Nachteil besteht darin, dass Werbung starken Konsumdruck erzeugen kann. In modernen Konsumgesellschaften werden Menschen ständig mit neuen Produkten, Trends, Marken und Angeboten konfrontiert. Werbung vermittelt dabei häufig den Eindruck, dass man mithalten muss, um gesellschaftlich dazuzugehören. Wer nicht die neueste Mode, das neue Gerät oder ein bestimmtes Markenprodukt besitzt, fühlt sich möglicherweise ausgeschlossen oder weniger wertvoll.</p><p>Dieser Konsumdruck betrifft nicht nur Erwachsene, sondern auch Jugendliche und junge Erwachsene. Gerade in sozialen Medien werden Produkte durch Influencer, gesponserte Beiträge und scheinbar persönliche Empfehlungen beworben. Dadurch verschwimmt die Grenze zwischen authentischer Empfehlung und bezahlter Werbung. Nutzer haben oft das Gefühl, dass alle anderen bestimmte Produkte besitzen oder bestimmte Lebensstile führen. Dies kann dazu führen, dass man Geld ausgibt, obwohl das eigene Budget begrenzt ist.</p><p>Finanzielle Belastungen entstehen besonders durch Spontankäufe, Ratenzahlungen, Rabattaktionen und ständige Sonderangebote. Menschen kaufen Produkte, weil sie angeblich günstig sind, obwohl sie diese gar nicht brauchen. Kurzfristig fühlt sich der Kauf wie ein Erfolg an, langfristig kann er jedoch zu Geldproblemen, Unzufriedenheit und einer stärkeren Abhängigkeit vom Konsum führen. Werbung fördert dadurch nicht nur einzelne Käufe, sondern auch eine Haltung, in der Besitz und Konsum überbewertet werden.</p><table><tbody><tr><td><b>C1/C2-Wortschatz</b></td><td>der Konsumdruck, die finanzielle Belastung, der Spontankauf, die Rabattaktion, der Materialismus, das Markenbewusstsein, die Kaufentscheidung, die Überschuldung</td></tr><tr><td><b>Nomen-Verb-Verbindungen</b></td><td>Konsumdruck ausüben, finanzielle Belastung verursachen, zu Spontankäufen verleiten, materialistisches Denken fördern, das Kaufverhalten steuern</td></tr></tbody></table><p><b>Musterabsatz:</b> Ein weiterer negativer Aspekt der Werbung liegt im Konsumdruck. Durch ständige Anzeigen, Rabattaktionen und Influencer-Beiträge entsteht bei vielen Menschen der Eindruck, immer neue Produkte kaufen zu müssen. Besonders Jugendliche können sich unter Druck gesetzt fühlen, bestimmte Marken zu besitzen, um dazuzugehören. Dadurch kaufen Verbraucher häufig mehr, als sie tatsächlich benötigen. Wenn solche Käufe regelmäßig stattfinden, kann Werbung finanzielle Belastungen verursachen und materialistisches Denken verstärken. Aus gesellschaftlicher Perspektive ist dies problematisch, weil Anerkennung zunehmend an Konsum geknüpft wird.</p><h4>4. Nachteil 3: Unrealistische Ideale und Vergleichsdruck</h4><p>Werbung vermittelt häufig ideale Bilder von Schönheit, Erfolg, Jugend, Körper, Beziehung und Lebensstil. Diese Bilder sind oft stark bearbeitet, inszeniert oder unrealistisch. Dennoch wirken sie auf viele Menschen wie ein Maßstab, an dem sie sich selbst messen. Besonders problematisch ist dieser Einfluss bei Jugendlichen, weil sie sich noch in der Entwicklung ihrer Identität und ihres Selbstwertgefühls befinden.</p><p>In der Mode-, Fitness-, Kosmetik- und Lifestyle-Werbung werden häufig perfekte Körper, makellose Haut, teure Produkte und scheinbar glückliche Menschen gezeigt. Dadurch entsteht ein Vergleichsdruck. Jugendliche und Erwachsene können das Gefühl bekommen, nicht schön genug, nicht erfolgreich genug oder nicht modern genug zu sein. Werbung verstärkt also nicht nur den Wunsch nach Produkten, sondern beeinflusst auch die Wahrnehmung des eigenen Körpers und Lebens.</p><p>Die Folgen können psychisch belastend sein. Wenn Menschen ständig mit idealisierten Bildern konfrontiert werden, sinkt möglicherweise die Zufriedenheit mit dem eigenen Aussehen, dem eigenen Alltag oder der eigenen sozialen Position. Manche versuchen dann, durch Konsum, Kleidung, Kosmetik oder Fitnessprodukte ein Ideal zu erreichen, das kaum realistisch ist. Werbung kann dadurch Unsicherheit, Anerkennungssuche und ein schwächeres Selbstwertgefühl begünstigen.</p><table><tbody><tr><td><b>C1/C2-Wortschatz</b></td><td>das Schönheitsideal, der Vergleichsdruck, das Selbstwertgefühl, die Körperwahrnehmung, die Selbstdarstellung, die Anerkennungssuche, die psychische Belastung</td></tr><tr><td><b>Nomen-Verb-Verbindungen</b></td><td>unrealistische Ideale vermitteln, Vergleichsdruck erzeugen, das Selbstwertgefühl beeinträchtigen, die Körperwahrnehmung verändern, Unsicherheit verstärken</td></tr></tbody></table><p><b>Musterabsatz:</b> Besonders problematisch ist außerdem, dass Werbung unrealistische Ideale vermittelt. In vielen Anzeigen werden perfekte Körper, erfolgreiche Lebensstile und makellose Schönheit dargestellt. Diese Bilder entsprechen häufig nicht der Realität, können aber trotzdem als Orientierung dienen. Vor allem Jugendliche vergleichen sich mit solchen Darstellungen und entwickeln das Gefühl, nicht attraktiv, beliebt oder erfolgreich genug zu sein. Dadurch kann Werbung das Selbstwertgefühl beeinträchtigen und psychischen Druck verursachen. Langfristig besteht die Gefahr, dass Menschen ihren eigenen Wert stärker über Aussehen, Besitz und Anerkennung definieren.</p><h4>5. Nachteil 4: Reizüberflutung, Ablenkung und digitale Kontrolle</h4><p>Ein weiterer Nachteil der Werbung zeigt sich im digitalen Alltag. Nutzer werden beim Lesen, Lernen, Arbeiten oder Entspannen ständig mit Anzeigen, Pop-ups, Bannern, Videos und gesponserten Beiträgen konfrontiert. Diese Werbeformen unterbrechen die Konzentration und beanspruchen Aufmerksamkeit. Besonders im Internet ist Werbung oft nicht klar vom eigentlichen Inhalt getrennt. Dadurch wird es schwieriger, sich auf Informationen, Texte oder Aufgaben zu konzentrieren.</p><p>Die ständige Präsenz von Werbung kann zu Reizüberflutung führen. Menschen nehmen täglich sehr viele visuelle und sprachliche Botschaften auf, ohne diese bewusst zu verarbeiten. Das kann Stress erzeugen, die Aufmerksamkeitsspanne verringern und das Gefühl verstärken, ständig angesprochen oder beeinflusst zu werden. Werbung wird dadurch zu einem Teil der digitalen Umgebung, der kaum noch zu vermeiden ist.</p><p>Hinzu kommt die personalisierte Werbung. Plattformen sammeln Daten über Suchverhalten, Interessen, Aufenthaltsdauer, Klicks und Käufe. Auf dieser Grundlage werden Anzeigen gezielt angepasst. Dadurch entsteht ein Datenschutzproblem: Nutzer wissen oft nicht genau, welche Daten gespeichert werden und wie stark ihr Verhalten analysiert wird. Personalisierte Werbung kann daher nicht nur Konsumdruck erzeugen, sondern auch digitale Kontrolle und den Verlust von Privatsphäre verstärken.</p><table><tbody><tr><td><b>C1/C2-Wortschatz</b></td><td>die Reizüberflutung, die Ablenkung, die Aufmerksamkeitsspanne, die personalisierte Werbung, der Datenmissbrauch, die Privatsphäre, die digitale Kontrolle</td></tr><tr><td><b>Nomen-Verb-Verbindungen</b></td><td>zu Reizüberflutung führen, die Konzentration stören, Daten gezielt auswerten, die Privatsphäre beeinträchtigen, digitale Kontrolle verstärken</td></tr></tbody></table><p><b>Musterabsatz:</b> Ein weiterer Nachteil der Werbung liegt in der digitalen Reizüberflutung. Im Internet werden Nutzer ständig durch Banner, Pop-ups, kurze Werbevideos und gesponserte Beiträge unterbrochen. Dadurch kann die Konzentration beim Lesen, Lernen oder Arbeiten gestört werden. Besonders problematisch ist zudem personalisierte Werbung, weil sie auf gesammelten Nutzerdaten basiert. Plattformen werten Interessen, Suchverhalten und Klicks aus, um möglichst passende Anzeigen zu zeigen. Dadurch entstehen Datenschutzfragen und das Gefühl digitaler Kontrolle. Somit ist Werbung nicht nur ein wirtschaftliches, sondern auch ein medienkritisches Problem.</p><h4>6. Redemittel für eine C1/C2-Erörterung</h4><table><tbody><tr><td><b>Nachteil nennen</b></td><td>Ein wesentlicher Nachteil besteht darin, dass ... / Problematisch ist vor allem, dass ...</td></tr><tr><td><b>Ursache erklären</b></td><td>Dies lässt sich damit begründen, dass Werbung gezielt Emotionen und soziale Wünsche anspricht.</td></tr><tr><td><b>Folge zeigen</b></td><td>Infolgedessen treffen Verbraucher weniger rationale Kaufentscheidungen.</td></tr><tr><td><b>Bewerten</b></td><td>Langfristig betrachtet kann Werbung materialistisches Denken und digitale Abhängigkeit verstärken.</td></tr></tbody></table><h4>7. Kompakte Kopiervorlage</h4><p>Nachteil 1: Werbung arbeitet mit Emotionen und Statussymbolen. Dadurch entstehen künstliche Bedürfnisse und manipulierte Kaufentscheidungen.</p><p>Nachteil 2: Werbung erzeugt Konsumdruck. Menschen kaufen mehr, als sie brauchen, und können finanziell belastet werden.</p><p>Nachteil 3: Werbung zeigt unrealistische Ideale. Besonders Jugendliche geraten unter Vergleichsdruck und verlieren Selbstvertrauen.</p><p>Nachteil 4: Digitale Werbung führt zu Reizüberflutung, stört Konzentration und nutzt personenbezogene Daten für personalisierte Anzeigen.</p><h4>8. Prüfungsnaher Gesamtabsatz</h4><p>Zusammenfassend lässt sich sagen, dass Werbung mehrere problematische Folgen haben kann. Sie informiert nicht nur über Produkte, sondern beeinflusst Wünsche, Gefühle und Kaufentscheidungen. Durch emotionale Bilder, Statussymbole und Influencer-Beiträge können künstliche Bedürfnisse entstehen. Gleichzeitig verstärken Rabattaktionen und Trends den Konsumdruck, sodass Menschen mehr kaufen, als sie eigentlich benötigen. Besonders kritisch ist der Einfluss auf Jugendliche, weil Werbung unrealistische Schönheits- und Erfolgsideale vermittelt und dadurch Vergleichsdruck erzeugt. Im digitalen Raum kommt hinzu, dass Werbung ständig präsent ist, die Konzentration stört und auf gesammelten Nutzerdaten basiert. Aus diesem Grund sollte Werbung in einer modernen Gesellschaft nicht nur wirtschaftlich, sondern auch psychologisch, sozial und datenschutzrechtlich kritisch betrachtet werden.</p>`;

  var WERBUNG_WORDS = ['die Werbung','die Manipulation','die Bedürfnisweckung','das Kaufverhalten','die Kaufentscheidung','der Konsumdruck','die finanzielle Belastung','der Spontankauf','die Rabattaktion','der Materialismus','das Schönheitsideal','der Vergleichsdruck','das Selbstwertgefühl','die Körperwahrnehmung','die Reizüberflutung','die Ablenkung','die Aufmerksamkeitsspanne','die personalisierte Werbung','der Datenmissbrauch','die digitale Kontrolle','Kaufentscheidungen beeinflussen','künstliche Bedürfnisse erzeugen','Konsumdruck ausüben','das Selbstwertgefühl beeinträchtigen','zu Reizüberflutung führen','Daten gezielt auswerten'];

  function patchWerbungSource(){
    window.DEUTSCH_TESTS = window.DEUTSCH_TESTS || {};
    window.DEUTSCH_LESSONS = window.DEUTSCH_LESSONS || {};
    window.DEUTSCH_TESTS.t31 = Object.assign(window.DEUTSCH_TESTS.t31 || {}, {
      category:'Bevor Schreiben',
      slug:'werbung_nachteile_c1_c2_source_locked',
      title:'Werbung – Nachteile · C1/C2 Nachteilsabsatz',
      topic:'Quelle: Werbung_Nachteile_C1_C2_Konuanlatimi (1).docx · Manipulation · Konsumdruck · unrealistische Ideale · Reizüberflutung · Datenschutz',
      words: WERBUNG_WORDS
    });
    window.DEUTSCH_LESSONS.t31 = window.DEUTSCH_LESSONS.t31 || {};
    window.DEUTSCH_LESSONS.t31.short = WERBUNG_SHORT;
    window.DEUTSCH_LESSONS.t31.medium = WERBUNG_MEDIUM;
    try{
      Object.defineProperty(window.DEUTSCH_LESSONS.t31,'long',{configurable:true,enumerable:true,get:function(){return WERBUNG_LONG;},set:function(){}});
    }catch(e){
      window.DEUTSCH_LESSONS.t31.long = WERBUNG_LONG;
    }
    window.DEUTSCH_LESSONS.t31.longSourceDocx = 'Werbung_Nachteile_C1_C2_Konuanlatimi (1).docx';
    window.DEUTSCH_LESSONS.t31.longSourceWordCount = 1828;
    window.DEUTSCH_LESSONS.t31.longSourceVerified = true;
    window.WERBUNG_NACHTEILE_SOURCE_LOCK_OK = window.DEUTSCH_LESSONS.t31.long.indexOf('Werbung – Nachteile') >= 0 && window.DEUTSCH_LESSONS.t31.long.indexOf('personalisierte Werbung') >= 0;
  }

  patchWerbungSource();
  document.addEventListener('DOMContentLoaded',patchWerbungSource);
  setInterval(patchWerbungSource,300);
})();
