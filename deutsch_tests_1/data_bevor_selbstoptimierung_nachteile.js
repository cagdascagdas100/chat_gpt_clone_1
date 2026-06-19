(function(){
  var KEY='t41';
  window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
  window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
  window.LESSONS=window.LESSONS||{};
  var title='Selbstoptimierung durch Vorbilder – Nachteile · C1/C2 Nachteilsabsatz';
  var topic='Erörterung · Selbstoptimierung durch Vorbilder · Nachteile · Vergleichsdruck · Perfektionsdruck · Individualität · Konsumdruck';
  var source='Selbstoptimierung_durch_Vorbilder_Nachteile_4_C1_C2_15_20(1).docx';
  var words=['der Vergleichsdruck','das Selbstwertgefühl','die Unsicherheit','die Selbstzweifel','der Leistungsdruck','die Selbstoptimierung','die Zielorientierung','das Vorbild','die Nachahmung','die Anerkennungssuche','die psychische Belastung','die Individualität','die Authentizität','die Fremdbestimmung','der Perfektionsdruck','die Überforderung','die Erschöpfung','die Burnout-Gefahr','der Produktivitätsdruck','die Fehlerangst','die Dauerbelastung','die Belastungsgrenze','die Selbstdarstellung','der Konsumdruck','die äußere Bestätigung','die oberflächliche Selbstoptimierung','das Influencer-Marketing','die finanzielle Belastung','die Konsumkultur','die Selbstinszenierung','sich ständig vergleichen','unter Druck geraten','das Selbstwertgefühl schwächen','unrealistische Erwartungen wecken','eigene Ziele aus den Augen verlieren','fremde Maßstäbe übernehmen','nach Anerkennung streben','psychische Belastung verursachen','Authentizität verlieren','Konsumdruck ausüben','Anerkennung suchen'];
  var fill=[
    ['Vorbilder können starken ____ erzeugen, wenn Menschen sich ständig mit ihnen vergleichen.','Vergleichsdruck','Nachteil 1'],
    ['Das ____ kann leiden, wenn man sich nicht gut genug fühlt.','Selbstwertgefühl','Nachteil 1'],
    ['Soziale Medien zeigen oft nur perfekte Ergebnisse und erzeugen ein ____ Bild.','verzerrtes','Nachteil 1'],
    ['Ein weiterer Nachteil besteht darin, dass Vorbilder unrealistische Erwartungen ____ können.','wecken','Nachteil 2'],
    ['Pausen werden dann manchmal als ____ empfunden.','Schwäche','Nachteil 2'],
    ['Langfristig kann Perfektionsdruck zu psychischer ____ führen.','Erschöpfung','Nachteil 2'],
    ['Wer fremde Lebensmodelle unkritisch übernimmt, kann die eigene ____ verlieren.','Individualität','Nachteil 3'],
    ['Vorbilder sollten Orientierung geben, aber nicht die eigenen Entscheidungen ____.','ersetzen','Nachteil 3'],
    ['Selbstoptimierung kann oberflächlich werden, wenn sie mit ____ verbunden wird.','Konsum','Nachteil 4'],
    ['Likes und Kommentare können zu einer Abhängigkeit von äußerer ____ führen.','Anerkennung','Nachteil 4'],
    ['Ein typischer Satzbaustein lautet: Ein zentraler Nachteil liegt ____, dass ...','darin','Satzbau'],
    ['Die feste Verbindung lautet: sich ___ Vorbildern orientieren.','an','Präposition'],
    ['Die feste Verbindung lautet: unter Druck ____.','geraten','NVV'],
    ['Die feste Verbindung lautet: das Selbstwertgefühl ____.','schwächen','NVV'],
    ['Die feste Verbindung lautet: fremde Maßstäbe ____.','übernehmen','NVV']
  ];
  var mc=[
    ['Welche Nomen-Verb-Verbindung ist korrekt?',['Vergleichsdruck erzeugen','Vergleichsdruck machen','Vergleichsdruck geben lassen','Vergleichsdruck besitzen','Vergleichsdruck sprechen'],0,'NVV'],
    ['Welche Präposition passt? Menschen orientieren sich ___ Vorbildern.',['an','auf','für','wegen','über'],0,'Präposition'],
    ['Welche Formulierung ist für einen Nachteilsabsatz passend?',['Ein zentraler Nachteil liegt darin, dass ...','Ein zentraler Nachteil macht, dass ...','Ein Nachteil ist wegen, dass ...','Ein Nachteil hat zu sein, dass ...','Nachteil bedeutet immer, weil ...'],0,'Satzbaustein'],
    ['Welche Verbindung ist korrekt?',['das Selbstwertgefühl schwächen','das Selbstwertgefühl machen','das Selbstwertgefühl tun','das Selbstwertgefühl herstellen','das Selbstwertgefühl bestehen'],0,'NVV'],
    ['Welche Verbindung passt zu Nachteil 2?',['unrealistische Erwartungen wecken','unrealistische Erwartungen essen','unrealistische Erwartungen sitzen','unrealistische Erwartungen schauen','unrealistische Erwartungen bezahlen'],0,'NVV'],
    ['Welche Formulierung drückt eine Folge aus?',['Dies führt dazu, dass ...','Dies obwohl dazu, dass ...','Dies außer dazu, dass ...','Dies trotzdem damit ...','Dies ohne dass weil ...'],0,'Konnektor'],
    ['Welche Verbindung passt zu Individualität?',['eigene Ziele aus den Augen verlieren','eigene Ziele auf den Händen tragen','eigene Ziele in den Augen kochen','eigene Ziele nebenbei kaufen','eigene Ziele über die Straße verlieren'],0,'Redemittel'],
    ['Welche Präposition ist korrekt? Menschen geraten ___ Druck.',['unter','an','bei','aus','gegen'],0,'Präposition'],
    ['Welche Formulierung passt zur kritischen Bewertung?',['Vorbilder sollten kritisch betrachtet und nicht blind übernommen werden.','Vorbilder müssen blind kopiert werden.','Vorbilder sind grammatisch immer perfekt.','Vorbilder ersetzen jede eigene Entscheidung.','Vorbilder verhindern alle Nachteile automatisch.'],0,'Bewertung'],
    ['Welche Verbindung passt zu Nachteil 4?',['Konsumdruck ausüben','Konsumdruck schlafen','Konsumdruck trinken','Konsumdruck sammeln ohne Objekt','Konsumdruck fallen'],0,'NVV'],
    ['Welche Satzstruktur passt zum Nachteilsabsatz?',['Beobachtung – Erklärung – Beispiel – Folge – Risiko – Bewertung','Nur Beispiel – Beispiel – Beispiel','Definition – Lob – Ende','These ohne Begründung','Wortliste ohne Satz'],0,'Struktur'],
    ['Welche Kasus-Verbindung ist richtig?',['abhängen von + Dativ','abhängen für + Akkusativ','abhängen über + Genitiv','abhängen gegen + Dativ','abhängen ohne + Dativ'],0,'Grammatik']
  ];
  var tf=[
    ['„sich an Vorbildern orientieren“ ist eine korrekte feste Verbindung.',true,'NVV'],
    ['„Vergleichsdruck machen“ ist die beste C1/C2-Verbindung.',false,'NVV'],
    ['„unter Druck geraten“ passt zu Nachteilen der Selbstoptimierung.',true,'NVV'],
    ['„eigene Ziele aus den Augen verlieren“ passt zum Verlust der Individualität.',true,'Redemittel'],
    ['In einem Nachteilsabsatz sollte man nur Vorteile nennen.',false,'Textlogik'],
    ['„Dies führt dazu, dass ...“ ist ein brauchbarer Folge-Satzbaustein.',true,'Satzbau'],
    ['„Vorbilder sollten kritisch betrachtet werden“ passt zur Bewertung.',true,'Bewertung'],
    ['Konsumdruck und äußere Anerkennung gehören zu Nachteil 4.',true,'Quelle'],
    ['Perfektionsdruck hat mit unrealistischen Erwartungen nichts zu tun.',false,'Quelle'],
    ['Der Word-Text behandelt vier Nachteile.',true,'Quelle']
  ];
  var wordMatch=[
    ['der Vergleichsdruck','ständiger Druck, sich mit erfolgreichen oder perfekten Personen zu messen'],
    ['das Selbstwertgefühl','die innere Bewertung der eigenen Person'],
    ['die Selbstzweifel','Unsicherheit gegenüber den eigenen Fähigkeiten'],
    ['der Perfektionsdruck','Druck, immer produktiv, kontrolliert und fehlerfrei zu sein'],
    ['die Überforderung','Zustand, in dem Ansprüche die eigenen Kräfte übersteigen'],
    ['die Individualität','eigene Persönlichkeit, eigene Wünsche und eigener Lebensweg'],
    ['die Nachahmung','unkritisches Kopieren fremder Verhaltensweisen'],
    ['die Fremdbestimmung','Orientierung an fremden Maßstäben statt an eigenen Bedürfnissen'],
    ['der Konsumdruck','Druck, Produkte, Kurse oder Programme kaufen zu müssen'],
    ['die Anerkennungssuche','ständiges Streben nach Lob, Likes oder äußerer Bestätigung'],
    ['die Selbstdarstellung','Darstellung der eigenen Person nach außen'],
    ['die psychische Belastung','seelischer Druck durch Erwartungen, Vergleich oder Überforderung']
  ];
  var phraseMatch=[
    ['Vergleichsdruck','erzeugen'],['das Selbstwertgefühl','schwächen'],['Unsicherheit','verstärken'],['Minderwertigkeitsgefühle','verursachen'],['unter sozialem Druck','stehen'],['nach Anerkennung','streben'],['unrealistische Erwartungen','wecken'],['unter Leistungsdruck','geraten'],['Erholung','vernachlässigen'],['die eigene Individualität','verlieren'],['fremde Maßstäbe','übernehmen'],['Konsumdruck','ausüben'],['Anerkennung','suchen'],['sich über Likes','definieren'],['Erfolg an Konsum','knüpfen']
  ];
  var prep=[
    ['Menschen orientieren sich ___ Vorbildern.','an','sich orientieren an + Dativ'],
    ['Viele geraten ___ sozialen Druck.','unter','unter Druck geraten'],
    ['Das Selbstwertgefühl hängt ___ äußerer Anerkennung ab.','von','abhängen von + Dativ'],
    ['Vorbilder werden häufig ___ sozialen Medien idealisiert dargestellt.','in','in + Dativ'],
    ['Man vergleicht das eigene Leben ___ idealisierten Bildern.','mit','vergleichen mit + Dativ'],
    ['Menschen streben ___ Anerkennung.','nach','streben nach + Dativ'],
    ['Selbstoptimierung wird ___ Konsum verbunden.','mit','verbinden mit + Dativ'],
    ['Eine Person entfernt sich ___ den eigenen Bedürfnissen.','von','sich entfernen von + Dativ'],
    ['Der Druck führt ___ Überforderung.','zu','führen zu + Dativ'],
    ['Vorbilder sollten ___ kritischer Distanz betrachtet werden.','mit','mit + Dativ']
  ];
  var hang=['Vergleichsdruck erzeugen','das Selbstwertgefühl schwächen','Unsicherheit verstärken','Minderwertigkeitsgefühle verursachen','unter sozialem Druck stehen','nach Anerkennung streben','sich an unrealistischen Bildern orientieren','unrealistische Erwartungen wecken','unter Leistungsdruck geraten','Perfektionsdruck erzeugen','zu Überforderung führen','Erholung vernachlässigen','die eigene Individualität verlieren','fremde Lebensmodelle übernehmen','eigene Bedürfnisse vernachlässigen','fremde Maßstäbe übernehmen','Konsumdruck ausüben','Anerkennung suchen','sich über Likes definieren','Produkte als Lösung darstellen','innere Motivation schwächen','Erfolg an Konsum knüpfen'];
  var short=`
<h3>Selbstoptimierung durch Vorbilder – Nachteile · Kurz</h3>
<p><b>Selbstoptimierung durch Vorbilder</b> bedeutet, dass Menschen sich an Personen orientieren, die sie als erfolgreich, diszipliniert, sportlich, schön, produktiv oder bewundernswert wahrnehmen. Im Nachteilsabsatz geht es nicht darum, Vorbilder grundsätzlich abzulehnen, sondern die problematischen Folgen einer unkritischen Orientierung zu erklären.</p>
<table>
<tr><th>Grundthese</th><td>Selbstoptimierung durch Vorbilder kann zwar motivieren, führt aber häufig zu Vergleichsdruck, unrealistischen Erwartungen, Verlust der Individualität und Abhängigkeit von Anerkennung.</td></tr>
<tr><th>Vier Nachteile</th><td>Vergleichsdruck · Perfektionsdruck · fremde Ziele · Konsumdruck und Anerkennungssuche.</td></tr>
<tr><th>Prüfungsformel</th><td>Beobachtung → Erklärung → Beispiel → Ergebnis → Risiko → kurz- und langfristige Wirkung → Bewertung.</td></tr>
</table>`;
  var medium=`
<h3>Selbstoptimierung durch Vorbilder – Nachteile · Mittel</h3>
<p>In einer C1/C2-Erörterung kann man dieses Thema sehr gut mit sozialen Medien, Schule, Studium, Fitness, Karriere und persönlicher Entwicklung verbinden. Entscheidend ist, dass Vorbilder nicht nur inspirieren, sondern auch zum Maßstab werden können. Wenn Menschen ihr normales Leben mit idealisierten Bildern vergleichen, entstehen Unsicherheit, Selbstzweifel und Druck. Besonders soziale Medien verstärken diese Wirkung, weil dort häufig nur Erfolge, perfekte Körper, produktive Routinen oder berufliche Höhepunkte gezeigt werden.</p>
<table>
<tr><th>Nachteil 1</th><td><b>Vergleichsdruck:</b> Menschen vergleichen sich mit idealisierten Vorbildern und fühlen sich weniger erfolgreich, schön oder produktiv. Das kann das Selbstwertgefühl schwächen.</td></tr>
<tr><th>Nachteil 2</th><td><b>Perfektionsdruck:</b> Vorbilder zeigen scheinbar perfekte Routinen. Dadurch entsteht der Eindruck, man müsse ständig leisten, optimieren und kontrollieren.</td></tr>
<tr><th>Nachteil 3</th><td><b>Verlust der Individualität:</b> Wer fremde Ziele kopiert, verliert leicht den Kontakt zu eigenen Bedürfnissen, Interessen und Lebenswegen.</td></tr>
<tr><th>Nachteil 4</th><td><b>Konsumdruck und Anerkennung:</b> Wenn Vorbilder Produkte, Kurse oder Programme verkaufen, wird Selbstoptimierung oberflächlich und abhängig von Likes, Lob oder Konsum.</td></tr>
</table>`;
  var long=`
<h3>Selbstoptimierung durch Vorbilder – Nachteile · ausführlich, prüfungsnah und ohne Fülltext</h3>
<p><b>Quelle:</b> Selbstoptimierung_durch_Vorbilder_Nachteile_4_C1_C2_15_20(1).docx. Diese Darstellung folgt dem Word-Dokument: Orientierung, Wortfeld, vier Nachteile, Satzbausteine, Musterabsätze, Kopiervorlage und Übungen. Der Text ist bewusst auf prüfungsnahe Formulierungen ausgerichtet und enthält keine allgemeinen Füllabschnitte.</p>
<table>
<tr><th>Kurze Orientierung</th><td>Selbstoptimierung durch Vorbilder bedeutet, dass Menschen sich an Personen orientieren, die als erfolgreich, diszipliniert, schön, sportlich, produktiv oder bewundernswert gelten. Das kann im Alltag, in der Schule, im Studium, im Beruf, im Sport oder in sozialen Medien passieren. Für einen Nachteilsabsatz ist wichtig: Vorbilder sind nicht automatisch schlecht, aber ihre unkritische Nachahmung kann problematisch werden.</td></tr>
<tr><th>Grundthese</th><td>Selbstoptimierung durch Vorbilder kann zwar motivierend wirken, führt jedoch häufig zu Vergleichsdruck, unrealistischen Erwartungen, Verlust der eigenen Individualität und einer Abhängigkeit von äußerer Anerkennung.</td></tr>
<tr><th>Schnelle Prüfungsformel</th><td>Beobachtung → Erklärung → Beispiel → Ergebnis → Risiko → kurz- und langfristige Wirkung → Bewertung.</td></tr>
</table>
<h4>1. Allgemeines Wortfeld und direkte Prüfungswörter</h4>
<table>
<tr><th>Nomen</th><td>der Vergleichsdruck, das Selbstwertgefühl, die Unsicherheit, die Selbstzweifel, der Leistungsdruck, die Selbstoptimierung, die Anerkennungssuche, die psychische Belastung, die Individualität, die Authentizität, die Fremdbestimmung, der Konsumdruck, die Selbstdarstellung.</td></tr>
<tr><th>Verben / NVV</th><td>sich an Vorbildern orientieren, sich ständig vergleichen, unter Druck geraten, das Selbstwertgefühl schwächen, unrealistische Erwartungen wecken, eigene Ziele aus den Augen verlieren, fremde Maßstäbe übernehmen, nach Anerkennung streben, psychische Belastung verursachen, Authentizität verlieren.</td></tr>
<tr><th>Adjektive</th><td>idealisiert, unrealistisch, oberflächlich, leistungsorientiert, belastend, unsicher, überfordert, selbstkritisch, abhängig, authentisch, langfristig, problematisch.</td></tr>
<tr><th>Satzanfänge</th><td>Ein zentraler Nachteil liegt darin, dass ... / Besonders problematisch ist, dass ... / Dies führt dazu, dass ... / Langfristig kann dieser Vergleich ... / Aus meiner Sicht sollte man Vorbilder kritisch betrachten.</td></tr>
</table>
<h4>2. Nachteil 1: Vergleichsdruck und geringeres Selbstwertgefühl</h4>
<table>
<tr><th>Kurze Idee</th><td>Der erste Nachteil besteht darin, dass Vorbilder starken Vergleichsdruck erzeugen können. Menschen sehen die Erfolge anderer und fragen sich, warum sie selbst nicht genauso schön, produktiv, sportlich oder erfolgreich sind. Besonders soziale Medien erzeugen ein verzerrtes Bild, weil dort häufig nur perfekte Momente sichtbar sind.</td></tr>
<tr><th>Beobachtungen</th><td>• ständiger Vergleich mit erfolgreichen Personen<br>• perfekte Körper und Lebensstile in sozialen Medien<br>• Influencer zeigen meist nur die besten Momente<br>• Likes und Kommentare wirken wie eine Bewertung der eigenen Person<br>• der Alltag anderer wirkt attraktiver als der eigene Alltag</td></tr>
<tr><th>Detaillierte Erklärung</th><td>Vorbilder können Orientierung geben, sie können aber auch zu einem ständigen Maßstab werden. Problematisch ist, dass der Vergleich oft unfair ist: Man vergleicht das eigene normale Leben mit einer ausgewählten Darstellung anderer Personen. Schwierigkeiten, Müdigkeit, Zweifel, Fehler oder Rückschläge werden selten gezeigt. Dadurch entsteht der Eindruck, dass andere mühelos erfolgreich sind. Wer diesem Bild glaubt, fühlt sich schnell weniger wertvoll oder weniger leistungsfähig.</td></tr>
<tr><th>Konkrete Beispiele</th><td>• Ein Jugendlicher vergleicht seinen Körper mit Fitness-Influencern.<br>• Eine Studentin sieht Lernvideos und glaubt, nicht genug zu leisten.<br>• Ein Schüler vergleicht seine Noten mit besonders erfolgreichen Mitschülern.<br>• Jemand sieht Karrieren auf LinkedIn und fühlt sich zurückgeblieben.<br>• Eine Person wird unzufrieden, weil sie perfekte Urlaubsbilder und Luxusleben sieht.</td></tr>
<tr><th>Folgen und Risiken</th><td>Vergleichsdruck kann Unsicherheit, Selbstzweifel, Minderwertigkeitsgefühle und psychische Belastung verstärken. Kurzfristig entsteht Unzufriedenheit; langfristig kann das Selbstwertgefühl geschwächt werden. In einem Prüfungsabsatz sollte man betonen, dass nicht das Vorbild selbst gefährlich ist, sondern die ständige Selbstabwertung durch idealisierte Vergleiche.</td></tr>
<tr><th>Prüfungsstarke Formulierung</th><td>Ein zentraler Nachteil der Selbstoptimierung durch Vorbilder liegt im entstehenden Vergleichsdruck. Besonders soziale Medien zeigen häufig nur Erfolge, schöne Körper oder perfekte Tagesabläufe. Dadurch kann der Eindruck entstehen, selbst nicht gut genug zu sein. Langfristig kann dieser Vergleich das Selbstwertgefühl schwächen und psychische Belastung erzeugen.</td></tr>
</table>
<h4>3. Nachteil 2: Unrealistische Erwartungen und Perfektionsdruck</h4>
<table>
<tr><th>Kurze Idee</th><td>Ein weiterer Nachteil ist der Perfektionsdruck. Vorbilder zeigen oft Disziplin, Erfolg und scheinbar perfekte Routinen. Dadurch glauben manche Menschen, sie müssten ebenfalls immer produktiv, gesund, erfolgreich und kontrolliert sein.</td></tr>
<tr><th>Beobachtungen</th><td>• perfekte Morgenroutinen in sozialen Medien<br>• Menschen wollen immer produktiver werden<br>• Fehler und Schwächen werden versteckt<br>• Pausen wirken wie Zeitverlust<br>• Sport, Lernen und Arbeit werden ständig optimiert<br>• Erholung wird weniger wichtig genommen</td></tr>
<tr><th>Detaillierte Erklärung</th><td>Vorbilder können zeigen, was möglich ist. Gleichzeitig können sie unrealistische Erwartungen wecken. Wenn ein Vorbild jeden Tag früh aufsteht, trainiert, arbeitet, lernt und immer erfolgreich wirkt, entsteht leicht die Vorstellung, ein normaler Alltag sei nicht genug. Dabei sieht man selten, wie viele Jahre, Unterstützung, finanzielle Mittel, Fehler oder schwierige Bedingungen hinter dem Erfolg stehen. Erfolg scheint dann nur eine Frage von Disziplin zu sein. Das kann Menschen unter Leistungsdruck setzen.</td></tr>
<tr><th>Konkrete Beispiele</th><td>• Eine Studentin fühlt sich schuldig, wenn sie eine Pause macht.<br>• Ein Schüler lernt bis spät in die Nacht, weil seine Vorbilder extrem fleißig wirken.<br>• Eine Person versucht, Ernährung, Sport, Schlaf und Arbeit komplett zu kontrollieren.<br>• Ein Berufstätiger glaubt, ständig erreichbar und produktiv sein zu müssen.<br>• Jugendliche glauben, sie müssten früh Karrierepläne haben und immer souverän wirken.</td></tr>
<tr><th>Folgen und Risiken</th><td>Perfektionsdruck kann zu Überforderung, Fehlerangst, Schuldgefühlen, Erschöpfung und Burnout-Gefahr führen. Besonders problematisch ist, dass persönliche Entwicklung dann nicht mehr freiwillig erlebt wird. Selbstoptimierung wird zur Pflicht: Man hat das Gefühl, nie fertig zu sein und immer noch mehr leisten zu müssen.</td></tr>
<tr><th>Prüfungsstarke Formulierung</th><td>Ein weiterer Nachteil besteht darin, dass Vorbilder unrealistische Erwartungen erzeugen können. Wenn Menschen sich ständig an idealisierten Routinen orientieren, setzen sie sich leicht selbst unter Druck. Pausen und Schwächen werden dann als persönliches Versagen empfunden. Langfristig kann dies zu Perfektionsdruck, Überforderung und psychischer Erschöpfung führen.</td></tr>
</table>
<h4>4. Nachteil 3: Verlust der eigenen Individualität und fremde Ziele</h4>
<table>
<tr><th>Kurze Idee</th><td>Der dritte Nachteil betrifft die eigene Individualität. Wer sich zu stark an Vorbildern orientiert, kann den Kontakt zu eigenen Wünschen, Bedürfnissen und Interessen verlieren. Nicht jedes Ziel passt zu jedem Menschen.</td></tr>
<tr><th>Beobachtungen</th><td>• Menschen kopieren Verhalten anderer<br>• Trends werden schnell übernommen<br>• eigene Interessen geraten in den Hintergrund<br>• Vorbilder bestimmen Lebensstil und Ziele<br>• Erfolg wird nach fremden Maßstäben bewertet<br>• Authentizität geht verloren</td></tr>
<tr><th>Detaillierte Erklärung</th><td>Vorbilder können Orientierung geben. Trotzdem hat jeder Mensch andere Voraussetzungen, Werte, Fähigkeiten und Lebensumstände. Was für ein Vorbild sinnvoll ist, muss nicht automatisch zum eigenen Leben passen. Wenn man fremde Ziele unkritisch übernimmt, arbeitet man nicht mehr an der eigenen Entwicklung, sondern versucht, eine andere Person zu imitieren. Das ist besonders bei jungen Menschen problematisch, weil sie ihre eigene Identität erst noch entwickeln.</td></tr>
<tr><th>Konkrete Beispiele</th><td>• Jemand wählt einen Beruf nur, weil ein Vorbild dort erfolgreich ist.<br>• Ein Jugendlicher kopiert Kleidung, Sprache oder Routinen eines Influencers.<br>• Eine Person übernimmt eine Fitnessroutine, die nicht zum eigenen Körper passt.<br>• Jemand studiert ein angesehenes Fach, obwohl es nicht den eigenen Interessen entspricht.<br>• Eine Person verliert Freude an Hobbys, weil sie nur noch Leistung zeigen möchte.</td></tr>
<tr><th>Folgen und Risiken</th><td>Die Folgen können Identitätsverlust, Fremdbestimmung, falsche Lebensentscheidungen, Unzufriedenheit und Abhängigkeit von fremden Maßstäben sein. Für die Prüfung ist wichtig: Vorbilder sollten nicht die eigenen Entscheidungen ersetzen. Sie dürfen Orientierung geben, aber sie sollten die eigene Persönlichkeit nicht verdrängen.</td></tr>
<tr><th>Prüfungsstarke Formulierung</th><td>Ein weiterer problematischer Aspekt ist der mögliche Verlust der eigenen Individualität. Wenn Menschen fremde Ziele oder Lebensmodelle unkritisch übernehmen, entfernen sie sich von den eigenen Bedürfnissen. Statt sich selbst zu entwickeln, versuchen sie, eine andere Person zu kopieren. Langfristig kann eine solche Nachahmung zu Unzufriedenheit und falschen Entscheidungen führen.</td></tr>
</table>
<h4>5. Nachteil 4: Oberflächliche Selbstoptimierung, Konsumdruck und Abhängigkeit von Anerkennung</h4>
<table>
<tr><th>Kurze Idee</th><td>Der vierte Nachteil besteht darin, dass Selbstoptimierung durch Vorbilder oberflächlich werden kann. Besonders in sozialen Medien sind Vorbilder oft mit Produkten, Kursen, Fitnessprogrammen, Apps, Marken oder Coaching-Angeboten verbunden.</td></tr>
<tr><th>Beobachtungen</th><td>• Influencer verkaufen Produkte und Kurse<br>• Selbstoptimierung wird mit Konsum verbunden<br>• Likes und Kommentare wirken wie Anerkennung<br>• Fortschritte werden öffentlich gezeigt<br>• Erfolg wird über Aussehen, Besitz oder Statussymbole definiert<br>• teure Programme versprechen schnelle Veränderung</td></tr>
<tr><th>Detaillierte Erklärung</th><td>Vorbilder in sozialen Medien sind nicht immer neutral. Viele verdienen Geld mit Werbung, Produkten oder Programmen. Dadurch entsteht der Eindruck, persönliche Entwicklung hänge vom Kauf bestimmter Dinge ab. Menschen glauben dann, sie müssten bestimmte Kleidung, Nahrungsergänzungsmittel, Apps, Fitnesspläne oder Kurse besitzen, um sich wirklich zu verbessern. Gleichzeitig kann Anerkennung durch Likes und Kommentare wichtiger werden als die innere Entwicklung.</td></tr>
<tr><th>Konkrete Beispiele</th><td>• Ein Influencer verkauft einen teuren Fitnessplan.<br>• Eine Person kauft ständig neue Produkte, um einem Vorbild ähnlicher zu werden.<br>• Jemand postet jeden Fortschritt und wartet auf Likes.<br>• Online-Kurse versprechen schnelle Karriere oder perfekte Produktivität.<br>• Jugendliche orientieren sich an Marken, Statussymbolen und äußeren Reaktionen.</td></tr>
<tr><th>Folgen und Risiken</th><td>Diese Form der Selbstoptimierung kann Konsumdruck, finanzielle Belastung, Manipulation durch Werbung, oberflächliche Werte und Anerkennungsabhängigkeit verursachen. Wenn Fortschritt nur dann wertvoll erscheint, wenn er gesehen oder gelobt wird, verliert Selbstentwicklung ihre innere Bedeutung. Sie wird zur Selbstdarstellung.</td></tr>
<tr><th>Prüfungsstarke Formulierung</th><td>Ein weiterer Nachteil besteht darin, dass Selbstoptimierung durch Vorbilder leicht oberflächlich werden kann. Besonders in sozialen Medien sind Vorbilder häufig mit Werbung, Produkten oder kostenpflichtigen Programmen verbunden. Dadurch entsteht der Eindruck, dass persönliche Entwicklung vom Kauf bestimmter Produkte abhängt. Langfristig kann dies zu Konsumdruck und Abhängigkeit von äußerer Anerkennung führen.</td></tr>
</table>
<h4>6. Satzbausteine für Einleitung, Hauptteil und Schluss</h4>
<table>
<tr><th>Einleitung</th><td>In der heutigen Gesellschaft orientieren sich viele Menschen an Vorbildern, um sich persönlich weiterzuentwickeln. Besonders durch soziale Medien sind erfolgreiche, disziplinierte oder attraktive Personen ständig sichtbar. Im Folgenden soll untersucht werden, welche Nachteile diese Form der Selbstoptimierung mit sich bringen kann.</td></tr>
<tr><th>Argument einführen</th><td>Ein wesentlicher Nachteil besteht darin, dass ... / Ein zentraler Aspekt dieses Problems ist, dass ... / Besonders problematisch ist vor allem, dass ... / Ein nicht zu unterschätzender Punkt ist, dass ...</td></tr>
<tr><th>Begründung</th><td>Dies lässt sich damit begründen, dass Vorbilder häufig nur ihre positiven Seiten zeigen. / Der Grund dafür liegt darin, dass soziale Medien oft ein idealisiertes Bild vermitteln.</td></tr>
<tr><th>Folge</th><td>Daraus ergibt sich, dass ... / Dies führt dazu, dass ... / Infolgedessen kann es dazu kommen, dass ... / Langfristig betrachtet kann dies zu ... führen.</td></tr>
<tr><th>Schluss</th><td>Abschließend lässt sich festhalten, dass Selbstoptimierung durch Vorbilder nicht nur positive Seiten hat. Vorbilder können hilfreich sein, solange sie nicht zu Druck, Vergleich und Selbstabwertung führen.</td></tr>
</table>
<h4>7. Mustertexte für die Prüfung</h4>
<table>
<tr><th>Mustertext 1</th><td>Ein wesentlicher Nachteil der Selbstoptimierung durch Vorbilder liegt darin, dass sie starken Vergleichsdruck erzeugen kann. Viele Menschen orientieren sich an erfolgreichen Personen und vergleichen das eigene Leben mit deren Leistungen. Besonders in sozialen Medien werden jedoch häufig nur perfekte Ergebnisse, schöne Körper oder produktive Tagesabläufe gezeigt. Schwierigkeiten und Rückschläge bleiben meist unsichtbar. Dadurch entsteht ein verzerrtes Bild von Erfolg. Wer sich ständig mit solchen Idealen vergleicht, kann schnell das Gefühl bekommen, nicht gut genug zu sein. Langfristig kann dies das Selbstwertgefühl schwächen und zu psychischer Belastung führen.</td></tr>
<tr><th>Mustertext 2</th><td>Ein weiterer problematischer Aspekt ist der mögliche Verlust der eigenen Individualität. Vorbilder können zwar Orientierung geben, aber nicht jedes Ziel passt zu jeder Person. Wenn Menschen fremde Lebensmodelle unkritisch übernehmen, entfernen sie sich möglicherweise von ihren eigenen Bedürfnissen. Statt sich selbst zu entwickeln, versucht man dann, jemand anderes zu imitieren. Langfristig kann dies zu Unzufriedenheit und falschen Lebensentscheidungen führen.</td></tr>
<tr><th>Mustertext 3</th><td>Auch die Verbindung von Vorbildern und Konsum kann problematisch sein. Viele Vorbilder in sozialen Medien empfehlen Produkte, Kurse, Fitnesspläne oder Apps. Dadurch entsteht leicht der Eindruck, dass persönliche Entwicklung nur durch bestimmte Käufe möglich ist. Hinzu kommt, dass Fortschritte häufig öffentlich gezeigt werden und Anerkennung durch Likes oder Kommentare gesucht wird. Wenn Selbstwert vor allem von äußerer Bestätigung abhängt, entsteht eine problematische Abhängigkeit.</td></tr>
</table>
<h4>8. Kopya kâğıdı</h4>
<table>
<tr><th>Nachteil 1</th><td>Vorbild → Vergleich → Unsicherheit → geringeres Selbstwertgefühl.</td></tr>
<tr><th>Nachteil 2</th><td>Vorbild → perfektes Ideal → Leistungsdruck → Überforderung.</td></tr>
<tr><th>Nachteil 3</th><td>Vorbild → Nachahmung → fremde Ziele → weniger Individualität.</td></tr>
<tr><th>Nachteil 4</th><td>Vorbild → Produktversprechen → Konsumdruck → äußere Anerkennung.</td></tr>
<tr><th>Top-NVV</th><td>Vergleichsdruck erzeugen · das Selbstwertgefühl schwächen · unrealistische Erwartungen wecken · fremde Maßstäbe übernehmen · Konsumdruck ausüben · nach Anerkennung streben · psychische Belastung verursachen.</td></tr>
</table>
<h4>9. Übungen</h4>
<p><b>Übung 1:</b> Ergänze: Vergleichsdruck, Selbstwertgefühl, Perfektionsdruck, Individualität, Konsumdruck, Anerkennung.</p>
<p><b>Übung 2:</b> Verbinde Sätze mit dadurch, infolgedessen, langfristig betrachtet, besonders problematisch ist, dass.</p>
<p><b>Übung 3:</b> Übersetze: Vorbilder können motivieren, aber auch Druck erzeugen. / Besonders soziale Medien zeigen Erfolg oft idealisiert. / Langfristig kann dies das Selbstwertgefühl schwächen.</p>
<p><b>Abschluss-Merksatz:</b> Vorbilder können Orientierung geben, aber sie werden problematisch, wenn sie zum ständigen Maßstab werden. In der Prüfung kannst du zeigen: Vergleich, Perfektionsdruck, fremde Ziele und Anerkennungssuche sind die wichtigsten Nachteile.</p>`;
  window.DEUTSCH_TESTS[KEY]={category:'Bevor Schreiben',slug:'selbstoptimierung_durch_vorbilder_nachteile_c1_c2',title:title,name:title,label:title,buttonTitle:title,displayTitle:title,topic:topic,meta:topic,words:words,fill:fill,mc:mc,tf:tf,wordMatch:wordMatch,phraseMatch:phraseMatch,prep:prep,hang:hang,source:source,sourceStatus:'WORD_SOURCE'};
  window.DEUTSCH_LESSONS[KEY]={title:title,short:short,medium:medium,long:long,lessonLong:long,longLesson:long,contentLong:long,source:source,sourceStatus:'WORD_SOURCE',wordTarget:'2000_plus',layout:'word_like_bullets_and_tables'};
  window.LESSONS[KEY]=window.DEUTSCH_LESSONS[KEY];
  try{ if(typeof renderTests==='function' && window.selectedCategory==='Bevor Schreiben') renderTests('Bevor Schreiben'); }catch(e){}
})();