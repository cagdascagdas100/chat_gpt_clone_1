let letterQuestions = [];
let letterQuestion = null;
let letterTarget = "";
let letterSlots = [];
let letterFilled = [];
let letterTileUse = [];
let letterTileChars = [];
let letterIndex = 0;
let letterScore = 0;

function isLetterChar(ch) {
  return /[A-Za-zÄÖÜäöüß]/.test(ch);
}

function createLetterItems(test) {
  const items = [];
  (test.phraseMatch || []).forEach(pair => {
    items.push({
      prompt: "Ergänzen Sie die C1/C2-Kollokation: „" + pair[0] + " …“",
      target: pair[1],
      full: pair[0] + " " + pair[1],
      type: "Kollokation"
    });
    items.push({
      prompt: "Welche Ergänzung bildet die korrekte feste Verbindung zu „" + pair[0] + "“?",
      target: pair[1],
      full: pair[0] + " " + pair[1],
      type: "Kalıp ifade"
    });
  });
  (test.wordMatch || []).forEach(pair => {
    items.push({
      prompt: "Bedeutung: " + pair[1],
      target: pair[0],
      full: pair[0] + " = " + pair[1],
      type: "C1/C2-Wort"
    });
  });
  (test.prep || []).forEach(pair => {
    const sentence = pair[0].replace("___", "____");
    items.push({
      prompt: "Setzen Sie die passende Präposition ein: " + sentence,
      target: pair[1],
      full: pair[0].replace("___", pair[1]),
      type: "Präposition"
    });
  });
  (test.fill || []).forEach(pair => {
    items.push({
      prompt: "Ergänzen Sie den fachsprachlichen Ausdruck: " + pair[0],
      target: pair[1],
      full: pair[0].replace("____", pair[1]),
      type: pair[2] || "Wortschatz"
    });
  });
  (test.hang || []).forEach(word => {
    items.push({
      prompt: "Schreiben Sie den passenden Begriff aus dem Themenfeld „" + test.topic + "“.",
      target: word,
      full: word,
      type: "Begriff"
    });
  });
  return sh(items).slice(0, 20);
}

function chooseHiddenSlots(text) {
  const slots = [];
  for (let i = 0; i < text.length; i++) {
    if (isLetterChar(text[i])) slots.push(i);
  }
  if (!slots.length) return [];
  const hidden = new Set();
  const minHidden = Math.max(1, Math.ceil(slots.length * 0.55));
  const shuffled = sh(slots);
  for (let i = 0; i < shuffled.length && hidden.size < minHidden; i++) {
    const pos = shuffled[i];
    const prevHidden = hidden.has(pos - 1);
    const nextHidden = hidden.has(pos + 1);
    if (slots.length < 6 || !prevHidden || !nextHidden) hidden.add(pos);
  }
  if (hidden.size < minHidden) {
    shuffled.forEach(pos => hidden.add(pos));
  }
  return [...hidden].sort((a, b) => a - b);
}

function renderLetterPuzzle() {
  const hiddenSet = new Set(letterSlots);
  let board = "";
  for (let i = 0; i < letterTarget.length; i++) {
    const ch = letterTarget[i];
    if (hiddenSet.has(i)) {
      const slotIndex = letterSlots.indexOf(i);
      const val = letterFilled[slotIndex] || "";
      board += '<span class="letterSlot" data-slot="' + slotIndex + '" style="display:inline-grid;place-items:center;min-width:30px;height:36px;margin:3px;border:2px solid #183642;border-radius:8px;background:#fff;font:22px Arial">' + esc(val) + '</span>';
    } else if (ch === " ") {
      board += '<span style="display:inline-block;width:18px"></span>';
    } else {
      board += '<span style="display:inline-grid;place-items:center;min-width:28px;height:36px;margin:3px;border:1px solid #d6d0c5;border-radius:8px;background:#f1eee7;font:22px Arial">' + esc(ch) + '</span>';
    }
  }
  $("hm").innerHTML = board;
  const tiles = letterTileChars.map((ch, i) => {
    const used = letterTileUse[i];
    return '<button class="letterTile ' + (used ? 'ghost' : '') + '" data-tile="' + i + '" ' + (used ? 'disabled' : '') + ' style="min-width:38px;margin:4px">' + esc(ch) + '</button>';
  }).join("");
  $("hr").innerHTML = '<div style="margin:12px 0">' + tiles + '</div><p><button id="letterBack" class="ghost">Zurück</button><button id="letterClear" class="ghost">Leeren</button></p><div id="letterMsg"></div>';
  document.querySelectorAll("[data-tile]").forEach(btn => btn.onclick = () => useTile(Number(btn.dataset.tile)));
  $("letterBack").onclick = undoLetter;
  $("letterClear").onclick = clearLetters;
}

