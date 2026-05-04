function lessonExamplesKey(){try{return typeof selected!=="undefined"?selected:"t4"}catch(e){return"t4"}}
function fillExampleText(item){if(!item||!item[0])return"";return String(item[0]).replace("____","<b>"+esc(item[1]||"")+"</b>")}
function plainTextFromHtml(s){return String(s||"").replace(/<[^>]*>/g,"").replace(/\s+/g," ").trim()}
function unique(arr,html){let key=plainTextFromHtml(html);if(key&&key.length>10&&!arr.some(x=>plainTextFromHtml(x)===key))arr.push(html)}
function getPhrases(test,limit){let out=[];(test.phraseMatch||[]).forEach(x=>{if(x&&x[0]&&x[1])unique(out,"<b>"+esc(String(x[0]+" "+x[1]).replace(/\s+/g," ").trim())+"</b>")});(test.hang||[]).forEach(x=>unique(out,"<b>"+esc(x)+"</b>"));return out.slice(0,limit)}
function getGrammarRows(test,limit){let rows=[];(test.prep||[]).forEach(x=>{if(!x||!x[0])return;rows.push("<tr><td>"+String(x[0]).replace("___","<b>"+esc(x[1])+"</b>")+"</td><td>"+esc(x[2]||"")+"</td></tr>")});(test.phraseMatch||[]).forEach(x=>{if(x&&x[0]&&x[1])rows.push("<tr><td><b>"+esc(x[0])+"</b> → "+esc(x[1])+"</td><td></td></tr>")});return rows.slice(0,limit).join("")}
function getExamples(test,limit){let out=[];(test.fill||[]).forEach(x=>unique(out,fillExampleText(x)));(test.mc||[]).forEach(x=>{let c=x&&x[1]?x[1][x[2]]:"";unique(out,esc(c))});(test.tf||[]).forEach(x=>{if(x&&x[1]===true)unique(out,esc(x[0]))});(test.prep||[]).forEach(x=>{if(x&&x[0])unique(out,String(x[0]).replace("___","<b>"+esc(x[1])+"</b>"))});return out.slice(0,limit)}
function getParagraphs(test,limit){let title=test.title||"das Thema";let phrases=getPhrases(test,4).map(plainTextFromHtml);let p1=phrases[0]||"eine zentrale Struktur";let p2=phrases[1]||"eine weitere Kollokation";let p3=phrases[2]||"eine präzise Formulierung";let arr=[
"Im Themenfeld <b>"+esc(title)+"</b> sollte nicht nur die Bedeutung einzelner Wörter gelernt werden. Entscheidend ist, Strukturen wie <b>"+esc(p1)+"</b> sicher in vollständige Sätze einzubauen.",
"Eine präzise C1/C2-Formulierung entsteht, wenn eine Kollokation wie <b>"+esc(p2)+"</b> mit einer klaren Begründung verbunden wird. Dadurch wirkt der Text strukturierter und weniger alltagssprachlich.",
"In einem argumentativen Absatz kann <b>"+esc(p3)+"</b> genutzt werden, um eine Beobachtung zu bewerten. Danach sollte ein konkretes Beispiel folgen.",
"Beim Schreiben ist die Reihenfolge wichtig: zuerst die Zielstruktur, dann die grammatische Ergänzung, danach Ursache, Folge oder Bewertung. So entsteht ein zusammenhängender Text."
];return arr.slice(0,limit)}
function appendGeneratedLessonExamples(level){
 const key=lessonExamplesKey(),test=(window.DEUTSCH_TESTS||{})[key],content=document.getElementById("lessonContent");
 if(!test||!content)return;
 const phraseLimit=level==="short"?8:level==="medium"?16:28;
 const grammarLimit=level==="short"?8:level==="medium"?16:28;
 const exLimit=level==="short"?10:level==="medium"?24:45;
 const paraLimit=level==="short"?1:level==="medium"?2:4;
 const phrases=getPhrases(test,phraseLimit).map(x=>"<li>"+x+"</li>").join("");
 const grammar=getGrammarRows(test,grammarLimit);
 const examples=getExamples(test,exLimit).map(x=>"<li>"+x+"</li>").join("");
 const paragraphs=getParagraphs(test,paraLimit).map((x,i)=>"<div style='padding:10px;margin:10px 0;border-left:4px solid #8a5a44;background:#fcfbf8'><p>"+x+"</p></div>").join("");
 content.innerHTML += "<section style='margin-top:18px;padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#ffffff'>"+
 "<h2>3. Ezberlenecek kalıplar</h2><ol>"+phrases+"</ol>"+
 "<h2>4. Gramer ve Rektion</h2><table style='width:100%;border-collapse:collapse'><tbody>"+grammar+"</tbody></table>"+
 "<h2>5. C1/C2 örnek cümleler</h2><ol>"+examples+"</ol>"+
 "<h2>6. Mini paragraf örnekleri</h2>"+paragraphs+
 "<h2>7. Hata uyarıları</h2><ul><li>Kelimeleri fiil ve Präposition ile birlikte ezberle.</li><li>Präpositiondan sonra Kasus kontrol et.</li><li><i>machen</i>, <i>sein</i>, <i>haben</i> yerine daha güçlü fiiller kullan.</li><li>Paragrafta kalıp, neden, örnek ve değerlendirme sırasını koru.</li></ul>"+
 "<h2>8. Yazma görevi</h2><p>Bu konudan beş kalıp seç ve her biriyle bir C1/C2 cümle yaz. Sonra cümleleri tek paragrafta birleştir.</p></section>"
}
document.addEventListener("DOMContentLoaded",function(){
 const b1=document.getElementById("btnLessonShort"),b2=document.getElementById("btnLessonMedium"),b3=document.getElementById("btnLessonLong");
 if(b1)b1.onclick=function(){startLesson("short");appendGeneratedLessonExamples("short")};
 if(b2)b2.onclick=function(){startLesson("medium");appendGeneratedLessonExamples("medium")};
 if(b3)b3.onclick=function(){startLesson("long");appendGeneratedLessonExamples("long")};
});
