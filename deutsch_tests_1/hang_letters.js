let letterTarget = "";
let letterSlots = [];
let letterFilled = [];
let letterTileUse = [];
let letterTileChars = [];

function isLetterChar(ch) {
  return /[A-Za-zÄÖÜäöüß]/.test(ch);
}

function chooseHiddenSlots(text) {
  const slots = [];
  for (let i = 0; i < text.length; i++) {
    if (isLetterChar(text[i])) slots.push(i);
  }
  const hidden = new Set();
  slots.forEach((pos, idx) => {
    const prev = text[pos - 1];
    const next = text[pos + 1];
    const keepVisible = idx === 0 || !isLetterChar(prev || "") || !isLetterChar(next || "") || idx % 4 === 0;
    if (!keepVisible) hidden.add(pos);
  });
  if (hidden.size < Math.ceil(slots.length * 0.45)) {
    slots.forEach((pos, idx) => {
      if (idx % 2 === 1) hidden.add(pos);
    });
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
  hangWords = sh(test.hang || []);
  hangIndex = 0;
  hangScore = 0;
  hide();
  $("hang").classList.remove("hide");
  $("ht").textContent = "Harf kutucukları: " + test.title;
  showHang();
}

function showHang() {
  letterTarget = hangWords[hangIndex] || "";
  letterSlots = chooseHiddenSlots(letterTarget);
  letterFilled = letterSlots.map(() => "");
  letterTileChars = sh(letterSlots.map(i => letterTarget[i]));
  letterTileUse = letterTileChars.map(() => false);
  $("hh").textContent = (hangIndex + 1) + "/" + hangWords.length + " · Eksik harfleri alttaki kutucuklardan soldan sağa doğru yerleştir.";
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
    hangScore++;
    msg.innerHTML = '<p class="dbok"><b>Richtig.</b></p>';
  } else {
    document.querySelectorAll("[data-slot]").forEach(el => {
      const idx = Number(el.dataset.slot);
      if (letterFilled[idx] !== letterTarget[letterSlots[idx]]) el.style.background = "#fff1f2";
    });
    msg.innerHTML = '<p class="dberr"><b>Yanlış var.</b> Richtig: <b>' + esc(letterTarget) + '</b></p>';
  }
}

function nextHang() {
  if (hangIndex < hangWords.length - 1) {
    hangIndex++;
    showHang();
  } else {
    $("hr").innerHTML = '<p><b>Fertig: ' + hangScore + '/' + hangWords.length + '</b></p><button id="hangRestart">Neu starten</button>';
    $("hangRestart").onclick = startHangman;
  }
}
