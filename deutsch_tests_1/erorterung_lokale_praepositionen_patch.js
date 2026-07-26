(function(){
'use strict';
const tests=window.erorterungTests||window.ERORTERUNG_TESTS;
if(!Array.isArray(tests))return;
if(tests.some(t=>t.id==='lokalprep1'||t.id==='lokalprep2'))return;
function q(text,options,answer,rule){return{q:text,options,answer,rule};}
const lokalprep1={id:'lokalprep1',title:'Lokale Präpositionen I – Wohin, Wo, Woher · C2',description:'C2-Erörterungssätze mit in, nach, an, auf, zu, bei, aus und von. Fokus: Richtung, Position und Herkunft.',questions:[
q('In einer differenzierten Stadtanalyse sollte man nicht nur fragen, warum Menschen ___ Zentrum ziehen, sondern auch, welche Folgen dies für bezahlbaren Wohnraum hat.',['ins','im','aus dem','vom','zum'],0,'Wohin? Richtung in einen geschlossenen/benannten Bereich: ins Zentrum.'),
q('Wer bereits ___ Zentrum wohnt, erlebt steigende Mieten oft anders als Pendler aus den Randbezirken.',['ins','im','aus dem','vom','zum'],1,'Wo? Position mit Dativ: im Zentrum.'),
q('Viele junge Familien ziehen ___ Zentrum weg, weil größere Wohnungen dort kaum bezahlbar sind.',['ins','im','aus dem','vom','zum'],2,'Woher? Herkunft aus einem Bereich: aus dem Zentrum.'),
q('Eine seriöse Bildungsdebatte darf nicht so tun, als könne man alle Lernprobleme einfach ___ Internet verlagern.',['ins','im','aus dem','vom','zum'],0,'Wohin? digitale Richtung/Zugang: ins Internet.'),
q('Viele Informationen stehen zwar ___ Internet, doch ihre Qualität muss kritisch geprüft werden.',['ins','im','aus dem','vom','zum'],1,'Wo? fester digitaler Raum: im Internet.'),
q('Wenn politische Meinungen ausschließlich ___ Internet stammen, steigt die Gefahr einseitiger Informationsblasen.',['ins','im','aus dem','vom','zum'],2,'Woher? Quelle/Herkunft: aus dem Internet.'),
q('In einer globalisierten Wirtschaft ziehen Fachkräfte oft ___ Schweiz, obwohl die Lebenshaltungskosten dort hoch sind.',['in die','in der','aus der','nach','von der'],0,'Wohin? Land mit Artikel: in die Schweiz.'),
q('Viele Beschäftigte arbeiten ___ Schweiz in Branchen, die stark von internationaler Zuwanderung profitieren.',['in die','in der','aus der','nach','von der'],1,'Wo? Land mit Artikel + Dativ: in der Schweiz.'),
q('Wer ___ Schweiz zurückkehrt, bringt häufig berufliche Erfahrungen aus einem hochregulierten Arbeitsmarkt mit.',['in die','in der','aus der','nach','von der'],2,'Woher? Land mit Artikel: aus der Schweiz.'),
q('Für eine Erörterung über Mobilität reicht es nicht, nur zu behaupten, Menschen müssten häufiger ___ Stadt ziehen.',['in die','in der','aus der','nach','von der'],0,'Wohin? Richtung in eine konkrete städtische Zone: in die Stadt.'),
q('Soziale Ungleichheit zeigt sich besonders ___ Stadt, wenn Wohnraum knapp und Verkehr teuer wird.',['in die','in der','aus der','nach','von der'],1,'Wo? Position: in der Stadt.'),
q('Viele Pendler kommen morgens ___ Stadt, arbeiten aber weiterhin im Zentrum.',['in die','in der','aus der','nach','von der'],2,'Woher? Herkunft aus einem Raum: aus der Stadt.'),
q('In Diskussionen über Tourismus fahren viele Menschen ___ Berge, ohne über ökologische Belastungen nachzudenken.',['in die','in den','aus den','auf die','von den'],0,'Wohin? Richtung in eine Gebirgsregion: in die Berge.'),
q('Massentourismus belastet sensible Lebensräume ___ Bergen besonders stark.',['in die','in den','aus den','auf die','von den'],1,'Wo? Position mit Dativ Plural: in den Bergen.'),
q('Wenn Besucher ___ Bergen zurückkehren, bleiben Abfall und Lärm oft in der Region zurück.',['in die','in den','aus den','auf die','von den'],2,'Woher? Herkunft aus einer Region: aus den Bergen.'),
q('Bei der Diskussion über Medienkompetenz sollte man junge Menschen nicht unbegleitet ___ soziale Netzwerke schicken.',['in die','in den','aus den','nach','von den'],0,'Wohin? Richtung in einen digitalen/sozialen Raum: in die Netzwerke.'),
q('Viele politische Debatten finden heute ___ sozialen Netzwerken statt, was schnelle Reaktionen fördert.',['in die','in den','aus den','nach','von den'],1,'Wo? Position in pluralischem Raum: in den sozialen Netzwerken.'),
q('Ein erheblicher Teil öffentlicher Empörung entsteht ___ sozialen Netzwerken und erreicht erst danach klassische Medien.',['in die','in den','aus den','nach','von den'],2,'Woher? Ursprung/Herkunft: aus den sozialen Netzwerken.'),
q('Wer die Verkehrsbelastung ernsthaft senken will, sollte nicht jeden Arbeitsplatz ___ Innenstadt konzentrieren.',['in die','in der','aus der','nach der','von der'],0,'Wohin? Richtung in einen Raum: in die Innenstadt.'),
q('Die Folgen hoher Mieten werden ___ Innenstadt besonders sichtbar, weil dort viele Nutzungsinteressen konkurrieren.',['in die','in der','aus der','nach der','von der'],1,'Wo? Position mit Dativ: in der Innenstadt.')
]};
const lokalprep2={id:'lokalprep2',title:'Lokale Präpositionen II – an, auf, zu, bei, von · C2',description:'Zweiter C2-Test mit bewusst ähnlichen Distraktoren: Strand/Meer, Computer, Amt, Person, Institution und Herkunft.',questions:[
q('In einer Debatte über digitale Bildung setzen sich viele Lernende zu lange ___ Computer, ohne ihre Quellen kritisch zu prüfen.',['an den','am','vom','zum','auf den'],0,'Wohin? Richtung an eine Arbeitsfläche/ein Gerät: an den Computer.'),
q('Wer stundenlang ___ Computer arbeitet, verwechselt technische Aktivität leicht mit echtem Lernen.',['an den','am','vom','zum','auf dem'],1,'Wo? am Computer = an dem Computer.'),
q('Viele Argumente gegen unkontrollierte Digitalisierung stammen nicht ___ Computer selbst, sondern aus der Art seiner Nutzung.',['an den','am','vom','zum','auf dem'],2,'Woher? vom Computer = von dem Computer; Quelle/Ausgangspunkt.'),
q('Touristische Werbung lockt immer mehr Menschen ___ Strand, obwohl dort empfindliche Ökosysteme belastet werden.',['an den','am','vom','zum','auf den'],0,'Wohin? an den Strand, weil Strand als Grenze/Uferbereich verstanden wird.'),
q('Wer ___ Strand über Nachhaltigkeit spricht, sollte Abfall, Verkehr und Wasserverbrauch zugleich berücksichtigen.',['an den','am','vom','zum','auf dem'],1,'Wo? am Strand = an dem Strand.'),
q('Viele Belastungen kommen nicht nur ___ Strand selbst, sondern auch aus Hotels, Verkehr und Gastronomie.',['an den','am','vom','zum','auf dem'],2,'Woher? vom Strand = von dem Strand; Herkunft/Ausgangspunkt.'),
q('Eine verantwortungsvolle Politik darf Menschen nicht erst dann ___ Arbeitsamt schicken, wenn ihre Qualifikation bereits entwertet wurde.',['auf das','auf dem','vom','zum','in das'],0,'Wohin? auf das Arbeitsamt als Institution/Behörde in der Tabelle.'),
q('Viele Betroffene fühlen sich ___ Arbeitsamt nicht nur beraten, sondern auch verwaltet.',['auf das','auf dem','vom','zum','in dem'],1,'Wo? auf dem Arbeitsamt als institutioneller Ort.'),
q('Wer ___ Arbeitsamt kommt, bringt häufig nicht nur Unterlagen, sondern auch Zukunftsangst mit.',['auf das','auf dem','vom','zum','in dem'],2,'Woher? vom Arbeitsamt = von dem Arbeitsamt.'),
q('In Konflikten um Pflegearbeit muss man manchmal ___ zuständige Stelle gehen, bevor Hilfe organisiert wird.',['zu der','bei der','von der','in die','aus der'],0,'Wohin? zu einer Institution/Stelle.'),
q('Viele Familien erhalten ___ zuständigen Stelle nur dann Unterstützung, wenn Zuständigkeiten klar geregelt sind.',['zu der','bei der','von der','in die','aus der'],1,'Wo? bei einer Stelle/Institution.'),
q('Die Entscheidung kommt ___ zuständigen Stelle, doch ihre Folgen treffen die Betroffenen unmittelbar.',['zu der','bei der','von der','in die','aus der'],2,'Woher? von einer Stelle/Institution.'),
q('Wer eine persönliche Beratung braucht, geht nicht zu einem Chatbot, sondern ___ erfahrenen Fachkraft.',['zu einer','bei einer','von einer','an eine','aus einer'],0,'Wohin? zu einer Person.'),
q('Komplexe soziale Probleme lassen sich ___ erfahrenen Fachkraft oft besser einordnen als durch standardisierte Antworten.',['zu einer','bei einer','von einer','an eine','aus einer'],1,'Wo? bei einer Person/Fachkraft.'),
q('Eine differenzierte Einschätzung kommt häufig ___ erfahrenen Fachkraft und nicht aus einer automatischen Vorlage.',['zu einer','bei einer','von einer','an eine','aus einer'],2,'Woher? von einer Person.'),
q('Eine demokratische Gesellschaft darf Verantwortung nicht einfach ___ Plattform verschieben, wenn politische Debatten eskalieren.',['auf die','auf der','von der','an die','zu der'],0,'Wohin? auf die Plattform als öffentliche/digitale Fläche.'),
q('Viele Konflikte werden ___ Plattform sichtbar, obwohl ihre Ursachen außerhalb des Netzes liegen.',['auf die','auf der','von der','an die','zu der'],1,'Wo? auf der Plattform.'),
q('Öffentliche Empörung geht oft ___ Plattform aus und wird anschließend von traditionellen Medien aufgegriffen.',['auf die','auf der','von der','an die','zu der'],2,'Woher? von der Plattform.'),
q('In einer Erörterung über Umweltschutz sollte man nicht nur ___ Meer fahren, sondern auch fragen, wie Küstenräume geschützt werden können.',['ans','am','vom','ins','aus dem'],0,'Wohin? ans Meer = an das Meer, Grenze/Ufer.'),
q('Viele wirtschaftliche Interessen treffen ___ Meer auf ökologische Grenzen, die politisch ernst genommen werden müssen.',['ans','am','vom','ins','aus dem'],1,'Wo? am Meer = an dem Meer.')
]};
tests.push(lokalprep1,lokalprep2);
window.erorterungTests=tests;
window.ERORTERUNG_TESTS=tests;
window.AAYS_LOKALE_PRAEPOSITIONEN_2_TESTS_OK=true;
window.AAYS_LOKALE_PRAEPOSITIONEN_FROM_TABLE_OK=true;
})();