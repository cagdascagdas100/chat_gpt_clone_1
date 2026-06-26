const letters=["A","B","C","D","E"];
function q(text,options,answer,rule){return{q:text,options,answer,rule};}
const tests=[
  {
    "id": "poss1",
    "title": "Possessivartikel I - Digitale Bildung",
    "description": "Possessivartikel in einem zusammenh\u00e4ngenden Er\u00f6rterungsthema: digitale Bildung.",
    "questions": [
      {
        "q": "Viele Schulen k\u00f6nnen ___ digitale Infrastruktur nur verbessern, wenn langfristig investiert wird.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural: Schulen -> ihre Infrastruktur"
      },
      {
        "q": "Der Staat sollte ___ bildungspolitische Verantwortung nicht auf einzelne Lehrkr\u00e4fte abw\u00e4lzen.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "der Staat -> seine Verantwortung"
      },
      {
        "q": "Ein modernes Bildungssystem zeigt ___ St\u00e4rke daran, ob alle Lernenden Zugang zu digitalen Ger\u00e4ten erhalten.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "das System -> seine St\u00e4rke"
      },
      {
        "q": "Lehrkr\u00e4fte m\u00fcssen ___ Unterricht so gestalten, dass digitale Medien einen erkennbaren Lernzweck erf\u00fcllen.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "Plural: Lehrkr\u00e4fte -> ihren Unterricht"
      },
      {
        "q": "Eine Schule darf ___ sozialen Auftrag nicht vergessen, wenn sie Tablets und Lernplattformen einf\u00fchrt.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "die Schule -> ihren Auftrag"
      },
      {
        "q": "Digitale Bildung entfaltet ___ Nutzen vor allem dann, wenn sie kritisch begleitet wird.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "die digitale Bildung -> ihren Nutzen"
      },
      {
        "q": "Das Lernen kann ___ Qualit\u00e4t verbessern, wenn digitale Werkzeuge verst\u00e4ndlich und barrierearm eingesetzt werden.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "das Lernen -> seine Qualit\u00e4t"
      },
      {
        "q": "Jugendliche m\u00fcssen ___ pers\u00f6nlichen Daten sch\u00fctzen, weil digitale Bildung auch Medienkompetenz verlangt.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural: Jugendliche -> ihre Daten"
      },
      {
        "q": "Eine Kommune sollte ___ Schulen technisch ausstatten, bevor sie neue digitale Konzepte fordert.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "die Kommune -> ihre Schulen"
      },
      {
        "q": "Der Unterricht verliert ___ pers\u00f6nliche Dimension, wenn digitale Aufgaben nur noch automatisch kontrolliert werden.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "der Unterricht -> seine Dimension"
      },
      {
        "q": "Eltern erkennen ___ Rolle in der digitalen Bildung oft erst, wenn zu Hause Lernplattformen genutzt werden.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural: Eltern -> ihre Rolle"
      },
      {
        "q": "Ein Lernender kann ___ Fortschritt besser einsch\u00e4tzen, wenn digitale R\u00fcckmeldungen verst\u00e4ndlich formuliert sind.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 3,
        "rule": "der Lernende -> seinen Fortschritt"
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
        "rule": "die Gesellschaft -> ihre Erwartungen"
      },
      {
        "q": "Ein digitales Lernkonzept \u00fcberzeugt nur, wenn ___ p\u00e4dagogischer Mehrwert klar erkennbar ist.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 0,
        "rule": "der Mehrwert eines Konzepts -> sein Mehrwert"
      },
      {
        "q": "Sch\u00fclerinnen und Sch\u00fcler entwickeln ___ Medienkompetenz nicht automatisch durch den Besitz eines Tablets.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural -> ihre Medienkompetenz"
      },
      {
        "q": "Die Schule muss ___ Lehrkr\u00e4fte entlasten, wenn neue Programme eingef\u00fchrt werden.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "die Schule -> ihre Lehrkr\u00e4fte"
      },
      {
        "q": "Ein Staat, der digitale Bildung f\u00f6rdern will, muss auch ___ l\u00e4ndliche Regionen ber\u00fccksichtigen.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "der Staat -> seine Regionen"
      },
      {
        "q": "Ein Kind kann ___ Lernmotivation verlieren, wenn digitale Aufgaben un\u00fcbersichtlich und \u00fcberfordernd wirken.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "das Kind -> seine Motivation"
      },
      {
        "q": "Eine Lernplattform sollte ___ Funktionen so erkl\u00e4ren, dass auch schw\u00e4chere Lernende selbstst\u00e4ndig arbeiten k\u00f6nnen.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "die Plattform -> ihre Funktionen"
      },
      {
        "q": "Digitale Bildung erreicht ___ Ziel nur dann, wenn Technik, Didaktik und soziale Gerechtigkeit zusammen gedacht werden.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 0,
        "rule": "die digitale Bildung -> ihr Ziel"
      }
    ]
  },
  {
    "id": "poss2",
    "title": "Possessivartikel II - Haustiere in der modernen Gesellschaft",
    "description": "Possessivartikel in einem Vorteilsabsatz zu Haustieren.",
    "questions": [
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
        "rule": "das Haustier -> seine Wirkung"
      },
      {
        "q": "Viele Alleinlebende sch\u00e4tzen ___ tierischen Begleiter, weil sie im Alltag Gesellschaft leisten.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "Plural -> ihren Begleiter"
      },
      {
        "q": "Eine Familie kann durch ___ gemeinsame Tierpflege Verantwortungsbewusstsein und R\u00fccksichtnahme st\u00e4rken.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "die Familie -> ihre Pflege"
      },
      {
        "q": "Ein Kind lernt durch ein Haustier, ___ eigenen W\u00fcnsche nicht immer an erste Stelle zu setzen.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "das Kind -> seine W\u00fcnsche"
      },
      {
        "q": "Der Besitzer eines Hundes ver\u00e4ndert oft ___ Tagesrhythmus, weil regelm\u00e4\u00dfige Spazierg\u00e4nge notwendig werden.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 3,
        "rule": "der Besitzer -> seinen Tagesrhythmus"
      },
      {
        "q": "Haustiere zeigen ___ positiven Einfluss nicht durch Worte, sondern durch N\u00e4he und Verl\u00e4sslichkeit.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "Plural: Haustiere -> ihren Einfluss"
      },
      {
        "q": "Eine Katze kann ___ ruhige Pr\u00e4senz nutzen, um in einer Wohnung Geborgenheit zu vermitteln.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "die Katze -> ihre Pr\u00e4senz"
      },
      {
        "q": "Ein \u00e4lterer Mensch erlebt durch ___ Haustier h\u00e4ufig mehr Struktur und emotionale Sicherheit.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 0,
        "rule": "der Mensch -> sein Haustier"
      },
      {
        "q": "Tierhalter erweitern durch ___ Spazierg\u00e4nge oft auch ihren sozialen Kontaktkreis.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural -> ihre Spazierg\u00e4nge"
      },
      {
        "q": "Die Tierhaltung zeigt ___ p\u00e4dagogischen Wert besonders dort, wo Kinder Verantwortung praktisch \u00fcbernehmen.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 3,
        "rule": "die Tierhaltung -> ihren Wert"
      },
      {
        "q": "Ein Haustier fordert ___ regelm\u00e4\u00dfige Pflege unabh\u00e4ngig davon, ob der Besitzer m\u00fcde oder besch\u00e4ftigt ist.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "das Haustier -> seine Pflege"
      },
      {
        "q": "Viele Menschen bauen zu ___ Tier eine emotionale Bindung auf, die den Alltag stabilisieren kann.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 2,
        "rule": "Plural: zu ihrem Tier"
      },
      {
        "q": "Eine Nachbarschaft kann ___ Gemeinschaftsgef\u00fchl st\u00e4rken, wenn Tierhalter einander unterst\u00fctzen.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 0,
        "rule": "die Nachbarschaft -> ihr Gef\u00fchl"
      },
      {
        "q": "Der Hund f\u00f6rdert durch ___ Bewegungsbedarf einen aktiveren Lebensstil.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 3,
        "rule": "der Hund -> seinen Bedarf"
      },
      {
        "q": "Haustiere k\u00f6nnen ___ Besitzer daran erinnern, den Alltag nicht ausschlie\u00dflich nach Arbeit auszurichten.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural -> ihre Besitzer"
      },
      {
        "q": "Ein Tier kann ___ tr\u00f6stende Funktion besonders in belastenden Lebensphasen entfalten.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "das Tier -> seine Funktion"
      },
      {
        "q": "Familien verteilen oft ___ Aufgaben neu, sobald ein Haustier versorgt werden muss.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "Plural: Familien -> ihre Aufgaben"
      },
      {
        "q": "Die moderne Gesellschaft erkennt ___ Bed\u00fcrfnis nach N\u00e4he auch daran, dass Haustiere immer wichtiger werden.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 0,
        "rule": "die Gesellschaft -> ihr Bed\u00fcrfnis"
      },
      {
        "q": "Ein Hundebesitzer kommt durch ___ t\u00e4gliche Runde leichter mit anderen Menschen ins Gespr\u00e4ch.",
        "options": [
          "sein",
          "seine",
          "seinem",
          "seinen",
          "seiner"
        ],
        "answer": 1,
        "rule": "der Besitzer -> seine Runde"
      },
      {
        "q": "Die Tierpflege entfaltet ___ erzieherische Wirkung, wenn sie regelm\u00e4\u00dfig und bewusst \u00fcbernommen wird.",
        "options": [
          "ihr",
          "ihre",
          "ihrem",
          "ihren",
          "ihrer"
        ],
        "answer": 1,
        "rule": "die Pflege -> ihre Wirkung"
      }
    ]
  },
  {
    "id": "dekl1",
    "title": "Deklination I - Umweltschutz und nachhaltige Stadtentwicklung",
    "description": "Artikel, Adjektive und Kasus in einem Umwelt-Er\u00f6rterungsthema.",
    "questions": [
      {
        "q": "Die F\u00f6rderung ___ nachhaltigen Stadtentwicklung verlangt langfristige politische Entscheidungen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin: der Entwicklung"
      },
      {
        "q": "Ein Ausbau ___ \u00f6ffentlichen Nahverkehrs kann den Autoverkehr in Innenst\u00e4dten verringern.",
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
        "q": "Viele St\u00e4dte brauchen ___ klare Strategie gegen Hitze, L\u00e4rm und Luftverschmutzung.",
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
        "q": "Ohne ___ konsequente Begr\u00fcnung bleiben dicht bebaute Viertel im Sommer stark belastet.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 1,
        "rule": "ohne + Akkusativ feminin"
      },
      {
        "q": "Der Schutz ___ st\u00e4dtischen Umwelt darf nicht allein privaten Initiativen \u00fcberlassen werden.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin: der Umwelt"
      },
      {
        "q": "Mit ___ gut ausgebauten Radwegen kann eine Stadt allt\u00e4gliche Wege klimafreundlicher machen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 3,
        "rule": "mit + Dativ Plural: den Radwegen"
      },
      {
        "q": "Eine Stadt gewinnt durch ___ verl\u00e4ssliche M\u00fclltrennung an \u00f6kologischer Glaubw\u00fcrdigkeit.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "einer"
        ],
        "answer": 1,
        "rule": "durch + Akkusativ feminin"
      },
      {
        "q": "Die Umsetzung ___ \u00f6kologischen Ma\u00dfnahmen scheitert oft an fehlender Finanzierung.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv Plural/Feminin: der Ma\u00dfnahmen"
      },
      {
        "q": "In ___ dicht besiedelten Quartieren ist saubere Luft besonders wichtig.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 3,
        "rule": "in + Dativ Plural: den Quartieren"
      },
      {
        "q": "Der Erhalt ___ alten Baumbestands kann die Lebensqualit\u00e4t eines Viertels deutlich erh\u00f6hen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 4,
        "rule": "Genitiv maskulin: des Bestands"
      },
      {
        "q": "Politik und Verwaltung m\u00fcssen ___ sozialen Folgen \u00f6kologischer Ma\u00dfnahmen mitdenken.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 1,
        "rule": "Akkusativ Plural: die Folgen"
      },
      {
        "q": "Eine gerechte Klimapolitik darf ___ \u00e4rmere Haushalte nicht zus\u00e4tzlich belasten.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 1,
        "rule": "Akkusativ Plural: die Haushalte"
      },
      {
        "q": "Der Ausbau ___ erneuerbaren Energien ist auch auf kommunaler Ebene relevant.",
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
        "q": "Mit ___ besseren W\u00e4rmed\u00e4mmung sinkt langfristig der Energieverbrauch.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "mit + Dativ feminin: der D\u00e4mmung"
      },
      {
        "q": "Viele B\u00fcrger w\u00fcnschen sich ___ lebenswerte Innenstadt mit weniger Verkehr.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "einer"
        ],
        "answer": 1,
        "rule": "Akkusativ feminin"
      },
      {
        "q": "Die Begrenzung ___ privaten Autoverkehrs kann neue Freir\u00e4ume schaffen.",
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
        "q": "Durch ___ transparente Planung entsteht mehr Akzeptanz f\u00fcr Umweltma\u00dfnahmen.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "einer"
        ],
        "answer": 1,
        "rule": "durch + Akkusativ feminin"
      },
      {
        "q": "Der Nutzen ___ gr\u00fcnen Infrastruktur wird in Krisenzeiten besonders sichtbar.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin"
      },
      {
        "q": "Eine Stadt mit ___ modernen Energiekonzept kann Vorbild f\u00fcr andere Kommunen werden.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "einer"
        ],
        "answer": 2,
        "rule": "mit + Dativ neutrum: einem Konzept"
      },
      {
        "q": "Der Schutz ___ nat\u00fcrlichen Ressourcen geh\u00f6rt zu den zentralen Aufgaben kommunaler Politik.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv Plural: der Ressourcen"
      }
    ]
  },
  {
    "id": "dekl2",
    "title": "Deklination II - Massentourismus in beliebten St\u00e4dten",
    "description": "Pr\u00e4positionen, Genitiv und attributive Gruppen im Thema Massentourismus.",
    "questions": [
      {
        "q": "Angesichts ___ wachsenden Besucherzahlen geraten beliebte St\u00e4dte zunehmend unter Druck.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "angesichts + Genitiv Plural/Feminin"
      },
      {
        "q": "Die Interessen ___ einheimischen Bev\u00f6lkerung d\u00fcrfen im Massentourismus nicht verdr\u00e4ngt werden.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin"
      },
      {
        "q": "Viele Altst\u00e4dte leiden unter ___ kurzfristigen Vermietung von Wohnungen an Touristen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "unter + Dativ feminin"
      },
      {
        "q": "Eine Regulierung ___ touristischen Infrastruktur kann Konflikte im Stadtzentrum verringern.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin"
      },
      {
        "q": "Durch ___ unkontrollierten Besucherandrang verlieren manche Viertel ihre allt\u00e4gliche Funktion.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 3,
        "rule": "durch + Akkusativ maskulin: den Andrang"
      },
      {
        "q": "Die Folgen ___ starken Saisonabh\u00e4ngigkeit treffen vor allem Besch\u00e4ftigte im Dienstleistungsbereich.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin"
      },
      {
        "q": "Mit ___ klaren Obergrenze f\u00fcr Kreuzfahrtschiffe k\u00f6nnte die Belastung sinken.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "einer"
        ],
        "answer": 4,
        "rule": "mit + Dativ feminin"
      },
      {
        "q": "Trotz ___ wirtschaftlichen Bedeutung des Tourismus braucht es soziale Regeln.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "trotz + Genitiv feminin"
      },
      {
        "q": "In ___ historischen Zentren wird Wohnraum oft durch Ferienwohnungen verdr\u00e4ngt.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 3,
        "rule": "in + Dativ Plural"
      },
      {
        "q": "Der Schutz ___ kulturellen Erbes darf nicht allein vom Ticketverkauf abh\u00e4ngen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 4,
        "rule": "Genitiv neutrum: des Erbes"
      },
      {
        "q": "Eine Stadt steht vor ___ schwierigen Aufgabe, Einnahmen und Lebensqualit\u00e4t auszubalancieren.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "einer"
        ],
        "answer": 4,
        "rule": "vor + Dativ feminin"
      },
      {
        "q": "Die Kritik ___ betroffenen Anwohner richtet sich h\u00e4ufig gegen L\u00e4rm und steigende Mieten.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv Plural: der Anwohner"
      },
      {
        "q": "Durch ___ bessere Verteilung der Besucher k\u00f6nnten \u00fcberf\u00fcllte Orte entlastet werden.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 1,
        "rule": "durch + Akkusativ feminin"
      },
      {
        "q": "Die Attraktivit\u00e4t ___ bekannten Sehensw\u00fcrdigkeiten f\u00fchrt oft zu \u00fcberf\u00fcllten Stra\u00dfen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv Plural"
      },
      {
        "q": "Ohne ___ langfristige Planung versch\u00e4rfen sich Konflikte zwischen Touristen und Einwohnern.",
        "options": [
          "ein",
          "eine",
          "einem",
          "einen",
          "einer"
        ],
        "answer": 1,
        "rule": "ohne + Akkusativ feminin"
      },
      {
        "q": "Der Ausbau ___ nachhaltigen Tourismus kann neue Qualit\u00e4tsstandards setzen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 4,
        "rule": "Genitiv maskulin"
      },
      {
        "q": "Mit ___ digitalen Besucherlenkung lassen sich Menschenstr\u00f6me besser verteilen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "mit + Dativ feminin"
      },
      {
        "q": "Eine Beschr\u00e4nkung ___ privaten Ferienvermietung kann den Wohnungsmarkt stabilisieren.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin"
      },
      {
        "q": "Die Verantwortung ___ kommunalen Politik besteht darin, klare Regeln durchzusetzen.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "Genitiv feminin"
      },
      {
        "q": "In ___ \u00fcberf\u00fcllten Innenstadt sinkt die Lebensqualit\u00e4t der Bewohner deutlich.",
        "options": [
          "der",
          "die",
          "dem",
          "den",
          "des"
        ],
        "answer": 0,
        "rule": "in + Dativ feminin"
      }
    ]
  },
  {
    "id": "pron",
    "title": "Nur Pronomen - K\u00fcnstliche Intelligenz im Bildungsbereich",
    "description": "Pronomenbezug und Koh\u00e4renz in einer KI-Er\u00f6rterung.",
    "questions": [
      {
        "q": "K\u00fcnstliche Intelligenz kann Lernende unterst\u00fctzen, wenn ___ sinnvoll in den Unterricht eingebunden wird.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "die KI -> sie"
      },
      {
        "q": "Ein digitales System ist nur hilfreich, wenn ___ transparente R\u00fcckmeldungen gibt.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 2,
        "rule": "das System -> es"
      },
      {
        "q": "Lehrkr\u00e4fte sollten KI nicht ersetzen lassen, sondern ___ als Werkzeug nutzen.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "die KI -> sie"
      },
      {
        "q": "Viele Sch\u00fclerinnen und Sch\u00fcler profitieren davon, wenn ___ individuelle Erkl\u00e4rungen erhalten.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "Plural -> sie"
      },
      {
        "q": "Ein Algorithmus wirkt problematisch, wenn ___ Lernleistungen zu einseitig bewertet.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 0,
        "rule": "der Algorithmus -> er"
      },
      {
        "q": "Die Schule muss pr\u00fcfen, ob ___ gen\u00fcgend Datenschutz gew\u00e4hrleisten kann.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "die Schule -> sie"
      },
      {
        "q": "Ein KI-Programm \u00fcberzeugt nur, wenn ___ Fehler erkl\u00e4rt und nicht nur Ergebnisse liefert.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 2,
        "rule": "das Programm -> es"
      },
      {
        "q": "Lernende brauchen Orientierung, damit ___ automatisierte Antworten kritisch einordnen k\u00f6nnen.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "Plural -> sie"
      },
      {
        "q": "Die Technik darf nicht \u00fcbersch\u00e4tzt werden, weil ___ p\u00e4dagogische Beziehungen nicht ersetzen kann.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "die Technik -> sie"
      },
      {
        "q": "Ein Lehrer kann KI einsetzen, wenn ___ die Verantwortung f\u00fcr die Bewertung beh\u00e4lt.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 0,
        "rule": "der Lehrer -> er"
      },
      {
        "q": "Die Daten der Lernenden m\u00fcssen gesch\u00fctzt werden, weil ___ sehr pers\u00f6nliche Informationen enthalten.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "Plural: Daten -> sie"
      },
      {
        "q": "Ein Argument f\u00fcr KI \u00fcberzeugt nur, wenn ___ auch soziale Ungleichheit ber\u00fccksichtigt.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 2,
        "rule": "das Argument -> es"
      },
      {
        "q": "Viele Eltern bef\u00fcrchten, dass ___ den Lernprozess ihrer Kinder nicht mehr nachvollziehen k\u00f6nnen.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "Plural: Eltern -> sie"
      },
      {
        "q": "Die Lehrkraft entscheidet, ob ___ eine KI-Antwort als Lernanlass verwendet.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "die Lehrkraft -> sie"
      },
      {
        "q": "Ein Sch\u00fcler kann KI nutzen, solange ___ die eigene Leistung nicht vollst\u00e4ndig ersetzt.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "die KI -> sie"
      },
      {
        "q": "Automatische Texte sind n\u00fctzlich, wenn ___ anschlie\u00dfend gemeinsam reflektiert werden.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "Plural: Texte -> sie"
      },
      {
        "q": "Eine Schule sollte KI einf\u00fchren, wenn ___ klare Regeln f\u00fcr die Nutzung formuliert.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "die Schule -> sie"
      },
      {
        "q": "Das Lernen ver\u00e4ndert sich, weil ___ durch digitale Werkzeuge st\u00e4rker individualisiert werden kann.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 2,
        "rule": "das Lernen -> es"
      },
      {
        "q": "Schw\u00e4chere Lernende brauchen Unterst\u00fctzung, damit ___ von KI nicht zus\u00e4tzlich abh\u00e4ngig werden.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 1,
        "rule": "Plural -> sie"
      },
      {
        "q": "Der Einsatz von KI bleibt \u00fcberzeugend, wenn ___ kritisch kontrolliert und p\u00e4dagogisch begr\u00fcndet wird.",
        "options": [
          "er",
          "sie",
          "es",
          "ihn",
          "ihnen"
        ],
        "answer": 0,
        "rule": "der Einsatz -> er"
      }
    ]
  },
  {
    "id": "indef1",
    "title": "Indefinitpronomen I - Homeoffice und moderne Arbeitswelt",
    "description": "man, niemand, einige und Personenbez\u00fcge im Thema Homeoffice.",
    "questions": [
      {
        "q": "Im Homeoffice sollte ___ klare Grenzen zwischen Arbeit und Freizeit ziehen.",
        "options": [
          "man",
          "niemand",
          "jemand",
          "einige",
          "mehrere"
        ],
        "answer": 0,
        "rule": "man als allgemeines Subjekt"
      },
      {
        "q": "___ kann dauerhaft konzentriert arbeiten, wenn st\u00e4ndig private Aufgaben dazwischenkommen.",
        "options": [
          "Man",
          "Niemand",
          "Jemand",
          "Einige",
          "Mehrere"
        ],
        "answer": 1,
        "rule": "Niemand als Subjekt"
      },
      {
        "q": "___ Besch\u00e4ftigte erleben im Homeoffice mehr Autonomie, andere dagegen mehr Isolation.",
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
        "q": "Wenn ___ im Team regelm\u00e4\u00dfig kommuniziert, entstehen weniger Missverst\u00e4ndnisse.",
        "options": [
          "man",
          "nichts",
          "niemanden",
          "mehreren",
          "etwas"
        ],
        "answer": 0,
        "rule": "man"
      },
      {
        "q": "___ sollte Homeoffice nur als Privileg f\u00fcr wenige Berufsgruppen verstehen.",
        "options": [
          "Niemand",
          "Nichts",
          "Mehrere",
          "Einige",
          "Jemanden"
        ],
        "answer": 0,
        "rule": "Niemand"
      },
      {
        "q": "F\u00fcr ___ kann flexible Arbeit eine Entlastung sein, besonders bei langen Pendelwegen.",
        "options": [
          "jemand",
          "niemand",
          "manche",
          "nichts",
          "jeder"
        ],
        "answer": 2,
        "rule": "manche"
      },
      {
        "q": "Wenn ___ Verantwortung f\u00fcr die eigene Tagesstruktur \u00fcbernimmt, verschwimmen Arbeitszeiten leichter.",
        "options": [
          "niemand",
          "nichts",
          "mehreren",
          "einige",
          "manchen"
        ],
        "answer": 0,
        "rule": "niemand"
      },
      {
        "q": "___ untersch\u00e4tzen, wie wichtig soziale Kontakte im B\u00fcro f\u00fcr Motivation sein k\u00f6nnen.",
        "options": [
          "Manche",
          "Niemand",
          "Nichts",
          "Jemanden",
          "Etwas"
        ],
        "answer": 0,
        "rule": "Manche"
      },
      {
        "q": "In einer modernen Arbeitswelt muss ___ \u00fcber Vertrauen statt \u00fcber st\u00e4ndige Kontrolle sprechen.",
        "options": [
          "man",
          "nichts",
          "niemanden",
          "mehreren",
          "etwas"
        ],
        "answer": 0,
        "rule": "man"
      },
      {
        "q": "___ der Beteiligten profitiert, wenn technische Ausstattung fehlt.",
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
        "q": "___ erwarten vom Homeoffice mehr Freiheit, \u00fcbersehen aber die Gefahr der Selbst\u00fcberforderung.",
        "options": [
          "Einige",
          "Niemand",
          "Nichts",
          "Jemandem",
          "Etwas"
        ],
        "answer": 0,
        "rule": "Einige"
      },
      {
        "q": "Wenn ___ erreichbar sein muss, entsteht schnell eine Kultur permanenter Verf\u00fcgbarkeit.",
        "options": [
          "jeder",
          "nichts",
          "niemand",
          "mehreren",
          "etwas"
        ],
        "answer": 0,
        "rule": "jeder"
      },
      {
        "q": "___ kann produktiv arbeiten, wenn Videokonferenzen den ganzen Tag f\u00fcllen.",
        "options": [
          "Niemand",
          "Nichts",
          "Manche",
          "Mehrere",
          "Jemanden"
        ],
        "answer": 0,
        "rule": "Niemand"
      },
      {
        "q": "F\u00fcr ___ Besch\u00e4ftigte ist das B\u00fcro weiterhin wichtig, weil dort informeller Austausch entsteht.",
        "options": [
          "manche",
          "manchem",
          "manchen",
          "mancher",
          "manches"
        ],
        "answer": 0,
        "rule": "manche Besch\u00e4ftigte"
      },
      {
        "q": "___ sollte die Vorteile des Homeoffice gegen soziale und organisatorische Risiken abw\u00e4gen.",
        "options": [
          "Man",
          "Nichts",
          "Niemanden",
          "Mehreren",
          "Etwas"
        ],
        "answer": 0,
        "rule": "Man"
      },
      {
        "q": "Wenn ___ klare Regeln vereinbart, werden Arbeitszeiten im Homeoffice oft ausgedehnt.",
        "options": [
          "niemand",
          "nichts",
          "mehrere",
          "einige",
          "manchen"
        ],
        "answer": 0,
        "rule": "niemand"
      },
      {
        "q": "___ empfinden die Arbeit zu Hause als konzentrierter, andere vermissen Teamn\u00e4he.",
        "options": [
          "Einige",
          "Nichts",
          "Niemand",
          "Jemanden",
          "Etwas"
        ],
        "answer": 0,
        "rule": "Einige"
      },
      {
        "q": "Ohne Vertrauen kann ___ im Homeoffice wirklich selbstst\u00e4ndig handeln.",
        "options": [
          "niemand",
          "nichts",
          "manche",
          "mehrere",
          "jeder"
        ],
        "answer": 0,
        "rule": "niemand"
      },
      {
        "q": "___ muss ber\u00fccksichtigen, dass nicht jede Wohnung als Arbeitsplatz geeignet ist.",
        "options": [
          "Man",
          "Nichts",
          "Niemanden",
          "Mehreren",
          "Etwas"
        ],
        "answer": 0,
        "rule": "Man"
      },
      {
        "q": "F\u00fcr ___ ist Homeoffice eine Chance, Beruf und Familie besser zu verbinden.",
        "options": [
          "viele",
          "viel",
          "vielem",
          "vieles",
          "keiner"
        ],
        "answer": 0,
        "rule": "viele"
      }
    ]
  },
  {
    "id": "indef2",
    "title": "Indefinitpronomen II - Fast Fashion und Konsumverhalten",
    "description": "alles, etwas, keines und Mengenbez\u00fcge im Thema Fast Fashion.",
    "questions": [
      {
        "q": "Nicht ___, was billig verkauft wird, ist unter sozialen Gesichtspunkten vertretbar.",
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
        "q": "___ der genannten Argumente rechtfertigt ausbeuterische Arbeitsbedingungen.",
        "options": [
          "Keiner",
          "Keine",
          "Keines",
          "Keinem",
          "Keinen"
        ],
        "answer": 2,
        "rule": "keines der Vorteile/Argumente? Better 'Argumente' neuter plural genitive -> keines"
      },
      {
        "q": "Viele kaufen ___ Neues, obwohl der Kleiderschrank bereits voll ist.",
        "options": [
          "etwas",
          "jemand",
          "alle",
          "manchen",
          "keinen"
        ],
        "answer": 0,
        "rule": "etwas Neues"
      },
      {
        "q": "F\u00fcr ___ Konsumenten z\u00e4hlt vor allem der Preis, nicht die Produktionskette.",
        "options": [
          "manche",
          "manchem",
          "manchen",
          "mancher",
          "manches"
        ],
        "answer": 0,
        "rule": "manche Konsumenten"
      },
      {
        "q": "Fast Fashion zeigt, dass ___ kurzfristig g\u00fcnstig wirkt, aber langfristig teuer werden kann.",
        "options": [
          "etwas",
          "jemand",
          "alle",
          "mehreren",
          "keinen"
        ],
        "answer": 0,
        "rule": "etwas"
      },
      {
        "q": "___ sollte ignorieren, dass Kleidung Ressourcen, Wasser und Energie verbraucht.",
        "options": [
          "Niemand",
          "Nichts",
          "Mehrere",
          "Einige",
          "Jemanden"
        ],
        "answer": 0,
        "rule": "Niemand"
      },
      {
        "q": "Nicht ___ Kleidungsst\u00fcck muss nach wenigen Wochen ersetzt werden.",
        "options": [
          "jedes",
          "jeder",
          "jedem",
          "jeden",
          "jede"
        ],
        "answer": 0,
        "rule": "jedes Kleidungsst\u00fcck"
      },
      {
        "q": "___ der gro\u00dfen Marken \u00fcbernimmt ausreichend Verantwortung f\u00fcr transparente Lieferketten.",
        "options": [
          "Keine",
          "Keiner",
          "Keines",
          "Keinem",
          "Keinen"
        ],
        "answer": 1,
        "rule": "keiner der Marken"
      },
      {
        "q": "Wenn ___ st\u00e4ndig neue Trends kauft, verst\u00e4rkt sich der Kreislauf des \u00dcberkonsums.",
        "options": [
          "man",
          "nichts",
          "niemand",
          "mehreren",
          "etwas"
        ],
        "answer": 0,
        "rule": "man"
      },
      {
        "q": "___ an Fast Fashion ist nur der niedrige Preis, wenn \u00f6kologische Kosten ausgeblendet werden.",
        "options": [
          "Problematisch",
          "Problematische",
          "Problematischem",
          "Problematischen",
          "Problematischer"
        ],
        "answer": 0,
        "rule": "pr\u00e4dikatives Adjektiv"
      },
      {
        "q": "Es gibt kaum ___, das ohne \u00f6kologische Spuren produziert werden kann.",
        "options": [
          "etwas",
          "jemand",
          "alle",
          "manchen",
          "keinen"
        ],
        "answer": 0,
        "rule": "etwas"
      },
      {
        "q": "F\u00fcr ___ Besch\u00e4ftigte in Produktionsl\u00e4ndern bleiben L\u00f6hne und Sicherheit zentrale Probleme.",
        "options": [
          "viele",
          "viel",
          "vielem",
          "vieles",
          "keiner"
        ],
        "answer": 0,
        "rule": "viele Besch\u00e4ftigte"
      },
      {
        "q": "___ spricht daf\u00fcr, Kleidung l\u00e4nger zu tragen und bewusster zu kaufen.",
        "options": [
          "Vieles",
          "Viele",
          "Vielem",
          "Viel",
          "Keinen"
        ],
        "answer": 0,
        "rule": "vieles"
      },
      {
        "q": "Nicht ___ kann sich nachhaltige Mode leisten, solange sie deutlich teurer bleibt.",
        "options": [
          "jeder",
          "jede",
          "jedem",
          "jeden",
          "jedes"
        ],
        "answer": 0,
        "rule": "jeder"
      },
      {
        "q": "___ der politischen Ma\u00dfnahmen wirkt, wenn Unternehmen ihre Lieferketten verschleiern.",
        "options": [
          "Keine",
          "Keiner",
          "Keines",
          "Keinem",
          "Keinen"
        ],
        "answer": 1,
        "rule": "keiner der Ma\u00dfnahmen"
      },
      {
        "q": "Wenn ___ \u00fcber Konsum spricht, muss auch Werbung als Einflussfaktor betrachtet werden.",
        "options": [
          "man",
          "nichts",
          "niemanden",
          "mehreren",
          "etwas"
        ],
        "answer": 0,
        "rule": "man"
      },
      {
        "q": "___ kaufen Kleidung spontan, weil soziale Medien st\u00e4ndig neue Trends sichtbar machen.",
        "options": [
          "Viele",
          "Viel",
          "Vielem",
          "Vieles",
          "Keiner"
        ],
        "answer": 0,
        "rule": "viele"
      },
      {
        "q": "Nicht ___, was modern aussieht, ist qualitativ langlebig.",
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
        "q": "F\u00fcr ___ kann Secondhand eine M\u00f6glichkeit sein, Konsum und Nachhaltigkeit zu verbinden.",
        "options": [
          "manche",
          "manchem",
          "manchen",
          "mancher",
          "manches"
        ],
        "answer": 0,
        "rule": "manche"
      },
      {
        "q": "___ bleibt glaubw\u00fcrdig, wenn Kritik an Fast Fashion auch das eigene Kaufverhalten einbezieht.",
        "options": [
          "Man",
          "Niemand",
          "Jemand",
          "Einige",
          "Mehrere"
        ],
        "answer": 0,
        "rule": "man"
      }
    ]
  },
  {
    "id": "neg1",
    "title": "Negationsw\u00f6rter I - Deklination in Er\u00f6rterungen",
    "description": "kein-Formen und negative Determinanten.",
    "questions": [
      {
        "q": "Keine verantwortungsvolle Politik darf die Risiken von digitale Bildung ignorieren.",
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
        "q": "Ohne ___ klare Begr\u00fcndung wirkt ein Argument oberfl\u00e4chlich.",
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
        "q": "Mit ___ einfachen L\u00f6sung ist bei Umweltschutz zu rechnen.",
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
        "q": "Keine verantwortungsvolle Politik darf die Risiken von Homeoffice ignorieren.",
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
        "q": "Ohne ___ klare Begr\u00fcndung wirkt ein Argument oberfl\u00e4chlich.",
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
        "q": "Mit ___ einfachen L\u00f6sung ist bei Fast Fashion zu rechnen.",
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
        "q": "Keine verantwortungsvolle Politik darf die Risiken von \u00f6ffentliche Verkehrsmittel ignorieren.",
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
        "q": "Ohne ___ klare Begr\u00fcndung wirkt ein Argument oberfl\u00e4chlich.",
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
        "q": "Mit ___ einfachen L\u00f6sung ist bei Studium im Ausland zu rechnen.",
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
        "q": "Keine verantwortungsvolle Politik darf die Risiken von E-Books ignorieren.",
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
        "q": "Ohne ___ klare Begr\u00fcndung wirkt ein Argument oberfl\u00e4chlich.",
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
        "q": "Mit ___ einfachen L\u00f6sung ist bei Datenschutz zu rechnen.",
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
        "q": "Keine verantwortungsvolle Politik darf die Risiken von Teamarbeit ignorieren.",
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
        "q": "Ohne ___ klare Begr\u00fcndung wirkt ein Argument oberfl\u00e4chlich.",
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
        "q": "Mit ___ einfachen L\u00f6sung ist bei Werbung in Medien zu rechnen.",
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
    "title": "Negationsw\u00f6rter II - Gegens\u00e4tze und Er\u00f6rterungssprache",
    "description": "nicht, weder noch und kontrastive Strukturen.",
    "questions": [
      {
        "q": "Weder wirtschaftliche Vorteile ___ technische Bequemlichkeit reichen als alleinige Begr\u00fcndung aus.",
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
        "q": "Ein Verbot ist ___ immer die \u00fcberzeugendste L\u00f6sung.",
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
        "q": "Weder wirtschaftliche Vorteile ___ technische Bequemlichkeit reichen als alleinige Begr\u00fcndung aus.",
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
        "q": "Ein Verbot ist ___ immer die \u00fcberzeugendste L\u00f6sung.",
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
        "q": "Weder wirtschaftliche Vorteile ___ technische Bequemlichkeit reichen als alleinige Begr\u00fcndung aus.",
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
        "q": "Ein Verbot ist ___ immer die \u00fcberzeugendste L\u00f6sung.",
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
        "q": "Weder wirtschaftliche Vorteile ___ technische Bequemlichkeit reichen als alleinige Begr\u00fcndung aus.",
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
        "q": "Ein Verbot ist ___ immer die \u00fcberzeugendste L\u00f6sung.",
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
        "q": "Weder wirtschaftliche Vorteile ___ technische Bequemlichkeit reichen als alleinige Begr\u00fcndung aus.",
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
        "q": "Ein Verbot ist ___ immer die \u00fcberzeugendste L\u00f6sung.",
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
    "title": "Satzstellung I - TeKaMoLo, Objektstellung und Verbklammer",
    "description": "Satzstellung, Nebens\u00e4tze und Verbklammer.",
    "questions": [
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "In Bezug auf digitale Bildung sollte man die langfristigen Folgen sorgf\u00e4ltig abw\u00e4gen.",
          "In Bezug auf digitale Bildung man sollte die langfristigen Folgen sorgf\u00e4ltig abw\u00e4gen.",
          "Man sollte in Bezug auf digitale Bildung sorgf\u00e4ltig abw\u00e4gen die langfristigen Folgen.",
          "Sorgf\u00e4ltig man sollte in Bezug auf digitale Bildung die langfristigen Folgen abw\u00e4gen.",
          "Die langfristigen Folgen sorgf\u00e4ltig sollte man in Bezug auf digitale Bildung abw\u00e4gen."
        ],
        "answer": 0,
        "rule": "Vorfeld + finites Verb + Mittelfeld + Verbklammer"
      },
      {
        "q": "Welche Variante ist C1/C2-gerecht?",
        "options": [
          "Obwohl soziale Medien Vorteile bietet, d\u00fcrfen m\u00f6gliche Risiken nicht ausgeblendet werden.",
          "Obwohl bietet soziale Medien Vorteile, m\u00f6gliche Risiken d\u00fcrfen nicht ausgeblendet werden.",
          "Obwohl soziale Medien bietet Vorteile, d\u00fcrfen nicht m\u00f6gliche Risiken ausgeblendet werden.",
          "Obwohl Vorteile bietet soziale Medien, d\u00fcrfen m\u00f6gliche Risiken nicht ausgeblendet werden.",
          "Obwohl soziale Medien Vorteile bietet, nicht d\u00fcrfen m\u00f6gliche Risiken ausgeblendet werden."
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
          "Viele Betroffene k\u00f6nnten durch k\u00fcnstliche Intelligenz langfristig entlastet werden.",
          "Viele Betroffene k\u00f6nnten durch k\u00fcnstliche Intelligenz langfristig werden entlastet.",
          "Viele Betroffene durch k\u00fcnstliche Intelligenz k\u00f6nnten langfristig entlastet werden.",
          "K\u00f6nnten viele Betroffene langfristig durch k\u00fcnstliche Intelligenz entlastet werden.",
          "Langfristig entlastet durch k\u00fcnstliche Intelligenz k\u00f6nnten viele Betroffene werden."
        ],
        "answer": 0,
        "rule": "Modalverb + Partizip/Infinitiv am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "In Bezug auf Homeoffice sollte man die langfristigen Folgen sorgf\u00e4ltig abw\u00e4gen.",
          "In Bezug auf Homeoffice man sollte die langfristigen Folgen sorgf\u00e4ltig abw\u00e4gen.",
          "Man sollte in Bezug auf Homeoffice sorgf\u00e4ltig abw\u00e4gen die langfristigen Folgen.",
          "Sorgf\u00e4ltig man sollte in Bezug auf Homeoffice die langfristigen Folgen abw\u00e4gen.",
          "Die langfristigen Folgen sorgf\u00e4ltig sollte man in Bezug auf Homeoffice abw\u00e4gen."
        ],
        "answer": 0,
        "rule": "Vorfeld + finites Verb + Mittelfeld + Verbklammer"
      },
      {
        "q": "Welche Variante ist C1/C2-gerecht?",
        "options": [
          "Obwohl Massentourismus Vorteile bietet, d\u00fcrfen m\u00f6gliche Risiken nicht ausgeblendet werden.",
          "Obwohl bietet Massentourismus Vorteile, m\u00f6gliche Risiken d\u00fcrfen nicht ausgeblendet werden.",
          "Obwohl Massentourismus bietet Vorteile, d\u00fcrfen nicht m\u00f6gliche Risiken ausgeblendet werden.",
          "Obwohl Vorteile bietet Massentourismus, d\u00fcrfen m\u00f6gliche Risiken nicht ausgeblendet werden.",
          "Obwohl Massentourismus Vorteile bietet, nicht d\u00fcrfen m\u00f6gliche Risiken ausgeblendet werden."
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
          "Viele Betroffene k\u00f6nnten durch gesunde Ern\u00e4hrung langfristig entlastet werden.",
          "Viele Betroffene k\u00f6nnten durch gesunde Ern\u00e4hrung langfristig werden entlastet.",
          "Viele Betroffene durch gesunde Ern\u00e4hrung k\u00f6nnten langfristig entlastet werden.",
          "K\u00f6nnten viele Betroffene langfristig durch gesunde Ern\u00e4hrung entlastet werden.",
          "Langfristig entlastet durch gesunde Ern\u00e4hrung k\u00f6nnten viele Betroffene werden."
        ],
        "answer": 0,
        "rule": "Modalverb + Partizip/Infinitiv am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "In Bezug auf \u00f6ffentliche Verkehrsmittel sollte man die langfristigen Folgen sorgf\u00e4ltig abw\u00e4gen.",
          "In Bezug auf \u00f6ffentliche Verkehrsmittel man sollte die langfristigen Folgen sorgf\u00e4ltig abw\u00e4gen.",
          "Man sollte in Bezug auf \u00f6ffentliche Verkehrsmittel sorgf\u00e4ltig abw\u00e4gen die langfristigen Folgen.",
          "Sorgf\u00e4ltig man sollte in Bezug auf \u00f6ffentliche Verkehrsmittel die langfristigen Folgen abw\u00e4gen.",
          "Die langfristigen Folgen sorgf\u00e4ltig sollte man in Bezug auf \u00f6ffentliche Verkehrsmittel abw\u00e4gen."
        ],
        "answer": 0,
        "rule": "Vorfeld + finites Verb + Mittelfeld + Verbklammer"
      },
      {
        "q": "Welche Variante ist C1/C2-gerecht?",
        "options": [
          "Obwohl Mehrsprachigkeit Vorteile bietet, d\u00fcrfen m\u00f6gliche Risiken nicht ausgeblendet werden.",
          "Obwohl bietet Mehrsprachigkeit Vorteile, m\u00f6gliche Risiken d\u00fcrfen nicht ausgeblendet werden.",
          "Obwohl Mehrsprachigkeit bietet Vorteile, d\u00fcrfen nicht m\u00f6gliche Risiken ausgeblendet werden.",
          "Obwohl Vorteile bietet Mehrsprachigkeit, d\u00fcrfen m\u00f6gliche Risiken nicht ausgeblendet werden.",
          "Obwohl Mehrsprachigkeit Vorteile bietet, nicht d\u00fcrfen m\u00f6gliche Risiken ausgeblendet werden."
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
          "Viele Betroffene k\u00f6nnten durch Ganztagsschule langfristig entlastet werden.",
          "Viele Betroffene k\u00f6nnten durch Ganztagsschule langfristig werden entlastet.",
          "Viele Betroffene durch Ganztagsschule k\u00f6nnten langfristig entlastet werden.",
          "K\u00f6nnten viele Betroffene langfristig durch Ganztagsschule entlastet werden.",
          "Langfristig entlastet durch Ganztagsschule k\u00f6nnten viele Betroffene werden."
        ],
        "answer": 0,
        "rule": "Modalverb + Partizip/Infinitiv am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "In Bezug auf E-Books sollte man die langfristigen Folgen sorgf\u00e4ltig abw\u00e4gen.",
          "In Bezug auf E-Books man sollte die langfristigen Folgen sorgf\u00e4ltig abw\u00e4gen.",
          "Man sollte in Bezug auf E-Books sorgf\u00e4ltig abw\u00e4gen die langfristigen Folgen.",
          "Sorgf\u00e4ltig man sollte in Bezug auf E-Books die langfristigen Folgen abw\u00e4gen.",
          "Die langfristigen Folgen sorgf\u00e4ltig sollte man in Bezug auf E-Books abw\u00e4gen."
        ],
        "answer": 0,
        "rule": "Vorfeld + finites Verb + Mittelfeld + Verbklammer"
      },
      {
        "q": "Welche Variante ist C1/C2-gerecht?",
        "options": [
          "Obwohl soziale Ungleichheit Vorteile bietet, d\u00fcrfen m\u00f6gliche Risiken nicht ausgeblendet werden.",
          "Obwohl bietet soziale Ungleichheit Vorteile, m\u00f6gliche Risiken d\u00fcrfen nicht ausgeblendet werden.",
          "Obwohl soziale Ungleichheit bietet Vorteile, d\u00fcrfen nicht m\u00f6gliche Risiken ausgeblendet werden.",
          "Obwohl Vorteile bietet soziale Ungleichheit, d\u00fcrfen m\u00f6gliche Risiken nicht ausgeblendet werden.",
          "Obwohl soziale Ungleichheit Vorteile bietet, nicht d\u00fcrfen m\u00f6gliche Risiken ausgeblendet werden."
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
          "Viele Betroffene k\u00f6nnten durch ehrenamtliches Engagement langfristig entlastet werden.",
          "Viele Betroffene k\u00f6nnten durch ehrenamtliches Engagement langfristig werden entlastet.",
          "Viele Betroffene durch ehrenamtliches Engagement k\u00f6nnten langfristig entlastet werden.",
          "K\u00f6nnten viele Betroffene langfristig durch ehrenamtliches Engagement entlastet werden.",
          "Langfristig entlastet durch ehrenamtliches Engagement k\u00f6nnten viele Betroffene werden."
        ],
        "answer": 0,
        "rule": "Modalverb + Partizip/Infinitiv am Ende"
      },
      {
        "q": "Welche Satzstellung ist korrekt?",
        "options": [
          "In Bezug auf Teamarbeit sollte man die langfristigen Folgen sorgf\u00e4ltig abw\u00e4gen.",
          "In Bezug auf Teamarbeit man sollte die langfristigen Folgen sorgf\u00e4ltig abw\u00e4gen.",
          "Man sollte in Bezug auf Teamarbeit sorgf\u00e4ltig abw\u00e4gen die langfristigen Folgen.",
          "Sorgf\u00e4ltig man sollte in Bezug auf Teamarbeit die langfristigen Folgen abw\u00e4gen.",
          "Die langfristigen Folgen sorgf\u00e4ltig sollte man in Bezug auf Teamarbeit abw\u00e4gen."
        ],
        "answer": 0,
        "rule": "Vorfeld + finites Verb + Mittelfeld + Verbklammer"
      },
      {
        "q": "Welche Variante ist C1/C2-gerecht?",
        "options": [
          "Obwohl lebenslanges Lernen Vorteile bietet, d\u00fcrfen m\u00f6gliche Risiken nicht ausgeblendet werden.",
          "Obwohl bietet lebenslanges Lernen Vorteile, m\u00f6gliche Risiken d\u00fcrfen nicht ausgeblendet werden.",
          "Obwohl lebenslanges Lernen bietet Vorteile, d\u00fcrfen nicht m\u00f6gliche Risiken ausgeblendet werden.",
          "Obwohl Vorteile bietet lebenslanges Lernen, d\u00fcrfen m\u00f6gliche Risiken nicht ausgeblendet werden.",
          "Obwohl lebenslanges Lernen Vorteile bietet, nicht d\u00fcrfen m\u00f6gliche Risiken ausgeblendet werden."
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
          "Viele Betroffene k\u00f6nnten durch autonomes Fahren langfristig entlastet werden.",
          "Viele Betroffene k\u00f6nnten durch autonomes Fahren langfristig werden entlastet.",
          "Viele Betroffene durch autonomes Fahren k\u00f6nnten langfristig entlastet werden.",
          "K\u00f6nnten viele Betroffene langfristig durch autonomes Fahren entlastet werden.",
          "Langfristig entlastet durch autonomes Fahren k\u00f6nnten viele Betroffene werden."
        ],
        "answer": 0,
        "rule": "Modalverb + Partizip/Infinitiv am Ende"
      }
    ]
  },
  {
    "id": "rede1",
    "title": "Redemittel I - Einleitung, Kontextualisierung und Begr\u00fcndung",
    "description": "Einleitungen, Begr\u00fcndungen und Abw\u00e4gungen.",
    "questions": [
      {
        "q": "Welche Einleitung passt am besten?",
        "options": [
          "In der aktuellen Debatte \u00fcber digitale Bildung stellt sich die Frage, welche Chancen und Risiken damit verbunden sind.",
          "Ich finde digitale Bildung gut und schreibe jetzt dar\u00fcber.",
          "Alle reden \u00fcber digitale Bildung, deshalb ist es wichtig.",
          "Das Thema digitale Bildung ist irgendwie modern.",
          "Man kann \u00fcber digitale Bildung viel sagen."
        ],
        "answer": 0,
        "rule": "pr\u00e4zise Einleitung"
      },
      {
        "q": "Welche Begr\u00fcndung ist am st\u00e4rksten?",
        "options": [
          "Dies ist darauf zur\u00fcckzuf\u00fchren, dass gesellschaftliche Ver\u00e4nderungen selten nur eine Ursache haben.",
          "Das ist so, weil es eben so ist.",
          "Viele finden das gut.",
          "Es gibt Gr\u00fcnde und Nachteile.",
          "Man sagt das oft."
        ],
        "answer": 0,
        "rule": "kausale Begr\u00fcndung"
      },
      {
        "q": "Welche Redemittel-Kombination ist korrekt?",
        "options": [
          "Einerseits er\u00f6ffnet Umweltschutz neue M\u00f6glichkeiten, andererseits entstehen dadurch neue Abh\u00e4ngigkeiten.",
          "Einerseits Umweltschutz er\u00f6ffnet, andererseits entstehen dadurch.",
          "Entweder er\u00f6ffnet Umweltschutz, andererseits entstehen Abh\u00e4ngigkeiten.",
          "Nicht nur er\u00f6ffnet Umweltschutz, sondern entstehen Abh\u00e4ngigkeiten.",
          "Sowohl er\u00f6ffnet Umweltschutz, aber auch entstehen Abh\u00e4ngigkeiten."
        ],
        "answer": 0,
        "rule": "Abw\u00e4gung"
      },
      {
        "q": "Welche Kontextualisierung ist C1/C2-gerecht?",
        "options": [
          "Vor dem Hintergrund gesellschaftlicher Ver\u00e4nderungen gewinnt k\u00fcnstliche Intelligenz zunehmend an Bedeutung.",
          "Im Hintergrund ist das Thema sehr wichtig.",
          "Wegen Gesellschaft wird das Thema gr\u00f6\u00dfer.",
          "k\u00fcnstliche Intelligenz macht eine Bedeutung.",
          "Das Thema hat Hintergrund."
        ],
        "answer": 0,
        "rule": "Kontextualisierung"
      },
      {
        "q": "Welche Einleitung passt am besten?",
        "options": [
          "In der aktuellen Debatte \u00fcber Homeoffice stellt sich die Frage, welche Chancen und Risiken damit verbunden sind.",
          "Ich finde Homeoffice gut und schreibe jetzt dar\u00fcber.",
          "Alle reden \u00fcber Homeoffice, deshalb ist es wichtig.",
          "Das Thema Homeoffice ist irgendwie modern.",
          "Man kann \u00fcber Homeoffice viel sagen."
        ],
        "answer": 0,
        "rule": "pr\u00e4zise Einleitung"
      },
      {
        "q": "Welche Begr\u00fcndung ist am st\u00e4rksten?",
        "options": [
          "Dies ist darauf zur\u00fcckzuf\u00fchren, dass gesellschaftliche Ver\u00e4nderungen selten nur eine Ursache haben.",
          "Das ist so, weil es eben so ist.",
          "Viele finden das gut.",
          "Es gibt Gr\u00fcnde und Nachteile.",
          "Man sagt das oft."
        ],
        "answer": 0,
        "rule": "kausale Begr\u00fcndung"
      },
      {
        "q": "Welche Redemittel-Kombination ist korrekt?",
        "options": [
          "Einerseits er\u00f6ffnet Fast Fashion neue M\u00f6glichkeiten, andererseits entstehen dadurch neue Abh\u00e4ngigkeiten.",
          "Einerseits Fast Fashion er\u00f6ffnet, andererseits entstehen dadurch.",
          "Entweder er\u00f6ffnet Fast Fashion, andererseits entstehen Abh\u00e4ngigkeiten.",
          "Nicht nur er\u00f6ffnet Fast Fashion, sondern entstehen Abh\u00e4ngigkeiten.",
          "Sowohl er\u00f6ffnet Fast Fashion, aber auch entstehen Abh\u00e4ngigkeiten."
        ],
        "answer": 0,
        "rule": "Abw\u00e4gung"
      },
      {
        "q": "Welche Kontextualisierung ist C1/C2-gerecht?",
        "options": [
          "Vor dem Hintergrund gesellschaftlicher Ver\u00e4nderungen gewinnt gesunde Ern\u00e4hrung zunehmend an Bedeutung.",
          "Im Hintergrund ist das Thema sehr wichtig.",
          "Wegen Gesellschaft wird das Thema gr\u00f6\u00dfer.",
          "gesunde Ern\u00e4hrung macht eine Bedeutung.",
          "Das Thema hat Hintergrund."
        ],
        "answer": 0,
        "rule": "Kontextualisierung"
      },
      {
        "q": "Welche Einleitung passt am besten?",
        "options": [
          "In der aktuellen Debatte \u00fcber \u00f6ffentliche Verkehrsmittel stellt sich die Frage, welche Chancen und Risiken damit verbunden sind.",
          "Ich finde \u00f6ffentliche Verkehrsmittel gut und schreibe jetzt dar\u00fcber.",
          "Alle reden \u00fcber \u00f6ffentliche Verkehrsmittel, deshalb ist es wichtig.",
          "Das Thema \u00f6ffentliche Verkehrsmittel ist irgendwie modern.",
          "Man kann \u00fcber \u00f6ffentliche Verkehrsmittel viel sagen."
        ],
        "answer": 0,
        "rule": "pr\u00e4zise Einleitung"
      },
      {
        "q": "Welche Begr\u00fcndung ist am st\u00e4rksten?",
        "options": [
          "Dies ist darauf zur\u00fcckzuf\u00fchren, dass gesellschaftliche Ver\u00e4nderungen selten nur eine Ursache haben.",
          "Das ist so, weil es eben so ist.",
          "Viele finden das gut.",
          "Es gibt Gr\u00fcnde und Nachteile.",
          "Man sagt das oft."
        ],
        "answer": 0,
        "rule": "kausale Begr\u00fcndung"
      },
      {
        "q": "Welche Redemittel-Kombination ist korrekt?",
        "options": [
          "Einerseits er\u00f6ffnet Studium im Ausland neue M\u00f6glichkeiten, andererseits entstehen dadurch neue Abh\u00e4ngigkeiten.",
          "Einerseits Studium im Ausland er\u00f6ffnet, andererseits entstehen dadurch.",
          "Entweder er\u00f6ffnet Studium im Ausland, andererseits entstehen Abh\u00e4ngigkeiten.",
          "Nicht nur er\u00f6ffnet Studium im Ausland, sondern entstehen Abh\u00e4ngigkeiten.",
          "Sowohl er\u00f6ffnet Studium im Ausland, aber auch entstehen Abh\u00e4ngigkeiten."
        ],
        "answer": 0,
        "rule": "Abw\u00e4gung"
      },
      {
        "q": "Welche Kontextualisierung ist C1/C2-gerecht?",
        "options": [
          "Vor dem Hintergrund gesellschaftlicher Ver\u00e4nderungen gewinnt Ganztagsschule zunehmend an Bedeutung.",
          "Im Hintergrund ist das Thema sehr wichtig.",
          "Wegen Gesellschaft wird das Thema gr\u00f6\u00dfer.",
          "Ganztagsschule macht eine Bedeutung.",
          "Das Thema hat Hintergrund."
        ],
        "answer": 0,
        "rule": "Kontextualisierung"
      },
      {
        "q": "Welche Einleitung passt am besten?",
        "options": [
          "In der aktuellen Debatte \u00fcber E-Books stellt sich die Frage, welche Chancen und Risiken damit verbunden sind.",
          "Ich finde E-Books gut und schreibe jetzt dar\u00fcber.",
          "Alle reden \u00fcber E-Books, deshalb ist es wichtig.",
          "Das Thema E-Books ist irgendwie modern.",
          "Man kann \u00fcber E-Books viel sagen."
        ],
        "answer": 0,
        "rule": "pr\u00e4zise Einleitung"
      },
      {
        "q": "Welche Begr\u00fcndung ist am st\u00e4rksten?",
        "options": [
          "Dies ist darauf zur\u00fcckzuf\u00fchren, dass gesellschaftliche Ver\u00e4nderungen selten nur eine Ursache haben.",
          "Das ist so, weil es eben so ist.",
          "Viele finden das gut.",
          "Es gibt Gr\u00fcnde und Nachteile.",
          "Man sagt das oft."
        ],
        "answer": 0,
        "rule": "kausale Begr\u00fcndung"
      },
      {
        "q": "Welche Redemittel-Kombination ist korrekt?",
        "options": [
          "Einerseits er\u00f6ffnet Datenschutz neue M\u00f6glichkeiten, andererseits entstehen dadurch neue Abh\u00e4ngigkeiten.",
          "Einerseits Datenschutz er\u00f6ffnet, andererseits entstehen dadurch.",
          "Entweder er\u00f6ffnet Datenschutz, andererseits entstehen Abh\u00e4ngigkeiten.",
          "Nicht nur er\u00f6ffnet Datenschutz, sondern entstehen Abh\u00e4ngigkeiten.",
          "Sowohl er\u00f6ffnet Datenschutz, aber auch entstehen Abh\u00e4ngigkeiten."
        ],
        "answer": 0,
        "rule": "Abw\u00e4gung"
      },
      {
        "q": "Welche Kontextualisierung ist C1/C2-gerecht?",
        "options": [
          "Vor dem Hintergrund gesellschaftlicher Ver\u00e4nderungen gewinnt ehrenamtliches Engagement zunehmend an Bedeutung.",
          "Im Hintergrund ist das Thema sehr wichtig.",
          "Wegen Gesellschaft wird das Thema gr\u00f6\u00dfer.",
          "ehrenamtliches Engagement macht eine Bedeutung.",
          "Das Thema hat Hintergrund."
        ],
        "answer": 0,
        "rule": "Kontextualisierung"
      },
      {
        "q": "Welche Einleitung passt am besten?",
        "options": [
          "In der aktuellen Debatte \u00fcber Teamarbeit stellt sich die Frage, welche Chancen und Risiken damit verbunden sind.",
          "Ich finde Teamarbeit gut und schreibe jetzt dar\u00fcber.",
          "Alle reden \u00fcber Teamarbeit, deshalb ist es wichtig.",
          "Das Thema Teamarbeit ist irgendwie modern.",
          "Man kann \u00fcber Teamarbeit viel sagen."
        ],
        "answer": 0,
        "rule": "pr\u00e4zise Einleitung"
      },
      {
        "q": "Welche Begr\u00fcndung ist am st\u00e4rksten?",
        "options": [
          "Dies ist darauf zur\u00fcckzuf\u00fchren, dass gesellschaftliche Ver\u00e4nderungen selten nur eine Ursache haben.",
          "Das ist so, weil es eben so ist.",
          "Viele finden das gut.",
          "Es gibt Gr\u00fcnde und Nachteile.",
          "Man sagt das oft."
        ],
        "answer": 0,
        "rule": "kausale Begr\u00fcndung"
      },
      {
        "q": "Welche Redemittel-Kombination ist korrekt?",
        "options": [
          "Einerseits er\u00f6ffnet Werbung in Medien neue M\u00f6glichkeiten, andererseits entstehen dadurch neue Abh\u00e4ngigkeiten.",
          "Einerseits Werbung in Medien er\u00f6ffnet, andererseits entstehen dadurch.",
          "Entweder er\u00f6ffnet Werbung in Medien, andererseits entstehen Abh\u00e4ngigkeiten.",
          "Nicht nur er\u00f6ffnet Werbung in Medien, sondern entstehen Abh\u00e4ngigkeiten.",
          "Sowohl er\u00f6ffnet Werbung in Medien, aber auch entstehen Abh\u00e4ngigkeiten."
        ],
        "answer": 0,
        "rule": "Abw\u00e4gung"
      },
      {
        "q": "Welche Kontextualisierung ist C1/C2-gerecht?",
        "options": [
          "Vor dem Hintergrund gesellschaftlicher Ver\u00e4nderungen gewinnt autonomes Fahren zunehmend an Bedeutung.",
          "Im Hintergrund ist das Thema sehr wichtig.",
          "Wegen Gesellschaft wird das Thema gr\u00f6\u00dfer.",
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
    "title": "Redemittel II - Folgen, Abw\u00e4gung, Kritik und Schluss",
    "description": "Folge, Kritik, Abw\u00e4gung und Schluss.",
    "questions": [
      {
        "q": "Welche Folgeformulierung passt?",
        "options": [
          "Dies kann dazu f\u00fchren, dass bestehende Ungleichheiten verst\u00e4rkt werden.",
          "Dies kann machen, dass es schlecht wird.",
          "Dies f\u00fchrt, dass Ungleichheiten.",
          "Dadurch ist es Folge.",
          "Es kommt eine Folge heraus."
        ],
        "answer": 0,
        "rule": "Folgen ausdr\u00fccken"
      },
      {
        "q": "Welche kritische Bewertung ist pr\u00e4zise?",
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
          "Zusammenfassend l\u00e4sst sich festhalten, dass Umweltschutz nur unter klaren Bedingungen sinnvoll genutzt werden kann.",
          "Am Ende ist Umweltschutz gut.",
          "Ich bin fertig mit dem Thema.",
          "Alles zusammen ist wichtig.",
          "Das war meine Meinung."
        ],
        "answer": 0,
        "rule": "Schlussfolgerung"
      },
      {
        "q": "Welche Abw\u00e4gung ist korrekt?",
        "options": [
          "W\u00e4hrend kurzfristige Vorteile sichtbar sind, m\u00fcssen langfristige Nebenwirkungen sorgf\u00e4ltig gepr\u00fcft werden.",
          "W\u00e4hrend Vorteile sind sichtbar, m\u00fcssen gepr\u00fcft Nebenwirkungen.",
          "Kurzfristig Vorteile, langfristig Nebenwirkungen.",
          "Obwohl Vorteile sichtbar, Nebenwirkungen m\u00fcssen.",
          "Vorteile sind, aber pr\u00fcfen."
        ],
        "answer": 0,
        "rule": "konzessive Abw\u00e4gung"
      },
      {
        "q": "Welche Folgeformulierung passt?",
        "options": [
          "Dies kann dazu f\u00fchren, dass bestehende Ungleichheiten verst\u00e4rkt werden.",
          "Dies kann machen, dass es schlecht wird.",
          "Dies f\u00fchrt, dass Ungleichheiten.",
          "Dadurch ist es Folge.",
          "Es kommt eine Folge heraus."
        ],
        "answer": 0,
        "rule": "Folgen ausdr\u00fccken"
      },
      {
        "q": "Welche kritische Bewertung ist pr\u00e4zise?",
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
          "Zusammenfassend l\u00e4sst sich festhalten, dass Fast Fashion nur unter klaren Bedingungen sinnvoll genutzt werden kann.",
          "Am Ende ist Fast Fashion gut.",
          "Ich bin fertig mit dem Thema.",
          "Alles zusammen ist wichtig.",
          "Das war meine Meinung."
        ],
        "answer": 0,
        "rule": "Schlussfolgerung"
      },
      {
        "q": "Welche Abw\u00e4gung ist korrekt?",
        "options": [
          "W\u00e4hrend kurzfristige Vorteile sichtbar sind, m\u00fcssen langfristige Nebenwirkungen sorgf\u00e4ltig gepr\u00fcft werden.",
          "W\u00e4hrend Vorteile sind sichtbar, m\u00fcssen gepr\u00fcft Nebenwirkungen.",
          "Kurzfristig Vorteile, langfristig Nebenwirkungen.",
          "Obwohl Vorteile sichtbar, Nebenwirkungen m\u00fcssen.",
          "Vorteile sind, aber pr\u00fcfen."
        ],
        "answer": 0,
        "rule": "konzessive Abw\u00e4gung"
      },
      {
        "q": "Welche Folgeformulierung passt?",
        "options": [
          "Dies kann dazu f\u00fchren, dass bestehende Ungleichheiten verst\u00e4rkt werden.",
          "Dies kann machen, dass es schlecht wird.",
          "Dies f\u00fchrt, dass Ungleichheiten.",
          "Dadurch ist es Folge.",
          "Es kommt eine Folge heraus."
        ],
        "answer": 0,
        "rule": "Folgen ausdr\u00fccken"
      },
      {
        "q": "Welche kritische Bewertung ist pr\u00e4zise?",
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
          "Zusammenfassend l\u00e4sst sich festhalten, dass Studium im Ausland nur unter klaren Bedingungen sinnvoll genutzt werden kann.",
          "Am Ende ist Studium im Ausland gut.",
          "Ich bin fertig mit dem Thema.",
          "Alles zusammen ist wichtig.",
          "Das war meine Meinung."
        ],
        "answer": 0,
        "rule": "Schlussfolgerung"
      },
      {
        "q": "Welche Abw\u00e4gung ist korrekt?",
        "options": [
          "W\u00e4hrend kurzfristige Vorteile sichtbar sind, m\u00fcssen langfristige Nebenwirkungen sorgf\u00e4ltig gepr\u00fcft werden.",
          "W\u00e4hrend Vorteile sind sichtbar, m\u00fcssen gepr\u00fcft Nebenwirkungen.",
          "Kurzfristig Vorteile, langfristig Nebenwirkungen.",
          "Obwohl Vorteile sichtbar, Nebenwirkungen m\u00fcssen.",
          "Vorteile sind, aber pr\u00fcfen."
        ],
        "answer": 0,
        "rule": "konzessive Abw\u00e4gung"
      },
      {
        "q": "Welche Folgeformulierung passt?",
        "options": [
          "Dies kann dazu f\u00fchren, dass bestehende Ungleichheiten verst\u00e4rkt werden.",
          "Dies kann machen, dass es schlecht wird.",
          "Dies f\u00fchrt, dass Ungleichheiten.",
          "Dadurch ist es Folge.",
          "Es kommt eine Folge heraus."
        ],
        "answer": 0,
        "rule": "Folgen ausdr\u00fccken"
      },
      {
        "q": "Welche kritische Bewertung ist pr\u00e4zise?",
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
          "Zusammenfassend l\u00e4sst sich festhalten, dass Datenschutz nur unter klaren Bedingungen sinnvoll genutzt werden kann.",
          "Am Ende ist Datenschutz gut.",
          "Ich bin fertig mit dem Thema.",
          "Alles zusammen ist wichtig.",
          "Das war meine Meinung."
        ],
        "answer": 0,
        "rule": "Schlussfolgerung"
      },
      {
        "q": "Welche Abw\u00e4gung ist korrekt?",
        "options": [
          "W\u00e4hrend kurzfristige Vorteile sichtbar sind, m\u00fcssen langfristige Nebenwirkungen sorgf\u00e4ltig gepr\u00fcft werden.",
          "W\u00e4hrend Vorteile sind sichtbar, m\u00fcssen gepr\u00fcft Nebenwirkungen.",
          "Kurzfristig Vorteile, langfristig Nebenwirkungen.",
          "Obwohl Vorteile sichtbar, Nebenwirkungen m\u00fcssen.",
          "Vorteile sind, aber pr\u00fcfen."
        ],
        "answer": 0,
        "rule": "konzessive Abw\u00e4gung"
      },
      {
        "q": "Welche Folgeformulierung passt?",
        "options": [
          "Dies kann dazu f\u00fchren, dass bestehende Ungleichheiten verst\u00e4rkt werden.",
          "Dies kann machen, dass es schlecht wird.",
          "Dies f\u00fchrt, dass Ungleichheiten.",
          "Dadurch ist es Folge.",
          "Es kommt eine Folge heraus."
        ],
        "answer": 0,
        "rule": "Folgen ausdr\u00fccken"
      },
      {
        "q": "Welche kritische Bewertung ist pr\u00e4zise?",
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
          "Zusammenfassend l\u00e4sst sich festhalten, dass Werbung in Medien nur unter klaren Bedingungen sinnvoll genutzt werden kann.",
          "Am Ende ist Werbung in Medien gut.",
          "Ich bin fertig mit dem Thema.",
          "Alles zusammen ist wichtig.",
          "Das war meine Meinung."
        ],
        "answer": 0,
        "rule": "Schlussfolgerung"
      },
      {
        "q": "Welche Abw\u00e4gung ist korrekt?",
        "options": [
          "W\u00e4hrend kurzfristige Vorteile sichtbar sind, m\u00fcssen langfristige Nebenwirkungen sorgf\u00e4ltig gepr\u00fcft werden.",
          "W\u00e4hrend Vorteile sind sichtbar, m\u00fcssen gepr\u00fcft Nebenwirkungen.",
          "Kurzfristig Vorteile, langfristig Nebenwirkungen.",
          "Obwohl Vorteile sichtbar, Nebenwirkungen m\u00fcssen.",
          "Vorteile sind, aber pr\u00fcfen."
        ],
        "answer": 0,
        "rule": "konzessive Abw\u00e4gung"
      }
    ]
  }
];