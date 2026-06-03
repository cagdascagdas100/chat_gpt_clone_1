(function(){
  function key(){
    var checked=document.querySelector('input[name="tc"]:checked');
    if(checked&&checked.value)return checked.value;
    try{if(typeof selected!=='undefined')return selected}catch(e){}
    return '';
  }
  function safe(v){return String(v||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]});}

  var IND_SHORT=`<h3>Individualität – Nachteile · Kurz</h3>
<p><b>Grundthese:</b> Individualität kann persönliche Freiheit ermöglichen, kann aber problematisch werden, wenn sie zu Egoismus, sozialer Distanz, Leistungsdruck oder Anpassungsproblemen führt.</p>
<ul><li><b>Soziale Isolation:</b> Zu starke Betonung des Ichs kann Zusammenhalt schwächen.</li><li><b>Egoismus:</b> Eigene Wünsche werden wichtiger als Verantwortung gegenüber anderen.</li><li><b>Leistungsdruck:</b> Menschen fühlen sich unter Druck, besonders und erfolgreich wirken zu müssen.</li><li><b>Anpassungsprobleme:</b> Wer sich gemeinsamen Regeln entzieht, hat Schwierigkeiten in Schule, Beruf und Gruppen.</li></ul>
<p><b>Merksatz:</b> Individualität bringt dann Nachteile mit sich, wenn Freiheit ohne Rücksichtnahme verstanden wird.</p>`;

  var IND_MEDIUM=`<h3>Individualität – Nachteile · Mittel</h3>
<h4>1. Grundidee</h4><p>Individualität bedeutet persönliche Freiheit, eigene Lebensgestaltung und die Möglichkeit, sich von anderen zu unterscheiden. In einer Nachteile-Erörterung darf man Individualität nicht pauschal als schlecht darstellen. Problematisch ist vor allem eine übertriebene Individualität oder eine zu starke Betonung eigener Interessen.</p>
<h4>2. Soziale Isolation</h4><p>Wenn jeder nur die eigenen Interessen verfolgt, können Rücksichtnahme, Kompromissbereitschaft und Gemeinschaftsgefühl schwächer werden. Dadurch entstehen soziale Distanz, weniger Solidarität und im Extremfall Vereinzelung.</p>
<h4>3. Egoismus und Selbstverwirklichung</h4><p>Individualität kann in Egoismus umschlagen, wenn persönliche Freiheit über alles gestellt wird. Dann geraten die Bedürfnisse anderer in den Hintergrund, wodurch Beziehungen, Teamfähigkeit und Verantwortung belastet werden.</p>
<h4>4. Leistungsdruck und Selbstdarstellung</h4><p>Vor allem soziale Medien verstärken den Eindruck, man müsse besonders, erfolgreich und einzigartig wirken. Dadurch können Vergleichsdruck, Selbstoptimierung, Unsicherheit und ein schwächeres Selbstwertgefühl entstehen.</p>
<h4>5. Anpassungsprobleme</h4><p>In Schule, Beruf und Gesellschaft sind gemeinsame Regeln, Verlässlichkeit und Kooperation notwendig. Wer ausschließlich die eigene Individualität betont, kann Schwierigkeiten haben, sich in gemeinsame Strukturen einzufügen.</p>
<h4>6. Schreibstrategie</h4><p>Ein starker Absatz verbindet Ursache, Beispiel, Folge und Bewertung. Nutze Formulierungen wie <b>kann dazu führen</b>, <b>unter bestimmten Umständen</b>, <b>langfristig betrachtet</b> und <b>nicht zu unterschätzen ist außerdem</b>.</p>`;

  var IND_LONG=`<h3>Individualität – Nachteile · C1/C2-Erörterungsvorbereitung · Vollständige Word-Version</h3>
<h4>Ziel dieses Arbeitsblatts</h4>
<p>Du lernst, wie man die Nachteile von Individualität in einer Erörterung differenziert und prüfungsnah erklärt. Der Fokus liegt auf Formulierungen, die in einer deutschen Sprachprüfung natürlich, gehoben und argumentativ sauber wirken. Alle Inhalte behandeln ausschließlich Nachteile: soziale, psychologische, schulische, berufliche und gesellschaftliche Aspekte.</p>
<p><b>Grundthese:</b> Individualität kann persönliche Freiheit ermöglichen, kann aber problematisch werden, wenn sie zu Egoismus, sozialer Distanz, Leistungsdruck oder Anpassungsproblemen führt.</p>
<h4>1. Überblick: Welche Nachteile kann Individualität haben?</h4>
<table style="width:100%;border-collapse:collapse"><tr><td><b>Nachteil</b></td><td><b>Kernidee</b></td><td><b>Prüfungslogik</b></td></tr><tr><td>Soziale Isolation und weniger Gemeinschaftsgefühl</td><td>Zu starke Betonung des Ichs kann Zusammenhalt schwächen.</td><td>Ich-Fokus → weniger Rücksicht → soziale Distanz</td></tr><tr><td>Egoismus und übertriebene Selbstverwirklichung</td><td>Eigene Wünsche werden wichtiger als Verantwortung gegenüber anderen.</td><td>Selbstverwirklichung → Egoismus → Konflikte</td></tr><tr><td>Leistungsdruck und ständige Selbstdarstellung</td><td>Menschen fühlen sich unter Druck, besonders und erfolgreich zu wirken.</td><td>Vergleich → Druck → Unsicherheit</td></tr><tr><td>Anpassungsprobleme in Schule, Beruf und Gesellschaft</td><td>Wer sich Regeln dauerhaft entzieht, hat Schwierigkeiten in Gruppen.</td><td>Individualität → Regelkonflikt → Zusammenarbeit wird schwieriger</td></tr></table>
<h4>Prüfungsstrategie</h4>
<ul><li>Nicht schreiben: Individualität ist grundsätzlich schlecht.</li><li>Besser schreiben: Übertriebene Individualität oder eine zu starke Betonung eigener Interessen kann problematisch sein.</li><li>Immer mit Alltagssituationen beginnen: Schule, soziale Medien, Beruf, Familie, Freundeskreis.</li><li>Dann erklären: Ursache → Beispiel → Folge → langfristige Wirkung.</li></ul>
<h4>2. Nachteil 1: Soziale Isolation und schwächeres Gemeinschaftsgefühl</h4>
<h5>Beobachtungen aus dem Alltag</h5><ul><li>jeder möchte anders oder besonders sein</li><li>weniger gemeinsame Werte in Gruppen</li><li>starker Fokus auf eigene Interessen</li><li>soziale Medien fördern Selbstdarstellung</li><li>weniger Bereitschaft, sich einer Gruppe anzupassen</li><li>Vergleich und Abgrenzung im Freundeskreis</li></ul>
<h5>Detailliert erklären</h5><p>Wenn Individualität sehr stark betont wird, kann das Gemeinschaftsgefühl schwächer werden. Menschen orientieren sich dann weniger an gemeinsamen Regeln oder Zielen und stärker an den eigenen Bedürfnissen. In einer Gesellschaft oder Gruppe braucht man jedoch Rücksichtnahme, gemeinsame Verantwortung und Kompromissbereitschaft. Wenn jeder nur den eigenen Weg gehen will, kann soziale Distanz entstehen. Besonders Jugendliche können dadurch das Gefühl bekommen, sich ständig abgrenzen zu müssen, statt Zugehörigkeit zu erleben.</p>
<h5>Konkrete Beispiele</h5><ul><li>Eine Schülerin beteiligt sich kaum an Gruppenaktivitäten, weil sie unabhängig bleiben will.</li><li>Im Freundeskreis entstehen Konflikte, weil jeder nur seine eigenen Pläne verfolgt.</li><li>In sozialen Medien wird Individualität stark inszeniert, echte Nähe nimmt aber ab.</li><li>Gemeinsame Regeln in Klasse oder Familie werden als Einschränkung empfunden.</li></ul>
<h5>Ergebnisse</h5><ul><li>weniger Zusammenhalt</li><li>mehr soziale Distanz</li><li>geringere Kompromissbereitschaft</li><li>Gefühl von Einsamkeit</li><li>schwächere Solidarität</li><li>oberflächlichere Beziehungen</li></ul>
<h5>C1/C2-Satzbausteine</h5><ul><li>Ein möglicher Nachteil der Individualität liegt darin, dass sie das Gemeinschaftsgefühl schwächen kann.</li><li>Wenn jeder nur seine eigenen Interessen verfolgt, kann der soziale Zusammenhalt leiden.</li><li>Dadurch nimmt die Bereitschaft ab, Rücksicht auf andere zu nehmen oder Kompromisse einzugehen.</li><li>Langfristig kann eine übertriebene Betonung des Individuums zu Vereinzelung führen.</li></ul>
<p><b>Mini-Merksatz:</b> zu viel Ich-Denken → weniger Rücksicht → soziale Distanz → Isolation</p>
<p><b>Musterabsatz:</b> Ein möglicher Nachteil der Individualität liegt darin, dass sie das Gemeinschaftsgefühl schwächen kann. Wenn Menschen vor allem ihre eigenen Interessen, Wünsche und Lebensentwürfe in den Mittelpunkt stellen, wird es schwieriger, Rücksicht auf andere zu nehmen. Besonders in Schule, Beruf oder Familie sind jedoch Kompromissbereitschaft und gemeinsame Regeln notwendig. Wird Individualität zu stark betont, können soziale Distanz und Vereinzelung entstehen. Langfristig betrachtet kann dies den Zusammenhalt innerhalb einer Gruppe oder sogar innerhalb der Gesellschaft beeinträchtigen.</p>
<h4>3. Nachteil 2: Egoismus und übertriebene Selbstverwirklichung</h4>
<h5>Beobachtungen aus dem Alltag</h5><ul><li>eigene Wünsche stehen immer im Vordergrund</li><li>weniger Verantwortung gegenüber anderen</li><li>Kritik wird schnell als Angriff verstanden</li><li>Menschen wollen sich ständig selbst verwirklichen</li><li>Teamfähigkeit und Rücksichtnahme werden schwieriger</li><li>persönliche Freiheit wird über gemeinsame Regeln gestellt</li></ul>
<h5>Detailliert erklären</h5><p>Individualität wird problematisch, wenn sie mit Egoismus verwechselt wird. Persönliche Freiheit ist wichtig, darf aber nicht bedeuten, dass die Bedürfnisse anderer ignoriert werden. In Familie, Schule und Beruf funktioniert Zusammenleben nur, wenn Menschen Verantwortung übernehmen und nicht ausschließlich die eigenen Ziele verfolgen. Übertriebene Selbstverwirklichung kann daher Beziehungen belasten und Zusammenarbeit erschweren.</p>
<h5>Konkrete Beispiele</h5><ul><li>Jemand akzeptiert keine Kritik, weil er nur seine eigene Meinung gelten lässt.</li><li>Bei Gruppenarbeiten möchte eine Person alles nach ihren Vorstellungen bestimmen.</li><li>Im Beruf werden gemeinsame Ziele vernachlässigt, weil einzelne nur an ihre Karriere denken.</li><li>In der Familie entstehen Spannungen, wenn jeder nur seinen eigenen Lebensstil durchsetzen will.</li></ul>
<h5>Ergebnisse</h5><ul><li>mehr Konflikte</li><li>weniger Teamgeist</li><li>schlechtere Zusammenarbeit</li><li>Rücksichtslosigkeit</li><li>schwächere soziale Bindungen</li><li>mehr Konkurrenzdenken</li></ul>
<h5>C1/C2-Satzbausteine</h5><ul><li>Ein weiterer Nachteil besteht darin, dass Individualität in Egoismus umschlagen kann.</li><li>Wenn persönliche Freiheit über alles gestellt wird, geraten die Bedürfnisse anderer leicht in den Hintergrund.</li><li>Dies kann soziale Beziehungen belasten und Konflikte hervorrufen.</li><li>Unter diesen Umständen wird Individualität nicht nur zur Freiheit, sondern auch zu einer Belastung für das Zusammenleben.</li></ul>
<p><b>Mini-Merksatz:</b> Selbstverwirklichung → Egoismus → Konflikte → schwächere soziale Bindungen</p>
<p><b>Musterabsatz:</b> Ein weiterer negativer Aspekt besteht darin, dass Individualität in Egoismus umschlagen kann. Persönliche Freiheit ist zwar wichtig, doch sie darf nicht dazu führen, dass Verantwortung gegenüber anderen vernachlässigt wird. Wenn jeder nur die eigenen Ziele verfolgt, geraten gemeinsame Interessen leicht in den Hintergrund. Dies kann besonders bei Teamarbeit, in Familien oder im Berufsleben zu Konflikten führen. Somit kann eine übertriebene Selbstverwirklichung das soziale Zusammenleben erheblich erschweren.</p>
<h4>4. Nachteil 3: Leistungsdruck und ständige Selbstdarstellung</h4>
<h5>Beobachtungen aus dem Alltag</h5><ul><li>Druck, besonders oder einzigartig zu sein</li><li>ständiger Vergleich in sozialen Medien</li><li>Angst, nicht interessant genug zu wirken</li><li>Selbstoptimierung als Dauerzustand</li><li>Unsicherheit durch Likes und Anerkennung</li><li>Oberflächlichkeit in der Selbstdarstellung</li></ul>
<h5>Detailliert erklären</h5><p>In modernen Gesellschaften wird Individualität oft mit Einzigartigkeit, Erfolg und besonderem Auftreten verbunden. Dadurch kann der Eindruck entstehen, man müsse ständig außergewöhnlich wirken. Vor allem soziale Medien verstärken diesen Druck: Menschen präsentieren ihren Stil, ihre Erfolge und ihr Leben. Wer sich damit vergleicht, kann schnell unzufrieden werden. Individualität kann dadurch paradoxerweise zu Anpassungsdruck führen, weil man nicht mehr einfach man selbst ist, sondern besonders erscheinen muss.</p>
<h5>Konkrete Beispiele</h5><ul><li>Jugendliche vergleichen Kleidung, Körper, Erfolge oder Lebensstil online.</li><li>Menschen posten nur positive Seiten ihres Lebens, um einzigartig zu wirken.</li><li>Schüler fühlen sich unter Druck, eine besondere Persönlichkeit darstellen zu müssen.</li><li>Im Beruf entsteht Druck, ein unverwechselbares Profil zu zeigen.</li></ul>
<h5>Ergebnisse</h5><ul><li>mehr Leistungsdruck</li><li>geringeres Selbstwertgefühl</li><li>ständige Selbstoptimierung</li><li>Stress und Unsicherheit</li><li>oberflächliche Selbstdarstellung</li><li>Angst vor Ablehnung</li></ul>
<h5>C1/C2-Satzbausteine</h5><ul><li>Problematisch ist außerdem, dass Individualität häufig mit ständiger Selbstdarstellung verbunden wird.</li><li>Dadurch entsteht der Druck, sich von anderen abheben und besonders wirken zu müssen.</li><li>Besonders soziale Medien können diesen Vergleichsdruck verstärken.</li><li>Langfristig kann dies das Selbstwertgefühl schwächen und psychischen Druck erzeugen.</li></ul>
<p><b>Mini-Merksatz:</b> Vergleich → Selbstdarstellung → Leistungsdruck → Unsicherheit</p>
<p><b>Musterabsatz:</b> Problematisch ist außerdem, dass Individualität in der heutigen Gesellschaft häufig mit Selbstdarstellung verbunden wird. Vor allem in sozialen Medien entsteht der Eindruck, man müsse besonders, erfolgreich und einzigartig wirken. Dadurch geraten viele Menschen unter Vergleichs- und Leistungsdruck. Anstatt die eigene Persönlichkeit frei zu entfalten, versuchen sie, ein möglichst interessantes Bild von sich zu zeigen. Langfristig kann dies zu Unsicherheit, Stress und einem geschwächten Selbstwertgefühl führen.</p>
<h4>5. Nachteil 4: Anpassungsprobleme in Schule, Beruf und Gesellschaft</h4>
<h5>Beobachtungen aus dem Alltag</h5><ul><li>Regeln werden als Einschränkung empfunden</li><li>gemeinsame Entscheidungen fallen schwer</li><li>Gruppenarbeit wird komplizierter</li><li>Autorität oder Vorgaben werden schnell abgelehnt</li><li>Menschen möchten nur ihren eigenen Stil durchsetzen</li><li>Konflikte zwischen Freiheit und Verantwortung</li></ul>
<h5>Detailliert erklären</h5><p>Individualität kann auch zu Anpassungsproblemen führen. In vielen Lebensbereichen gibt es Regeln, Termine und gemeinsame Ziele, die nicht beliebig verändert werden können. Wer seine Individualität sehr stark betont, kann Schwierigkeiten haben, sich in eine Gruppe, Schule oder Arbeitsstruktur einzufügen. Dadurch entstehen Spannungen zwischen persönlicher Freiheit und sozialer Verantwortung. Vor allem in der Arbeitswelt sind Zuverlässigkeit, Kooperation und gemeinsame Standards wichtig. Eine übertriebene Betonung der eigenen Besonderheit kann dort hinderlich sein.</p>
<h5>Konkrete Beispiele</h5><ul><li>Eine Person hält sich nicht an Gruppenabsprachen, weil sie lieber allein entscheidet.</li><li>Im Unterricht entstehen Probleme, wenn Regeln dauerhaft infrage gestellt werden.</li><li>Im Beruf erschwert ein sehr individueller Arbeitsstil die Abstimmung im Team.</li><li>Gemeinsame Projekte leiden darunter, dass jeder seine eigene Methode durchsetzen möchte.</li></ul>
<h5>Ergebnisse</h5><ul><li>schwierige Zusammenarbeit</li><li>mehr organisatorische Probleme</li><li>Konflikte mit Regeln und Erwartungen</li><li>geringere Verlässlichkeit</li><li>schwächere Gruppenergebnisse</li><li>Anpassungsschwierigkeiten</li></ul>
<h5>C1/C2-Satzbausteine</h5><ul><li>Ein weiterer negativer Aspekt zeigt sich in möglichen Anpassungsproblemen.</li><li>In Schule, Beruf und Gesellschaft sind gemeinsame Regeln und Verlässlichkeit notwendig.</li><li>Wer ausschließlich die eigene Individualität betont, kann Schwierigkeiten haben, sich in gemeinsame Strukturen einzufügen.</li><li>Dies kann Zusammenarbeit erschweren und Konflikte mit Erwartungen oder Regeln hervorrufen.</li></ul>
<p><b>Mini-Merksatz:</b> zu viel Eigenwilligkeit → Regelkonflikte → schwierige Zusammenarbeit → geringere Verlässlichkeit</p>
<p><b>Musterabsatz:</b> Ein weiterer Nachteil zeigt sich in möglichen Anpassungsproblemen. In vielen Bereichen des Lebens, etwa in der Schule oder im Beruf, sind gemeinsame Regeln, Zuverlässigkeit und Kooperation unverzichtbar. Wer jedoch die eigene Individualität übermäßig betont, kann Schwierigkeiten haben, sich in solche Strukturen einzufügen. Dies kann die Zusammenarbeit erschweren und Konflikte mit Erwartungen oder Vorgaben hervorrufen. Deshalb kann Individualität dann problematisch werden, wenn sie gemeinsame Verantwortung und Verlässlichkeit verdrängt.</p>
<h4>6. C1/C2-Wortschatz für die Erörterung</h4>
<table style="width:100%;border-collapse:collapse"><tr><td><b>Bereich</b></td><td><b>Nomen</b></td><td><b>Starke Verben / NVV</b></td></tr><tr><td>Gemeinschaft</td><td>der Zusammenhalt; das Gemeinschaftsgefühl; die Solidarität; die Rücksichtnahme; die soziale Distanz; die Vereinzelung</td><td>den Zusammenhalt schwächen; Rücksicht nehmen auf; Kompromisse eingehen; soziale Distanz schaffen; zu Vereinzelung führen</td></tr><tr><td>Egoismus</td><td>die Selbstverwirklichung; die Eigeninteressen; die Rücksichtslosigkeit; die Verantwortung; die Teamfähigkeit; die soziale Bindung</td><td>eigene Interessen in den Vordergrund stellen; Verantwortung vernachlässigen; die Teamfähigkeit beeinträchtigen; Konflikte verursachen</td></tr><tr><td>Selbstdarstellung</td><td>die Anerkennungssuche; der Vergleichsdruck; die Selbstoptimierung; das Selbstwertgefühl; die Oberflächlichkeit</td><td>nach Anerkennung streben; unter Druck geraten; sich mit anderen vergleichen; das Selbstwertgefühl schwächen</td></tr><tr><td>Anpassung</td><td>die Anpassungsfähigkeit; die Regelakzeptanz; die Verlässlichkeit; die Kooperationsbereitschaft; die Eigenwilligkeit</td><td>sich in Strukturen einfügen; Regeln akzeptieren; Kooperation erschweren; Erwartungen nicht erfüllen</td></tr></table>
<h4>7. Einfach → C1/C2</h4><table style="width:100%;border-collapse:collapse"><tr><td>Individualität macht Menschen einsam.</td><td>Eine übertriebene Betonung der Individualität kann soziale Isolation begünstigen.</td></tr><tr><td>Jeder denkt nur an sich.</td><td>Eigeninteressen können zu stark in den Vordergrund treten.</td></tr><tr><td>Man will immer besonders sein.</td><td>Der Wunsch nach Einzigartigkeit kann zu Selbstdarstellungs- und Leistungsdruck führen.</td></tr><tr><td>Man passt nicht gut in Gruppen.</td><td>Zu starke Eigenwilligkeit kann die Anpassung an gemeinsame Strukturen erschweren.</td></tr><tr><td>Es gibt mehr Streit.</td><td>Unterschiedliche Vorstellungen können Konflikte hervorrufen und das Zusammenleben belasten.</td></tr></table>
<h4>8. Konnektoren und argumentative Struktur</h4><table style="width:100%;border-collapse:collapse"><tr><td><b>Funktion</b></td><td><b>Formulierungen</b></td></tr><tr><td>Argument einleiten</td><td>Ein zentraler Nachteil besteht darin, dass ...; Problematisch ist vor allem, dass ...; Aus gesellschaftlicher Sicht ist kritisch, dass ...</td></tr><tr><td>Begründen</td><td>Dies lässt sich damit erklären, dass ...; Der Grund dafür liegt darin, dass ...; Dies ist darauf zurückzuführen, dass ...</td></tr><tr><td>Beispiel nennen</td><td>Dies zeigt sich beispielsweise daran, dass ...; Ein typisches Beispiel dafür ist ...; Besonders im Alltag wird deutlich, dass ...</td></tr><tr><td>Folge erklären</td><td>Dies führt dazu, dass ...; Infolgedessen ...; Dadurch kann ...; Somit besteht die Gefahr, dass ...</td></tr><tr><td>Vorsichtig formulieren</td><td>kann dazu führen; könnte begünstigen; unter bestimmten Umständen; langfristig betrachtet; nicht selten</td></tr></table>
<h4>Grundstruktur eines Nachteilsabsatzes</h4><ol><li>Nachteil nennen: Ein zentraler Nachteil liegt darin, dass ...</li><li>Erklärung geben: Dies lässt sich damit erklären, dass ...</li><li>Beispiel einbauen: Besonders in Schule/Beruf/sozialen Medien zeigt sich ...</li><li>Folge erklären: Dadurch kann ...</li><li>Schlussfolgerung: Langfristig betrachtet besteht die Gefahr, dass ...</li></ol>
<h4>9. Kurze Kopiervorlage für die Prüfung</h4><table style="width:100%;border-collapse:collapse"><tr><td><b>Soziale Isolation</b></td><td>Ich-Fokus → weniger Rücksicht → soziale Distanz</td><td>der Zusammenhalt; die Rücksichtnahme; die Vereinzelung</td></tr><tr><td><b>Egoismus</b></td><td>Selbstverwirklichung → Eigeninteressen → Konflikte</td><td>der Egoismus; die Verantwortung; die Rücksichtslosigkeit</td></tr><tr><td><b>Leistungsdruck</b></td><td>Vergleich → Selbstdarstellung → Unsicherheit</td><td>der Vergleichsdruck; die Anerkennungssuche; das Selbstwertgefühl</td></tr><tr><td><b>Anpassungsprobleme</b></td><td>Eigenwilligkeit → Regelkonflikt → schwierige Zusammenarbeit</td><td>die Anpassungsfähigkeit; die Regelakzeptanz; die Kooperationsbereitschaft</td></tr></table>
<h4>Prüfungsstarke Kurzsätze</h4><ul><li>Individualität kann problematisch werden, wenn sie zu stark auf Eigeninteressen reduziert wird.</li><li>Eine übertriebene Betonung des Ichs kann den gesellschaftlichen Zusammenhalt schwächen.</li><li>Soziale Medien können den Druck verstärken, sich ständig als besonders darzustellen.</li><li>In Schule und Beruf kann zu starke Eigenwilligkeit die Zusammenarbeit erschweren.</li><li>Insgesamt bringt Individualität dann Nachteile mit sich, wenn Freiheit ohne Rücksichtnahme verstanden wird.</li></ul>
<h4>10. Kleine Übungen zur Aktivierung</h4><h5>A. Formuliere die einfachen Sätze auf C1/C2-Niveau um.</h5><ol><li>Zu viel Individualität macht Menschen egoistisch.</li><li>Viele wollen nur besonders sein.</li><li>Dann gibt es weniger Gemeinschaft.</li><li>Man kann schlechter mit anderen arbeiten.</li><li>Soziale Medien machen den Druck größer.</li></ol><h5>B. Ergänze passende Wörter</h5><p><b>Zusammenhalt – Selbstdarstellung – Rücksichtnahme – Vergleichsdruck – Anpassungsprobleme</b></p><ol><li>Eine zu starke Betonung der eigenen Interessen kann den __________ schwächen.</li><li>In sozialen Medien spielt __________ eine große Rolle.</li><li>Wenn Menschen sich ständig vergleichen, entsteht __________.</li><li>Ohne __________ wird das Zusammenleben schwieriger.</li><li>In Schule und Beruf können durch übertriebene Individualität __________ entstehen.</li></ol><h5>C. Schreibe einen eigenen Nachteilsabsatz</h5><ul><li>Ein zentraler Nachteil der Individualität liegt darin, dass ...</li><li>Dies lässt sich damit erklären, dass ...</li><li>Ein Beispiel dafür ist ...</li><li>Dadurch kann ...</li><li>Langfristig betrachtet besteht die Gefahr, dass ...</li></ul>`;

  function render(level){
    var tests=window.DEUTSCH_TESTS||{};
    var lessons=window.DEUTSCH_LESSONS||{};
    var test=tests.t28||{};
    var lesson=lessons.t28&&lessons.t28[level];
    if(!lesson){lesson='<h3>Teamarbeit – Nachteile</h3><p>Teamarbeit kann zwar kreative Prozesse fördern, führt jedoch häufig zu Konflikten, Zeitverlust, ungleicher Arbeitsverteilung und verwässerter Verantwortlichkeit.</p>';}
    if(typeof hide==='function')hide();
    document.getElementById('lesson').classList.remove('hide');
    document.getElementById('lessonTitle').textContent='Konu anlatımı: '+(test.title||'Teamarbeit – Nachteile · C1/C2 Nachteilsabsatz');
    document.getElementById('lessonMeta').textContent='Seviye: '+(level==='short'?'Kısa':level==='medium'?'Orta':'Uzun')+' · C1/C2 Nachteilsabsatz';
    var words=(test.words||[]).slice(0,level==='short'?8:level==='medium'?16:28).map(function(w){return '<li>'+safe(w)+'</li>';}).join('');
    document.getElementById('lessonContent').innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>1. Genel bakış</h2><p><b>Thema:</b> '+safe(test.topic||'Teamarbeit – Nachteile')+'</p>'+(words?'<h3>Öncelikli kavramlar</h3><ul>'+words+'</ul>':'')+'</section><section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>2. Konu açıklaması</h2>'+lesson+'</section>';
    document.getElementById('lesson').scrollIntoView({behavior:'smooth'});
  }
  function renderIndividualitaet(level){
    var tests=window.DEUTSCH_TESTS||{};
    var test=tests.t29||{};
    var lesson=level==='short'?IND_SHORT:level==='medium'?IND_MEDIUM:IND_LONG;
    if(typeof hide==='function')hide();
    document.getElementById('lesson').classList.remove('hide');
    document.getElementById('lessonTitle').textContent='Konu anlatımı: '+(test.title||'Individualität – Nachteile · C1/C2 Nachteilsabsatz');
    document.getElementById('lessonMeta').textContent='Seviye: '+(level==='short'?'Kısa':level==='medium'?'Orta':'Uzun')+' · tam Word yapısı zorla gösteriliyor';
    var words=(test.words||[]).slice(0,level==='short'?8:level==='medium'?18:32).map(function(w){return '<li>'+safe(w)+'</li>';}).join('');
    document.getElementById('lessonContent').innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>1. Genel bakış</h2><p><b>Thema:</b> '+safe(test.topic||'Individualität – Nachteile')+'</p>'+(words?'<h3>Öncelikli kavramlar</h3><ul>'+words+'</ul>':'')+'</section><section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>2. Konu açıklaması</h2>'+lesson+'</section>';
    document.getElementById('lesson').scrollIntoView({behavior:'smooth'});
  }
  function bind(){
    [['btnLessonShort','short'],['btnLessonMedium','medium'],['btnLessonLong','long']].forEach(function(pair){
      var btn=document.getElementById(pair[0]);
      if(!btn||btn.dataset.teamarbeitIndividualitaetForce==='2')return;
      btn.dataset.teamarbeitIndividualitaetForce='2';
      btn.addEventListener('click',function(ev){
        if(key()==='t28'){
          ev.preventDefault();ev.stopImmediatePropagation();render(pair[1]);return false;
        }
        if(key()==='t29'){
          ev.preventDefault();ev.stopImmediatePropagation();renderIndividualitaet(pair[1]);return false;
        }
      },true);
    });
  }
  function loadIndividualitaetData(){
    if((window.DEUTSCH_TESTS||{}).t29)return;
    if(document.querySelector('script[data-individualitaet-nachteile="1"]'))return;
    var s=document.createElement('script');
    s.src='data_bevor_individualitaet_nachteile.js?v=1';
    s.dataset.individualitaetNachteile='1';
    s.onload=function(){setTimeout(injectIndividualitaetOption,100);};
    document.head.appendChild(s);
  }
  function injectIndividualitaetOption(){
    var tests=window.DEUTSCH_TESTS||{};
    var t=tests.t29;
    if(!t)return;
    var list=document.getElementById('testList');
    if(!list||document.querySelector('input[name="tc"][value="t29"]'))return;
    var txt=list.textContent||'';
    if(txt.indexOf('Teamarbeit')<0&&txt.indexOf('Bevor Schreiben')<0&&txt.indexOf('Mindestlohn')<0)return;
    var label=document.createElement('label');
    label.className='opt';
    label.style.display='block';
    label.style.margin='8px 0';
    label.innerHTML='<input type="radio" name="tc" value="t29"> <b>'+safe(t.title)+'</b><br><span class="muted">'+safe(t.topic)+'</span>';
    var input=label.querySelector('input');
    input.addEventListener('change',function(){try{selected='t29'}catch(e){};var m=document.getElementById('modeControls');if(m)m.classList.remove('hide');});
    label.addEventListener('click',function(){input.checked=true;try{selected='t29'}catch(e){};var m=document.getElementById('modeControls');if(m)m.classList.remove('hide');});
    var team=document.querySelector('input[name="tc"][value="t28"]');
    if(team&&team.closest('label')) team.closest('label').after(label); else list.appendChild(label);
  }
  document.addEventListener('DOMContentLoaded',function(){bind();loadIndividualitaetData();setTimeout(injectIndividualitaetOption,500);});
  setInterval(function(){bind();loadIndividualitaetData();injectIndividualitaetOption();},700);
  window.forceTeamarbeitLesson=render;
  window.forceIndividualitaetLesson=renderIndividualitaet;
})();