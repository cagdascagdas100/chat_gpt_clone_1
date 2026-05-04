function lessonExamplesKey() {
  try {
    return typeof selected !== "undefined" ? selected : "t4";
  } catch (e) {
    return "t4";
  }
}

function fillExampleText(item) {
  if (!item || !item[0]) return "";
  return String(item[0]).replace("____", "<b>" + esc(item[1] || "") + "</b>");
}

function plainTextFromHtml(s) {
  return String(s || "").replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim();
}

function collectGeneratedExamples(test) {
  const examples = [];
  const add = function (html, label) {
    const text = plainTextFromHtml(html);
    if (!text || text.length < 18) return;
    if (examples.some(x => plainTextFromHtml(x.html) === text)) return;
    examples.push({ html: html, label: label });
  };

  (test.fill || []).forEach(x => add(fillExampleText(x), "Lückensatz im Kontext"));
  (test.mc || []).forEach(x => {
    const correct = x && x[1] ? x[1][x[2]] : "";
    add(esc(correct), "Prüfungsnaher C1/C2-Satz");
  });
  (test.tf || []).forEach(x => {
    if (x && x[1] === true) add(esc(x[0]), "Richtige Aussage als Merksatz");
  });
  (test.prep || []).forEach(x => {
    if (x && x[0]) add(String(x[0]).replace("___", "<b>" + esc(x[1] || "") + "</b>"), "Präposition im Kontext");
  });
  (test.phraseMatch || []).forEach(x => {
    if (!x || !x[0] || !x[1]) return;
    const full = String(x[0] + " " + x[1]).replace(/\s+/g, " ").trim();
    add("<b>" + esc(full) + "</b> ist eine zentrale C1/C2-Kollokation, die in argumentativen Texten idiomatisch verwendet werden kann.", "Kollokation" );
    add("In einer differenzierten Argumentation lässt sich die Struktur <b>" + esc(full) + "</b> verwenden, um den Zusammenhang präziser und weniger alltagssprachlich darzustellen.", "Akademische Anwendung" );
  });
  (test.wordMatch || []).forEach(x => {
    if (!x || !x[0] || !x[1]) return;
    add("Der Ausdruck <b>" + esc(x[0]) + "</b> bezeichnet " + esc(x[1]) + ".", "Begriffserklärung" );
    add("Wer den Begriff <b>" + esc(x[0]) + "</b> verwendet, sollte ihn nicht isoliert nennen, sondern mit einer präzisen Begründung oder einem konkreten Beispiel verbinden.", "Stilhinweis" );
  });
  (test.hang || []).forEach(x => {
    add("Die Wendung <b>" + esc(x) + "</b> eignet sich als aktiver Baustein für gehobene schriftliche und mündliche Argumentation.", "Aktiver Baustein" );
  });
  return examples;
}

function collectWritingPatterns(test) {
  const phrases = (test.phraseMatch || []).map(x => String((x[0] || "") + " " + (x[1] || "")).replace(/\s+/g, " ").trim()).filter(Boolean);
  const words = (test.words || []).slice(0, 18);
  const fills = (test.fill || []).slice(0, 8).map(fillExampleText).map(plainTextFromHtml);
  const patterns = [];
  const add = (s) => { if (s && !patterns.includes(s)) patterns.push(s); };

  phrases.slice(0, 12).forEach(p => {
    add("Ein besonders tragfähiger Ausdruck in diesem Themenfeld ist <b>" + esc(p) + "</b>, weil er eine präzise und idiomatische Verbindung von Inhalt und Struktur ermöglicht.");
    add("Statt eine allgemeine Formulierung zu verwenden, kann man schreiben: <b>" + esc(p) + "</b>; dadurch wirkt die Aussage fachsprachlicher und argumentativ kontrollierter.");
  });
  words.slice(0, 10).forEach(w => {
    add("Der Begriff <b>" + esc(w) + "</b> sollte in C1/C2-Texten mit Ursache, Folge, Beispiel oder Bewertung verbunden werden, damit die Aussage nicht bloß aufzählend wirkt.");
  });
  fills.forEach(s => add("Als vollständiger Beispielsatz eignet sich: <b>" + esc(s) + "</b>"));
  return patterns;
}