function firstEmptySlot() {
  for (let i = 0; i < letterFilled.length; i++) {
    if (!letterFilled[i]) return i;
  }
  return -1;
}

function useTile(tileIndex) {
  if (letterTileUse[tileIndex]) return;
  const slotIndex = firstEmptySlot();
  if (slotIndex < 0) return;
  letterFilled[slotIndex] = letterTileChars[tileIndex];
  letterTileUse[tileIndex] = true;
  renderLetterPuzzle();
}

function undoLetter() {
  for (let i = letterFilled.length - 1; i >= 0; i--) {
    if (letterFilled[i]) {
      const ch = letterFilled[i];
      const tileIndex = letterTileChars.findIndex((c, idx) => c === ch && letterTileUse[idx]);
      if (tileIndex >= 0) letterTileUse[tileIndex] = false;
      letterFilled[i] = "";
      renderLetterPuzzle();
      return;
    }
  }
}

function clearLetters() {
  letterFilled = letterFilled.map(() => "");
  letterTileUse = letterTileUse.map(() => false);
  renderLetterPuzzle();
}

function startHangman() {
  const test = window.DEUTSCH_TESTS[selected];
  letterQuestions = createLetterItems(test);
  letterIndex = 0;
  letterScore = 0;
  hide();
  $("hang").classList.remove("hide");
  $("ht").textContent = "Harf kutucukları: " + test.title;
  showHang();
}

function showHang() {
  letterQuestion = letterQuestions[letterIndex];
  letterTarget = letterQuestion ? letterQuestion.target : "";
  letterSlots = chooseHiddenSlots(letterTarget);
  letterFilled = letterSlots.map(() => "");
  letterTileChars = sh(letterSlots.map(i => letterTarget[i]));
  letterTileUse = letterTileChars.map(() => false);
  $("hh").innerHTML = '<b>' + (letterIndex + 1) + '/20 · ' + esc(letterQuestion.type) + '</b><br>' + esc(letterQuestion.prompt) + '<br><span class="muted">Eksik harfleri alttaki kutucuklardan soldan sağa doğru yerleştir.</span>';
  $("hi").style.display = "none";
  renderLetterPuzzle();
}

function checkHang() {
  const missing = letterFilled.some(x => !x);
  const msg = $("letterMsg") || $("hr");
  if (missing) {
    msg.innerHTML = '<p class="dberr"><b>Eksik harf var.</b></p>';
    return;
  }
  let ok = true;
  for (let i = 0; i < letterSlots.length; i++) {
    if (letterFilled[i] !== letterTarget[letterSlots[i]]) ok = false;
  }
  if (ok) {
    letterScore++;
    msg.innerHTML = '<p class="dbok"><b>Richtig.</b> Vollständige Form: <b>' + esc(letterQuestion.full) + '</b></p>';
  } else {
    document.querySelectorAll("[data-slot]").forEach(el => {
      const idx = Number(el.dataset.slot);
      if (letterFilled[idx] !== letterTarget[letterSlots[idx]]) el.style.background = "#fff1f2";
    });
    msg.innerHTML = '<p class="dberr"><b>Yanlış var.</b> Richtig: <b>' + esc(letterTarget) + '</b><br>Vollständige Form: <b>' + esc(letterQuestion.full) + '</b></p>';
  }
}

function nextHang() {
  if (letterIndex < letterQuestions.length - 1) {
    letterIndex++;
    showHang();
  } else {
    $("hr").innerHTML = '<p><b>Fertig: ' + letterScore + '/' + letterQuestions.length + '</b></p><button id="hangRestart">Yeni 20 soru oluştur</button>';
    $("hangRestart").onclick = startHangman;
  }
}
