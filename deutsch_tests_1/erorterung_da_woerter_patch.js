(function(){
'use strict';
const tests=window.erorterungTests||window.ERORTERUNG_TESTS;
if(!Array.isArray(tests))return;
if(tests.some(t=>t.id==='dawoerter1'||t.id==='dawoerter2'))return;
function q(text,options,answer,rule){return{q:text,options,answer,rule};}
const dawoerter1={id:'dawoerter1',title:'Da-Wörter I – da, dabei, damit, dafür · C2',description:'C2-Erörterungssätze zu da als Zeitangabe, dabei als Parallelhandlung, damit/dafür als Pronominaladverb und damit als finaler Konnektor.',questions:[
q('Viele junge Menschen informieren sich online; ___ entsteht jedoch leicht der Eindruck, jede schnelle Meinung sei bereits ein fundiertes Argument.',['dabei','damit','dafür','daraufhin','daraus'],0,'dabei = währenddessen / bei diesem Vorgang; zwei Handlungen laufen parallel.'),
q('Digitale Lernplattformen sammeln Daten; ___ sollten Schulen nicht automatisch schließen, dass jede Messung pädagogisch sinnvoll ist.',['daraus','dabei','dafür','damit','da'],0,'daraus schließen = aus dieser Sache eine Folgerung ziehen.'),
q('Viele Beschäftigte akzeptieren Homeoffice; ___ sind sie allerdings nicht automatisch einverstanden, ständig erreichbar zu sein.',['damit','dabei','dafür','da','daraufhin'],0,'damit = mit dieser vorher genannten Sache; Bezug auf die ganze Aussage.'),
q('Ein Teil der Bevölkerung ist ___, dass öffentliche Verkehrsmittel stärker subventioniert werden.',['dafür','damit','dabei','da','daraus'],0,'dafür sein = eine Meinung vertreten / dafür eintreten.'),
q('Die Regierung kündigte strengere Datenschutzregeln an; ___ passten mehrere Unternehmen ihre internen Prozesse an.',['daraufhin','dabei','damit','dafür','da'],0,'daraufhin = zeitliche Folge/Reaktion infolge dessen.'),
q('___ soziale Medien politische Debatten beschleunigen, müssen Quellen umso sorgfältiger geprüft werden.',['Da','Dabei','Damit','Dafür','Daraufhin'],0,'da = weil; kausaler Nebensatz mit Verb am Ende.'),
q('Schulen brauchen klare Medienkonzepte, ___ digitale Geräte nicht nur als teure Schreibmaschinen benutzt werden.',['damit','dabei','dafür','daraus','da'],0,'damit = finaler Nebensatz: zu welchem Zweck?'),
q('Viele Eltern kaufen Tablets für ihre Kinder; ___ ersetzen sie jedoch keine pädagogische Begleitung.',['damit','dabei','dafür','daraus','da'],0,'damit = mit diesen Geräten / dadurch; Pronominaladverb, kein finaler Konnektor.'),
q('Ein Unternehmen kann flexible Arbeitszeiten anbieten; ___ bleibt die Frage nach sozialer Absicherung ungelöst.',['dabei','damit','daraufhin','dafür','daraus'],0,'dabei = dennoch / obwohl das der Fall ist; einschränkender Bezug.'),
q('Die Stadt baute sichere Radwege; ___ stieg die Bereitschaft vieler Pendler, das Auto stehen zu lassen.',['daraufhin','dabei','damit','dafür','daraus'],0,'daraufhin = danach als Reaktion/Folge.'),
q('Viele Kritiker wenden ein, KI könne Fehler machen; ___ haben sie in sensiblen Bereichen durchaus ein starkes Argument.',['damit','dabei','dafür','da','daraufhin'],0,'damit = mit diesem Einwand / mit dieser Aussage.'),
q('Nicht jede technische Neuerung verbessert die Bildung; ___ sollte man Investitionen stärker an didaktischen Zielen ausrichten.',['daher','dabei','damit','dafür','daraus'],0,'daher/darum = Folge/Konsequenz: deshalb.'),
q('Die Kommune versprach mehr Grünflächen; ___ wurde die geplante Versiegelung am Stadtrand politisch noch stärker kritisiert.',['daraufhin','dafür','damit','dabei','da'],0,'daraufhin = als Reaktion auf die vorherige Handlung.'),
q('Viele Lernende nutzen Übersetzungsprogramme; ___ trainieren sie eigene Ausdrucksfähigkeit oft weniger intensiv.',['dabei','damit','dafür','daraus','da'],0,'dabei = während dieser Nutzung / gleichzeitig.'),
q('Ein Autor kann eine These zuspitzen; ___ darf er jedoch Gegenargumente nicht einfach ausblenden.',['dabei','damit','dafür','daraus','daraufhin'],0,'dabei = dabei/trotzdem: bei diesem Vorgehen bleibt etwas zu beachten.'),
q('Die Schule sollte Schreibfeedback geben, ___ Lernende ihre Argumentation präziser überarbeiten können.',['damit','dabei','dafür','daraus','daraufhin'],0,'damit = finaler Konnektor, Zweck: damit sie können.'),
q('Viele Menschen wünschen sich mehr Klimaschutz; ___ fehlt ihnen im Alltag manchmal die Bereitschaft zu konkreten Einschränkungen.',['dabei','damit','dafür','daraus','da'],0,'dabei = obwohl/trotzdem; kontrastiver Bezug.'),
q('Der Bericht war sprachlich überzeugend; ___ war die zentrale Begründung nicht ausreichend belegt.',['dabei','dafür','damit','daraus','daraufhin'],0,'dabei = allerdings/trotzdem im Sinne eines einschränkenden Kontrasts.'),
q('Wer nur einzelne Beispiele sammelt, kann ___ noch keine allgemeingültige Schlussfolgerung ziehen.',['daraus','dabei','damit','dafür','da'],0,'daraus = aus den Beispielen / aus dieser Sache.'),
q('Die Maßnahme ist teuer; ___ spricht jedoch, dass sie langfristig soziale Folgekosten senken könnte.',['dafür','damit','dabei','daraus','da'],0,'dafür spricht = ein Argument zugunsten davon.')
]};
const dawoerter2={id:'dawoerter2',title:'Da-Wörter II – Konnektoren und Verben mit da-/dabei- · C2',description:'Zweiter C2-Test mit daran/dran-, da-/dabei-Verben und stark ablenkenden Konnektoroptionen.',questions:[
q('An einer einmal begonnenen Bildungsreform muss die Politik auch dann ___, wenn erste Ergebnisse noch widersprüchlich wirken.',['dranbleiben','dalassen','dabeihaben','dableiben','drüberschauen'],0,'dranbleiben = nicht aufgeben / weiter daran arbeiten.'),
q('Kannst du vor der Abgabe noch einmal kurz ___, ob die Argumentationskette wirklich logisch ist?',['drüberschauen','dableiben','dalassen','dabeihaben','dranbleiben'],0,'drüberschauen = etwas kurz überprüfen.'),
q('Wer aus alten Industrieflächen lebendige Stadtviertel entwickeln will, muss ___ mehr machen als nur teure Wohnungen.',['daraus','dafür','damit','dabei','daraufhin'],0,'daraus machen = aus einer Sache etwas gestalten.'),
q('Viele Bürger sind ___, dass kommunale Entscheidungen transparenter erklärt werden.',['dafür','damit','dabei','daraus','da'],0,'dafür sein = eine Meinung vertreten / unterstützen.'),
q('Bei einer Anhörung sollte jeder die wichtigsten Unterlagen ___, damit die Diskussion sachlich bleibt.',['dabeihaben','dabeibleiben','dalassen','dranbleiben','drüberschauen'],0,'dabeihaben = etwas bei sich haben.'),
q('Wenn die Debatte länger dauert, werde ich bis zur Abstimmung ___.',['dableiben','dabei sein','dabeihaben','dalassen','daraus machen'],0,'dableiben = an einem Ort bleiben.'),
q('Ich möchte bei der Arbeitsgruppe ___, weil die Entscheidung langfristige Folgen für die Schule hat.',['dabei sein','dableiben','dabeihaben','drüberschauen','dalassen'],0,'dabei sein = an einer Aktivität teilnehmen.'),
q('Eine kurze Nachricht sollte man nicht ungeprüft ___, wenn sie sensible Daten enthält.',['dalassen','dabei sein','dableiben','daraus machen','dranbleiben'],0,'dalassen = etwas an einem Ort zurücklassen.'),
q('Die Verwaltung legte neue Zahlen vor; ___ wurde die Kritik an der bisherigen Planung noch schärfer.',['daraufhin','dabei','dafür','damit','daraus'],0,'daraufhin = Reaktion/Folge im nächsten Schritt.'),
q('Viele Programme versprechen Objektivität; ___ können sie bestehende Vorurteile sogar unsichtbar fortsetzen.',['dabei','dafür','damit','daraufhin','daraus'],0,'dabei = trotzdem/obwohl das so ist; kontrastive Einschränkung.'),
q('___ der Zugang zu Behörden zunehmend digitalisiert wird, dürfen ältere Menschen nicht ausgeschlossen werden.',['Da','Dabei','Dafür','Damit','Daraus'],0,'da = weil/angesichts der Tatsache, dass; kausaler Nebensatz.'),
q('Die Schule stellt Leihgeräte bereit, ___ soziale Unterschiede nicht noch stärker auf die Lernleistungen durchschlagen.',['damit','dabei','daher','dafür','daraus'],0,'damit = finaler Nebensatz; Zweck.'),
q('Die Schüler nutzen KI für erste Entwürfe; ___ müssen sie aber lernen, die Ergebnisse kritisch zu überarbeiten.',['dabei','damit','daraus','dafür','daraufhin'],0,'dabei = bei dieser Nutzung / gleichzeitig mit einschränkender Aussage.'),
q('Aus einem einzelnen erfolgreichen Modellprojekt kann man nicht automatisch ___, dass die Lösung überall funktioniert.',['schließen','drüberschauen','dalassen','dableiben','dabeihaben'],0,'aus etwas schließen = aus einer Sache eine Folgerung ableiten.'),
q('Wenn eine Reform gesellschaftlich notwendig ist, sollte man trotz Widerständen ___.',['dranbleiben','dalassen','dabeihaben','dableiben','dabei sein'],0,'dranbleiben = nicht aufgeben.'),
q('Viele Menschen kritisieren Datensammlung; ___ akzeptieren sie im Alltag zahlreiche Apps ohne genaue Prüfung.',['dabei','damit','dafür','daraus','daraufhin'],0,'dabei = allerdings/trotzdem; Gegensatz zur ersten Aussage.'),
q('Wer eine Statistik zitiert, sollte kurz ___, ob Quelle, Zeitraum und Definitionen wirklich passen.',['drüberschauen','dabeihaben','dableiben','dalassen','dabei sein'],0,'drüberschauen = etwas überprüfen.'),
q('Die Stadt kaufte eine alte Fabrikhalle; ___ soll ein öffentliches Kulturzentrum entstehen.',['daraus','dafür','damit','dabei','daraufhin'],0,'daraus = aus dieser Sache; daraus soll etwas werden/gemacht werden.'),
q('Ich bin ___, dass Prüfungen nicht nur Wissen, sondern auch begründetes Urteilen messen sollten.',['dafür','damit','dabei','daraus','da'],0,'dafür sein, dass ... = eine Position vertreten.'),
q('Die Teilnehmenden sollten ihre Ausweise ___, weil der Zugang zur Veranstaltung kontrolliert wird.',['dabeihaben','dableiben','dalassen','dabei sein','dranbleiben'],0,'dabeihaben = etwas bei sich führen.')
]};
tests.push(dawoerter1,dawoerter2);
window.erorterungTests=tests;
window.ERORTERUNG_TESTS=tests;
window.AAYS_DA_WOERTER_2_TESTS_OK=true;
window.AAYS_DA_WOERTER_FROM_TABLE_OK=true;
})();