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

function uniquePush(arr, item) {
  const key = plainTextFromHtml(item.html || item);
  if (!key || key.length < 12) return;
  if (!arr.some(x => plainTextFromHtml(x.html || x) === key)) arr.push(item);
}

function collectGeneratedExamples(test) {
  const examples = [];
  const add = function (html, label) {
    uniquePush(examples, { html: html, label: label });
  };

  (test.fill || []).forEach(x => add(fillExampleText(x), "Satz mit Zielform"));
  (test.mc || []).forEach(x => {
    const correct = x && x[1] ? x[1][x[2]] : "";
    add(esc(correct), "Prüfungsnaher C1/C2-Satz");
  });
  (test.tf || []).forEach(x => {
    if (x && x[1] === true) add(esc(x[0]), "Merksatz");
  });
  (test.prep || []).forEach(x => {
    if (x && x[0]) add(String(x[0]).replace("___", "<b>" + esc(x[1] || "") + "</b>"), "Rektion/Kasus im Kontext");
  });
  (test.phraseMatch || []).forEach(x => {
    if (!x || !x[0] || !x[1]) return;
    const full = String(x[0] + " " + x[1]).replace(/\s+/g, " ").trim();
    add("<b>" + esc(full) + "</b> ist eine zentrale C1/C2-Kollokation, die als vollständiger Baustein gelernt werden sollte.", "Kollokationsbaustein");
    add("In einem argumentativen Text kann <b>" + esc(full) + "</b> verwendet werden, um eine Aussage präziser, fachsprachlicher und weniger alltagssprachlich zu formulieren.", "Anwendung im Text");
  });
  (test.wordMatch || []).forEach(x => {
    if (!x || !x[0] || !x[1]) return;
    add("Der Ausdruck <b>" + esc(x[0]) + "</b> bezeichnet " + esc(x[1]) + ".", "Begriff + Bedeutung");
    add("Der Begriff <b>" + esc(x[0]) + "</b> sollte in C1/C2-Texten nicht isoliert stehen, sondern durch Ursache, Folge, Beispiel oder Bewertung eingebettet werden.", "Schreibregel");
  });
  (test.hang || []).forEach(x => {
    add("Die Wendung <b>" + esc(x) + "</b> eignet sich als aktiver Baustein für gehobene schriftliche und mündliche Argumentation.", "Aktiver Baustein");
  });
  return examples;
}

function collectCoreChunks(test, limit) {
  const chunks = [];
  (test.phraseMatch || []).forEach(x => {
    if (x && x[0] && x[1]) uniquePush(chunks, { html: "<b>" + esc(String(x[0] + " " + x[1]).replace(/\s+/g, " ").trim()) + "</b>", label: "Kollokation" });
  });
  (test.prep || []).forEach(x => {
    if (x && x[0]) uniquePush(chunks, { html: String(x[0]).replace("___", "<b>" + esc(x[1]) + "</b>"), label: x[2] || "Präposition" });
  });
  (test.hang || []).forEach(x => uniquePush(chunks, { html: "<b>" + esc(x) + "</b>", label: "Auswendig lernen" }));
  return chunks.slice(0, limit);
}

function collectWritingPatterns(test) {
  const phrases = (test.phraseMatch || []).map(x => String((x[0] || "") + " " + (x[1] || "")).replace(/\s+/g, " ").trim()).filter(Boolean);
  const words = (test.words || []).slice(0, 18);
  const fills = (test.fill || []).slice(0, 10).map(fillExampleText).map(plainTextFromHtml);
  const patterns = [];
  const add = (s) => { if (s && !patterns.includes(s)) patterns.push(s); };

  phrases.slice(0, 18).forEach(p => {
    add("<b>" + esc(p) + "</b> nicht als Einzelwort lernen, sondern als vollständige Kollokation mit typischem Kontext memorisieren.");
    add("C1/C2-Schreibbaustein: <b>" + esc(p) + "</b> + Begründung / Beispiel / Folge.");
  });
  words.slice(0, 12).forEach(w => {
    add("Der Begriff <b>" + esc(w) + "</b> sollte in einem Text mit einem präzisen Verb verbunden werden, damit die Aussage nicht nominal und statisch wirkt.");
  });
  fills.forEach(s => add("Mustersatz mit korrekter Grammatik: <b>" + esc(s) + "</b>"));
  return patterns;
}

