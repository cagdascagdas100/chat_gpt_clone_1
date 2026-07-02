const contexts=["Kontext 1", "Kontext 2", "Kontext 3", "Kontext 4", "Kontext 5", "Kontext 6", "Kontext 7", "Kontext 8", "Kontext 9", "Kontext 10", "Kontext 11", "Kontext 12", "Kontext 13", "Kontext 14", "Kontext 15", "Kontext 16", "Kontext 17", "Kontext 18", "Kontext 19", "Kontext 20"];
const letters=["A","B","C","D","E"];
function q(text,options,answer,rule){return{q:text,options,answer,rule};}
const fixed={
  "poss1": [
    {
      "q": "Viele Schulen k\u00f6nnen ___ digitale Infrastruktur nur verbessern, wenn langfristig investiert wird.",
      "options": [
        "sein",
        "seine",
        "ihre",
        "ihren",
        "ihrer"
      ],
      "answer": 2,
      "rule": "Schulen = Plural; Infrastruktur = feminin Akkusativ: ihre"
    },
    {
      "q": "Ein moderner Unterricht entfaltet ___ Wirkung erst, wenn Lehrkr\u00e4fte didaktisch vorbereitet sind.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 1,
      "rule": "der Unterricht; Wirkung = feminin Akkusativ: seine"
    },
    {
      "q": "Die Schule muss ___ Medienkonzept regelm\u00e4\u00dfig \u00fcberpr\u00fcfen, damit digitale Bildung nicht zuf\u00e4llig bleibt.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 0,
      "rule": "die Schule; Medienkonzept = Neutrum Akkusativ: ihr"
    },
    {
      "q": "Viele Eltern sehen ___ Verantwortung darin, Kinder beim kritischen Umgang mit Onlinequellen zu begleiten.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "Eltern = Plural; Verantwortung = feminin Akkusativ: ihre"
    },
    {
      "q": "Der Staat darf ___ Bildungsauftrag nicht allein auf technische Ger\u00e4te reduzieren.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 3,
      "rule": "der Staat; Bildungsauftrag = maskulin Akkusativ: seinen"
    },
    {
      "q": "Eine Schule st\u00e4rkt ___ digitale Lernkultur, wenn sie klare Regeln f\u00fcr Plattformen entwickelt.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "die Schule; Lernkultur = feminin Akkusativ: ihre"
    },
    {
      "q": "Ein Tablet verliert ___ p\u00e4dagogischen Wert, wenn Aufgaben nur oberfl\u00e4chlich digitalisiert werden.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 3,
      "rule": "das Tablet; Wert = maskulin Akkusativ: seinen"
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
      "rule": "die Bildungspolitik; Strategie = feminin Akkusativ: ihre"
    },
    {
      "q": "Ein Sch\u00fcler kann ___ Lernfortschritt besser einsch\u00e4tzen, wenn digitale R\u00fcckmeldungen verst\u00e4ndlich sind.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 3,
      "rule": "ein Sch\u00fcler; Lernfortschritt = maskulin Akkusativ: seinen"
    },
    {
      "q": "Eine Lehrerin ver\u00e4ndert ___ Unterricht, wenn digitale Werkzeuge echte Zusammenarbeit erm\u00f6glichen.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 3,
      "rule": "eine Lehrerin; Unterricht = maskulin Akkusativ: ihren"
    },
    {
      "q": "Das Bildungssystem zeigt ___ St\u00e4rke nicht durch Ger\u00e4te, sondern durch gerechte Zugangsm\u00f6glichkeiten.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 1,
      "rule": "das Bildungssystem; St\u00e4rke = feminin Akkusativ: seine"
    },
    {
      "q": "Viele Familien k\u00f6nnen ___ Kinder nur unterst\u00fctzen, wenn digitale Angebote verst\u00e4ndlich erkl\u00e4rt werden.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 3,
      "rule": "Familien = Plural; Kinder = Plural Akkusativ: ihre"
    },
    {
      "q": "Ein Lernprogramm beweist ___ Nutzen erst, wenn es selbstst\u00e4ndiges Denken f\u00f6rdert.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 3,
      "rule": "das Lernprogramm; Nutzen = maskulin Akkusativ: seinen"
    },
    {
      "q": "Die Schule sollte ___ Lehrkr\u00e4fte nicht mit technischen Problemen alleinlassen.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "die Schule; Lehrkr\u00e4fte = Plural Akkusativ: ihre"
    },
    {
      "q": "Ein digitaler Kurs erreicht ___ Ziel nur, wenn Lernende aktiv und kritisch arbeiten.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 0,
      "rule": "der Kurs; Ziel = Neutrum Akkusativ: sein"
    },
    {
      "q": "Die Gesellschaft muss ___ Erwartungen an digitale Bildung realistisch formulieren.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "die Gesellschaft; Erwartungen = Plural Akkusativ: ihre"
    },
    {
      "q": "Ein Lehrer kann ___ Rolle als Lernbegleiter ausbauen, wenn Technik Routineaufgaben erleichtert.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 1,
      "rule": "ein Lehrer; Rolle = feminin Akkusativ: seine"
    },
    {
      "q": "Eine digitale Plattform sollte ___ Inhalte transparent ordnen, damit Lernende Orientierung behalten.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "die Plattform; Inhalte = Plural Akkusativ: ihre"
    },
    {
      "q": "Der Unterricht kann ___ Qualit\u00e4t steigern, wenn digitale Aufgaben argumentatives Schreiben trainieren.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 1,
      "rule": "der Unterricht; Qualit\u00e4t = feminin Akkusativ: seine"
    },
    {
      "q": "Die Schule darf ___ soziale Aufgabe trotz Digitalisierung nicht aus dem Blick verlieren.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "die Schule; Aufgabe = feminin Akkusativ: ihre"
    }
  ],
  "poss2": [
    {
      "q": "Ein Haustier entfaltet ___ emotionale Wirkung besonders bei Menschen, die im Alltag wenig N\u00e4he erleben.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 1,
      "rule": "das Haustier; Wirkung = feminin Akkusativ: seine"
    },
    {
      "q": "Viele \u00e4ltere Menschen gewinnen durch ___ tierischen Begleiter mehr Sicherheit im Alltag.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 3,
      "rule": "Menschen = Plural; Begleiter = maskulin Akkusativ/Pluralbezug: ihren"
    },
    {
      "q": "Eine Familie st\u00e4rkt durch Tierpflege ___ Verantwortungsbewusstsein, weil Aufgaben regelm\u00e4\u00dfig erledigt werden m\u00fcssen.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 0,
      "rule": "Familie; Verantwortungsbewusstsein = Neutrum Akkusativ: ihr"
    },
    {
      "q": "Ein Kind entwickelt durch ___ Umgang mit einem Tier h\u00e4ufig mehr Geduld und Empathie.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 3,
      "rule": "das Kind; Umgang = maskulin Akkusativ: seinen"
    },
    {
      "q": "Der Hund f\u00f6rdert durch ___ t\u00e4glichen Spazierg\u00e4nge die Bewegung seiner Besitzer.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 1,
      "rule": "der Hund; Spazierg\u00e4nge = Plural Akkusativ: seine"
    },
    {
      "q": "Eine Katze kann durch ___ ruhige Anwesenheit Geborgenheit vermitteln.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "Katze; Anwesenheit = feminin Akkusativ: ihre"
    },
    {
      "q": "Ein Tierhalter strukturiert ___ Alltag oft st\u00e4rker, weil F\u00fctterung und Pflege feste Zeiten verlangen.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 3,
      "rule": "Tierhalter; Alltag = maskulin Akkusativ: seinen"
    },
    {
      "q": "Haustiere verbessern ___ Bedeutung im Familienleben, wenn Kinder Verantwortung praktisch erfahren.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "Haustiere = Plural; Bedeutung = feminin Akkusativ: ihre"
    },
    {
      "q": "Ein Hund kann ___ Besitzer leichter mit anderen Menschen ins Gespr\u00e4ch bringen.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 3,
      "rule": "Hund; Besitzer = maskulin Akkusativ: seinen"
    },
    {
      "q": "Eine Nachbarschaft st\u00e4rkt ___ Zusammenhalt, wenn Tierhalter sich gegenseitig unterst\u00fctzen.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 3,
      "rule": "Nachbarschaft; Zusammenhalt = maskulin Akkusativ: ihren"
    },
    {
      "q": "Ein Haustier zeigt ___ positiven Einfluss nicht nur emotional, sondern auch sozial.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 3,
      "rule": "Haustier; Einfluss = maskulin Akkusativ: seinen"
    },
    {
      "q": "Viele Kinder \u00fcbernehmen durch ___ Aufgaben bei der Tierpflege mehr Verantwortung.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "Kinder = Plural; Aufgaben = Plural Akkusativ: ihre"
    },
    {
      "q": "Der Kontakt zu einem Tier kann ___ beruhigende Wirkung nach einem stressigen Tag entfalten.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 1,
      "rule": "Kontakt; Wirkung = feminin Akkusativ: seine"
    },
    {
      "q": "Eine alleinlebende Person erlebt durch ___ Haustier mehr N\u00e4he und Alltagsstruktur.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 0,
      "rule": "Person; Haustier = Neutrum Akkusativ: ihr"
    },
    {
      "q": "Ein Haustier kann ___ Platz in der modernen Gesellschaft als sozialer Begleiter festigen.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 3,
      "rule": "Haustier; Platz = maskulin Akkusativ: seinen"
    },
    {
      "q": "Familien verbessern durch ___ gemeinsame Tierpflege die Zusammenarbeit im Alltag.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "Familien = Plural; Tierpflege = feminin Akkusativ: ihre"
    },
    {
      "q": "Der Spaziergang mit dem Hund erh\u00e4lt ___ sozialen Wert, weil Begegnungen leichter entstehen.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 3,
      "rule": "Spaziergang; Wert = maskulin Akkusativ: seinen"
    },
    {
      "q": "Eine \u00e4ltere Frau kann durch ___ Katze das Gef\u00fchl von Einsamkeit verringern.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "Frau; Katze = feminin Akkusativ: ihre"
    },
    {
      "q": "Ein Tier vermittelt durch ___ N\u00e4he oft ein Gef\u00fchl von Geborgenheit.",
      "options": [
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner"
      ],
      "answer": 1,
      "rule": "Tier; N\u00e4he = feminin Akkusativ: seine"
    },
    {
      "q": "Tierhalter erweitern durch ___ Erfahrungen h\u00e4ufig ihr Verantwortungsbewusstsein.",
      "options": [
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer"
      ],
      "answer": 1,
      "rule": "Tierhalter = Plural; Erfahrungen = Plural Akkusativ: ihre"
    }
  ],
  "dekl1": [
    {
      "q": "Die Wirkung ___ nachhaltigen Stadtplanung zeigt sich besonders in dicht bebauten Vierteln.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "Genitiv feminin: der Stadtplanung"
    },
    {
      "q": "Viele Kommunen brauchen ___ klare Strategie gegen zunehmende Hitzebelastung.",
      "options": [
        "ein",
        "eine",
        "einem",
        "einen",
        "einer"
      ],
      "answer": 1,
      "rule": "Akkusativ feminin: eine Strategie"
    },
    {
      "q": "Mit ___ konsequenten Ausbau \u00f6ffentlicher Verkehrsmittel sinkt die Abh\u00e4ngigkeit vom Auto.",
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
      "q": "Ohne ___ verbindliche Regelung bleibt nachhaltige Stadtentwicklung oft ein leeres Versprechen.",
      "options": [
        "ein",
        "eine",
        "einem",
        "einen",
        "einer"
      ],
      "answer": 1,
      "rule": "ohne + Akkusativ feminin: eine Regelung"
    },
    {
      "q": "Der Schutz ___ urbanen Gr\u00fcnfl\u00e4chen ist ein zentraler Bestandteil moderner Umweltpolitik.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "Genitiv Plural: der Gr\u00fcnfl\u00e4chen"
    },
    {
      "q": "Eine Stadt mit ___ gut ausgebauten Radwegenetz f\u00f6rdert klimafreundliche Mobilit\u00e4t.",
      "options": [
        "ein",
        "eine",
        "einem",
        "einen",
        "einer"
      ],
      "answer": 2,
      "rule": "mit + Dativ Neutrum: einem Radwegenetz"
    },
    {
      "q": "Durch ___ st\u00e4rkere Begr\u00fcnung k\u00f6nnen Innenst\u00e4dte im Sommer sp\u00fcrbar entlastet werden.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 1,
      "rule": "durch + Akkusativ feminin: die Begr\u00fcnung"
    },
    {
      "q": "Die Einf\u00fchrung ___ neuen Energiekonzepts erfordert politische Ausdauer.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 4,
      "rule": "Genitiv Neutrum: des Konzepts"
    },
    {
      "q": "Viele B\u00fcrger w\u00fcnschen sich ___ sauberere Luft und weniger L\u00e4rm.",
      "options": [
        "ein",
        "eine",
        "einem",
        "einen",
        "einer"
      ],
      "answer": 1,
      "rule": "Akkusativ feminin: eine Luft"
    },
    {
      "q": "In ___ lebenswerten Stadt m\u00fcssen \u00f6kologische und soziale Ziele verbunden werden.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "in + Dativ feminin: der Stadt"
    },
    {
      "q": "Die F\u00f6rderung ___ regionalen Energieversorgung kann Transportwege verk\u00fcrzen.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "Genitiv feminin: der Energieversorgung"
    },
    {
      "q": "Trotz ___ hohen Kosten lohnt sich die Sanierung \u00f6ffentlicher Geb\u00e4ude langfristig.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "trotz + Genitiv Plural: der Kosten"
    },
    {
      "q": "Ein Ausbau ___ \u00f6ffentlichen Nahverkehrs macht nachhaltige Mobilit\u00e4t alltagstauglich.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 4,
      "rule": "Genitiv maskulin: des Nahverkehrs"
    },
    {
      "q": "Viele St\u00e4dte stehen vor ___ schwierigen Aufgabe, Wachstum und Klimaschutz zu verbinden.",
      "options": [
        "ein",
        "eine",
        "einem",
        "einen",
        "einer"
      ],
      "answer": 4,
      "rule": "vor + Dativ feminin: einer Aufgabe"
    },
    {
      "q": "Die Nutzung ___ erneuerbarer Energien sollte systematisch erleichtert werden.",
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
      "q": "Mit ___ sozialen Ausgleich kann Klimapolitik mehr Akzeptanz gewinnen.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 2,
      "rule": "mit + Dativ maskulin: dem Ausgleich"
    },
    {
      "q": "Eine Kommune braucht ___ langfristigen Plan, statt nur einzelne Projekte zu f\u00f6rdern.",
      "options": [
        "ein",
        "eine",
        "einem",
        "einen",
        "einer"
      ],
      "answer": 3,
      "rule": "Akkusativ maskulin: einen Plan"
    },
    {
      "q": "Der Ausbau ___ gr\u00fcnen Infrastruktur verbessert die Lebensqualit\u00e4t in Wohnvierteln.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "Genitiv feminin: der Infrastruktur"
    },
    {
      "q": "Durch ___ bewussteren Umgang mit Fl\u00e4chen kann weiterer Bodenverbrauch begrenzt werden.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 3,
      "rule": "durch + Akkusativ maskulin: den Umgang"
    },
    {
      "q": "Die Debatte \u00fcber ___ nachhaltige Stadt zeigt, dass Umweltpolitik konkret im Alltag beginnt.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 1,
      "rule": "\u00fcber + Akkusativ feminin: die Stadt"
    }
  ],
  "dekl2": [
    {
      "q": "Angesichts ___ steigenden Besucherzahlen geraten viele Altst\u00e4dte unter Druck.",
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
      "q": "Die Interessen ___ lokalen Bev\u00f6lkerung d\u00fcrfen im Tourismuskonzept nicht \u00fcbergangen werden.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "Genitiv feminin: der Bev\u00f6lkerung"
    },
    {
      "q": "Durch ___ unkontrollierte Vermietung von Ferienwohnungen steigen die Mieten in beliebten Vierteln.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 1,
      "rule": "durch + Akkusativ feminin: die Vermietung"
    },
    {
      "q": "Viele St\u00e4dte suchen nach ___ ausgewogenen Verh\u00e4ltnis zwischen G\u00e4sten und Einheimischen.",
      "options": [
        "ein",
        "eine",
        "einem",
        "einen",
        "einer"
      ],
      "answer": 2,
      "rule": "nach + Dativ Neutrum: einem Verh\u00e4ltnis"
    },
    {
      "q": "Trotz ___ wirtschaftlichen Vorteile entstehen erhebliche Belastungen f\u00fcr die Infrastruktur.",
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
      "q": "Die Einf\u00fchrung ___ begrenzten Besucherzahl kann empfindliche Orte sch\u00fctzen.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "Genitiv feminin: der Besucherzahl"
    },
    {
      "q": "In ___ \u00fcberf\u00fcllten Innenstadt verlieren Bewohner oft das Gef\u00fchl von Normalit\u00e4t.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "in + Dativ feminin: der Innenstadt"
    },
    {
      "q": "Ein Konzept mit ___ klaren Regeln kann den Tourismus besser steuern.",
      "options": [
        "ein",
        "eine",
        "einem",
        "einen",
        "einer"
      ],
      "answer": 2,
      "rule": "mit + Dativ Plural/Regeln: klaren Regeln; hier einem Konzept"
    },
    {
      "q": "Die Abh\u00e4ngigkeit ___ touristischen Einnahmen macht manche St\u00e4dte krisenanf\u00e4llig.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "Genitiv Plural: der Einnahmen"
    },
    {
      "q": "Ohne ___ faire Verteilung der Gewinne bleibt Tourismus sozial problematisch.",
      "options": [
        "ein",
        "eine",
        "einem",
        "einen",
        "einer"
      ],
      "answer": 1,
      "rule": "ohne + Akkusativ feminin: eine Verteilung"
    },
    {
      "q": "Der Schutz ___ kulturellen Erbes sollte Vorrang vor kurzfristigem Profit haben.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 4,
      "rule": "Genitiv Neutrum: des Erbes"
    },
    {
      "q": "Mit ___ besseren Lenkung der Besucherstr\u00f6me k\u00f6nnen Engp\u00e4sse vermieden werden.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "mit + Dativ feminin: der Lenkung"
    },
    {
      "q": "Eine Stadt steht vor ___ komplexen Herausforderung, attraktiv und bewohnbar zu bleiben.",
      "options": [
        "ein",
        "eine",
        "einem",
        "einen",
        "einer"
      ],
      "answer": 4,
      "rule": "vor + Dativ feminin: einer Herausforderung"
    },
    {
      "q": "Die Begrenzung ___ privaten Kurzzeitvermietung kann Wohnraum sch\u00fctzen.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "Genitiv feminin: der Kurzzeitvermietung"
    },
    {
      "q": "F\u00fcr ___ nachhaltigen Tourismus braucht man klare politische Rahmenbedingungen.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 3,
      "rule": "f\u00fcr + Akkusativ maskulin: den Tourismus"
    },
    {
      "q": "Die Belastung ___ historischen Zentrums wird in der Hochsaison besonders sichtbar.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 4,
      "rule": "Genitiv Neutrum: des Zentrums"
    },
    {
      "q": "Bei ___ starken Konzentration auf wenige Sehensw\u00fcrdigkeiten entstehen massive Besucherstr\u00f6me.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "bei + Dativ feminin: der Konzentration"
    },
    {
      "q": "Viele Einwohner fordern ___ wirksamere Kontrolle touristischer Angebote.",
      "options": [
        "ein",
        "eine",
        "einem",
        "einen",
        "einer"
      ],
      "answer": 1,
      "rule": "Akkusativ feminin: eine Kontrolle"
    },
    {
      "q": "Die Erhaltung ___ st\u00e4dtischen Lebensqualit\u00e4t muss Teil jeder Tourismusstrategie sein.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 0,
      "rule": "Genitiv feminin: der Lebensqualit\u00e4t"
    },
    {
      "q": "Durch ___ langfristige Planung kann eine Stadt Massentourismus sozial vertr\u00e4glicher gestalten.",
      "options": [
        "der",
        "die",
        "dem",
        "den",
        "des"
      ],
      "answer": 1,
      "rule": "durch + Akkusativ feminin: die Planung"
    }
  ],
  "pron": [
    {
      "q": "K\u00fcnstliche Intelligenz kann Lernende unterst\u00fctzen, wenn ___ gezielt eingesetzt wird.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "die Intelligenz = sie"
    },
    {
      "q": "Ein KI-System liefert Vorschl\u00e4ge, doch ___ ersetzt keine p\u00e4dagogische Entscheidung.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 2,
      "rule": "das System = es"
    },
    {
      "q": "Lehrkr\u00e4fte nutzen digitale Assistenten, wenn ___ den Unterricht sinnvoll erg\u00e4nzen.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "Assistenten = sie"
    },
    {
      "q": "Ein Algorithmus wirkt \u00fcberzeugend, obwohl man ___ kritisch pr\u00fcfen muss.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 3,
      "rule": "Algorithmus maskulin Akkusativ = ihn"
    },
    {
      "q": "Viele Sch\u00fcler erhalten R\u00fcckmeldungen, aber ___ verstehen deren Grenzen nicht immer.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "Sch\u00fcler Plural = sie"
    },
    {
      "q": "Das Programm kann Texte analysieren, doch ___ bewertet nicht automatisch die Argumentationsqualit\u00e4t.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 2,
      "rule": "Programm = es"
    },
    {
      "q": "Eine Lehrerin entscheidet, ob ___ KI-Aufgaben in den Unterricht integriert.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "Lehrerin = sie"
    },
    {
      "q": "Die Daten sind sensibel, deshalb muss man ___ besonders sch\u00fctzen.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "Daten Plural = sie"
    },
    {
      "q": "Ein Sch\u00fcler kann KI nutzen, wenn ___ die Ergebnisse nicht ungepr\u00fcft \u00fcbernimmt.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 0,
      "rule": "Sch\u00fcler = er"
    },
    {
      "q": "Die Schule tr\u00e4gt Verantwortung, weil ___ den Rahmen f\u00fcr den Einsatz festlegt.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "Schule = sie"
    },
    {
      "q": "Ein Argument wird schw\u00e4cher, wenn ___ nur von einer Maschine formuliert wurde.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 2,
      "rule": "Argument = es"
    },
    {
      "q": "Lernplattformen sammeln Informationen, weshalb man ___ transparent erkl\u00e4ren muss.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "Informationen = sie"
    },
    {
      "q": "Der Unterricht ver\u00e4ndert sich, wenn ___ st\u00e4rker auf individuelle Lernwege reagiert.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 0,
      "rule": "Unterricht = er"
    },
    {
      "q": "KI kann Fehler zeigen, doch ___ kann den Lernprozess nicht vollst\u00e4ndig \u00fcbernehmen.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "KI/Intelligenz = sie"
    },
    {
      "q": "Viele Eltern fragen, ob ___ den Datenschutz der Kinder ausreichend ber\u00fccksichtigt.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "die Schule/die Anwendung im Kontext feminin = sie"
    },
    {
      "q": "Ein Chatbot hilft beim \u00dcben, wenn man ___ als Werkzeug und nicht als Ersatz nutzt.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 3,
      "rule": "Chatbot maskulin Akkusativ = ihn"
    },
    {
      "q": "Die Aufgaben wirken modern, aber ___ m\u00fcssen didaktisch sinnvoll eingebettet werden.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "Aufgaben Plural = sie"
    },
    {
      "q": "Ein KI-Feedback ist n\u00fctzlich, wenn ___ verst\u00e4ndlich und nachvollziehbar bleibt.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 2,
      "rule": "Feedback = es"
    },
    {
      "q": "Lehrkr\u00e4fte behalten ihre Rolle, weil ___ Lernprozesse menschlich begleiten.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "Lehrkr\u00e4fte Plural = sie"
    },
    {
      "q": "Technik \u00fcberzeugt nur dann, wenn ___ Bildung gerechter und nicht oberfl\u00e4chlicher macht.",
      "options": [
        "er",
        "sie",
        "es",
        "ihn",
        "ihnen"
      ],
      "answer": 1,
      "rule": "Technik = sie"
    }
  ],
  "indef1": [
    {
      "q": "___ erlebt im Homeoffice mehr Konzentration, wenn zu Hause ein ruhiger Arbeitsplatz vorhanden ist.",
      "options": [
        "Jemand",
        "Niemand",
        "Etwas",
        "Mehrere",
        "Nichts"
      ],
      "answer": 0,
      "rule": "Jemand als Person"
    },
    {
      "q": "___ sollte die sozialen Folgen flexibler Arbeit untersch\u00e4tzen.",
      "options": [
        "Jemand",
        "Niemand",
        "Etwas",
        "Mehrere",
        "Manche"
      ],
      "answer": 1,
      "rule": "Niemand = keine Person"
    },
    {
      "q": "___ Besch\u00e4ftigte profitieren von Homeoffice, w\u00e4hrend andere klare Trennung zwischen Arbeit und Privatleben verlieren.",
      "options": [
        "Jemand",
        "Niemand",
        "Einige",
        "Nichts",
        "Einer"
      ],
      "answer": 2,
      "rule": "Einige Besch\u00e4ftigte"
    },
    {
      "q": "Wenn ___ regelm\u00e4\u00dfig erreichbar bleiben muss, kann Flexibilit\u00e4t schnell zur Belastung werden.",
      "options": [
        "jemand",
        "nichts",
        "mehrere",
        "manche",
        "alles"
      ],
      "answer": 0,
      "rule": "jemand als Person"
    },
    {
      "q": "___ sehen im Homeoffice vor allem eine Chance f\u00fcr bessere Vereinbarkeit.",
      "options": [
        "Manche",
        "Nichts",
        "Jemand",
        "Niemand",
        "Etwas"
      ],
      "answer": 0,
      "rule": "Manche = einige Personen"
    },
    {
      "q": "F\u00fcr ___ ist der Wegfall des Arbeitswegs eine sp\u00fcrbare Entlastung.",
      "options": [
        "jemand",
        "niemand",
        "manche",
        "etwas",
        "nichts"
      ],
      "answer": 2,
      "rule": "f\u00fcr manche"
    },
    {
      "q": "___ kann produktiv arbeiten, wenn digitale Kommunikation klar organisiert ist.",
      "options": [
        "Man",
        "Nichts",
        "Niemanden",
        "Etwas",
        "Mehreren"
      ],
      "answer": 0,
      "rule": "man als unpers\u00f6nliches Subjekt"
    },
    {
      "q": "___ darf erwarten, dass Homeoffice ohne klare Regeln automatisch gerecht funktioniert.",
      "options": [
        "Jemand",
        "Niemand",
        "Mehrere",
        "Etwas",
        "Manche"
      ],
      "answer": 1,
      "rule": "Niemand darf erwarten"
    },
    {
      "q": "___ Mitarbeitende brauchen regelm\u00e4\u00dfigen Austausch, damit sie nicht isoliert werden.",
      "options": [
        "Einige",
        "Jemand",
        "Niemand",
        "Nichts",
        "Etwas"
      ],
      "answer": 0,
      "rule": "Einige Mitarbeitende"
    },
    {
      "q": "Wenn ___ Kinder betreut, kann flexible Arbeit den Alltag erleichtern.",
      "options": [
        "jemand",
        "nichts",
        "mehrere",
        "allem",
        "keines"
      ],
      "answer": 0,
      "rule": "jemand betreut"
    },
    {
      "q": "___ f\u00fchlt sich im Homeoffice entlastet, andere dagegen vermissen direkte Gespr\u00e4che.",
      "options": [
        "Mancher",
        "Nichts",
        "Niemanden",
        "Mehreren",
        "Etwas"
      ],
      "answer": 0,
      "rule": "Mancher = manche Person"
    },
    {
      "q": "___ der Besch\u00e4ftigten m\u00f6chte vollst\u00e4ndig auf Pr\u00e4senzarbeit verzichten.",
      "options": [
        "Nicht jeder",
        "Nichts",
        "Etwas",
        "Niemanden",
        "Mehrere"
      ],
      "answer": 0,
      "rule": "Nicht jeder der Besch\u00e4ftigten"
    },
    {
      "q": "___ sollte ausgeschlossen werden, nur weil er zu Hause arbeitet.",
      "options": [
        "Niemand",
        "Nichts",
        "Etwas",
        "Mehrere",
        "Alle"
      ],
      "answer": 0,
      "rule": "Niemand als Person"
    },
    {
      "q": "___ brauchen klare Grenzen, damit Arbeit nicht den gesamten Tag bestimmt.",
      "options": [
        "Viele",
        "Nichts",
        "Jemand",
        "Etwas",
        "Niemand"
      ],
      "answer": 0,
      "rule": "Viele Personen"
    },
    {
      "q": "Wenn ___ selten ins B\u00fcro kommt, k\u00f6nnen informelle Informationen verloren gehen.",
      "options": [
        "jemand",
        "nichts",
        "mehrere",
        "allem",
        "keiner"
      ],
      "answer": 0,
      "rule": "jemand als Subjekt"
    },
    {
      "q": "___ kann Homeoffice nutzen, um konzentrierte Aufgaben ohne Unterbrechung zu erledigen.",
      "options": [
        "Man",
        "Nichts",
        "Niemanden",
        "Etwas",
        "Mehreren"
      ],
      "answer": 0,
      "rule": "man"
    },
    {
      "q": "F\u00fcr ___ Besch\u00e4ftigte ist Pr\u00e4senz wichtig, weil Teamgef\u00fchl vor Ort entsteht.",
      "options": [
        "manche",
        "manchem",
        "manchen",
        "mancher",
        "manches"
      ],
      "answer": 0,
      "rule": "f\u00fcr + Akkusativ Plural: manche Besch\u00e4ftigte"
    },
    {
      "q": "___ darf aus dem Blick geraten, dass Homeoffice auch F\u00fchrungskultur ver\u00e4ndert.",
      "options": [
        "Niemandem",
        "Niemand",
        "Nichts",
        "Manche",
        "Jemanden"
      ],
      "answer": 2,
      "rule": "Nichts als Sachverhalt"
    },
    {
      "q": "___ im Team muss wissen, wann digitale Besprechungen wirklich notwendig sind.",
      "options": [
        "Jeder",
        "Nichts",
        "Etwas",
        "Niemanden",
        "Mehreren"
      ],
      "answer": 0,
      "rule": "Jeder im Team"
    },
    {
      "q": "___ profitieren nur dann, wenn technische Ausstattung und Vertrauen zusammenkommen.",
      "options": [
        "Viele",
        "Jemand",
        "Nichts",
        "Niemand",
        "Etwas"
      ],
      "answer": 0,
      "rule": "Viele Personen"
    }
  ],
  "indef2": [
    {
      "q": "Nicht ___, was billig angeboten wird, ist gesellschaftlich verantwortbar.",
      "options": [
        "alles",
        "alle",
        "jeder",
        "jemand",
        "mehrere"
      ],
      "answer": 0,
      "rule": "alles f\u00fcr Sachverhalte"
    },
    {
      "q": "___ der genannten Vorteile rechtfertigt allein die \u00f6kologischen Kosten von Fast Fashion.",
      "options": [
        "Keine",
        "Keiner",
        "Keines",
        "Keinem",
        "Keinen"
      ],
      "answer": 2,
      "rule": "keines der Vorteile/Argumente"
    },
    {
      "q": "F\u00fcr ___ Kleidungsst\u00fccke werden Ressourcen verbraucht, die kaum im Preis sichtbar sind.",
      "options": [
        "manche",
        "manchem",
        "manchen",
        "mancher",
        "manches"
      ],
      "answer": 0,
      "rule": "f\u00fcr manche Kleidungsst\u00fccke"
    },
    {
      "q": "Es gibt kaum ___, das an Fast Fashion ohne Nebenwirkungen positiv bewertet werden kann.",
      "options": [
        "etwas",
        "jemand",
        "alle",
        "manchen",
        "keinen"
      ],
      "answer": 0,
      "rule": "etwas als Sache"
    },
    {
      "q": "___ von dem, was schnell produziert wird, bleibt lange im Kleiderschrank.",
      "options": [
        "Vieles",
        "Jemand",
        "Niemand",
        "Mehrere",
        "Alle"
      ],
      "answer": 0,
      "rule": "Vieles als Sachverhalt"
    },
    {
      "q": "___ sollte gekauft werden, nur weil ein Trend kurzfristig Aufmerksamkeit erzeugt.",
      "options": [
        "Nichts",
        "Jemand",
        "Mehrere",
        "Alle",
        "Manche"
      ],
      "answer": 0,
      "rule": "Nichts als Sache"
    },
    {
      "q": "___ der billigen Angebote verschleiert die Arbeitsbedingungen in der Produktion.",
      "options": [
        "Manches",
        "Jemand",
        "Niemand",
        "Mehrere",
        "Alle"
      ],
      "answer": 0,
      "rule": "Manches der Angebote"
    },
    {
      "q": "Wenn ___ st\u00e4ndig neu erscheint, verlieren Verbraucher leicht den \u00dcberblick.",
      "options": [
        "etwas",
        "jemand",
        "alle",
        "keinen",
        "mancher"
      ],
      "answer": 0,
      "rule": "etwas erscheint"
    },
    {
      "q": "___ der Kleidungsst\u00fccke wird nach kurzer Zeit kaum noch getragen.",
      "options": [
        "Manches",
        "Jemand",
        "Niemand",
        "Mehrere",
        "Alle"
      ],
      "answer": 0,
      "rule": "Manches der Kleidungsst\u00fccke"
    },
    {
      "q": "Nicht ___ muss sofort ersetzt werden, nur weil Werbung einen neuen Stil pr\u00e4sentiert.",
      "options": [
        "alles",
        "alle",
        "jeder",
        "jemand",
        "mehrere"
      ],
      "answer": 0,
      "rule": "alles"
    },
    {
      "q": "___ kann nachhaltiger werden, wenn Reparatur und Wiederverwendung attraktiver werden.",
      "options": [
        "Vieles",
        "Jemand",
        "Niemand",
        "Mehrere",
        "Alle"
      ],
      "answer": 0,
      "rule": "Vieles als System/Sachverhalt"
    },
    {
      "q": "___ der Argumente gegen Fast Fashion betrifft nicht nur Umwelt, sondern auch soziale Gerechtigkeit.",
      "options": [
        "Manches",
        "Jemand",
        "Niemand",
        "Mehrere",
        "Alle"
      ],
      "answer": 0,
      "rule": "Manches der Argumente"
    },
    {
      "q": "F\u00fcr ___ Konsumentscheidungen fehlen vielen Menschen transparente Informationen.",
      "options": [
        "manche",
        "manchem",
        "manchen",
        "mancher",
        "manches"
      ],
      "answer": 0,
      "rule": "f\u00fcr manche Entscheidungen"
    },
    {
      "q": "___ bleibt problematisch, wenn niedrige Preise nur durch schlechten Arbeitsschutz m\u00f6glich sind.",
      "options": [
        "Etwas",
        "Jemand",
        "Mehrere",
        "Alle",
        "Niemand"
      ],
      "answer": 0,
      "rule": "Etwas bleibt problematisch"
    },
    {
      "q": "___ davon l\u00e4sst sich durch bewusstere Kaufentscheidungen zumindest verringern.",
      "options": [
        "Einiges",
        "Jemand",
        "Niemand",
        "Mehrere",
        "Alle"
      ],
      "answer": 0,
      "rule": "Einiges davon"
    },
    {
      "q": "___ der neuen Kollektionen erzeugt k\u00fcnstlichen Kaufdruck.",
      "options": [
        "Manche",
        "Jemand",
        "Niemand",
        "Etwas",
        "Alles"
      ],
      "answer": 0,
      "rule": "Manche der Kollektionen"
    },
    {
      "q": "Nicht ___, das modisch wirkt, verbessert tats\u00e4chlich die Lebensqualit\u00e4t.",
      "options": [
        "alles",
        "alle",
        "jeder",
        "jemand",
        "mehrere"
      ],
      "answer": 0,
      "rule": "alles"
    },
    {
      "q": "___ kann gegen Wegwerfmentalit\u00e4t helfen, wenn Qualit\u00e4t st\u00e4rker gesch\u00e4tzt wird.",
      "options": [
        "Etwas",
        "Jemand",
        "Mehrere",
        "Niemand",
        "Alle"
      ],
      "answer": 0,
      "rule": "Etwas kann helfen"
    },
    {
      "q": "___ der \u00f6kologischen Sch\u00e4den wird erst sichtbar, wenn Produktion und Entsorgung zusammen betrachtet werden.",
      "options": [
        "Manches",
        "Jemand",
        "Niemand",
        "Mehrere",
        "Alle"
      ],
      "answer": 0,
      "rule": "Manches der Sch\u00e4den"
    },
    {
      "q": "___ spricht daf\u00fcr, weniger Kleidung zu kaufen und vorhandene St\u00fccke l\u00e4nger zu nutzen.",
      "options": [
        "Vieles",
        "Jemand",
        "Niemand",
        "Mehrere",
        "Alle"
      ],
      "answer": 0,
      "rule": "Vieles spricht daf\u00fcr"
    }
  ]
};
function fixedPattern(id){return fixed[id].map(item=>()=>q(item.q,item.options,item.answer,item.rule));}
const patterns={
poss1:fixedPattern("poss1"),
poss2:fixedPattern("poss2"),
dekl1:fixedPattern("dekl1"),
dekl2:fixedPattern("dekl2"),
pron:fixedPattern("pron"),
indef1:fixedPattern("indef1"),
indef2:fixedPattern("indef2"),
neg1:[c=>q(`Keine verantwortungsvolle Politik darf die Risiken von ${c} ignorieren.`,["Kein","Keine","Keinem","Keinen","Keiner"],1,"keine + feminine Subjektgruppe"),c=>q("Ohne ___ klare Begründung wirkt ein Argument oberflächlich.",["kein","keine","keinem","keinen","keiner"],1,"ohne + Akkusativ feminin"),c=>q(`Mit keiner einfachen Lösung ist bei ${c} zu rechnen.`,["kein","keine","keinem","keinen","keiner"],4,"mit + Dativ feminin"),c=>q("Keiner der genannten Aspekte sollte isoliert betrachtet werden.",["Kein","Keine","Keines","Keinem","Keiner"],4,"keiner der Aspekte")],
neg2:[c=>q("Weder wirtschaftliche Vorteile ___ technische Bequemlichkeit reichen als alleinige Begründung aus.",["oder","noch","aber","sondern","denn"],1,"weder ... noch"),c=>q(`${c} ist nicht nur eine private Frage, ___ auch ein gesellschaftliches Thema.`,["aber","oder","sondern","denn","noch"],2,"nicht nur, sondern auch"),c=>q("Je komplexer ein Thema ist, desto ___ sollte man pauschal urteilen.",["mehr","weniger","kaum","nie","keiner"],1,"je ... desto weniger"),c=>q("Ein Verbot ist ___ immer die überzeugendste Lösung.",["nicht","kein","keine","keiner","keinen"],0,"Satznegation mit nicht")],
satz:[c=>q("Welche Satzstellung ist korrekt?",[`In Bezug auf ${c} sollte man die langfristigen Folgen sorgfältig abwägen.`,`In Bezug auf ${c} man sollte die langfristigen Folgen sorgfältig abwägen.`,`Man sollte in Bezug auf ${c} sorgfältig abwägen die langfristigen Folgen.`,`Sorgfältig man sollte in Bezug auf ${c} die langfristigen Folgen abwägen.`,`Die langfristigen Folgen sorgfältig sollte man in Bezug auf ${c} abwägen.`],0,"Vorfeld + finites Verb + Mittelfeld + Verbklammer"),c=>q("Welche Variante ist C1/C2-gerecht?",[`Obwohl ${c} Vorteile bietet, dürfen mögliche Risiken nicht ausgeblendet werden.`,`Obwohl bietet ${c} Vorteile, mögliche Risiken dürfen nicht ausgeblendet werden.`,`Obwohl ${c} bietet Vorteile, dürfen nicht mögliche Risiken ausgeblendet werden.`,`Obwohl Vorteile bietet ${c}, dürfen mögliche Risiken nicht ausgeblendet werden.`,`Obwohl ${c} Vorteile bietet, nicht dürfen mögliche Risiken ausgeblendet werden.`],0,"Nebensatz mit Verb am Ende"),c=>q("Welche Satzstellung ist korrekt?",["Daher muss die Politik klare Rahmenbedingungen schaffen.","Daher die Politik muss klare Rahmenbedingungen schaffen.","Daher klare Rahmenbedingungen muss die Politik schaffen.","Die Politik klare Rahmenbedingungen daher schaffen muss.","Muss daher die Politik klare Rahmenbedingungen schaffen."],0,"Konsekutivadverb im Vorfeld"),c=>q("Welche Formulierung hat die richtige Verbklammer?",[`Viele Betroffene könnten durch ${c} langfristig entlastet werden.`,`Viele Betroffene könnten durch ${c} langfristig werden entlastet.`,`Viele Betroffene durch ${c} könnten langfristig entlastet werden.`,`Könnten viele Betroffene langfristig durch ${c} entlastet werden.`,`Langfristig entlastet durch ${c} könnten viele Betroffene werden.`],0,"Modalverb + Infinitiv/Partizip am Ende")],
rede1:[c=>q("Welche Einleitung passt am besten?",[`In der aktuellen Debatte über ${c} stellt sich die Frage, welche Chancen und Risiken damit verbunden sind.`,`Ich finde ${c} gut und schreibe jetzt darüber.`,`Alle reden über ${c}, deshalb ist es wichtig.`,`Das Thema ${c} ist irgendwie modern.`,`Man kann über ${c} viel sagen.`],0,"präzise Einleitung"),c=>q("Welche Begründung ist am stärksten?",["Dies ist darauf zurückzuführen, dass gesellschaftliche Veränderungen selten nur eine Ursache haben.","Das ist so, weil es eben so ist.","Viele finden das gut.","Es gibt Gründe und Nachteile.","Man sagt das oft."],0,"kausale Begründung"),c=>q("Welche Redemittel-Kombination ist korrekt?",[`Einerseits eröffnet ${c} neue Möglichkeiten, andererseits entstehen dadurch neue Abhängigkeiten.`,`Einerseits ${c} eröffnet, andererseits entstehen dadurch.`,`Entweder eröffnet ${c}, andererseits entstehen Abhängigkeiten.`,`Nicht nur eröffnet ${c}, sondern entstehen Abhängigkeiten.`,`Sowohl eröffnet ${c}, aber auch entstehen Abhängigkeiten.`],0,"Abwägung"),c=>q("Welche Kontextualisierung ist C1/C2-gerecht?",[`Vor dem Hintergrund gesellschaftlicher Veränderungen gewinnt ${c} zunehmend an Bedeutung.`,`Im Hintergrund ist ${c} sehr wichtig.`,`Wegen Gesellschaft ist ${c} größer.`,`${c} macht eine Bedeutung.`,"Das Thema hat Hintergrund."],0,"Kontextualisierung")],
rede2:[c=>q("Welche Folgeformulierung passt?",["Dies kann dazu führen, dass bestehende Ungleichheiten verstärkt werden.","Dies kann machen, dass es schlecht wird.","Dies führt, dass Ungleichheiten.","Dadurch ist es Folge.","Es kommt eine Folge heraus."],0,"Folgen ausdrücken"),c=>q("Welche kritische Bewertung ist präzise?",["Problematisch ist weniger die Idee selbst als ihre unzureichend regulierte Umsetzung.","Das ist schlecht, weil es schlecht ist.","Die Idee ist immer problematisch.","Regulierung ist nicht wichtig.","Alles daran ist falsch."],0,"differenzierte Kritik"),c=>q("Welche Schlussformel ist angemessen?",[`Zusammenfassend lässt sich festhalten, dass ${c} nur unter klaren Bedingungen sinnvoll genutzt werden kann.`,`Am Ende ist ${c} gut.`,"Ich bin fertig mit dem Thema.","Alles zusammen ist wichtig.","Das war meine Meinung."],0,"Schlussfolgerung"),c=>q("Welche Abwägung ist korrekt?",["Während kurzfristige Vorteile sichtbar sind, müssen langfristige Nebenwirkungen sorgfältig geprüft werden.","Während Vorteile sind sichtbar, müssen geprüft Nebenwirkungen.","Kurzfristig Vorteile, langfristig Nebenwirkungen.","Obwohl Vorteile sichtbar, Nebenwirkungen müssen.","Vorteile sind, aber prüfen."],0,"konzessive Abwägung")]
};
const testDefs=[
["poss1","Possessivartikel I – Digitale Bildung","Digitale Bildung als zusammenhängender Erörterungstext · thematische C1/C2-Erörterungssätze."],
["poss2","Possessivartikel II – Haustiere Vorteile","Haustiere in der modernen Gesellschaft · Vorteile · thematische C1/C2-Erörterungssätze."],
["dekl1","Deklination I – Umweltschutz","Umweltschutz und nachhaltige Stadtentwicklung · Artikel, Adjektive und Kasus."],
["dekl2","Deklination II – Massentourismus","Massentourismus in beliebten Städten · Präpositionen, Genitiv und attributive Gruppen."],
["pron","Nur Pronomen – Künstliche Intelligenz","Künstliche Intelligenz im Bildungsbereich · Pronomenbezug und Kohärenz."],
["indef1","Indefinitpronomen I – Homeoffice","Homeoffice und moderne Arbeitswelt · Personenbezüge in Erörterungssätzen."],
["indef2","Indefinitpronomen II – Fast Fashion","Fast Fashion und Konsumverhalten · Dinge, Mengen und abstrakte Bezüge."],
["neg1","Negationswörter I – Deklination in Erörterungen","kein-Formen und negative Determinanten."],
["neg2","Negationswörter II – Gegensätze und Erörterungssprache","nicht, weder noch und kontrastive Strukturen."],
["satz","Satzstellung I – TeKaMoLo, Objektstellung und Verbklammer","Satzstellung, Nebensätze und Verbklammer."],
["rede1","Redemittel I – Einleitung, Kontextualisierung und Begründung","Einleitungen, Begründungen und Abwägungen."],
["rede2","Redemittel II – Folgen, Abwägung, Kritik und Schluss","Folge, Kritik, Abwägung und Schluss."]
];
const tests=testDefs.map(([id,title,description])=>({id,title,description,questions:contexts.map((c,i)=>patterns[id][i%patterns[id].length](c,i))}));
window.erorterungTests = tests;
window.ERORTERUNG_TESTS = tests;
