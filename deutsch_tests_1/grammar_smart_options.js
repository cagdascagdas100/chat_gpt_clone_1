(function(){
  function norm(s){return String(s||'').toLocaleLowerCase('de-DE').replace(/\s+/g,' ').trim();}
  function fit(t,name){var h=norm([t&&t.slug,t&&t.title,t&&t.topic].join(' '));return h.indexOf(name)>-1;}
  function rows(kind){
    var poss=[
      ['Nach der Prüfung änderte die Behörde ____.','ihre ursprüngliche Einschätzung','ihren ursprünglichen Einschätzung','ihrer ursprünglichen Einschätzung','ihrem ursprünglichen Einschätzung','ihres ursprünglichen Einschätzung','Possessivartikel'],
      ['Trotz ____ blieb der Beschluss gültig.','seines verspäteten Widerspruchs','seinem verspäteten Widerspruch','seinen verspäteten Widerspruch','sein verspäteter Widerspruch','seine verspätete Widersprüche','Possessivartikel'],
      ['Die Kommission folgte ____ nur teilweise.','unserer sachlichen Begründung','unsere sachliche Begründung','unseren sachlichen Begründung','unseres sachlichen Begründung','unserem sachliche Begründung','Possessivartikel'],
      ['Ohne ____ kann der Antrag nicht genehmigt werden.','Ihren schriftlichen Nachweis','Ihrem schriftlichen Nachweis','Ihres schriftlichen Nachweises','Ihr schriftlicher Nachweis','Ihrer schriftlichen Nachweis','Possessivartikel'],
      ['Die Kritik widerspricht ____.','seinen eigenen Interessen','seine eigenen Interessen','seiner eigenen Interessen','seinem eigenen Interessen','seines eigenen Interesses','Possessivartikel'],
      ['Angesichts ____ ist eine Neubewertung nötig.','eurer kritischen Einwände','euren kritischen Einwänden','eure kritischen Einwände','eurem kritischen Einwand','eures kritischen Einwands','Possessivartikel'],
      ['Die Verwaltung kam ____ entgegen.','Ihren berechtigten Forderungen','Ihre berechtigten Forderungen','Ihrer berechtigten Forderungen','Ihres berechtigten Forderungen','Ihrem berechtigten Forderung','Possessivartikel'],
      ['Wegen ____ wurde die Frist verlängert.','meines früheren Versäumnisses','meinem früheren Versäumnis','mein früheres Versäumnis','meinen früheren Versäumnis','meiner früheren Versäumnisse','Possessivartikel']
    ];
    var dekl=[
      ['____ wurde die Verordnung geändert.','Wegen neuer gesetzlicher Vorgaben','Wegen neuen gesetzlichen Vorgaben','Mit neuen gesetzlichen Vorgaben','Durch neue gesetzliche Vorgaben','Bei neue gesetzliche Vorgaben','Deklination'],
      ['____ musste die Studie überarbeitet werden.','Trotz deutlicher methodischer Schwächen','Trotz deutliche methodische Schwächen','Mit deutlichen methodischen Schwächen','Für deutliche methodische Schwächen','Bei deutlicher methodischer Schwächen','Deklination'],
      ['Die Entscheidung beruht auf ____.','einem nachvollziehbaren fachlichen Gutachten','ein nachvollziehbares fachliches Gutachten','eines nachvollziehbaren fachlichen Gutachtens','einen nachvollziehbaren fachlichen Gutachten','einer nachvollziehbaren fachlichen Gutachten','Deklination'],
      ['Ohne ____ ist die These nicht haltbar.','ausreichende empirische Belege','ausreichenden empirischen Belegen','ausreichender empirischer Belege','ausreichendem empirischem Belegen','ausreichende empirischen Belege','Deklination'],
      ['Die Kommission veröffentlichte ____.','die von Experten geprüften Unterlagen','der von Experten geprüften Unterlagen','den von Experten geprüften Unterlagen','die von Experten geprüfte Unterlagen','dem von Experten geprüften Unterlagen','Deklination'],
      ['Die Bewertung ____ wurde kritisiert.','der von Experten geprüften Unterlagen','die von Experten geprüften Unterlagen','den von Experten geprüften Unterlagen','dem von Experten geprüften Unterlagen','des von Experten geprüften Unterlagen','Deklination'],
      ['Die Behörde arbeitet mit ____.','den in der Sitzung vorgelegten Anträgen','die in der Sitzung vorgelegten Anträge','der in der Sitzung vorgelegten Anträge','das in der Sitzung vorgelegte Anträge','den in der Sitzung vorgelegte Anträge','Deklination'],
      ['Erforderlich ist ____.','ein nach transparenten Kriterien entwickeltes Verfahren','eines nach transparenten Kriterien entwickelten Verfahrens','einem nach transparenten Kriterien entwickelten Verfahren','einen nach transparenten Kriterien entwickelten Verfahren','eine nach transparenten Kriterien entwickelte Verfahren','Deklination']
    ];
    return kind==='poss'?poss:dekl;
  }
  function apply(t,kind){
    var r=rows(kind);
    t._smartOptions=true;
    t.words=r.reduce(function(a,x){return a.concat(x.slice(1,6));},[]);
    t.fill=r.map(function(x){return ['Welche vollständige Form passt? '+x[0],x[1],x[6]];});
    t.mc=r.map(function(x){return ['Welche Option ist grammatisch korrekt? '+x[0],x.slice(1,6),0,x[6]];});
    t.wordMatch=r.map(function(x){return [x[1],'korrekte vollständige Nominalgruppe im passenden Kasus'];});
    t.phraseMatch=r.map(function(x){return [x[0].replace('____','...'),x[1]];});
    t.tf=[
      ['Die richtige Lösung muss zur Präposition, zum Verb und zum Kasus der ganzen Nominalgruppe passen.',true,'Kasus'],
      ['Bei diesen Aufgaben reicht es nicht, nur auf den letzten Buchstaben zu achten.',true,'Ablenker'],
      ['Genitiv-, Dativ- und Akkusativformen können in langen Gruppen sehr ähnlich aussehen.',true,'Formkontrast'],
      ['Eine Option ist schon korrekt, wenn nur das Nomen richtig endet.',false,'Kongruenz']
    ];
    t.prep=[];
  }
  function install(){var all=window.DEUTSCH_TESTS||{};Object.keys(all).forEach(function(k){var t=all[k]||{};if(fit(t,'possessivartikel i')||fit(t,'possessivartikel ii'))apply(t,'poss');if(fit(t,'deklination i')||fit(t,'deklination ii'))apply(t,'dekl');});}
  var old=(typeof build==='function')?build:null;
  function hardBuild(t,n){if(!t||!t._smartOptions||typeof bank!=='function')return old?old(t,n):[];var g=bank(t),ks=['tf','fill','mc','wordMatch','phraseMatch'],out=[],i=0;while(out.length<n&&ks.some(function(k){return(g[k]||[]).length;})){var a=g[ks[i%ks.length]]||[];if(a.length)out.push(a.shift());i++;}return out;}
  install();
  try{if(old){window.build=hardBuild;build=hardBuild;}}catch(e){}
  document.addEventListener('DOMContentLoaded',install);
})();