function collectGrammarFocus(test, limit) {
  const rows = [];
  const add = (left, right, note) => {
    if (!left || !right) return;
    rows.push("<tr><td><b>" + esc(left) + "</b></td><td>" + esc(right) + "</td><td class='muted'>" + esc(note || "merken") + "</td></tr>");
  };
  (test.prep || []).forEach(x => {
    const sentence = plainTextFromHtml(String(x[0] || "").replace("___", x[1] || ""));
    add(x[1] || "", sentence, x[2] || "Präposition/Kasus");
  });
  (test.phraseMatch || []).forEach(x => add(x[0], x[1], "feste Verbindung"));
  return rows.slice(0, limit).join("");
}

function collectMiniParagraphs(test) {
  const title = test.title || "das Thema";
  const phrases = (test.phraseMatch || []).map(x => String((x[0] || "") + " " + (x[1] || "")).replace(/\s+/g, " ").trim()).filter(Boolean);
  const words = test.words || [];
  const p1 = phrases[0] || words[0] || "eine zentrale Struktur";
  const p2 = phrases[1] || words[1] || "ein weiterer Aspekt";
  const p3 = phrases[2] || words[2] || "eine differenzierte Betrachtung";
  const p4 = phrases[3] || words[3] || "eine präzise Formulierung";
  return [
    "Im Themenfeld <b>" + esc(title) + "</b> ist entscheidend, nicht nur einzelne Wörter zu kennen, sondern sie in argumentativ tragfähige Satzstrukturen einzubetten. Eine Formulierung wie <b>" + esc(p1) + "</b> zeigt, dass Wortschatz, Grammatik und inhaltliche Präzision zusammenwirken müssen.",
    "Eine differenzierte Darstellung sollte Ursache, Wirkung und Bewertung miteinander verbinden. Dabei kann die Struktur <b>" + esc(p2) + "</b> helfen, weil sie eine konkrete Beziehung zwischen zwei Aspekten herstellt und den Text kohärenter wirken lässt.",
    "Für einen C1/C2-Text reicht es nicht aus, eine Meinung zu äußern. Vielmehr sollte man mit Formulierungen wie <b>" + esc(p3) + "</b> zeigen, dass man Zusammenhänge erkennt, abwägt und sprachlich präzise darstellen kann.",
    "Besonders überzeugend wirkt ein Text, wenn zentrale Begriffe nicht additiv aufgelistet, sondern funktional eingesetzt werden. Das bedeutet, dass Begriffe wie <b>" + esc((words[0] || title)) + "</b> durch Beispiele, Kontraste und Schlussfolgerungen erläutert werden sollten.",
    "In mündlichen Prüfungen kann dieselbe Struktur genutzt werden, um spontan präziser zu sprechen. Wer aktiv mit Wendungen wie <b>" + esc(p1) + "</b> arbeitet, vermeidet einfache Alltagssprache und gewinnt an Ausdruckssicherheit.",
    "Ein vollständiger Prüfungsabschnitt sollte mindestens drei Ebenen enthalten: erstens den Begriff, zweitens die korrekte grammatische Verbindung und drittens eine argumentative Funktion. Dafür eignet sich besonders <b>" + esc(p4) + "</b>."
  ];
}

