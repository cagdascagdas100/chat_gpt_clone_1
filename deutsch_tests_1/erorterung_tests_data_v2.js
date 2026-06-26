const letters=["A","B","C","D","E"];
function q(text,options,answer,rule){return{q:text,options,answer,rule};}
const tests=[
  {
    "id": "poss1",
    "title": "Possessivartikel I â€“ Digitale Bildung",
    "description": "Possessivartikel in einem zusammenhÃ¤ngenden ErÃ¶rterungsthema: digitale Bildung.",
    "questions": [
      {
        "q": "Viele Schulen kÃ¶nnen ___ digitale Infrastruktur nur verbessern, wenn langfristig investiert wird.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural: Schulen â†’ ihre; feminin Akkusativ"
      },
      {
        "q": "Ein SchÃ¼ler entwickelt ___ Medienkompetenz nicht durch GerÃ¤te allein, sondern durch reflektierte Aufgaben.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "maskulin Singular: SchÃ¼ler â†’ seine; feminin Akkusativ"
      },
      {
        "q": "Die Lehrkraft sollte ___ pÃ¤dagogische Verantwortung nicht vollstÃ¤ndig an Lernplattformen abgeben.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "feminin Singular: Lehrkraft â†’ ihre; feminin Akkusativ"
      },
      {
        "q": "Der Staat muss ___ finanziellen Beitrag erhÃ¶hen, wenn digitale Bildung nicht vom Wohnort abhÃ¤ngen soll.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 3,
        "rule": "maskulin Singular: Staat â†’ seinen; maskulin Akkusativ"
      },
      {
        "q": "Jede Schule braucht ___ eigenes Konzept, damit Technik didaktisch sinnvoll eingesetzt wird.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 0,
        "rule": "feminin Singular: Schule â†’ ihr; Neutrum Akkusativ"
      },
      {
        "q": "Lernende erkennen ___ individuellen Fortschritt besser, wenn RÃ¼ckmeldungen verstÃ¤ndlich erklÃ¤rt werden.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "Plural: Lernende â†’ ihren; maskulin Akkusativ"
      },
      {
        "q": "Ein digitales GerÃ¤t entfaltet ___ Nutzen erst, wenn es in ein pÃ¤dagogisches Konzept eingebettet ist.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 3,
        "rule": "Neutrum Singular: GerÃ¤t â†’ seinen; maskulin Akkusativ"
      },
      {
        "q": "Die Bildungspolitik muss ___ langfristige Strategie an sozialen Unterschieden ausrichten.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "feminin Singular: Bildungspolitik â†’ ihre; feminin Akkusativ"
      },
      {
        "q": "Der Unterricht verliert ___ soziale QualitÃ¤t, wenn digitale Aufgaben persÃ¶nliche GesprÃ¤che verdrÃ¤ngen.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "maskulin Singular: Unterricht â†’ seine; feminin Akkusativ"
      },
      {
        "q": "Eine Lernplattform zeigt ___ StÃ¤rke vor allem dann, wenn sie individuelle FÃ¶rderung ermÃ¶glicht.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "feminin Singular: Lernplattform â†’ ihre; feminin Akkusativ"
      },
      {
        "q": "Das Kind braucht ___ vertraute Lernumgebung, auch wenn digitale Angebote den Unterricht ergÃ¤nzen.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "Neutrum Singular: Kind â†’ seine; feminin Akkusativ"
      },
      {
        "q": "Viele Eltern kennen ___ technische Unsicherheit nicht genau und benÃ¶tigen verstÃ¤ndliche UnterstÃ¼tzung.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural: Eltern â†’ ihre; feminin Akkusativ"
      },
      {
        "q": "Ein guter ErÃ¶rterungsabsatz macht ___ zentrale These bereits im ersten Satz erkennbar.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "maskulin Singular: Absatz â†’ seine; feminin Akkusativ"
      },
      {
        "q": "Die Schule darf ___ sozialen Auftrag nicht auf die Bereitstellung von Tablets reduzieren.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "feminin Singular: Schule â†’ ihren; maskulin Akkusativ"
      },
      {
        "q": "Der digitale Unterricht muss ___ pÃ¤dagogischen Mehrwert konkret nachweisen.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 3,
        "rule": "maskulin Singular: Unterricht â†’ seinen; maskulin Akkusativ"
      },
      {
        "q": "Eine Kommune zeigt ___ Verantwortung, wenn sie auch benachteiligte Familien technisch unterstÃ¼tzt.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "feminin Singular: Kommune â†’ ihre; feminin Akkusativ"
      },
      {
        "q": "Das Bildungssystem erreicht ___ Ziel nur, wenn LehrkrÃ¤fte ausreichend fortgebildet werden.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 0,
        "rule": "Neutrum Singular: System â†’ sein; Neutrum Akkusativ"
      },
      {
        "q": "SchÃ¼lerinnen und SchÃ¼ler stÃ¤rken ___ Urteilskraft, wenn sie digitale Quellen kritisch prÃ¼fen.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural â†’ ihre; feminin Akkusativ"
      },
      {
        "q": "Ein Online-Angebot verliert ___ GlaubwÃ¼rdigkeit, sobald Datenschutz und Transparenz fehlen.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "Neutrum Singular: Angebot â†’ seine; feminin Akkusativ"
      },
      {
        "q": "Die moderne Schule sollte ___ technischen MÃ¶glichkeiten nutzen, ohne den Menschen aus dem Zentrum zu verdrÃ¤ngen.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "feminin Singular: Schule â†’ ihre; Plural Akkusativ"
      }
    ]
  },
  {
    "id": "poss2",
    "title": "Possessivartikel II â€“ Haustiere in der modernen Gesellschaft",
    "description": "Possessivartikel in einem Vorteilsabsatz Ã¼ber Haustiere.",
    "questions": [
      {
        "q": "Ein Haustier entfaltet ___ emotionale Wirkung besonders bei Menschen, die im Alltag wenig NÃ¤he erleben.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "Neutrum Singular: Haustier â†’ seine; feminin Akkusativ"
      },
      {
        "q": "Viele Alleinlebende erleben durch ___ Tier mehr Struktur und weniger Einsamkeit.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 0,
        "rule": "Plural: Alleinlebende â†’ ihr; Neutrum Akkusativ"
      },
      {
        "q": "Ein Hund kann ___ Besitzer zu regelmÃ¤ÃŸiger Bewegung motivieren.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 3,
        "rule": "maskulin Singular: Hund â†’ seinen; maskulin Akkusativ"
      },
      {
        "q": "Die Familie stÃ¤rkt ___ Verantwortungsbewusstsein, wenn sie Pflegeaufgaben gemeinsam Ã¼bernimmt.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 0,
        "rule": "feminin Singular: Familie â†’ ihr; Neutrum Akkusativ"
      },
      {
        "q": "Das Kind entwickelt durch ___ Haustier oft mehr Empathie und Geduld.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 0,
        "rule": "Neutrum Singular: Kind â†’ sein; Neutrum Akkusativ"
      },
      {
        "q": "Ã„ltere Menschen behalten durch ___ tierischen Begleiter hÃ¤ufig einen klareren Tagesrhythmus.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "Plural: Ã¤ltere Menschen â†’ ihren; maskulin Akkusativ"
      },
      {
        "q": "Eine Katze zeigt ___ beruhigende Wirkung vor allem in einem stillen hÃ¤uslichen Umfeld.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "feminin Singular: Katze â†’ ihre; feminin Akkusativ"
      },
      {
        "q": "Der Tierhalter muss ___ Pflichten auch dann erfÃ¼llen, wenn er mÃ¼de oder gestresst ist.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "maskulin Singular: Tierhalter â†’ seine; Plural Akkusativ"
      },
      {
        "q": "Haustiere kÃ¶nnen ___ soziale Funktion entfalten, wenn sie GesprÃ¤che in der Nachbarschaft erleichtern.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural: Haustiere â†’ ihre; feminin Akkusativ"
      },
      {
        "q": "Ein Tier ersetzt keine Menschen, kann aber ___ Besitzer emotional stabilisieren.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 3,
        "rule": "Neutrum Singular: Tier â†’ seinen; maskulin Akkusativ"
      },
      {
        "q": "Die Nachbarschaft verbessert ___ Zusammenhalt, wenn Tierhalter einander unterstÃ¼tzen.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "feminin Singular: Nachbarschaft â†’ ihren; maskulin Akkusativ"
      },
      {
        "q": "Ein Haustier fordert ___ regelmÃ¤ÃŸige Pflege und macht Verantwortung praktisch erfahrbar.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "Neutrum Singular: Haustier â†’ seine; feminin Akkusativ"
      },
      {
        "q": "Kinder lernen, dass ___ WÃ¼nsche nicht immer wichtiger sind als die BedÃ¼rfnisse eines Lebewesens.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural: Kinder â†’ ihre; Plural Nominativ"
      },
      {
        "q": "Der Hund schafft durch ___ SpaziergÃ¤nge natÃ¼rliche GesprÃ¤chsanlÃ¤sse im Wohnviertel.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "maskulin Singular: Hund â†’ seine; Plural Akkusativ"
      },
      {
        "q": "Eine verantwortungsvolle Tierhaltung zeigt ___ Wert nicht im Besitz, sondern in FÃ¼rsorge und VerlÃ¤sslichkeit.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "feminin Singular: Tierhaltung â†’ ihren; maskulin Akkusativ"
      },
      {
        "q": "Das Haustier gibt ___ Halter das GefÃ¼hl, gebraucht zu werden.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 4,
        "rule": "geben + Dativ: seinem Halter"
      },
      {
        "q": "Viele Familien organisieren ___ Alltag bewusster, sobald ein Tier versorgt werden muss.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "Plural: Familien â†’ ihren; maskulin Akkusativ"
      },
      {
        "q": "Die emotionale Bindung zeigt ___ Bedeutung besonders in belastenden Lebensphasen.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "feminin Singular: Bindung â†’ ihre; feminin Akkusativ"
      },
      {
        "q": "Ein Tier kann ___ Platz in der modernen Gesellschaft finden, wenn seine BedÃ¼rfnisse respektiert werden.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 3,
        "rule": "Neutrum Singular: Tier â†’ seinen; maskulin Akkusativ"
      },
      {
        "q": "Haustiere stÃ¤rken ___ positive Wirkung auf LebensqualitÃ¤t, Gemeinschaft und Alltagsstruktur nicht automatisch, sondern durch verantwortliche Haltung.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural: Haustiere â†’ ihre; feminin Akkusativ"
      }
    ]
  },
  {
    "id": "dekl1",
    "title": "Deklination I â€“ Umweltschutz und nachhaltige Stadtentwicklung",
    "description": "Artikel, Kasus und Adjektivdeklination in einem ErÃ¶rterungsthema zum Umweltschutz.",
    "questions": [
      {
        "q": "Die Umsetzung ___ nachhaltigen Verkehrskonzepts kann die LuftqualitÃ¤t in StÃ¤dten deutlich verbessern.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 4,
        "rule": "Genitiv Neutrum: eines nachhaltigen Konzepts"
      },
      {
        "q": "Mit ___ konsequenten Ausbau des Radverkehrs lassen sich kurze Autofahrten reduzieren.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 2,
        "rule": "mit + Dativ maskulin: dem Ausbau"
      },
      {
        "q": "Viele BÃ¼rger wÃ¼nschen sich ___ sauberere Innenstadt mit weniger LÃ¤rm und Abgasen.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 1,
        "rule": "Akkusativ feminin: eine Innenstadt"
      },
      {
        "q": "Ohne ___ klare politische Strategie bleibt Umweltschutz oft symbolisch.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 1,
        "rule": "ohne + Akkusativ feminin"
      },
      {
        "q": "Die Kosten ___ Ã¶kologischen Modernisierung werden hÃ¤ufig als Gegenargument genannt.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin: der Modernisierung"
      },
      {
        "q": "In ___ dicht bebauten Stadtvierteln fehlt oft Platz fÃ¼r neue GrÃ¼nflÃ¤chen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 3,
        "rule": "Dativ Plural: den Stadtvierteln"
      },
      {
        "q": "Durch ___ bessere WÃ¤rmedÃ¤mmung kÃ¶nnen Haushalte langfristig Energie sparen.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 1,
        "rule": "durch + Akkusativ feminin"
      },
      {
        "q": "Der Schutz ___ stÃ¤dtischen GrÃ¼nraums verbessert auch das soziale Wohlbefinden.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 4,
        "rule": "Genitiv maskulin: des GrÃ¼nraums"
      },
      {
        "q": "Eine Kommune braucht ___ realistischen Zeitplan, damit Ã¶kologische Ziele erreichbar bleiben.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 3,
        "rule": "Akkusativ maskulin: einen Zeitplan"
      },
      {
        "q": "Trotz ___ hohen Anfangskosten kann nachhaltige Infrastruktur langfristig gÃ¼nstiger sein.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 1,
        "rule": "trotz + Genitiv Plural: der Kosten"
      },
      {
        "q": "Bei ___ Ã¶ffentlichen Debatte sollte auch soziale Gerechtigkeit berÃ¼cksichtigt werden.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "bei + Dativ feminin: der Debatte"
      },
      {
        "q": "Die EinfÃ¼hrung ___ autofreien Zone kann den lokalen Handel zunÃ¤chst verunsichern.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "einer"
        ],
        "answer": 4,
        "rule": "Genitiv feminin: einer autofreien Zone"
      },
      {
        "q": "FÃ¼r ___ wirksamen Klimaschutz mÃ¼ssen Energie, Verkehr und Wohnen gemeinsam gedacht werden.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 3,
        "rule": "fÃ¼r + Akkusativ maskulin"
      },
      {
        "q": "Der Ausbau ___ erneuerbaren Energien darf nicht an BÃ¼rokratie scheitern.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv Plural: der Energien"
      },
      {
        "q": "Nach ___ erfolgreichen Pilotprojekt kann eine Stadt weitere MaÃŸnahmen planen.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 2,
        "rule": "nach + Dativ Neutrum: einem Projekt"
      },
      {
        "q": "Die Beteiligung ___ betroffenen Bewohner erhÃ¶ht die Akzeptanz neuer MaÃŸnahmen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv Plural: der Bewohner"
      },
      {
        "q": "Ein Park in ___ dicht besiedelten Viertel ist mehr als ein dekoratives Element.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 2,
        "rule": "in + Dativ Neutrum: einem Viertel"
      },
      {
        "q": "Die Reduzierung ___ privaten Autoverkehrs verlangt attraktive Alternativen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 4,
        "rule": "Genitiv maskulin: des Autoverkehrs"
      },
      {
        "q": "Mit ___ besseren Planung kÃ¶nnen Ã¶kologische und wirtschaftliche Interessen verbunden werden.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 2,
        "rule": "mit + Dativ feminin: einer Planung"
      },
      {
        "q": "Am Ende entscheidet die QualitÃ¤t ___ konkreten Umsetzung Ã¼ber den Erfolg.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin: der Umsetzung"
      }
    ]
  },
  {
    "id": "dekl2",
    "title": "Deklination II â€“ Massentourismus in beliebten StÃ¤dten",
    "description": "PrÃ¤positionen, Genitiv und attributive Gruppen in einem ErÃ¶rterungsthema zum Massentourismus.",
    "questions": [
      {
        "q": "Angesichts ___ steigenden Besucherzahlen geraten viele AltstÃ¤dte zunehmend unter Druck.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "angesichts + Genitiv Plural: der Besucherzahlen"
      },
      {
        "q": "Der Erhalt ___ historischen Stadtbildes ist fÃ¼r viele Bewohner ein zentrales Anliegen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 4,
        "rule": "Genitiv Neutrum: des Stadtbildes"
      },
      {
        "q": "In ___ beliebten Vierteln steigen Mieten oft schneller als die Einkommen der Einheimischen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 3,
        "rule": "Dativ Plural: den Vierteln"
      },
      {
        "q": "Durch ___ unkontrollierten Tourismus verlieren manche Orte ihre alltÃ¤gliche Funktion.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 3,
        "rule": "durch + Akkusativ maskulin: den Tourismus"
      },
      {
        "q": "Eine Stadt braucht ___ ausgewogene Strategie zwischen wirtschaftlichem Nutzen und LebensqualitÃ¤t.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 1,
        "rule": "Akkusativ feminin"
      },
      {
        "q": "Trotz ___ finanziellen Vorteile darf die Belastung der BevÃ¶lkerung nicht ignoriert werden.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "trotz + Genitiv Plural: der Vorteile"
      },
      {
        "q": "Mit ___ besseren Besucherlenkung lassen sich Ã¼berfÃ¼llte PlÃ¤tze entlasten.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 2,
        "rule": "mit + Dativ feminin: einer Besucherlenkung"
      },
      {
        "q": "Die EinfÃ¼hrung ___ begrenzten Zugangszahl kann sensible Orte schÃ¼tzen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "einer"
        ],
        "answer": 4,
        "rule": "Genitiv feminin: einer Zugangszahl"
      },
      {
        "q": "FÃ¼r ___ nachhaltigen Tourismus mÃ¼ssen lokale Interessen stÃ¤rker berÃ¼cksichtigt werden.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 3,
        "rule": "fÃ¼r + Akkusativ maskulin"
      },
      {
        "q": "Ohne ___ faire Verteilung der Einnahmen wÃ¤chst der Unmut in der BevÃ¶lkerung.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 1,
        "rule": "ohne + Akkusativ feminin"
      },
      {
        "q": "Die Rechte ___ ansÃ¤ssigen BevÃ¶lkerung sollten nicht hinter kommerziellen Interessen verschwinden.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin: der BevÃ¶lkerung"
      },
      {
        "q": "Bei ___ Ã¶ffentlichen Diskussion Ã¼ber Massentourismus geht es nicht nur um Geld.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "bei + Dativ feminin"
      },
      {
        "q": "Die Begrenzung ___ kurzfristigen Ferienwohnungen kann Wohnraum schÃ¼tzen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv Plural: der Wohnungen"
      },
      {
        "q": "Ein Verbot ohne ___ klare BegrÃ¼ndung wirkt willkÃ¼rlich und schwer vermittelbar.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 1,
        "rule": "ohne + Akkusativ feminin"
      },
      {
        "q": "Nach ___ erfolgreichen Regulierung kÃ¶nnten auch andere StÃ¤dte Ã¤hnliche Modelle Ã¼bernehmen.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 2,
        "rule": "nach + Dativ feminin: einer Regulierung"
      },
      {
        "q": "Der Verlust ___ lokalen Alltagskultur ist ein hÃ¤ufig unterschÃ¤tztes Problem.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin: der Alltagskultur"
      },
      {
        "q": "Mit ___ transparenten Regelwerk kann die Akzeptanz neuer MaÃŸnahmen steigen.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "eines"
        ],
        "answer": 2,
        "rule": "mit + Dativ Neutrum: einem Regelwerk"
      },
      {
        "q": "Die Interessen ___ kleinen Betriebe unterscheiden sich oft von denen groÃŸer Hotelketten.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv Plural: der Betriebe"
      },
      {
        "q": "In ___ Ã¼berfÃ¼llten Innenstadt sinkt fÃ¼r Bewohner oft die LebensqualitÃ¤t.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Dativ feminin: der Innenstadt"
      },
      {
        "q": "Eine LÃ¶sung muss ___ wirtschaftlichen Bedeutung des Tourismus ebenso gerecht werden wie dem Schutz des Wohnraums.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Dativ feminin: der Bedeutung"
      }
    ]
  },
  {
    "id": "pron",
    "title": "Nur Pronomen â€“ KÃ¼nstliche Intelligenz im Bildungsbereich",
    "description": "Pronomenbezug und KohÃ¤renz in einem ErÃ¶rterungsthema zu KI im Unterricht.",
    "questions": [
      {
        "q": "KÃ¼nstliche Intelligenz kann Lernende unterstÃ¼tzen, wenn ___ gezielt und transparent eingesetzt wird.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "feminin: die kÃ¼nstliche Intelligenz â†’ sie"
      },
      {
        "q": "Ein automatisches Feedback ist hilfreich, sofern ___ verstÃ¤ndlich erklÃ¤rt, was verbessert werden sollte.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 2,
        "rule": "Neutrum: das Feedback â†’ es"
      },
      {
        "q": "Viele SchÃ¼ler nutzen digitale Assistenten, ohne dass ___ deren Grenzen genau kennen.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "Plural: viele SchÃ¼ler â†’ sie"
      },
      {
        "q": "Der Lehrer bleibt wichtig, weil ___ pÃ¤dagogische Entscheidungen nicht vollstÃ¤ndig automatisieren darf.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 0,
        "rule": "maskulin: der Lehrer â†’ er"
      },
      {
        "q": "Ein KI-System wirkt objektiv, obwohl ___ von Daten und Vorgaben abhÃ¤ngig ist.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 2,
        "rule": "Neutrum: das System â†’ es"
      },
      {
        "q": "Die Lernenden profitieren nur dann, wenn ___ RÃ¼ckmeldungen kritisch prÃ¼fen.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "Plural: die Lernenden â†’ sie"
      },
      {
        "q": "Der Datenschutz ist zentral, weil man ___ im Bildungsbereich besonders ernst nehmen muss.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 3,
        "rule": "maskulin Akkusativ: den Datenschutz â†’ ihn"
      },
      {
        "q": "Eine Schule sollte KI nicht einsetzen, wenn ___ keine klaren Regeln dafÃ¼r hat.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "feminin: die Schule â†’ sie"
      },
      {
        "q": "Das Argument Ã¼berzeugt, weil ___ Chancen und Risiken miteinander verbindet.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 2,
        "rule": "Neutrum: das Argument â†’ es"
      },
      {
        "q": "LehrkrÃ¤fte brauchen Fortbildungen, damit ___ KI sinnvoll in den Unterricht integrieren kÃ¶nnen.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "Plural: LehrkrÃ¤fte â†’ sie"
      },
      {
        "q": "Ein Algorithmus kann Fehler verstÃ¤rken, wenn ___ einseitige Daten verarbeitet.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 0,
        "rule": "maskulin: der Algorithmus â†’ er"
      },
      {
        "q": "Die Technik ersetzt keine Beziehung, sondern kann ___ hÃ¶chstens ergÃ¤nzen.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "feminin Akkusativ: die Beziehung â†’ sie"
      },
      {
        "q": "Viele Eltern befÃ¼rchten, dass KI Entscheidungen trifft, die ___ nicht nachvollziehen kÃ¶nnen.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "Plural: Eltern â†’ sie"
      },
      {
        "q": "Das Lernen wird individueller, wenn ___ an den tatsÃ¤chlichen Bedarf angepasst wird.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 2,
        "rule": "Neutrum: das Lernen â†’ es"
      },
      {
        "q": "Die Lehrkraft muss erklÃ¤ren, warum ___ ein digitales Werkzeug auswÃ¤hlt.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "feminin: Lehrkraft â†’ sie"
      },
      {
        "q": "Ein SchÃ¼ler verliert Motivation, wenn ___ nur noch maschinelle RÃ¼ckmeldungen erhÃ¤lt.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 0,
        "rule": "maskulin: SchÃ¼ler â†’ er"
      },
      {
        "q": "Die Daten der Lernenden sind sensibel; deshalb muss man ___ besonders schÃ¼tzen.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "Plural Akkusativ: Daten â†’ sie"
      },
      {
        "q": "Ein System kann nÃ¼tzlich sein, aber ___ darf die Verantwortung des Menschen nicht verdrÃ¤ngen.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 2,
        "rule": "Neutrum: System â†’ es"
      },
      {
        "q": "Die Schule muss prÃ¼fen, ob ___ durch KI soziale Ungleichheiten verstÃ¤rkt.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "diese"
        ],
        "answer": 4,
        "rule": "diese = die Schule/Entwicklung im Kontext; Demonstrativbezug"
      },
      {
        "q": "KI kann ein Werkzeug sein; entscheidend ist, wie man ___ pÃ¤dagogisch einbettet.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "feminin Akkusativ: KI â†’ sie"
      }
    ]
  },
  {
    "id": "indef1",
    "title": "Indefinitpronomen I â€“ Homeoffice und moderne Arbeitswelt",
    "description": "Indefinitpronomen fÃ¼r Personen in einem ErÃ¶rterungsthema zum Homeoffice.",
    "questions": [
      {
        "q": "___ profitiert vom Homeoffice, wenn zu Hause weder Ruhe noch ein geeigneter Arbeitsplatz vorhanden sind.",
        "options": [
          "Jemand",
          "Niemand",
          "Einige",
          "Manche",
          "Mehrere"
        ],
        "answer": 1,
        "rule": "Niemand als negatives Subjekt"
      },
      {
        "q": "___ BeschÃ¤ftigte gewinnen durch Homeoffice Zeit, weil lange Arbeitswege entfallen.",
        "options": [
          "Jemand",
          "Niemand",
          "Einige",
          "Nichts",
          "Einer"
        ],
        "answer": 2,
        "rule": "Einige + Plural"
      },
      {
        "q": "Wenn ___ im Team erreichbar ist, leidet die Zusammenarbeit trotz digitaler Tools.",
        "options": [
          "jemand",
          "niemand",
          "mehrere",
          "manche",
          "alle"
        ],
        "answer": 1,
        "rule": "niemand als Subjekt"
      },
      {
        "q": "___ sollte Homeoffice nur als private Bequemlichkeit darstellen.",
        "options": [
          "Man",
          "Niemand",
          "Etwas",
          "Mehrere",
          "Alle"
        ],
        "answer": 1,
        "rule": "Niemand = keiner sollte"
      },
      {
        "q": "FÃ¼r ___ ist die flexible Arbeitsform eine Chance, Familie und Beruf besser zu verbinden.",
        "options": [
          "manche",
          "jemand",
          "niemand",
          "nichts",
          "keiner"
        ],
        "answer": 0,
        "rule": "manche als Personenbezug"
      },
      {
        "q": "___ muss klare Regeln vereinbaren, damit Arbeitszeit und Freizeit nicht verschwimmen.",
        "options": [
          "Man",
          "Nichts",
          "Niemanden",
          "Etwas",
          "Mehreren"
        ],
        "answer": 0,
        "rule": "man als unpersÃ¶nliches Subjekt"
      },
      {
        "q": "Wenn ___ stÃ¤ndig erreichbar sein muss, verliert Homeoffice seinen entlastenden Charakter.",
        "options": [
          "jemand",
          "nichts",
          "mehrere",
          "keiner",
          "allem"
        ],
        "answer": 0,
        "rule": "jemand als Person"
      },
      {
        "q": "___ der Beteiligten kann gute Ergebnisse erzielen, wenn Kommunikation nur zufÃ¤llig stattfindet.",
        "options": [
          "Keiner",
          "Keine",
          "Keines",
          "Keinem",
          "Keinen"
        ],
        "answer": 0,
        "rule": "Keiner der Beteiligten"
      },
      {
        "q": "___ empfinden Homeoffice als isolierend, obwohl sie die Freiheit grundsÃ¤tzlich schÃ¤tzen.",
        "options": [
          "Manche",
          "Niemand",
          "Etwas",
          "Jemand",
          "Nichts"
        ],
        "answer": 0,
        "rule": "Manche als Pluralpersonen"
      },
      {
        "q": "___ im Unternehmen sollte ausgeschlossen werden, nur weil er nicht tÃ¤glich im BÃ¼ro ist.",
        "options": [
          "Jemand",
          "Niemand",
          "Nichts",
          "Etwas",
          "Mehrere"
        ],
        "answer": 1,
        "rule": "Niemand als Subjekt"
      },
      {
        "q": "___ brauchen klare RÃ¼ckmeldungen, damit Leistung im Homeoffice sichtbar bleibt.",
        "options": [
          "Einige",
          "Niemand",
          "Etwas",
          "Nichts",
          "Jemand"
        ],
        "answer": 0,
        "rule": "Einige + Plural"
      },
      {
        "q": "Wenn ___ Verantwortung Ã¼bernimmt, entstehen Konflikte Ã¼ber Erreichbarkeit und Aufgabenverteilung.",
        "options": [
          "niemand",
          "jemandem",
          "manchen",
          "etwas",
          "mehreren"
        ],
        "answer": 0,
        "rule": "niemand als Subjekt"
      },
      {
        "q": "___ kann produktiver arbeiten, wenn die TÃ¤tigkeit Konzentration und wenig direkte Abstimmung erfordert.",
        "options": [
          "Jemand",
          "Nichts",
          "Niemanden",
          "Allein",
          "Keines"
        ],
        "answer": 0,
        "rule": "Jemand als Person"
      },
      {
        "q": "In einer ErÃ¶rterung muss ___ zwischen individueller Freiheit und betrieblicher Organisation unterscheiden.",
        "options": [
          "man",
          "etwas",
          "nichts",
          "niemanden",
          "mehreren"
        ],
        "answer": 0,
        "rule": "man als unpersÃ¶nliches Subjekt"
      },
      {
        "q": "___ BeschÃ¤ftigten fÃ¤llt es schwer, nach Feierabend wirklich abzuschalten.",
        "options": [
          "Manchen",
          "Niemand",
          "Etwas",
          "Jemand",
          "Nichts"
        ],
        "answer": 0,
        "rule": "Dativ Plural: manchen BeschÃ¤ftigten"
      },
      {
        "q": "___ darf erwarten, dass digitale Zusammenarbeit ohne Vertrauen funktioniert.",
        "options": [
          "Niemand",
          "Jemand",
          "Einige",
          "Manche",
          "Mehrere"
        ],
        "answer": 0,
        "rule": "Niemand als Subjekt"
      },
      {
        "q": "FÃ¼r ___ kann das BÃ¼ro ein wichtiger sozialer Ort bleiben.",
        "options": [
          "einige",
          "nichts",
          "niemand",
          "jemandem",
          "keines"
        ],
        "answer": 0,
        "rule": "einige als Personenbezug"
      },
      {
        "q": "Wenn ___ im Homeoffice vereinsamt, muss das Unternehmen Austausch bewusst organisieren.",
        "options": [
          "jemand",
          "nichts",
          "keines",
          "mehreren",
          "allen"
        ],
        "answer": 0,
        "rule": "jemand als Subjekt"
      },
      {
        "q": "___ sollte aus EinzelfÃ¤llen ableiten, dass Homeoffice grundsÃ¤tzlich schlecht ist.",
        "options": [
          "Niemand",
          "Jemand",
          "Etwas",
          "Manche",
          "Mehrere"
        ],
        "answer": 0,
        "rule": "Niemand = keiner sollte"
      },
      {
        "q": "___ profitieren besonders dann, wenn Vertrauen, Technik und klare Erwartungen zusammenkommen.",
        "options": [
          "Viele",
          "Nichts",
          "Niemand",
          "Jemand",
          "Keines"
        ],
        "answer": 0,
        "rule": "Viele als Personenbezug"
      }
    ]
  },
  {
    "id": "indef2",
    "title": "Indefinitpronomen II â€“ Fast Fashion und Konsumverhalten",
    "description": "Indefinitpronomen fÃ¼r Dinge, Mengen und Sachverhalte in einem ErÃ¶rterungsthema zu Fast Fashion.",
    "questions": [
      {
        "q": "Nicht ___, was billig angeboten wird, ist langfristig gesellschaftlich vertretbar.",
        "options": [
          "alles",
          "alle",
          "jeder",
          "jemand",
          "mehrere"
        ],
        "answer": 0,
        "rule": "alles fÃ¼r Sachverhalte"
      },
      {
        "q": "___ der genannten Argumente rechtfertigt allein den massenhaften Kauf kurzlebiger Kleidung.",
        "options": [
          "Keine",
          "Keiner",
          "Keines",
          "Keinem",
          "Keinen"
        ],
        "answer": 2,
        "rule": "Keines der Argumente"
      },
      {
        "q": "FÃ¼r ___ Verbraucher ist der niedrige Preis entscheidend, obwohl die Ã¶kologischen Folgen bekannt sind.",
        "options": [
          "manche",
          "manchem",
          "manchen",
          "mancher",
          "manches"
        ],
        "answer": 0,
        "rule": "manche + Plural Nominativ"
      },
      {
        "q": "Es gibt kaum ___, das ohne Ressourcenverbrauch produziert werden kann.",
        "options": [
          "etwas",
          "jemand",
          "alle",
          "manchen",
          "keinen"
        ],
        "answer": 0,
        "rule": "etwas als Sachbezug"
      },
      {
        "q": "___ von den sozialen Kosten bleibt unsichtbar, wenn nur der Preis im GeschÃ¤ft betrachtet wird.",
        "options": [
          "Vieles",
          "Viele",
          "Jemand",
          "Keiner",
          "Alle"
        ],
        "answer": 0,
        "rule": "Vieles als Sachbezug"
      },
      {
        "q": "Nicht ___ kann sich nachhaltige Kleidung leisten, selbst wenn der Wille vorhanden ist.",
        "options": [
          "jeder",
          "alles",
          "etwas",
          "nichts",
          "mehrere"
        ],
        "answer": 0,
        "rule": "jeder als Personenbezug"
      },
      {
        "q": "___ spricht dafÃ¼r, Kleidung lÃ¤nger zu tragen, statt stÃ¤ndig neuen Trends zu folgen.",
        "options": [
          "Vieles",
          "Jemand",
          "Alle",
          "Keiner",
          "Manchen"
        ],
        "answer": 0,
        "rule": "Vieles als zusammenfassender Sachbezug"
      },
      {
        "q": "Ohne ___ an den Produktionsbedingungen zu Ã¤ndern, bleibt Kritik an Fast Fashion oberflÃ¤chlich.",
        "options": [
          "etwas",
          "jemand",
          "alle",
          "keiner",
          "mehreren"
        ],
        "answer": 0,
        "rule": "etwas Ã¤ndern"
      },
      {
        "q": "___ der KleidungsstÃ¼cke wird oft gekauft, obwohl es nur wenige Male getragen wird.",
        "options": [
          "Manches",
          "Manche",
          "Manchem",
          "Manchen",
          "Mehrere"
        ],
        "answer": 0,
        "rule": "Manches der KleidungsstÃ¼cke"
      },
      {
        "q": "Wenn ___ Ã¼ber Lieferketten bekannt ist, kÃ¶nnen Konsumenten schwer Verantwortung Ã¼bernehmen.",
        "options": [
          "nichts",
          "niemand",
          "alle",
          "jeder",
          "manche"
        ],
        "answer": 0,
        "rule": "nichts als Sachbezug"
      },
      {
        "q": "___ der Beteiligten profitiert gleichermaÃŸen von niedrigen Preisen.",
        "options": [
          "Keiner",
          "Keine",
          "Keines",
          "Keinem",
          "Keinen"
        ],
        "answer": 0,
        "rule": "Keiner der Beteiligten"
      },
      {
        "q": "FÃ¼r ___ reicht ein moralischer Appell nicht aus, solange nachhaltige Alternativen teuer bleiben.",
        "options": [
          "viele",
          "nichts",
          "niemand",
          "etwas",
          "keines"
        ],
        "answer": 0,
        "rule": "viele als Personenbezug"
      },
      {
        "q": "___ an Fast Fashion wirkt harmlos, wenn die globalen Folgen ausgeblendet werden.",
        "options": [
          "Manches",
          "Manche",
          "Manchem",
          "Manchen",
          "Alle"
        ],
        "answer": 0,
        "rule": "Manches als Sachbezug"
      },
      {
        "q": "Nicht ___ lÃ¤sst sich allein durch Konsumentscheidungen lÃ¶sen.",
        "options": [
          "alles",
          "alle",
          "jeder",
          "jemand",
          "mehrere"
        ],
        "answer": 0,
        "rule": "alles als Sachbezug"
      },
      {
        "q": "___ muss sich Ã¤ndern, wenn Kleidung nicht lÃ¤nger als Wegwerfprodukt gelten soll.",
        "options": [
          "Etwas",
          "Jemand",
          "Alle",
          "Keiner",
          "Manchen"
        ],
        "answer": 0,
        "rule": "etwas als unbestimmter Sachverhalt"
      },
      {
        "q": "___ Verbraucherinnen kaufen bewusster, sobald Herkunft und Arbeitsbedingungen transparent werden.",
        "options": [
          "Manche",
          "Manchem",
          "Manchen",
          "Mancher",
          "Manches"
        ],
        "answer": 0,
        "rule": "manche + Plural Nominativ"
      },
      {
        "q": "___ der Probleme entsteht nicht beim Kauf, sondern bereits in der Produktion.",
        "options": [
          "Manches",
          "Manche",
          "Manchem",
          "Manchen",
          "Keinen"
        ],
        "answer": 0,
        "rule": "Manches der Probleme"
      },
      {
        "q": "Wenn ___ nur auf Verbote setzt, wird die soziale Frage gÃ¼nstiger Kleidung Ã¼bersehen.",
        "options": [
          "man",
          "etwas",
          "nichts",
          "niemanden",
          "mehreren"
        ],
        "answer": 0,
        "rule": "man als unpersÃ¶nliches Subjekt"
      },
      {
        "q": "___ spricht gegen die Idee, Trends vÃ¶llig zu verbieten; entscheidend ist verantwortlicher Konsum.",
        "options": [
          "Vieles",
          "Jemand",
          "Keiner",
          "Alle",
          "Manchen"
        ],
        "answer": 0,
        "rule": "Vieles als Sachbezug"
      },
      {
        "q": "Am Ende reicht ___ allein aus, wenn Politik, Unternehmen und Verbraucher nicht gemeinsam handeln.",
        "options": [
          "nichts",
          "niemand",
          "alle",
          "jeder",
          "manche"
        ],
        "answer": 0,
        "rule": "nichts als Sachbezug"
      }
    ]
  },
  {
    "id": "neg1",
    "title": "NegationswÃ¶rter I â€“ Deklination in ErÃ¶rterungen",
    "description": "kein-Formen und negative Determinanten.",
    "questions": [
      {
        "q": "___ verantwortungsvolle Politik darf die Risiken von digitale Bildung ignorieren.",
        "options": [
          "Kein",
          "Keine",
          "Keinem",
          "Keinen",
          "Keiner"
        ],
        "answer": 1,
        "rule": "keine + feminine Subjektgruppe"
      },
      {
        "q": "Ohne ___ klare BegrÃ¼ndung wirkt ein Argument oberflÃ¤chlich.",
        "options": [
          "kein",
          "keine",
          "keinem",
          "keinen",
          "keiner"
        ],
        "answer": 1,
        "rule": "ohne + Akkusativ feminin"
      },
      {
        "q": "Mit ___ einfachen LÃ¶sung ist bei Umweltschutz zu rechnen.",
        "options": [
          "kein",
          "keine",
          "keinem",
          "keinen",
          "keiner"
        ],
        "answer": 4,
        "rule": "mit + Dativ feminin"
      },
      {
        "q": "___ der genannten Aspekte sollte isoliert betrachtet werden.",
        "options": [
          "Kein",
          "Keine",
          "Keines",
          "Keinem",
          "Keinen"
        ],
        "answer": 2,
        "rule": "keines der Aspekte"
      },
      {
        "q": "___ verantwortungsvolle Politik darf die Risiken von Homeoffice ignorieren.",
        "options": [
          "Kein",
          "Keine",
          "Keinem",
          "Keinen",
          "Keiner"
        ],
        "answer": 1,
        "rule": "keine + feminine Subjektgruppe"
      },
      {
        "q": "Ohne ___ klare BegrÃ¼ndung wirkt ein Argument oberflÃ¤chlich.",
        "options": [
          "kein",
          "keine",
          "keinem",
          "keinen",
          "keiner"
        ],
        "answer": 1,
        "rule": "ohne + Akkusativ feminin"
      },
      {
        "q": "Mit ___ einfachen LÃ¶sung ist bei Fast Fashion zu rechnen.",
        "options": [
          "kein",
          "keine",
          "keinem",
          "keinen",
          "keiner"
        ],
        "answer": 4,
        "rule": "mit + Dativ feminin"
      },
      {
        "q": "___ der genannten Aspekte sollte isoliert betrachtet werden.",
        "options": [
          "Kein",
          "Keine",
          "Keines",
          "Keinem",
          "Keinen"
        ],
        "answer": 2,
        "rule": "keines der Aspekte"
      },
      {
        "q": "___ verantwortungsvolle Politik darf die Risiken von Ã¶ffentliche Verkehrsmittel ignorieren.",
        "options": [
          "Kein",
          "Keine",
          "Keinem",
          "Keinen",
          "Keiner"
        ],
        "answer": 1,
        "rule": "keine + feminine Subjektgruppe"
      },
      {
        "q": "Ohne ___ klare BegrÃ¼ndung wirkt ein Argument oberflÃ¤chlich.",
        "options": [
          "kein",
          "keine",
          "keinem",
          "keinen",
          "keiner"
        ],
        "answer": 1,
        "rule": "ohne + Akkusativ feminin"
      },
      {
        "q": "Mit ___ einfachen LÃ¶sung ist bei Studium im Ausland zu rechnen.",
        "options": [
          "kein",
          "keine",
          "keinem",
          "keinen",
          "keiner"
        ],
        "answer": 4,
        "rule": "mit + Dativ feminin"
      },
      {
        "q": "___ der genannten Aspekte sollte isoliert betrachtet werden.",
        "options": [
          "Kein",
          "Keine",
          "Keines",
          "Keinem",
          "Keinen"
        ],
        "answer": 2,
        "rule": "keines der Aspekte"
      },
      {
        "q": "___ verantwortungsvolle Politik darf die Risiken von E-Books ignorieren.",
        "options": [
          "Kein",
          "Keine",
          "Keinem",
          "Keinen",
          "Keiner"
        ],
        "answer": 1,
        "rule": "keine + feminine Subjektgruppe"
      },
      {
        "q": "Ohne ___ klare BegrÃ¼ndung wirkt ein Argument oberflÃ¤chlich.",
        "options": [
          "kein",
          "keine",
          "keinem",
          "keinen",
          "keiner"
        ],
        "answer": 1,
        "rule": "ohne + Akkusativ feminin"
      },
      {
        "q": "Mit ___ einfachen LÃ¶sung ist bei Datenschutz zu rechnen.",
        "options": [
          "kein",
          "keine",
          "keinem",
          "keinen",
          "keiner"
        ],
        "answer": 4,
        "rule": "mit + Dativ feminin"
      },
      {
        "q": "___ der genannten Aspekte sollte isoliert betrachtet werden.",
        "options": [
          "Kein",
          "Keine",
          "Keines",
          "Keinem",
          "Keinen"
        ],
        "answer": 2,
        "rule": "keines der Aspekte"
      },
      {
        "q": "___ verantwortungsvolle Politik darf die Risiken von Teamarbeit ignorieren.",
        "options": [
          "Kein",
          "Keine",
          "Keinem",
          "Keinen",
          "Keiner"
        ],
        "answer": 1,
        "rule": "keine + feminine Subjektgruppe"
      },
      {
        "q": "Ohne ___ klare BegrÃ¼ndung wirkt ein Argument oberflÃ¤chlich.",
        "options": [
          "kein",
          "keine",
          "keinem",
          "keinen",
          "keiner"
        ],
        "answer": 1,
        "rule": "ohne + Akkusativ feminin"
      },
      {
        "q": "Mit ___ einfachen LÃ¶sung ist bei Werbung in Medien zu rechnen.",
        "options": [
          "kein",
          "keine",
          "keinem",
          "keinen",
          "keiner"
        ],
        "answer": 4,
        "rule": "mit + Dativ feminin"
      },
      {
        "q": "___ der genannten Aspekte sollte isoliert betrachtet werden.",
        "options": [
          "Kein",
          "Keine",
          "Keines",
          "Keinem",
          "Keinen"
        ],
        "answer": 2,
        "rule": "keines der Aspekte"
      }
    ]
  },
  {
    "id": "neg2",
    "title": "NegationswÃ¶rter II â€“ GegensÃ¤tze und ErÃ¶rterungssprache",
    "description": "nicht, weder noch und kontrastive Strukturen.",
    "questions": [
      {
        "q": "Weder wirtschaftliche Vorteile ___ technische Bequemlichkeit reichen als alleinige BegrÃ¼ndung aus.",
        "options": [
          "oder",
          "noch",
          "aber",
          "sondern",
          "denn"
        ],
        "answer": 1,
        "rule": "weder ... noch"
      },
      {
        "q": "soziale Medien ist nicht nur eine private Frage, ___ auch ein gesellschaftliches Thema.",
        "options": [
          "aber",
          "oder",
          "sondern",
          "denn",
          "noch"
        ],
        "answer": 2,
        "rule": "nicht nur, sondern auch"
      },
      {
        "q": "Je komplexer ein Thema ist, desto ___ sollte man pauschal urteilen.",
        "options": [
          "mehr",
          "weniger",
          "kaum",
          "nie",
          "keiner"
        ],
        "answer": 1,
        "rule": "je ... desto weniger"
      },
      {
        "q": "Ein Verbot ist ___ immer die Ã¼berzeugendste LÃ¶sung.",
        "options": [
          "nicht",
          "kein",
          "keine",
          "keiner",
          "keinen"
        ],
        "answer": 0,
        "rule": "Satznegation mit nicht"
      },
      {
        "q": "Weder wirtschaftliche Vorteile ___ technische Bequemlichkeit reichen als alleinige BegrÃ¼ndung aus.",
        "options": [
          "oder",
          "noch",
          "aber",
          "sondern",
          "denn"
        ],
        "answer": 1,
        "rule": "weder ... noch"
      },
      {
        "q": "Massentourismus ist nicht nur eine private Frage, ___ auch ein gesellschaftliches Thema.",
        "options": [
          "aber",
          "oder",
          "sondern",
          "denn",
          "noch"
        ],
        "answer": 2,
        "rule": "nicht nur, sondern auch"
      },
      {
        "q": "Je komplexer ein Thema ist, desto ___ sollte man pauschal urteilen.",
        "options": [
          "mehr",
          "weniger",
          "kaum",
          "nie",
          "keiner"
        ],
        "answer": 1,
        "rule": "je ... desto weniger"
      },
      {
        "q": "Ein Verbot ist ___ immer die Ã¼berzeugendste LÃ¶sung.",
        "options": [
          "nicht",
          "kein",
          "keine",
          "keiner",
          "keinen"
        ],
        "answer": 0,
        "rule": "Satznegation mit nicht"
      },
      {
        "q": "Weder wirtschaftliche Vorteile ___ technische Bequemlichkeit reichen als alleinige BegrÃ¼ndung aus.",
        "options": [
          "oder",
          "noch",
          "aber",
          "sondern",
          "denn"
        ],
        "answer": 1,
        "rule": "weder ... noch"
      },
      {
        "q": "Mehrsprachigkeit ist nicht nur eine private Frage, ___ auch ein gesellschaftliches Thema.",
        "options": [
          "aber",
          "oder",
          "sondern",
          "denn",
          "noch"
        ],
        "answer": 2,
        "rule": "nicht nur, sondern auch"
      },
      {
        "q": "Je komplexer ein Thema ist, desto ___ sollte man pauschal urteilen.",
        "options": [
          "mehr",
          "weniger",
          "kaum",
          "nie",
          "keiner"
        ],
        "answer": 1,
        "rule": "je ... desto weniger"
      },
      {
        "q": "Ein Verbot ist ___ immer die Ã¼berzeugendste LÃ¶sung.",
        "options": [
          "nicht",
          "kein",
          "keine",
          "keiner",
          "keinen"
        ],
        "answer": 0,
        "rule": "Satznegation mit nicht"
      },
      {
        "q": "Weder wirtschaftliche Vorteile ___ technische Bequemlichkeit reichen als alleinige BegrÃ¼ndung aus.",
        "options": [
          "oder",
          "noch",
          "aber",
          "sondern",
          "denn"
        ],
        "answer": 1,
        "rule": "weder ... noch"
      },
      {
        "q": "soziale Ungleichheit ist nicht nur eine private Frage, ___ auch ein gesellschaftliches Thema.",
        "options": [
          "aber",
          "oder",
          "sondern",
          "denn",
          "noch"
        ],
        "answer": 2,
        "rule": "nicht nur, sondern auch"
      },
      {
        "q": "Je komplexer ein Thema ist, desto ___ sollte man pauschal urteilen.",
        "options": [
          "mehr",
          "weniger",
          "kaum",
          "nie",
          "keiner"
        ],
        "answer": 1,
        "rule": "je ... desto weniger"
      },
      {
        "q": "Ein Verbot ist ___ immer die Ã¼berzeugendste LÃ¶sung.",
        "options": [
          "nicht",
          "kein",
          "keine",
          "keiner",
          "keinen"
        ],
        "answer": 0,
        "rule": "Satznegation mit nicht"
      },
      {
        "q": "Weder wirtschaftliche Vorteile ___ technische Bequemlichkeit reichen als alleinige BegrÃ¼ndung aus.",
        "options": [
          "oder",
          "noch",
          "aber",
          "sondern",
          "denn"
        ],
        "answer": 1,
        "rule": "weder ... noch"
      },
      {
        "q": "lebenslanges Lernen ist nicht nur eine private Frage, ___ auch ein gesellschaftliches Thema.",
        "options": [
          "aber",
          "oder",
          "sondern",
          "denn",
          "noch"
        ],
        "answer": 2,
        "rule": "nicht nur, sondern auch"
      },
      {
        "q": "Je komplexer ein Thema ist, desto ___ sollte man pauschal urteilen.",
        "options": [
          "mehr",
          "weniger",
          "kaum",
          "nie",
          "keiner"
        ],
        "answer": 1,
        "rule": "je ... desto weniger"
      },
      {
        "q": "Ein Verbot ist ___ immer die Ã¼berzeugendste LÃ¶sung.",
        "options": [
          "nicht",
          "kein",
          "keine",
          "keiner",
          "keinen"
        ],
        "answer": 0,
        "rule": "Satznegation mit nicht"
      }
    ]
  },
  {
    "id": "satz",
    "title": "Satzstellung I â€“ TeKaMoLo, Objektstellung und Verbklammer",
    "description": "Satzstellung, NebensÃ¤tze und Verbklammer.",
    "questions": [
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "In Bezug auf digitale Bildung sollte man die langfristigen Folgen sorgfÃ¤ltig abwÃ¤gen.",
          "In Bezug auf digitale Bildung man sollte die langfristigen Folgen sorgfÃ¤ltig abwÃ¤gen.",
          "Man sollte in Bezug auf digitale Bildung sorgfÃ¤ltig abwÃ¤gen die langfristigen Folgen.",
          "SorgfÃ¤ltig man sollte in Bezug auf digitale Bildung die langfristigen Folgen abwÃ¤gen.",
          "Die langfristigen Folgen sorgfÃ¤ltig sollte man in Bezug auf digitale Bildung abwÃ¤gen."
        ],
        "answer": 0,
        "rule": "Vorfeld + finites Verb + Mittelfeld + Verbklammer"
      },
      {
        "q": "Welche Variante ist C1/C2-gerecht?",
        "options": [
          "Obwohl soziale Medien Vorteile bietet, dÃ¼rfen mÃ¶gliche Risiken nicht ausgeblendet werden.",
          "Obwohl bietet soziale Medien Vorteile, mÃ¶gliche Risiken dÃ¼rfen nicht ausgeblendet werden.",
          "Obwohl soziale Medien bietet Vorteile, dÃ¼rfen nicht mÃ¶gliche Risiken ausgeblendet werden.",
          "Obwohl Vorteile bietet soziale Medien, dÃ¼rfen mÃ¶gliche Risiken nicht ausgeblendet werden.",
          "Obwohl soziale Medien Vorteile bietet, nicht dÃ¼rfen mÃ¶gliche Risiken ausgeblendet werden."
        ],
        "answer": 0,
        "rule": "Nebensatz mit Verb am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "Daher muss die Politik klare Rahmenbedingungen schaffen.",
          "Daher die Politik muss klare Rahmenbedingungen schaffen.",
          "Daher klare Rahmenbedingungen muss die Politik schaffen.",
          "Die Politik klare Rahmenbedingungen daher schaffen muss.",
          "Muss daher die Politik klare Rahmenbedingungen schaffen."
        ],
        "answer": 0,
        "rule": "Konsekutivadverb im Vorfeld"
      },
      {
        "q": "Welche Formulierung hat die richtige Verbklammer?",
        "options": [
          "Viele Betroffene kÃ¶nnten durch kÃ¼nstliche Intelligenz langfristig entlastet werden.",
          "Viele Betroffene kÃ¶nnten durch kÃ¼nstliche Intelligenz langfristig werden entlastet.",
          "Viele Betroffene durch kÃ¼nstliche Intelligenz kÃ¶nnten langfristig entlastet werden.",
          "KÃ¶nnten viele Betroffene langfristig durch kÃ¼nstliche Intelligenz entlastet werden.",
          "Langfristig entlastet durch kÃ¼nstliche Intelligenz kÃ¶nnten viele Betroffene werden."
        ],
        "answer": 0,
        "rule": "Modalverb + Infinitiv/Partizip am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "In Bezug auf Homeoffice sollte man die langfristigen Folgen sorgfÃ¤ltig abwÃ¤gen.",
          "In Bezug auf Homeoffice man sollte die langfristigen Folgen sorgfÃ¤ltig abwÃ¤gen.",
          "Man sollte in Bezug auf Homeoffice sorgfÃ¤ltig abwÃ¤gen die langfristigen Folgen.",
          "SorgfÃ¤ltig man sollte in Bezug auf Homeoffice die langfristigen Folgen abwÃ¤gen.",
          "Die langfristigen Folgen sorgfÃ¤ltig sollte man in Bezug auf Homeoffice abwÃ¤gen."
        ],
        "answer": 0,
        "rule": "Vorfeld + finites Verb + Mittelfeld + Verbklammer"
      },
      {
        "q": "Welche Variante ist C1/C2-gerecht?",
        "options": [
          "Obwohl Massentourismus Vorteile bietet, dÃ¼rfen mÃ¶gliche Risiken nicht ausgeblendet werden.",
          "Obwohl bietet Massentourismus Vorteile, mÃ¶gliche Risiken dÃ¼rfen nicht ausgeblendet werden.",
          "Obwohl Massentourismus bietet Vorteile, dÃ¼rfen nicht mÃ¶gliche Risiken ausgeblendet werden.",
          "Obwohl Vorteile bietet Massentourismus, dÃ¼rfen mÃ¶gliche Risiken nicht ausgeblendet werden.",
          "Obwohl Massentourismus Vorteile bietet, nicht dÃ¼rfen mÃ¶gliche Risiken ausgeblendet werden."
        ],
        "answer": 0,
        "rule": "Nebensatz mit Verb am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "Daher muss die Politik klare Rahmenbedingungen schaffen.",
          "Daher die Politik muss klare Rahmenbedingungen schaffen.",
          "Daher klare Rahmenbedingungen muss die Politik schaffen.",
          "Die Politik klare Rahmenbedingungen daher schaffen muss.",
          "Muss daher die Politik klare Rahmenbedingungen schaffen."
        ],
        "answer": 0,
        "rule": "Konsekutivadverb im Vorfeld"
      },
      {
        "q": "Welche Formulierung hat die richtige Verbklammer?",
        "options": [
          "Viele Betroffene kÃ¶nnten durch gesunde ErnÃ¤hrung langfristig entlastet werden.",
          "Viele Betroffene kÃ¶nnten durch gesunde ErnÃ¤hrung langfristig werden entlastet.",
          "Viele Betroffene durch gesunde ErnÃ¤hrung kÃ¶nnten langfristig entlastet werden.",
          "KÃ¶nnten viele Betroffene langfristig durch gesunde ErnÃ¤hrung entlastet werden.",
          "Langfristig entlastet durch gesunde ErnÃ¤hrung kÃ¶nnten viele Betroffene werden."
        ],
        "answer": 0,
        "rule": "Modalverb + Infinitiv/Partizip am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "In Bezug auf Ã¶ffentliche Verkehrsmittel sollte man die langfristigen Folgen sorgfÃ¤ltig abwÃ¤gen.",
          "In Bezug auf Ã¶ffentliche Verkehrsmittel man sollte die langfristigen Folgen sorgfÃ¤ltig abwÃ¤gen.",
          "Man sollte in Bezug auf Ã¶ffentliche Verkehrsmittel sorgfÃ¤ltig abwÃ¤gen die langfristigen Folgen.",
          "SorgfÃ¤ltig man sollte in Bezug auf Ã¶ffentliche Verkehrsmittel die langfristigen Folgen abwÃ¤gen.",
          "Die langfristigen Folgen sorgfÃ¤ltig sollte man in Bezug auf Ã¶ffentliche Verkehrsmittel abwÃ¤gen."
        ],
        "answer": 0,
        "rule": "Vorfeld + finites Verb + Mittelfeld + Verbklammer"
      },
      {
        "q": "Welche Variante ist C1/C2-gerecht?",
        "options": [
          "Obwohl Mehrsprachigkeit Vorteile bietet, dÃ¼rfen mÃ¶gliche Risiken nicht ausgeblendet werden.",
          "Obwohl bietet Mehrsprachigkeit Vorteile, mÃ¶gliche Risiken dÃ¼rfen nicht ausgeblendet werden.",
          "Obwohl Mehrsprachigkeit bietet Vorteile, dÃ¼rfen nicht mÃ¶gliche Risiken ausgeblendet werden.",
          "Obwohl Vorteile bietet Mehrsprachigkeit, dÃ¼rfen mÃ¶gliche Risiken nicht ausgeblendet werden.",
          "Obwohl Mehrsprachigkeit Vorteile bietet, nicht dÃ¼rfen mÃ¶gliche Risiken ausgeblendet werden."
        ],
        "answer": 0,
        "rule": "Nebensatz mit Verb am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "Daher muss die Politik klare Rahmenbedingungen schaffen.",
          "Daher die Politik muss klare Rahmenbedingungen schaffen.",
          "Daher klare Rahmenbedingungen muss die Politik schaffen.",
          "Die Politik klare Rahmenbedingungen daher schaffen muss.",
          "Muss daher die Politik klare Rahmenbedingungen schaffen."
        ],
        "answer": 0,
        "rule": "Konsekutivadverb im Vorfeld"
      },
      {
        "q": "Welche Formulierung hat die richtige Verbklammer?",
        "options": [
          "Viele Betroffene kÃ¶nnten durch Ganztagsschule langfristig entlastet werden.",
          "Viele Betroffene kÃ¶nnten durch Ganztagsschule langfristig werden entlastet.",
          "Viele Betroffene durch Ganztagsschule kÃ¶nnten langfristig entlastet werden.",
          "KÃ¶nnten viele Betroffene langfristig durch Ganztagsschule entlastet werden.",
          "Langfristig entlastet durch Ganztagsschule kÃ¶nnten viele Betroffene werden."
        ],
        "answer": 0,
        "rule": "Modalverb + Infinitiv/Partizip am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "In Bezug auf E-Books sollte man die langfristigen Folgen sorgfÃ¤ltig abwÃ¤gen.",
          "In Bezug auf E-Books man sollte die langfristigen Folgen sorgfÃ¤ltig abwÃ¤gen.",
          "Man sollte in Bezug auf E-Books sorgfÃ¤ltig abwÃ¤gen die langfristigen Folgen.",
          "SorgfÃ¤ltig man sollte in Bezug auf E-Books die langfristigen Folgen abwÃ¤gen.",
          "Die langfristigen Folgen sorgfÃ¤ltig sollte man in Bezug auf E-Books abwÃ¤gen."
        ],
        "answer": 0,
        "rule": "Vorfeld + finites Verb + Mittelfeld + Verbklammer"
      },
      {
        "q": "Welche Variante ist C1/C2-gerecht?",
        "options": [
          "Obwohl soziale Ungleichheit Vorteile bietet, dÃ¼rfen mÃ¶gliche Risiken nicht ausgeblendet werden.",
          "Obwohl bietet soziale Ungleichheit Vorteile, mÃ¶gliche Risiken dÃ¼rfen nicht ausgeblendet werden.",
          "Obwohl soziale Ungleichheit bietet Vorteile, dÃ¼rfen nicht mÃ¶gliche Risiken ausgeblendet werden.",
          "Obwohl Vorteile bietet soziale Ungleichheit, dÃ¼rfen mÃ¶gliche Risiken nicht ausgeblendet werden.",
          "Obwohl soziale Ungleichheit Vorteile bietet, nicht dÃ¼rfen mÃ¶gliche Risiken ausgeblendet werden."
        ],
        "answer": 0,
        "rule": "Nebensatz mit Verb am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "Daher muss die Politik klare Rahmenbedingungen schaffen.",
          "Daher die Politik muss klare Rahmenbedingungen schaffen.",
          "Daher klare Rahmenbedingungen muss die Politik schaffen.",
          "Die Politik klare Rahmenbedingungen daher schaffen muss.",
          "Muss daher die Politik klare Rahmenbedingungen schaffen."
        ],
        "answer": 0,
        "rule": "Konsekutivadverb im Vorfeld"
      },
      {
        "q": "Welche Formulierung hat die richtige Verbklammer?",
        "options": [
          "Viele Betroffene kÃ¶nnten durch ehrenamtliches Engagement langfristig entlastet werden.",
          "Viele Betroffene kÃ¶nnten durch ehrenamtliches Engagement langfristig werden entlastet.",
          "Viele Betroffene durch ehrenamtliches Engagement kÃ¶nnten langfristig entlastet werden.",
          "KÃ¶nnten viele Betroffene langfristig durch ehrenamtliches Engagement entlastet werden.",
          "Langfristig entlastet durch ehrenamtliches Engagement kÃ¶nnten viele Betroffene werden."
        ],
        "answer": 0,
        "rule": "Modalverb + Infinitiv/Partizip am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "In Bezug auf Teamarbeit sollte man die langfristigen Folgen sorgfÃ¤ltig abwÃ¤gen.",
          "In Bezug auf Teamarbeit man sollte die langfristigen Folgen sorgfÃ¤ltig abwÃ¤gen.",
          "Man sollte in Bezug auf Teamarbeit sorgfÃ¤ltig abwÃ¤gen die langfristigen Folgen.",
          "SorgfÃ¤ltig man sollte in Bezug auf Teamarbeit die langfristigen Folgen abwÃ¤gen.",
          "Die langfristigen Folgen sorgfÃ¤ltig sollte man in Bezug auf Teamarbeit abwÃ¤gen."
        ],
        "answer": 0,
        "rule": "Vorfeld + finites Verb + Mittelfeld + Verbklammer"
      },
      {
        "q": "Welche Variante ist C1/C2-gerecht?",
        "options": [
          "Obwohl lebenslanges Lernen Vorteile bietet, dÃ¼rfen mÃ¶gliche Risiken nicht ausgeblendet werden.",
          "Obwohl bietet lebenslanges Lernen Vorteile, mÃ¶gliche Risiken dÃ¼rfen nicht ausgeblendet werden.",
          "Obwohl lebenslanges Lernen bietet Vorteile, dÃ¼rfen nicht mÃ¶gliche Risiken ausgeblendet werden.",
          "Obwohl Vorteile bietet lebenslanges Lernen, dÃ¼rfen mÃ¶gliche Risiken nicht ausgeblendet werden.",
          "Obwohl lebenslanges Lernen Vorteile bietet, nicht dÃ¼rfen mÃ¶gliche Risiken ausgeblendet werden."
        ],
        "answer": 0,
        "rule": "Nebensatz mit Verb am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "Daher muss die Politik klare Rahmenbedingungen schaffen.",
          "Daher die Politik muss klare Rahmenbedingungen schaffen.",
          "Daher klare Rahmenbedingungen muss die Politik schaffen.",
          "Die Politik klare Rahmenbedingungen daher schaffen muss.",
          "Muss daher die Politik klare Rahmenbedingungen schaffen."
        ],
        "answer": 0,
        "rule": "Konsekutivadverb im Vorfeld"
      },
      {
        "q": "Welche Formulierung hat die richtige Verbklammer?",
        "options": [
          "Viele Betroffene kÃ¶nnten durch autonomes Fahren langfristig entlastet werden.",
          "Viele Betroffene kÃ¶nnten durch autonomes Fahren langfristig werden entlastet.",
          "Viele Betroffene durch autonomes Fahren kÃ¶nnten langfristig entlastet werden.",
          "KÃ¶nnten viele Betroffene langfristig durch autonomes Fahren entlastet werden.",
          "Langfristig entlastet durch autonomes Fahren kÃ¶nnten viele Betroffene werden."
        ],
        "answer": 0,
        "rule": "Modalverb + Infinitiv/Partizip am Ende"
      }
    ]
  },
  {
    "id": "rede1",
    "title": "Redemittel I â€“ Einleitung, Kontextualisierung und BegrÃ¼ndung",
    "description": "Einleitungen, BegrÃ¼ndungen und AbwÃ¤gungen.",
    "questions": [
      {
        "q": "Welche Einleitung passt am besten?",
        "options": [
          "In der aktuellen Debatte Ã¼ber digitale Bildung stellt sich die Frage, welche Chancen und Risiken damit verbunden sind.",
          "Ich finde digitale Bildung gut und schreibe jetzt darÃ¼ber.",
          "Alle reden Ã¼ber digitale Bildung, deshalb ist es wichtig.",
          "Das Thema digitale Bildung ist irgendwie modern.",
          "Man kann Ã¼ber digitale Bildung viel sagen."
        ],
        "answer": 0,
        "rule": "prÃ¤zise Einleitung"
      },
      {
        "q": "Welche BegrÃ¼ndung ist am stÃ¤rksten?",
        "options": [
          "Dies ist darauf zurÃ¼ckzufÃ¼hren, dass gesellschaftliche VerÃ¤nderungen selten nur eine Ursache haben.",
          "Das ist so, weil es eben so ist.",
          "Viele finden das gut.",
          "Es gibt GrÃ¼nde und Nachteile.",
          "Man sagt das oft."
        ],
        "answer": 0,
        "rule": "kausale BegrÃ¼ndung"
      },
      {
        "q": "Welche Redemittel-Kombination ist korrekt?",
        "options": [
          "Einerseits erÃ¶ffnet Umweltschutz neue MÃ¶glichkeiten, andererseits entstehen dadurch neue AbhÃ¤ngigkeiten.",
          "Einerseits Umweltschutz erÃ¶ffnet, andererseits entstehen dadurch.",
          "Entweder erÃ¶ffnet Umweltschutz, andererseits entstehen AbhÃ¤ngigkeiten.",
          "Nicht nur erÃ¶ffnet Umweltschutz, sondern entstehen AbhÃ¤ngigkeiten.",
          "Sowohl erÃ¶ffnet Umweltschutz, aber auch entstehen AbhÃ¤ngigkeiten."
        ],
        "answer": 0,
        "rule": "AbwÃ¤gung"
      },
      {
        "q": "Welche Kontextualisierung ist C1/C2-gerecht?",
        "options": [
          "Vor dem Hintergrund gesellschaftlicher VerÃ¤nderungen gewinnt kÃ¼nstliche Intelligenz zunehmend an Bedeutung.",
          "Im Hintergrund ist {c} sehr wichtig.",
          "Wegen Gesellschaft ist kÃ¼nstliche Intelligenz grÃ¶ÃŸer.",
          "kÃ¼nstliche Intelligenz macht eine Bedeutung.",
          "Das Thema hat Hintergrund."
        ],
        "answer": 0,
        "rule": "Kontextualisierung"
      },
      {
        "q": "Welche Einleitung passt am besten?",
        "options": [
          "In der aktuellen Debatte Ã¼ber Homeoffice stellt sich die Frage, welche Chancen und Risiken damit verbunden sind.",
          "Ich finde Homeoffice gut und schreibe jetzt darÃ¼ber.",
          "Alle reden Ã¼ber Homeoffice, deshalb ist es wichtig.",
          "Das Thema Homeoffice ist irgendwie modern.",
          "Man kann Ã¼ber Homeoffice viel sagen."
        ],
        "answer": 0,
        "rule": "prÃ¤zise Einleitung"
      },
      {
        "q": "Welche BegrÃ¼ndung ist am stÃ¤rksten?",
        "options": [
          "Dies ist darauf zurÃ¼ckzufÃ¼hren, dass gesellschaftliche VerÃ¤nderungen selten nur eine Ursache haben.",
          "Das ist so, weil es eben so ist.",
          "Viele finden das gut.",
          "Es gibt GrÃ¼nde und Nachteile.",
          "Man sagt das oft."
        ],
        "answer": 0,
        "rule": "kausale BegrÃ¼ndung"
      },
      {
        "q": "Welche Redemittel-Kombination ist korrekt?",
        "options": [
          "Einerseits erÃ¶ffnet Fast Fashion neue MÃ¶glichkeiten, andererseits entstehen dadurch neue AbhÃ¤ngigkeiten.",
          "Einerseits Fast Fashion erÃ¶ffnet, andererseits entstehen dadurch.",
          "Entweder erÃ¶ffnet Fast Fashion, andererseits entstehen AbhÃ¤ngigkeiten.",
          "Nicht nur erÃ¶ffnet Fast Fashion, sondern entstehen AbhÃ¤ngigkeiten.",
          "Sowohl erÃ¶ffnet Fast Fashion, aber auch entstehen AbhÃ¤ngigkeiten."
        ],
        "answer": 0,
        "rule": "AbwÃ¤gung"
      },
      {
        "q": "Welche Kontextualisierung ist C1/C2-gerecht?",
        "options": [
          "Vor dem Hintergrund gesellschaftlicher VerÃ¤nderungen gewinnt gesunde ErnÃ¤hrung zunehmend an Bedeutung.",
          "Im Hintergrund ist {c} sehr wichtig.",
          "Wegen Gesellschaft ist gesunde ErnÃ¤hrung grÃ¶ÃŸer.",
          "gesunde ErnÃ¤hrung macht eine Bedeutung.",
          "Das Thema hat Hintergrund."
        ],
        "answer": 0,
        "rule": "Kontextualisierung"
      },
      {
        "q": "Welche Einleitung passt am besten?",
        "options": [
          "In der aktuellen Debatte Ã¼ber Ã¶ffentliche Verkehrsmittel stellt sich die Frage, welche Chancen und Risiken damit verbunden sind.",
          "Ich finde Ã¶ffentliche Verkehrsmittel gut und schreibe jetzt darÃ¼ber.",
          "Alle reden Ã¼ber Ã¶ffentliche Verkehrsmittel, deshalb ist es wichtig.",
          "Das Thema Ã¶ffentliche Verkehrsmittel ist irgendwie modern.",
          "Man kann Ã¼ber Ã¶ffentliche Verkehrsmittel viel sagen."
        ],
        "answer": 0,
        "rule": "prÃ¤zise Einleitung"
      },
      {
        "q": "Welche BegrÃ¼ndung ist am stÃ¤rksten?",
        "options": [
          "Dies ist darauf zurÃ¼ckzufÃ¼hren, dass gesellschaftliche VerÃ¤nderungen selten nur eine Ursache haben.",
          "Das ist so, weil es eben so ist.",
          "Viele finden das gut.",
          "Es gibt GrÃ¼nde und Nachteile.",
          "Man sagt das oft."
        ],
        "answer": 0,
        "rule": "kausale BegrÃ¼ndung"
      },
      {
        "q": "Welche Redemittel-Kombination ist korrekt?",
        "options": [
          "Einerseits erÃ¶ffnet Studium im Ausland neue MÃ¶glichkeiten, andererseits entstehen dadurch neue AbhÃ¤ngigkeiten.",
          "Einerseits Studium im Ausland erÃ¶ffnet, andererseits entstehen dadurch.",
          "Entweder erÃ¶ffnet Studium im Ausland, andererseits entstehen AbhÃ¤ngigkeiten.",
          "Nicht nur erÃ¶ffnet Studium im Ausland, sondern entstehen AbhÃ¤ngigkeiten.",
          "Sowohl erÃ¶ffnet Studium im Ausland, aber auch entstehen AbhÃ¤ngigkeiten."
        ],
        "answer": 0,
        "rule": "AbwÃ¤gung"
      },
      {
        "q": "Welche Kontextualisierung ist C1/C2-gerecht?",
        "options": [
          "Vor dem Hintergrund gesellschaftlicher VerÃ¤nderungen gewinnt Ganztagsschule zunehmend an Bedeutung.",
          "Im Hintergrund ist {c} sehr wichtig.",
          "Wegen Gesellschaft ist Ganztagsschule grÃ¶ÃŸer.",
          "Ganztagsschule macht eine Bedeutung.",
          "Das Thema hat Hintergrund."
        ],
        "answer": 0,
        "rule": "Kontextualisierung"
      },
      {
        "q": "Welche Einleitung passt am besten?",
        "options": [
          "In der aktuellen Debatte Ã¼ber E-Books stellt sich die Frage, welche Chancen und Risiken damit verbunden sind.",
          "Ich finde E-Books gut und schreibe jetzt darÃ¼ber.",
          "Alle reden Ã¼ber E-Books, deshalb ist es wichtig.",
          "Das Thema E-Books ist irgendwie modern.",
          "Man kann Ã¼ber E-Books viel sagen."
        ],
        "answer": 0,
        "rule": "prÃ¤zise Einleitung"
      },
      {
        "q": "Welche BegrÃ¼ndung ist am stÃ¤rksten?",
        "options": [
          "Dies ist darauf zurÃ¼ckzufÃ¼hren, dass gesellschaftliche VerÃ¤nderungen selten nur eine Ursache haben.",
          "Das ist so, weil es eben so ist.",
          "Viele finden das gut.",
          "Es gibt GrÃ¼nde und Nachteile.",
          "Man sagt das oft."
        ],
        "answer": 0,
        "rule": "kausale BegrÃ¼ndung"
      },
      {
        "q": "Welche Redemittel-Kombination ist korrekt?",
        "options": [
          "Einerseits erÃ¶ffnet Datenschutz neue MÃ¶glichkeiten, andererseits entstehen dadurch neue AbhÃ¤ngigkeiten.",
          "Einerseits Datenschutz erÃ¶ffnet, andererseits entstehen dadurch.",
          "Entweder erÃ¶ffnet Datenschutz, andererseits entstehen AbhÃ¤ngigkeiten.",
          "Nicht nur erÃ¶ffnet Datenschutz, sondern entstehen AbhÃ¤ngigkeiten.",
          "Sowohl erÃ¶ffnet Datenschutz, aber auch entstehen AbhÃ¤ngigkeiten."
        ],
        "answer": 0,
        "rule": "AbwÃ¤gung"
      },
      {
        "q": "Welche Kontextualisierung ist C1/C2-gerecht?",
        "options": [
          "Vor dem Hintergrund gesellschaftlicher VerÃ¤nderungen gewinnt ehrenamtliches Engagement zunehmend an Bedeutung.",
          "Im Hintergrund ist {c} sehr wichtig.",
          "Wegen Gesellschaft ist ehrenamtliches Engagement grÃ¶ÃŸer.",
          "ehrenamtliches Engagement macht eine Bedeutung.",
          "Das Thema hat Hintergrund."
        ],
        "answer": 0,
        "rule": "Kontextualisierung"
      },
      {
        "q": "Welche Einleitung passt am besten?",
        "options": [
          "In der aktuellen Debatte Ã¼ber Teamarbeit stellt sich die Frage, welche Chancen und Risiken damit verbunden sind.",
          "Ich finde Teamarbeit gut und schreibe jetzt darÃ¼ber.",
          "Alle reden Ã¼ber Teamarbeit, deshalb ist es wichtig.",
          "Das Thema Teamarbeit ist irgendwie modern.",
          "Man kann Ã¼ber Teamarbeit viel sagen."
        ],
        "answer": 0,
        "rule": "prÃ¤zise Einleitung"
      },
      {
        "q": "Welche BegrÃ¼ndung ist am stÃ¤rksten?",
        "options": [
          "Dies ist darauf zurÃ¼ckzufÃ¼hren, dass gesellschaftliche VerÃ¤nderungen selten nur eine Ursache haben.",
          "Das ist so, weil es eben so ist.",
          "Viele finden das gut.",
          "Es gibt GrÃ¼nde und Nachteile.",
          "Man sagt das oft."
        ],
        "answer": 0,
        "rule": "kausale BegrÃ¼ndung"
      },
      {
        "q": "Welche Redemittel-Kombination ist korrekt?",
        "options": [
          "Einerseits erÃ¶ffnet Werbung in Medien neue MÃ¶glichkeiten, andererseits entstehen dadurch neue AbhÃ¤ngigkeiten.",
          "Einerseits Werbung in Medien erÃ¶ffnet, andererseits entstehen dadurch.",
          "Entweder erÃ¶ffnet Werbung in Medien, andererseits entstehen AbhÃ¤ngigkeiten.",
          "Nicht nur erÃ¶ffnet Werbung in Medien, sondern entstehen AbhÃ¤ngigkeiten.",
          "Sowohl erÃ¶ffnet Werbung in Medien, aber auch entstehen AbhÃ¤ngigkeiten."
        ],
        "answer": 0,
        "rule": "AbwÃ¤gung"
      },
      {
        "q": "Welche Kontextualisierung ist C1/C2-gerecht?",
        "options": [
          "Vor dem Hintergrund gesellschaftlicher VerÃ¤nderungen gewinnt autonomes Fahren zunehmend an Bedeutung.",
          "Im Hintergrund ist {c} sehr wichtig.",
          "Wegen Gesellschaft ist autonomes Fahren grÃ¶ÃŸer.",
          "autonomes Fahren macht eine Bedeutung.",
          "Das Thema hat Hintergrund."
        ],
        "answer": 0,
        "rule": "Kontextualisierung"
      }
    ]
  },
  {
    "id": "rede2",
    "title": "Redemittel II â€“ Folgen, AbwÃ¤gung, Kritik und Schluss",
    "description": "Folge, Kritik, AbwÃ¤gung und Schluss.",
    "questions": [
      {
        "q": "Welche Folgeformulierung passt?",
        "options": [
          "Dies kann dazu fÃ¼hren, dass bestehende Ungleichheiten verstÃ¤rkt werden.",
          "Dies kann machen, dass es schlecht wird.",
          "Dies fÃ¼hrt, dass Ungleichheiten.",
          "Dadurch ist es Folge.",
          "Es kommt eine Folge heraus."
        ],
        "answer": 0,
        "rule": "Folgen ausdrÃ¼cken"
      },
      {
        "q": "Welche kritische Bewertung ist prÃ¤zise?",
        "options": [
          "Problematisch ist weniger die Idee selbst als ihre unzureichend regulierte Umsetzung.",
          "Das ist schlecht, weil es schlecht ist.",
          "Die Idee ist immer problematisch.",
          "Regulierung ist nicht wichtig.",
          "Alles daran ist falsch."
        ],
        "answer": 0,
        "rule": "differenzierte Kritik"
      },
      {
        "q": "Welche Schlussformel ist angemessen?",
        "options": [
          "Zusammenfassend lÃ¤sst sich festhalten, dass Umweltschutz nur unter klaren Bedingungen sinnvoll genutzt werden kann.",
          "Am Ende ist Umweltschutz gut.",
          "Ich bin fertig mit dem Thema.",
          "Alles zusammen ist wichtig.",
          "Das war meine Meinung."
        ],
        "answer": 0,
        "rule": "Schlussfolgerung"
      },
      {
        "q": "Welche AbwÃ¤gung ist korrekt?",
        "options": [
          "WÃ¤hrend kurzfristige Vorteile sichtbar sind, mÃ¼ssen langfristige Nebenwirkungen sorgfÃ¤ltig geprÃ¼ft werden.",
          "WÃ¤hrend Vorteile sind sichtbar, mÃ¼ssen geprÃ¼ft Nebenwirkungen.",
          "Kurzfristig Vorteile, langfristig Nebenwirkungen.",
          "Obwohl Vorteile sichtbar, Nebenwirkungen mÃ¼ssen.",
          "Vorteile sind, aber prÃ¼fen."
        ],
        "answer": 0,
        "rule": "konzessive AbwÃ¤gung"
      },
      {
        "q": "Welche Folgeformulierung passt?",
        "options": [
          "Dies kann dazu fÃ¼hren, dass bestehende Ungleichheiten verstÃ¤rkt werden.",
          "Dies kann machen, dass es schlecht wird.",
          "Dies fÃ¼hrt, dass Ungleichheiten.",
          "Dadurch ist es Folge.",
          "Es kommt eine Folge heraus."
        ],
        "answer": 0,
        "rule": "Folgen ausdrÃ¼cken"
      },
      {
        "q": "Welche kritische Bewertung ist prÃ¤zise?",
        "options": [
          "Problematisch ist weniger die Idee selbst als ihre unzureichend regulierte Umsetzung.",
          "Das ist schlecht, weil es schlecht ist.",
          "Die Idee ist immer problematisch.",
          "Regulierung ist nicht wichtig.",
          "Alles daran ist falsch."
        ],
        "answer": 0,
        "rule": "differenzierte Kritik"
      },
      {
        "q": "Welche Schlussformel ist angemessen?",
        "options": [
          "Zusammenfassend lÃ¤sst sich festhalten, dass Fast Fashion nur unter klaren Bedingungen sinnvoll genutzt werden kann.",
          "Am Ende ist Fast Fashion gut.",
          "Ich bin fertig mit dem Thema.",
          "Alles zusammen ist wichtig.",
          "Das war meine Meinung."
        ],
        "answer": 0,
        "rule": "Schlussfolgerung"
      },
      {
        "q": "Welche AbwÃ¤gung ist korrekt?",
        "options": [
          "WÃ¤hrend kurzfristige Vorteile sichtbar sind, mÃ¼ssen langfristige Nebenwirkungen sorgfÃ¤ltig geprÃ¼ft werden.",
          "WÃ¤hrend Vorteile sind sichtbar, mÃ¼ssen geprÃ¼ft Nebenwirkungen.",
          "Kurzfristig Vorteile, langfristig Nebenwirkungen.",
          "Obwohl Vorteile sichtbar, Nebenwirkungen mÃ¼ssen.",
          "Vorteile sind, aber prÃ¼fen."
        ],
        "answer": 0,
        "rule": "konzessive AbwÃ¤gung"
      },
      {
        "q": "Welche Folgeformulierung passt?",
        "options": [
          "Dies kann dazu fÃ¼hren, dass bestehende Ungleichheiten verstÃ¤rkt werden.",
          "Dies kann machen, dass es schlecht wird.",
          "Dies fÃ¼hrt, dass Ungleichheiten.",
          "Dadurch ist es Folge.",
          "Es kommt eine Folge heraus."
        ],
        "answer": 0,
        "rule": "Folgen ausdrÃ¼cken"
      },
      {
        "q": "Welche kritische Bewertung ist prÃ¤zise?",
        "options": [
          "Problematisch ist weniger die Idee selbst als ihre unzureichend regulierte Umsetzung.",
          "Das ist schlecht, weil es schlecht ist.",
          "Die Idee ist immer problematisch.",
          "Regulierung ist nicht wichtig.",
          "Alles daran ist falsch."
        ],
        "answer": 0,
        "rule": "differenzierte Kritik"
      },
      {
        "q": "Welche Schlussformel ist angemessen?",
        "options": [
          "Zusammenfassend lÃ¤sst sich festhalten, dass Studium im Ausland nur unter klaren Bedingungen sinnvoll genutzt werden kann.",
          "Am Ende ist Studium im Ausland gut.",
          "Ich bin fertig mit dem Thema.",
          "Alles zusammen ist wichtig.",
          "Das war meine Meinung."
        ],
        "answer": 0,
        "rule": "Schlussfolgerung"
      },
      {
        "q": "Welche AbwÃ¤gung ist korrekt?",
        "options": [
          "WÃ¤hrend kurzfristige Vorteile sichtbar sind, mÃ¼ssen langfristige Nebenwirkungen sorgfÃ¤ltig geprÃ¼ft werden.",
          "WÃ¤hrend Vorteile sind sichtbar, mÃ¼ssen geprÃ¼ft Nebenwirkungen.",
          "Kurzfristig Vorteile, langfristig Nebenwirkungen.",
          "Obwohl Vorteile sichtbar, Nebenwirkungen mÃ¼ssen.",
          "Vorteile sind, aber prÃ¼fen."
        ],
        "answer": 0,
        "rule": "konzessive AbwÃ¤gung"
      },
      {
        "q": "Welche Folgeformulierung passt?",
        "options": [
          "Dies kann dazu fÃ¼hren, dass bestehende Ungleichheiten verstÃ¤rkt werden.",
          "Dies kann machen, dass es schlecht wird.",
          "Dies fÃ¼hrt, dass Ungleichheiten.",
          "Dadurch ist es Folge.",
          "Es kommt eine Folge heraus."
        ],
        "answer": 0,
        "rule": "Folgen ausdrÃ¼cken"
      },
      {
        "q": "Welche kritische Bewertung ist prÃ¤zise?",
        "options": [
          "Problematisch ist weniger die Idee selbst als ihre unzureichend regulierte Umsetzung.",
          "Das ist schlecht, weil es schlecht ist.",
          "Die Idee ist immer problematisch.",
          "Regulierung ist nicht wichtig.",
          "Alles daran ist falsch."
        ],
        "answer": 0,
        "rule": "differenzierte Kritik"
      },
      {
        "q": "Welche Schlussformel ist angemessen?",
        "options": [
          "Zusammenfassend lÃ¤sst sich festhalten, dass Datenschutz nur unter klaren Bedingungen sinnvoll genutzt werden kann.",
          "Am Ende ist Datenschutz gut.",
          "Ich bin fertig mit dem Thema.",
          "Alles zusammen ist wichtig.",
          "Das war meine Meinung."
        ],
        "answer": 0,
        "rule": "Schlussfolgerung"
      },
      {
        "q": "Welche AbwÃ¤gung ist korrekt?",
        "options": [
          "WÃ¤hrend kurzfristige Vorteile sichtbar sind, mÃ¼ssen langfristige Nebenwirkungen sorgfÃ¤ltig geprÃ¼ft werden.",
          "WÃ¤hrend Vorteile sind sichtbar, mÃ¼ssen geprÃ¼ft Nebenwirkungen.",
          "Kurzfristig Vorteile, langfristig Nebenwirkungen.",
          "Obwohl Vorteile sichtbar, Nebenwirkungen mÃ¼ssen.",
          "Vorteile sind, aber prÃ¼fen."
        ],
        "answer": 0,
        "rule": "konzessive AbwÃ¤gung"
      },
      {
        "q": "Welche Folgeformulierung passt?",
        "options": [
          "Dies kann dazu fÃ¼hren, dass bestehende Ungleichheiten verstÃ¤rkt werden.",
          "Dies kann machen, dass es schlecht wird.",
          "Dies fÃ¼hrt, dass Ungleichheiten.",
          "Dadurch ist es Folge.",
          "Es kommt eine Folge heraus."
        ],
        "answer": 0,
        "rule": "Folgen ausdrÃ¼cken"
      },
      {
        "q": "Welche kritische Bewertung ist prÃ¤zise?",
        "options": [
          "Problematisch ist weniger die Idee selbst als ihre unzureichend regulierte Umsetzung.",
          "Das ist schlecht, weil es schlecht ist.",
          "Die Idee ist immer problematisch.",
          "Regulierung ist nicht wichtig.",
          "Alles daran ist falsch."
        ],
        "answer": 0,
        "rule": "differenzierte Kritik"
      },
      {
        "q": "Welche Schlussformel ist angemessen?",
        "options": [
          "Zusammenfassend lÃ¤sst sich festhalten, dass Werbung in Medien nur unter klaren Bedingungen sinnvoll genutzt werden kann.",
          "Am Ende ist Werbung in Medien gut.",
          "Ich bin fertig mit dem Thema.",
          "Alles zusammen ist wichtig.",
          "Das war meine Meinung."
        ],
        "answer": 0,
        "rule": "Schlussfolgerung"
      },
      {
        "q": "Welche AbwÃ¤gung ist korrekt?",
        "options": [
          "WÃ¤hrend kurzfristige Vorteile sichtbar sind, mÃ¼ssen langfristige Nebenwirkungen sorgfÃ¤ltig geprÃ¼ft werden.",
          "WÃ¤hrend Vorteile sind sichtbar, mÃ¼ssen geprÃ¼ft Nebenwirkungen.",
          "Kurzfristig Vorteile, langfristig Nebenwirkungen.",
          "Obwohl Vorteile sichtbar, Nebenwirkungen mÃ¼ssen.",
          "Vorteile sind, aber prÃ¼fen."
        ],
        "answer": 0,
        "rule": "konzessive AbwÃ¤gung"
      }
    ]
  }
];