function collectMiniParagraphs(test) {
  const title = test.title || "das Thema";
  const phrases = (test.phraseMatch || []).map(x => String((x[0] || "") + " " + (x[1] || "")).replace(/\s+/g, " ").trim()).filter(Boolean);
  const words = test.words || [];
  const p1 = phrases[0] || words[0] || "eine zentrale Struktur";
  const p2 = phrases[1] || words[1] || "ein weiterer Aspekt";
  const p3 = phrases[2] || words[2] || "eine differenzierte Betrachtung";
  return [
    "Im Themenfeld <b>" + esc(title) + "</b> ist entscheidend, nicht nur einzelne Wörter zu kennen, sondern sie in argumentativ tragfähige Satzstrukturen einzubetten. Eine Formulierung wie <b>" + esc(p1) + "</b> zeigt, dass Wortschatz, Grammatik und inhaltliche Präzision zusammenwirken müssen.",
    "Eine differenzierte Darstellung sollte Ursache, Wirkung und Bewertung miteinander verbinden. Dabei kann die Struktur <b>" + esc(p2) + "</b> helfen, weil sie eine konkrete Beziehung zwischen zwei Aspekten herstellt und den Text kohärenter wirken lässt.",
    "Für einen C1/C2-Text reicht es nicht aus, eine Meinung zu äußern. Vielmehr sollte man mit Formulierungen wie <b>" + esc(p3) + "</b> zeigen, dass man Zusammenhänge erkennt, abwägt und sprachlich präzise darstellen kann.",
    "Besonders überzeugend wirkt ein Text, wenn zentrale Begriffe nicht additiv aufgelistet, sondern funktional eingesetzt werden. Das bedeutet, dass Begriffe wie <b>" + esc((words[0] || title)) + "</b> durch Beispiele, Kontraste und Schlussfolgerungen erläutert werden sollten.",
    "In mündlichen Prüfungen kann dieselbe Struktur genutzt werden, um spontan präziser zu sprechen. Wer aktiv mit Wendungen wie <b>" + esc(p1) + "</b> arbeitet, vermeidet einfache Alltagssprache und gewinnt an Ausdruckssicherheit."
  ];
}

function appendGeneratedLessonExamples(level) {
  const key = lessonExamplesKey();
  const test = (window.DEUTSCH_TESTS || {})[key];
  const content = document.getElementById("lessonContent");
  if (!test || !content) return;
  const examples = collectGeneratedExamples(test);
  const limit = level === "short" ? 20 : level === "medium" ? 50 : 120;
  const phraseLimit = level === "short" ? 12 : level === "medium" ? 25 : 60;
  const prepLimit = level === "short" ? 10 : level === "medium" ? 22 : 50;
  const patternLimit = level === "short" ? 8 : level === "medium" ? 18 : 40;
  const paragraphLimit = level === "short" ? 1 : level === "medium" ? 3 : 5;

  const rows = examples.slice(0, limit).map((ex) => {
    return "<li><span class='pill'>" + esc(ex.label) + "</span> " + ex.html + "</li>";
  }).join("");
  const phraseRows = (test.phraseMatch || []).slice(0, phraseLimit).map(x => {
    return "<tr><td><b>" + esc(x[0]) + "</b></td><td>" + esc(x[1]) + "</td></tr>";
  }).join("");
  const prepRows = (test.prep || []).slice(0, prepLimit).map(x => {
    return "<li>" + String(x[0]).replace("___", "<b>" + esc(x[1]) + "</b>") + " <span class='muted'>[" + esc(x[2] || "Präposition") + "]</span></li>";
  }).join("");
  const patterns = collectWritingPatterns(test).slice(0, patternLimit).map(s => "<li>" + s + "</li>").join("");
  const paragraphs = collectMiniParagraphs(test).slice(0, paragraphLimit).map(s => "<p>" + s + "</p>").join("");

  content.innerHTML += "<section style='margin-top:24px;padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fffdf9'>" +
    "<h3>Erweiterte C1/C2-Beispielsätze</h3>" +
    "<p>Diese zusätzlichen Sätze stammen direkt aus dem gewählten Themenfeld. Sie zeigen die Wörter, Kollokationen und grammatischen Strukturen in anspruchsvollen Kontexten.</p>" +
    "<ol>" + rows + "</ol>" +
    "<h3>Musterformulierungen für Schreiben und Sprechen</h3>" +
    "<ol>" + patterns + "</ol>" +
    "<h3>C1/C2-Mini-Absätze</h3>" + paragraphs +
    "<h3>Aktive Kollokationsliste</h3>" +
    "<table style='width:100%;border-collapse:collapse'><tbody>" + phraseRows + "</tbody></table>" +
    "<h3>Präpositionen im Kontext</h3>" +
    "<ol>" + prepRows + "</ol>" +
    "</section>";
}

document.addEventListener("DOMContentLoaded", function () {
  const b1 = document.getElementById("btnLessonShort");
  const b2 = document.getElementById("btnLessonMedium");
  const b3 = document.getElementById("btnLessonLong");
  if (b1) b1.onclick = function () { startLesson("short"); appendGeneratedLessonExamples("short"); };
  if (b2) b2.onclick = function () { startLesson("medium"); appendGeneratedLessonExamples("medium"); };
  if (b3) b3.onclick = function () { startLesson("long"); appendGeneratedLessonExamples("long"); };
});