function buildLessonWorkflow(test, level) {
  const coreLimit = level === "short" ? 10 : level === "medium" ? 22 : 45;
  const grammarLimit = level === "short" ? 10 : level === "medium" ? 24 : 55;
  const chunkRows = collectCoreChunks(test, coreLimit).map((x, i) => "<li><span class='pill'>" + esc(x.label) + "</span> " + x.html + "</li>").join("");
  const grammarRows = collectGrammarFocus(test, grammarLimit);
  return "<section style='margin-top:24px;padding:14px;border:2px solid #183642;border-radius:14px;background:#ffffff'>" +
    "<h2>Strukturierter Lernplan: Kalıp ezberleme + korrektes Schreiben</h2>" +
    "<h3>1. Lernziel</h3>" +
    "<p>In diesem Abschnitt lernst du die wichtigsten Wörter nicht isoliert, sondern als <b>grammatisch vollständige Schreibbausteine</b>. Ziel ist, die Strukturen aktiv in C1/C2-Texten verwenden zu können.</p>" +
    "<h3>2. Schlüsselbausteine zum Auswendiglernen</h3>" +
    "<ol>" + chunkRows + "</ol>" +
    "<h3>3. Grammatik- und Rektionstabelle</h3>" +
    "<p>Diese Tabelle zeigt, welche Präposition, welcher Kasus oder welche feste Ergänzung mitgelernt werden muss.</p>" +
    "<table style='width:100%;border-collapse:collapse'><thead><tr><th style='text-align:left'>Form</th><th style='text-align:left'>Kontext</th><th style='text-align:left'>Fokus</th></tr></thead><tbody>" + grammarRows + "</tbody></table>" +
    "<h3>4. Schreibregel</h3>" +
    "<p>Verwende jede neue Struktur in dieser Reihenfolge: <b>Begriff/Kollokation → korrektes Verb/Präposition → Ursache/Folge → Beispiel oder Bewertung</b>. Dadurch entsteht ein zusammenhängender Text statt einer bloßen Wortliste.</p>" +
    "</section>";
}

function appendGeneratedLessonExamples(level) {
  const key = lessonExamplesKey();
  const test = (window.DEUTSCH_TESTS || {})[key];
  const content = document.getElementById("lessonContent");
  if (!test || !content) return;
  const examples = collectGeneratedExamples(test);
  const limit = level === "short" ? 20 : level === "medium" ? 50 : 120;
  const patternLimit = level === "short" ? 10 : level === "medium" ? 24 : 55;
  const paragraphLimit = level === "short" ? 2 : level === "medium" ? 4 : 6;

  const rows = examples.slice(0, limit).map((ex) => {
    return "<li><span class='pill'>" + esc(ex.label) + "</span> " + ex.html + "</li>";
  }).join("");
  const patterns = collectWritingPatterns(test).slice(0, patternLimit).map(s => "<li>" + s + "</li>").join("");
  const paragraphs = collectMiniParagraphs(test).slice(0, paragraphLimit).map((s, i) => "<div style='padding:10px;margin:10px 0;border-left:4px solid #8a5a44;background:#fcfbf8'><b>Musterabsatz " + (i + 1) + ":</b><p>" + s + "</p></div>").join("");

  content.innerHTML += buildLessonWorkflow(test, level) +
    "<section style='margin-top:24px;padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fffdf9'>" +
    "<h2>Vertiefung: Beispiele, Schreibbausteine und Mini-Texte</h2>" +
    "<h3>5. C1/C2-Beispielsätze mit Zielstrukturen</h3>" +
    "<p>Diese Sätze zeigen, wie die Zielwörter und festen Verbindungen in anspruchsvollen Kontexten verwendet werden.</p>" +
    "<ol>" + rows + "</ol>" +
    "<h3>6. Musterformulierungen für Schreiben und Sprechen</h3>" +
    "<ol>" + patterns + "</ol>" +
    "<h3>7. C1/C2-Mini-Absätze</h3>" + paragraphs +
    "<h3>8. Typische Fehler vermeiden</h3>" +
    "<ul><li>Lerne keine Nomen ohne Artikel und keine Verben ohne Präposition.</li><li>Ersetze <i>machen</i>, <i>sein</i> und <i>haben</i> möglichst durch präzisere Verben.</li><li>Prüfe nach jeder Präposition den Kasus.</li><li>Nutze Kollokationen als komplette Textbausteine, nicht als lose Wörter.</li></ul>" +
    "<h3>9. Aktive Wiederholung</h3>" +
    "<p>Wähle fünf Strukturen aus diesem Abschnitt und schreibe damit einen eigenen argumentativen Absatz. Achte auf Verbform, Präposition, Kasus und Satzstellung.</p>" +
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
