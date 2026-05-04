function startLesson(level) {
  const lessons = window.DEUTSCH_LESSONS || {};
  const tests = window.DEUTSCH_TESTS || {};
  const key = selected || "t4";
  const lesson = lessons[key];
  const test = tests[key];
  if (!lesson || !lesson[level]) {
    alert("Bu test için konu anlatımı bulunamadı.");
    return;
  }

  const levelName = level === "short" ? "Kısa" : level === "medium" ? "Orta" : "Uzun";
  const title = test ? test.title : key;
  const topic = test && test.topic ? test.topic : "C1/C2 Wortschatz und Grammatik";
  const terms = (test && test.words ? test.words.slice(0, level === "short" ? 6 : level === "medium" ? 12 : 18) : [])
    .map(w => "<span class='pill'>" + esc(w) + "</span>").join(" ");

  hide();
  document.getElementById("lesson").classList.remove("hide");
  document.getElementById("lessonTitle").textContent = "Konu anlatımı: " + title;
  document.getElementById("lessonMeta").textContent = "Seviye: " + levelName + " · Amaç: kalıp ezberleme ve doğru gramerle C1/C2 metin yazma";

  document.getElementById("lessonContent").innerHTML = `
    <section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fffdf9;margin-bottom:18px">
      <h2>1. Überblick</h2>
      <p><b>Thema:</b> ${esc(topic)}</p>
      <p>Bu bölümde amaç kelimeleri tek tek ezberlemek değil; her kelimeyi <b>fiil bağlantısı, Präposition, Kasus ve örnek metin</b> içinde öğrenmektir. Böylece kalıp doğrudan yazma ve konuşmada kullanılabilir hale gelir.</p>
      <p><b>Yazma formülü:</b> Begriff/Kollokation → korrektes Verb → Präposition/Kasus → Ursache/Folge → Beispiel/Bewertung.</p>
      ${terms ? `<p><b>Öncelikli kavramlar:</b><br>${terms}</p>` : ""}
    </section>

    <section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#ffffff;margin-bottom:18px">
      <h2>2. Temel açıklama</h2>
      ${lesson[level]}
    </section>
  `;

  document.getElementById("lesson").scrollIntoView({ behavior: "smooth" });
}

document.addEventListener("DOMContentLoaded", function () {
  const shortBtn = document.getElementById("btnLessonShort");
  const mediumBtn = document.getElementById("btnLessonMedium");
  const longBtn = document.getElementById("btnLessonLong");
  const backBtn = document.getElementById("btnLessonBack");
  if (shortBtn) shortBtn.onclick = function () { startLesson("short"); };
  if (mediumBtn) mediumBtn.onclick = function () { startLesson("medium"); };
  if (longBtn) longBtn.onclick = function () { startLesson("long"); };
  if (backBtn) backBtn.onclick = menu;
});
