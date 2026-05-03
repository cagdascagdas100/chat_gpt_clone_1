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
  hide();
  document.getElementById("lesson").classList.remove("hide");
  document.getElementById("lessonTitle").textContent = "Konu anlatımı: " + (test ? test.title : key);
  document.getElementById("lessonMeta").textContent = "Seviye: " + (level === "short" ? "Kısa" : level === "medium" ? "Orta" : "Uzun") + " · Teste özel kelime ve kalıp çalışması";
  document.getElementById("lessonContent").innerHTML = lesson[level];
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
