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
  const exampleCount = level === "short" ? "kompakt" : level === "medium" ? "genişletilmiş" : "çok kapsamlı";
  const title = test ? test.title : key;
  const topic = test && test.topic ? test.topic : "C1/C2 Wortschatz und Grammatik";
  const wordPreview = (test && test.words ? test.words.slice(0, level === "short" ? 8 : level === "medium" ? 14 : 24) : [])
    .map(w => "<span class='pill'>" + esc(w) + "</span>").join(" ");

  hide();
  document.getElementById("lesson").classList.remove("hide");
  document.getElementById("lessonTitle").textContent = "Konu anlatımı: " + title;
  document.getElementById("lessonMeta").textContent = "Seviye: " + levelName + " · Amaç: Kalıpları ezberlemek, doğru Rektion/Kasus ile C1/C2 metin yazmak";

  document.getElementById("lessonContent").innerHTML = `
    <section style="padding:14px;border:2px solid #183642;border-radius:14px;background:#fffdf9;margin-bottom:18px">
      <h2>Didaktischer Aufbau: Redemittel → Grammatik → Textproduktion</h2>
      <p><b>Thema:</b> ${esc(topic)}</p>
      <p>Bu konu anlatımı, kelimeleri sadece anlam olarak vermek için değil, onları <b>doğru Präposition, doğru Kasus, doğru Verbform ve C1/C2 yazma bağlamı</b> içinde aktif kullanabilmen için düzenlendi.</p>
      <h3>1. Lernziel</h3>
      <p>Bu dersten sonra seçilen temadaki temel <b>Kollokationen</b>, <b>feste Verbindungen</b> ve <b>akademische Satzbausteine</b> ile kısa ama doğru Almanca paragraflar kurabilmen hedeflenir.</p>
      <h3>2. Çalışma sırası</h3>
      <ol>
        <li><b>Begriff verstehen:</b> Kelimenin Almanca anlamını ve bağlamını öğren.</li>
        <li><b>Kollokation memorisieren:</b> Kelimeyi tek başına değil, birlikte kullanıldığı fiil ve Präposition ile ezberle.</li>
        <li><b>Rektion/Kasus prüfen:</b> Hangi Präposition hangi Kasus ile geliyor, bunu kontrol et.</li>
        <li><b>Satz bilden:</b> Kalıbı tam cümlede kullan.</li>
        <li><b>Mini-Absatz schreiben:</b> Cümleyi neden-sonuç, örnek veya değerlendirme ile paragrafa dönüştür.</li>
      </ol>
      <h3>3. Kullanılacak yazma formülü</h3>
      <p><b>Begriff/Kollokation → korrektes Verb → Präposition/Kasus → Ursache oder Folge → Beispiel oder Bewertung</b></p>
      <p>Örnek yapı: <i>Diese Entwicklung kann … beeinflussen, weil … . Dadurch wird deutlich, dass … .</i></p>
      <h3>4. Öncelikli kelime ve kavramlar</h3>
      <div>${wordPreview}</div>
    </section>

    <section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#ffffff;margin-bottom:18px">
      <h2>A. Themenüberblick und zentrale Erklärungen</h2>
      <p>Bu bölüm temanın ana mantığını açıklar. Ardından gelen bölümlerde aynı kelimeler kalıp, gramer ve metin yazma odağıyla tekrar işlenir.</p>
      ${lesson[level]}
    </section>

    <section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fcfbf8;margin-bottom:18px">
      <h2>B. Lernfokus dieses Moduls</h2>
      <ul>
        <li><b>Ezberlenecek şey:</b> tek tek kelime değil, tam kalıp ve fiil bağlantısı.</li>
        <li><b>Gramer odağı:</b> Präposition, Kasus, Artikel, Verbform ve Nebensatzstellung.</li>
        <li><b>Yazma odağı:</b> C1/C2 düzeyinde neden-sonuç, karşılaştırma, örnek ve değerlendirme cümleleri.</li>
        <li><b>Uygulama:</b> Her kalıp en az bir tam cümlede ve bir mini paragrafta görülür.</li>
        <li><b>Kapsam:</b> Bu seviyede ${exampleCount} örnek ve kalıp bağlamı gösterilir.</li>
      </ul>
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
