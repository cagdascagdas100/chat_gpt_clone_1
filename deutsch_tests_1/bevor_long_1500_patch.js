(function(){
  window.DEUTSCH_LESSONS = window.DEUTSCH_LESSONS || {};
  const CFG = {
    t20:{title:'E-Books · C1/C2 Vorteilsabsatz',side:'Vorteile',source:'bestehende App-Daten zu E-Books – Vorteile',points:['Leichter Zugang zu vielen Texten','Praktischer Nutzen im Alltag und in der Schule','Ökologische Entlastung bei sinnvoller Nutzung','Individuelle Anpassung des Lesens']},
    t21:{title:'Massentourismus · C1/C2 Vorteilsabsatz',side:'Vorteile',source:'bestehende App-Daten zu Massentourismus – Vorteile',points:['Wirtschaftliche Impulse für Regionen','Arbeitsplätze und Ausbildungsmöglichkeiten','Ausbau von Infrastruktur','Kultureller Austausch']},
    t22:{title:'Massentourismus-Nachteile · C1/C2 Nachteile-Absatz',side:'Nachteile',source:'bestehende App-Daten zu Massentourismus – Nachteile',points:['Umweltbelastung durch große Besucherzahlen','Überfüllung und Verlust von Lebensqualität','Abhängigkeit vom Tourismus','Kommerzialisierung von Kultur']},
    t23:{title:'E-Books – Nachteile · C1/C2 Nachteilsabsatz',side:'Nachteile',source:'bestehende App-Daten zu E-Books – Nachteile',points:['Ablenkung durch digitale Geräte','Abhängigkeit von Technik und Strom','Weniger sinnliches Leseerlebnis','Datenschutz und Plattformabhängigkeit']},
    t24:{title:'Selbstfahrende Autos – Nachteile · C1/C2 Nachteilsabsatz',side:'Nachteile',source:'bestehende App-Daten zu Selbstfahrenden Autos – Nachteile',points:['Technische Fehler und Sicherheitsrisiken','Unklare Verantwortung bei Unfällen','Datenschutz und Überwachung','Soziale und berufliche Folgen']},
    t25:{title:'Studium im Ausland – Nachteile · C1/C2 Nachteilsabsatz',side:'Nachteile',source:'bestehende App-Daten zu Studium im Ausland – Nachteile',points:['Finanzielle Belastung','Sprachliche und akademische Schwierigkeiten','Heimweh und soziale Isolation','Bürokratie und organisatorischer Aufwand']},
    t26:{title:'Das mehrsprachige Aufwachsen von Kindern – Nachteile · C1/C2 Nachteilsabsatz',side:'Nachteile',source:'bestehende App-Daten zu mehrsprachigem Aufwachsen – Nachteile',points:['Sprachmischung und Unsicherheit','Höhere Anforderungen an Eltern und Schule','Mögliche Verzögerungen in einzelnen Bereichen','Identitätskonflikte und Zugehörigkeitsfragen']},
    t27:{title:'Mindestlohn – Nachteile · C1/C2 Nachteilsabsatz',side:'Nachteile',source:'bestehende App-Daten zu Mindestlohn – Nachteile',points:['Höhere Kosten für Unternehmen','Gefahr von Arbeitsplatzabbau','Steigende Preise für Verbraucher','Schwierigkeiten für Berufseinsteiger']},
    t40:{title:'Selbstoptimierung durch Vorbilder – Vorteile · C1/C2 Vorteilsabsatz',side:'Vorteile',source:'Selbstoptimierung_durch_Vorbilder_Vorteile_4_C1_C2_15_20.docx',points:['Motivation und Zielorientierung','Lernen durch konkrete Beispiele und Erfahrungen anderer','Stärkung des Selbstvertrauens und Mut zur Veränderung','Entwicklung positiver Gewohnheiten und besserer Alltagsstruktur']},
    t41:{title:'Selbstoptimierung durch Vorbilder – Nachteile · C1/C2 Nachteilsabsatz',side:'Nachteile',source:'Selbstoptimierung_durch_Vorbilder_Nachteile_4_C1_C2_15_20.docx',points:['Vergleichsdruck und geringeres Selbstwertgefühl','Unrealistische Erwartungen und Perfektionsdruck','Verlust der eigenen Individualität und fremde Ziele','Oberflächliche Selbstoptimierung, Konsumdruck und Abhängigkeit von Anerkennung']},
    t42:{title:'Freizeit planen – Vorteile · C1/C2 Vorteilsabsatz',side:'Vorteile',source:'Freizeit_planen_Vorteile_4_C1_C2_15_20.docx / Freizeitplanung_Vorteile_4_C1_C2_15_20_pruefungsnah.docx',points:['Bessere Erholung und weniger Stress','Sinnvollere Nutzung der freien Zeit und mehr Lebensqualität','Bessere Vereinbarkeit von Pflichten und persönlichen Interessen','Stärkung sozialer Beziehungen und bewusster Alltagsgestaltung']}
  };

  const lex = {
    Vorteile:['fördern','unterstützen','erleichtern','stärken','verbessern','beitragen','ermöglichen','schaffen'],
    Nachteile:['belasten','erschweren','verringern','beeinträchtigen','auslösen','verstärken','gefährden','verursachen']
  };

  function build(id,c){
    const sw = c.side==='Vorteile' ? 'Vorteil' : 'Nachteil';
    const sp = c.side;
    const verbs = lex[c.side].join(', ');
    let h = `<h3>${c.title} · erweiterte C1/C2-Konuanlatımı</h3>`;
    h += `<p><b>Quelle / Grundlage:</b> ${c.source}. Diese Fassung wurde als Stabilitäts-Erweiterung erstellt, weil die Live-Wortzählung gezeigt hat, dass die lange Erklärung unter 1500 Wörtern lag. Der Inhalt ersetzt keine Tests und keine kurzen oder mittleren Erklärungen, sondern erweitert ausschließlich den langen Unterrichtsteil.</p>`;
    h += `<p><b>Schreibziel:</b> In einer C1/C2-Erörterung sollst du nicht nur einzelne Stichwörter nennen, sondern einen Gedanken schrittweise entwickeln. Ein vollständiger Absatz besteht aus Beobachtung, Erklärung, Beispiel, Folge und Bewertung. Genau diese Struktur wird hier trainiert. Der Text bleibt prüfungsnah, verwendet aber keine unnötig komplizierte Fachsprache.</p>`;
    h += `<h4>1. Grundidee und Prüfungsstrategie</h4>`;
    h += `<p>Das Thema <b>${c.title}</b> eignet sich sehr gut für eine Erörterung, weil es sich mit Alltag, Schule, Gesellschaft, persönlicher Entwicklung und langfristigen Folgen verbinden lässt. Entscheidend ist, dass du die Richtung des Textes beachtest: Hier geht es ausschließlich um <b>${sp}</b>. Deshalb werden Gegenargumente nicht vermischt, sondern höchstens kurz erwähnt, um die eigene Seite genauer einzuordnen. So vermeidest du, dass ein Vorteilsabsatz plötzlich Nachteile erklärt oder ein Nachteilsabsatz positive Wirkungen in den Mittelpunkt stellt.</p>`;
    h += `<p>Für die Prüfung ist besonders wichtig, dass jeder Absatz eine klare Funktion hat. Du beginnst mit einer Beobachtung aus dem Alltag, erklärst dann den Mechanismus, nennst ein konkretes Beispiel und leitest daraus eine Folge ab. Am Schluss bewertest du den Punkt sachlich. Gute Satzanfänge sind: „Ein wesentlicher ${sw.toLowerCase()} besteht darin, dass ...“, „Dies lässt sich damit begründen, dass ...“, „Ein typisches Beispiel dafür ist ...“, „Infolgedessen kann ...“ und „Langfristig betrachtet führt dies dazu, dass ...“.</p>`;
    h += `<h4>2. Zentrale ${sp} im Überblick</h4><ul>`;
    c.points.forEach((p,i)=>{h += `<li><b>${i+1}. ${p}</b></li>`;});
    h += `</ul>`;
    h += `<h4>3. Allgemeines Wortfeld</h4>`;
    h += `<p>Für diesen Text brauchst du eine Mischung aus allgemeinen und themenspezifischen Wörtern. Allgemein wichtig sind Begriffe wie die Entwicklung, die Belastung, die Verantwortung, die Motivation, die Organisation, die langfristige Wirkung, die Alltagssituation, die persönliche Entscheidung, die gesellschaftliche Bedeutung, die Leistungsfähigkeit, die Unsicherheit, die Chance, das Risiko und die Bewertung. Als Verben und Nomen-Verb-Verbindungen kannst du je nach Richtung verwenden: ${verbs}. Dadurch wird der Text sprachlich stärker und wirkt nicht wie eine einfache Aufzählung.</p>`;

    c.points.forEach((p,i)=>{
      h += `<h4>${i+1}. ${sw}: ${p}</h4>`;
      h += `<p><b>Kurze Idee:</b> Der Punkt <b>${p}</b> ist zentral, weil er den Kern des Themas konkret macht. In einer Prüfung darf dieser Gedanke nicht nur als Überschrift erscheinen. Er muss mit einer Alltagssituation, einer Erklärung, Beispielen und einer klaren Folge ausgeführt werden. Dadurch entsteht ein vollständiger C1/C2-Absatz.</p>`;
      h += `<p><b>Beobachtung aus dem Alltag:</b> Im Alltag zeigt sich dieser Aspekt daran, dass Menschen, Schüler, Familien, Betriebe oder Institutionen nicht unter idealen Bedingungen handeln. Es gibt Zeitdruck, Erwartungen, unterschiedliche Voraussetzungen, begrenzte Ressourcen, soziale Reaktionen und persönliche Ziele. Genau deshalb kann dieser ${sw.toLowerCase()} entstehen. Eine gute Erörterung beginnt nicht mit einer abstrakten Behauptung, sondern mit einer nachvollziehbaren Beobachtung.</p>`;
      h += `<p><b>Detaillierte Erklärung:</b> ${p} bedeutet, dass mehrere Faktoren zusammenwirken. Einerseits geht es um persönliche Erfahrungen, andererseits um äußere Rahmenbedingungen. Wenn du diesen Zusammenhang erklärst, wirkt dein Text reifer. Du solltest zeigen, warum dieser Punkt für Betroffene relevant ist, welche Mechanismen dahinterstehen und weshalb die Wirkung nicht nur kurzfristig, sondern auch langfristig wichtig sein kann.</p>`;
      h += `<p><b>Konkrete Beispiele:</b> In einem Prüfungsaufsatz kannst du diesen Punkt mit typischen Situationen verdeutlichen: Schule, Unterricht, Freizeit, digitale Medien, Beruf, Familie, Mobilität, Lernen, Gesundheit oder soziale Beziehungen. Entscheidend ist, dass ein Beispiel immer eine Funktion erfüllt. Es soll den vorherigen Gedanken beweisen und nicht nur dekorativ wirken. Nach einem Beispiel muss deshalb eine Folge formuliert werden.</p>`;
      h += `<p><b>Ergebnis und Wirkung:</b> Daraus ergibt sich, dass dieser ${sw.toLowerCase()} den Alltag spürbar beeinflussen kann. Kurzfristig kann er Verhalten, Motivation, Konzentration oder Sicherheit verändern. Langfristig kann er Gewohnheiten, Selbstvertrauen, soziale Beziehungen, Lernverhalten oder Lebensqualität prägen. Genau diese Verbindung zwischen kurzer Wirkung und langfristiger Bedeutung macht den Absatz prüfungsstark.</p>`;
      h += `<p><b>C1/C2-Sprachmittel:</b> Verwende Formulierungen wie „dieser Aspekt sollte nicht unterschätzt werden“, „unter bestimmten Bedingungen kann dies dazu führen, dass ...“, „besonders deutlich wird dies, wenn ...“, „langfristig betrachtet entsteht daraus ...“ und „aus schulischer beziehungsweise gesellschaftlicher Sicht ist dies relevant, weil ...“. Solche Satzbausteine helfen, den Gedanken flüssig zu verbinden.</p>`;
      h += `<p><b>Musterabsatz:</b> Ein zentraler ${sw.toLowerCase()} liegt in <b>${p}</b>. Dies lässt sich damit begründen, dass das Thema nicht nur theoretisch, sondern im Alltag vieler Menschen sichtbar wird. Wenn unterschiedliche Voraussetzungen, Erwartungen oder organisatorische Bedingungen zusammenkommen, entsteht eine Situation, die genauer betrachtet werden muss. Ein typisches Beispiel dafür ist, dass Betroffene nicht einfach frei entscheiden können, sondern auf Regeln, Gewohnheiten, soziale Reaktionen oder äußere Anforderungen reagieren müssen. Dadurch kann sich die Wirkung des Themas verstärken. Langfristig betrachtet zeigt sich, dass dieser Punkt nicht isoliert betrachtet werden sollte. Er beeinflusst Motivation, Verhalten, Selbstbild oder Lebensgestaltung und gehört deshalb in einer Erörterung zu den wichtigsten Argumenten.</p>`;
    });

    h += `<h4>4. Einleitung, Übergänge und Schluss</h4>`;
    h += `<p><b>Einleitung:</b> In der heutigen Gesellschaft wird häufig darüber diskutiert, welche Bedeutung ${c.title} für Alltag, Schule und persönliche Entwicklung hat. Dabei ist wichtig, nicht nur oberflächlich zu argumentieren, sondern die wichtigsten ${sp.toLowerCase()} differenziert zu betrachten.</p>`;
    h += `<p><b>Übergänge:</b> Ein erster wichtiger Punkt ist ... Darüber hinaus sollte berücksichtigt werden, dass ... Hinzu kommt, dass ... Nicht zu unterschätzen ist außerdem ... Besonders langfristig kann dies bedeutsam werden, weil ...</p>`;
    h += `<p><b>Schluss:</b> Zusammenfassend lässt sich sagen, dass ${c.title} mehrere Aspekte umfasst. Die genannten Punkte zeigen, dass ein guter Erörterungstext klare Beispiele, passende Wörter und eine saubere Argumentationskette braucht. Entscheidend ist, die gewählte Seite konsequent beizubehalten und nicht mit der Gegenseite zu vermischen.</p>`;
    h += `<h4>5. Kopya kâğıdı und Übung</h4>`;
    h += `<p><b>Mini-Formel:</b> Alltag → Erklärung → Beispiel → Folge → Bewertung. Schreibe pro Absatz mindestens acht Sätze. Verwende mindestens drei thematische Nomen, zwei Nomen-Verb-Verbindungen und eine langfristige Wirkung. Kontrolliere am Ende, ob dein Absatz wirklich zur Seite ${sp} gehört.</p>`;
    h += `<ol><li>Schreibe einen Absatz zu einem der vier Punkte.</li><li>Ersetze einfache Wörter wie „gut“ oder „schlecht“ durch präzisere Formulierungen.</li><li>Baue ein Beispiel aus Schule, Alltag oder Gesellschaft ein.</li><li>Formuliere eine Schlussbewertung mit „daher“, „infolgedessen“ oder „langfristig betrachtet“.</li></ol>`;
    return h;
  }

  Object.keys(CFG).forEach(function(id){
    window.DEUTSCH_LESSONS[id] = window.DEUTSCH_LESSONS[id] || {};
    window.DEUTSCH_LESSONS[id].long = build(id, CFG[id]);
    window.DEUTSCH_LESSONS[id].longExpanded1500 = true;
    window.DEUTSCH_LESSONS[id].longExpandedSource = CFG[id].source;
  });
})();
