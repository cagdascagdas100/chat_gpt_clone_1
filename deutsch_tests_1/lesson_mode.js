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
  const terms = (test && test.words ? test.words.slice(0, level === "short" ? 5 : level === "medium" ? 10 : 16) : []);
  const termList = terms.length ? "<ul>" + terms.map(w => "<li>" + esc(w) + "</li>").join("") + "</ul>" : "";

  hide();
  document.getElementById("lesson").classList.remove("hide");
  document.getElementById("lessonTitle").textContent = "Konu anlatımı: " + title;
  document.getElementById("lessonMeta").textContent = "Seviye: " + levelName + " · Kalıp ezberleme ve doğru gramerle metin yazma";

  document.getElementById("lessonContent").innerHTML = `
    <section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#ffffff;margin-bottom:18px">
      <h2>1. Genel bakış</h2>
      <p><b>Thema:</b> ${esc(topic)}</p>
      <p>Bu bölümde kelimeler tek tek değil, yazıda kullanılabilecek tam yapılar olarak çalışılır: <b>kalıp + doğru fiil + Präposition/Kasus + örnek cümle</b>.</p>
      <p><b>Yazma sırası:</b> Kalıp → doğru gramer → neden/sonuç → örnek veya kısa değerlendirme.</p>
      ${termList ? `<h3>Öncelikli kavramlar</h3>${termList}` : ""}
    </section>

    <section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#ffffff;margin-bottom:18px">
      <h2>2. Konu açıklaması</h2>
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
