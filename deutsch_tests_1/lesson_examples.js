function lessonExamplesKey() {
  try {
    return typeof selected !== "undefined" ? selected : "t4";
  } catch (e) {
    return "t4";
  }
}

function fillExampleText(item) {
  if (!item || !item[0]) return "";
  const sentence = String(item[0]).replace("____", "<b>" + esc(item[1] || "") + "</b>");
  return sentence;
}

function plainTextFromHtml(s) {
  return String(s || "").replace(/<[^>]*>/g, "");
}

function collectGeneratedExamples(test) {
  const examples = [];
  const add = function (html, label) {
    const text = plainTextFromHtml(html).replace(/\s+/g, " ").trim();
    if (!text || text.length < 18) return;
    if (examples.some(x => plainTextFromHtml(x.html) === text)) return;
    examples.push({ html: html, label: label });
  };

  (test.fill || []).forEach(x => add(fillExampleText(x), "Lückensatz"));
  (test.mc || []).forEach(x => {
    const correct = x && x[1] ? x[1][x[2]] : "";
    add(esc(correct), "Prüfungsnaher Satz");
  });
  (test.tf || []).forEach(x => {
    if (x && x[1] === true) add(esc(x[0]), "Richtige Aussage");
  });
  (test.prep || []).forEach(x => {
    if (x && x[0]) add(String(x[0]).replace("___", "<b>" + esc(x[1] || "") + "</b>"), "Präposition im Kontext");
  });
  (test.phraseMatch || []).forEach(x => {
    if (!x || !x[0] || !x[1]) return;
    add("<b>" + esc(x[0] + " " + x[1]) + "</b> ist eine zentrale C1/C2-Kollokation, die in argumentativen Texten idiomatisch verwendet werden kann.", "Kollokation");
  });
  (test.wordMatch || []).forEach(x => {
    if (!x || !x[0] || !x[1]) return;
    add("Der Ausdruck <b>" + esc(x[0]) + "</b> bezeichnet " + esc(x[1]) + ".", "Begriffserklärung");
  });
  return examples;
}

function appendGeneratedLessonExamples(level) {
  const key = lessonExamplesKey();
  const test = (window.DEUTSCH_TESTS || {})[key];
  const content = document.getElementById("lessonContent");
  if (!test || !content) return;
  const examples = collectGeneratedExamples(test);
  const limit = level === "short" ? 12 : level === "medium" ? 28 : 60;
  const selectedExamples = examples.slice(0, limit);
  const rows = selectedExamples.map((ex, i) => {
    return "<li><span class='pill'>" + esc(ex.label) + "</span> " + ex.html + "</li>";
  }).join("");
  const phraseRows = (test.phraseMatch || []).slice(0, level === "short" ? 8 : level === "medium" ? 16 : 30).map(x => {
    return "<tr><td><b>" + esc(x[0]) + "</b></td><td>" + esc(x[1]) + "</td></tr>";
  }).join("");
  const prepRows = (test.prep || []).slice(0, level === "short" ? 6 : level === "medium" ? 12 : 25).map(x => {
    return "<li>" + String(x[0]).replace("___", "<b>" + esc(x[1]) + "</b>") + " <span class='muted'>[" + esc(x[2] || "Präposition") + "]</span></li>";
  }).join("");

  content.innerHTML += "<section style='margin-top:24px;padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fffdf9'>" +
    "<h3>Erweiterte C1/C2-Beispielsätze</h3>" +
    "<p>Diese zusätzlichen Sätze stammen direkt aus dem gewählten Themenfeld. Sie zeigen die Wörter, Kollokationen und grammatischen Strukturen in anspruchsvollen Kontexten.</p>" +
    "<ol>" + rows + "</ol>" +
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
