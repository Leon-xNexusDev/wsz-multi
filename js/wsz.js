/* WSZ – gemeinsames Script für alle Seiten.
   Städte-Daten kommen aus staedte.js (window.WSZ_CITIES). Zahlen und Treffpunkte sind Beispieldaten.
   Versprechen werden in dieser Vorschau nur im eigenen Browser gezählt.
   Für den echten Betrieb: sendPledge() an euren Server anbinden (siehe unten). */
(function(){
  'use strict';
  var C=(window.WSZ_CITIES||[]).map(function(c){var o={};for(var k in c)o[k]=c[k];return o});
  var B=document.documentElement.getAttribute('data-base')||'';
  var byId={}; C.forEach(function(c){byId[c.id]=c});
  function fmt(n){return n.toLocaleString('de-DE')}
  function esc(s){return String(s).replace(/[&<>"]/g,function(ch){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]})}
  function cityUrl(id){return B+'staedte/'+id+'.html'}

  /* ---------- Versprechen-Status ---------- */
  var mine=null; try{mine=localStorage.getItem('wsz-pledge')}catch(e){}
  if(mine&&!byId[mine])mine=null;
  if(mine)byId[mine].c+=1;
  var thanks={}, renderers=[];
  function total(){return C.reduce(function(s,c){return s+c.c},0)}
  function updateCounts(){
    var els=document.querySelectorAll('[data-count]');
    for(var i=0;i<els.length;i++){var id=els[i].getAttribute('data-count');els[i].textContent=id==='total'?fmt(total()):(byId[id]?fmt(byId[id].c):'')}
  }
  function rerender(){renderers.forEach(function(f){f()});updateCounts()}

  /* Hier später an den Server schicken, z. B.:
     fetch('/api/versprechen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}) */
  function sendPledge(data){return Promise.resolve(data)}

  /* ---------- Formular ---------- */
  var TVOED=['Krankenhaus (TVöD-K)','Pflege- und Betreuungseinrichtung (TVöD-B)','Kita / Sozial- und Erziehungsdienst (TVöD SuE)','Kommunalverwaltung (TVöD-V)','Entsorgung / Stadtreinigung (TVöD-E)','Sparkasse (TVöD-S)','Flughafen (TVöD-F)','Bundesverwaltung (TVöD Bund)','Ausbildung im öffentlichen Dienst (TVAöD)','Anderer Tarifvertrag (z. B. TV-L, TV-N, TV-V)','Nicht im öffentlichen Dienst / weiß nicht'];
  function formHTML(c,opts){
    opts=opts||{};
    var sw=(mine&&mine!==c.id)?'<p class="switch-note">Du hast bisher für '+byId[mine].n+' zugesagt. Mit dem Absenden wechselst du nach '+c.n+'.</p>':'';
    return '<form class="pform" data-pform="'+c.id+'" novalidate>'+
      (opts.noTitle?'':'<p class="pf-title">Dein Versprechen für '+c.n+'</p>')+sw+
      '<div class="pf-row">'+
        '<label class="pf"><span>Name</span><input id="pf-name-'+c.id+'" name="name" autocomplete="name" placeholder="Vor- und Nachname" required></label>'+
        '<label class="pf"><span>E-Mail</span><input id="pf-mail-'+c.id+'" name="email" type="email" autocomplete="email" placeholder="du@beispiel.de" required></label>'+
      '</div>'+
      '<label class="pf"><span>Wo bist du im TVöD angestellt?</span><select id="pf-tvoed-'+c.id+'" name="tvoed" required><option value="">Bitte wählen</option>'+TVOED.map(function(o){return '<option>'+o+'</option>'}).join('')+'</select></label>'+
      '<label class="pf"><span>Betrieb / Arbeitgeber <em>(optional)</em></span><input id="pf-betrieb-'+c.id+'" name="betrieb" placeholder="z. B. Uniklinik, Stadtreinigung, Kita-Eigenbetrieb"></label>'+
      '<label class="pf-check"><input type="checkbox" id="pf-ok-'+c.id+'" required> <span>Ich bin einverstanden, dass ihr meine Angaben speichert, um mich zu Aktionen in '+c.n+' und in meinem Bereich zu informieren. Widerruf jederzeit möglich, Details in der <a href="'+B+'datenschutz.html">Datenschutzerklärung</a>.</span></label>'+
      '<div class="pf-acts"><button type="submit" class="pf-send">Versprechen abgeben</button>'+(opts.cancel?'<button type="button" class="pf-cancel" data-cancel="1">Abbrechen</button>':'')+'</div>'+
      '<span class="note" id="pf-note-'+c.id+'" role="status" hidden></span>'+
    '</form>';
  }
  document.addEventListener('submit',function(e){
    var f=e.target.closest&&e.target.closest('[data-pform]'); if(!f)return; e.preventDefault();
    var id=f.getAttribute('data-pform'), c=byId[id], g=function(k){return document.getElementById('pf-'+k+'-'+id)};
    var note=g('note'), name=g('name').value.trim(), mail=g('mail').value.trim(), tv=g('tvoed').value, ok=g('ok').checked;
    var err=!name?'Bitte gib deinen Namen ein.':!/^\S+@\S+\.\S+$/.test(mail)?'Bitte gib eine gültige E-Mail-Adresse ein.':!tv?'Bitte wähl aus, wo du angestellt bist.':!ok?'Bitte bestätige die Einwilligung.':'';
    if(err){note.hidden=false;note.textContent=err;return}
    sendPledge({stadt:id,name:name,email:mail,tvoed:tv,betrieb:g('betrieb').value.trim()}).then(function(){
      if(mine&&byId[mine])byId[mine].c-=1;
      mine=id; c.c+=1; thanks[id]=name.split(' ')[0];
      try{localStorage.setItem('wsz-pledge',id)}catch(x){}
      openForm=null; rerender();
    });
  });

  /* ---------- Karte ---------- */
  var DE=[[8.6,54.9],[9.9,54.8],[10.9,54.4],[11.1,54.0],[11.7,54.15],[12.4,54.45],[13.4,54.65],[13.9,54.2],[14.2,53.9],[14.4,53.3],[14.1,52.8],[14.6,52.6],[14.7,51.6],[15.0,51.1],[14.6,50.9],[13.6,50.7],[12.9,50.4],[12.1,50.3],[12.5,49.9],[12.9,49.4],[13.8,48.8],[13.4,48.6],[13.0,48.3],[12.8,47.7],[13.0,47.5],[12.2,47.6],[11.1,47.4],[10.5,47.5],[9.6,47.5],[8.6,47.7],[7.6,47.6],[7.6,48.1],[8.2,48.97],[7.0,49.1],[6.4,49.5],[6.2,49.9],[6.4,50.3],[6.0,50.8],[5.9,51.1],[6.2,51.4],[5.95,51.8],[6.8,51.9],[7.05,52.3],[6.7,52.5],[7.1,52.9],[7.2,53.3],[8.0,53.6],[8.5,53.5],[8.9,53.9],[8.6,54.3]];
  var K=Math.cos(51*Math.PI/180), BOX=[24,20,472,640], NS='http://www.w3.org/2000/svg';
  function proj(lon,lat){var b=BOX,x0=5.6,x1=15.2,y1=55.1,sw=(x1-x0)*K,sh=y1-47.2,s=Math.min(b[2]/sw,b[3]/sh),ox=b[0]+(b[2]-sw*s)/2,oy=b[1]+(b[3]-sh*s)/2;return [ox+(lon-x0)*K*s,oy+(y1-lat)*s]}
  function el(tag,a,p){var e=document.createElementNS(NS,tag);for(var k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e}
  function drawMap(svg,opts){
    opts=opts||{};
    el('path',{class:'land',d:DE.map(function(p,i){var q=proj(p[0],p[1]);return (i?'L':'M')+q[0].toFixed(1)+' '+q[1].toFixed(1)}).join('')+'Z'},svg);
    var marks={};
    C.slice().sort(function(a,b){return a.c-b.c}).forEach(function(c){
      var q=proj(c.lon,c.lat), focus=opts.focus===c.id, s=focus?16:10;
      var g=el('g',{class:'city'+(focus?' on':''),tabindex:opts.labelsOnlyFocus&&!focus?-1:0,role:'link','aria-label':c.n},svg);
      el('rect',{class:'ring',x:q[0]-s/2-5,y:q[1]-s/2-5,width:s+10,height:s+10},g);
      el('rect',{x:q[0]-s/2,y:q[1]-s/2,width:s,height:s},g);
      if(!opts.labelsOnlyFocus||focus){
        var tx=c.side==='l'?q[0]-s/2-7:c.side==='b'?q[0]:q[0]+s/2+7, ty=c.side==='b'?q[1]+s/2+17:q[1]+5;
        var t=el('text',{x:tx,y:ty,'text-anchor':c.side==='l'?'end':c.side==='b'?'middle':'start'},g);t.textContent=c.n;
        if(focus)t.setAttribute('style','font-size:20px');
      }
      var go=function(){if(opts.onPick)opts.onPick(c.id);else location.href=cityUrl(c.id)};
      g.addEventListener('click',go);
      g.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}});
      marks[c.id]=g;
    });
    function sync(){Object.keys(marks).forEach(function(id){marks[id].classList.toggle('mine',id===mine)})}
    renderers.push(sync); sync();
    return marks;
  }
  var maps=document.querySelectorAll('svg.demap[data-map]');
  for(var mi=0;mi<maps.length;mi++){
    var m=maps[mi], mode=m.getAttribute('data-map');
    if(mode==='all')drawMap(m,{});
    if(mode==='focus')drawMap(m,{focus:m.getAttribute('data-focus'),labelsOnlyFocus:true});
  }

  /* ---------- Startseite: Karte + Rangliste ---------- */
  var list=document.getElementById('cities'), openForm=null;
  if(list){
    var more=document.getElementById('more'), search=document.getElementById('city-search'), sel=null, showAll=false, TOP=6;
    var marks=drawMap(document.getElementById('map'),{onPick:function(id){select(id,true)}});
    var itemHTML=function(c,i){
      var isMine=c.id===mine;
      var h='<span class="rk">'+(i+1)+'</span><span class="nm">'+c.n+'</span>'+
        '<button type="button" class="go" data-go="'+c.id+'"'+(openForm===c.id?' aria-expanded="true"':'')+'>'+(isMine?'Du bist dabei ✓':'Ich bin dabei')+'</button>'+
        '<span class="sub">'+c.tp+' · <b>'+fmt(c.c)+'</b> dabei</span>';
      if(c.id===sel){
        h+='<div class="detail">';
        if(openForm===c.id&&!isMine){h+=formHTML(c,{cancel:true})}
        else{
          if(isMine&&thanks[c.id])h+='<span class="note">Danke, '+esc(thanks[c.id])+'! Dein Versprechen für '+c.n+' zählt. Wir melden uns per E-Mail.</span>';
          h+='<span class="meta">Nächste Aktion: [Datum, Zeit] <span class="ph dark">Platzhalter</span></span>'+
             '<a class="to-city" href="'+cityUrl(c.id)+'">Zur Stadtseite '+c.n+' →</a>';
        }
        h+='</div>';
      }
      return h;
    };
    var ranked=function(){return C.slice().sort(function(a,b){return b.c-a.c})};
    var render=function(){
      var q=search.value.trim().toLowerCase(), R=ranked();
      var rows=R.map(function(c,i){return {c:c,i:i}}).filter(function(r){return !q||(r.c.n+' '+r.c.tp).toLowerCase().indexOf(q)>-1});
      var vis=(q||showAll)?rows:rows.filter(function(r,k){return k<TOP||r.c.id===sel||r.c.id===mine});
      list.innerHTML='';
      vis.forEach(function(r){
        var li=document.createElement('li');
        li.className='ci'+(r.c.id===sel?' on':'')+(r.c.id===mine?' mine':'');
        li.id='ci-'+r.c.id; li.innerHTML=itemHTML(r.c,r.i);
        li.addEventListener('click',function(e){if(e.target.closest('button,a,input,select,label,form'))return;select(r.c.id,false)});
        list.appendChild(li);
      });
      if(!vis.length)list.innerHTML='<li class="missing">Keine Stadt gefunden. <a href="'+B+'mitmachen.html#gruenden">Gründe eine Gruppe</a> und bring deine Stadt auf die Karte.</li>';
      more.hidden=!!q||rows.length<=TOP;
      more.textContent=showAll?'Nur Top '+TOP+' anzeigen':'Alle '+C.length+' Städte anzeigen';
      Object.keys(marks).forEach(function(id){marks[id].classList.toggle('on',id===sel)});
    };
    var select=function(id,fromMap){
      sel=(sel===id&&!fromMap)?null:id; render();
      if(fromMap){var li=document.getElementById('ci-'+id);if(li)li.scrollIntoView({block:'nearest',behavior:'smooth'})}
    };
    list.addEventListener('click',function(e){
      if(e.target.closest('[data-cancel]')){openForm=null;render();return}
      var b=e.target.closest('[data-go]'); if(!b)return;
      var id=b.getAttribute('data-go'); sel=id; openForm=(mine===id)?null:(openForm===id?null:id); render();
      var nm=document.getElementById('pf-name-'+id); if(nm)nm.focus();
    });
    more.addEventListener('click',function(){showAll=!showAll;render()});
    search.addEventListener('input',render);
    renderers.push(render);
    sel=mine||'dresden'; render();
  }

  /* ---------- Stadtseite ---------- */
  var cp=document.getElementById('city-pledge');
  if(cp){
    var cid=cp.getAttribute('data-city'), cc=byId[cid];
    var renderCity=function(){
      if(mine===cid){
        cp.innerHTML='<div class="done"><span class="badge">Du bist dabei ✓</span>'+
          (thanks[cid]?'<p>Danke, '+esc(thanks[cid])+'! Dein Versprechen für '+cc.n+' zählt. Wir melden uns per E-Mail, sobald es losgeht.</p>':'<p>Du hast für '+cc.n+' zugesagt. Wir melden uns per E-Mail, sobald es losgeht.</p>')+
          '<p>Erzähl es deinen Kolleg*innen. Jede Zusage macht '+cc.n+' lauter.</p></div>';
      } else cp.innerHTML=formHTML(cc,{noTitle:true});
    };
    renderers.push(renderCity); renderCity();
  }

  /* ---------- Menü ---------- */
  var mb=document.querySelector('.menu-btn'), nl=document.getElementById('navlinks');
  if(mb&&nl){
    mb.addEventListener('click',function(){var o=nl.classList.toggle('open');mb.setAttribute('aria-expanded',o?'true':'false')});
    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&nl.classList.contains('open')){nl.classList.remove('open');mb.setAttribute('aria-expanded','false');mb.focus()}});
  }

  /* ---------- Kopieren ---------- */
  document.addEventListener('click',function(e){
    var b=e.target.closest&&e.target.closest('[data-copy]'); if(!b)return;
    var src=document.getElementById(b.getAttribute('data-copy')); if(!src)return;
    var txt=src.textContent.trim();
    var done=function(){var o=b.textContent;b.textContent='Kopiert';setTimeout(function(){b.textContent=o},1500)};
    var fb=function(){var r=document.createRange();r.selectNodeContents(src);var s=getSelection();s.removeAllRanges();s.addRange(r)};
    try{navigator.clipboard.writeText(txt).then(done,fb)}catch(x){fb()}
  });

  /* Teaser läuft als Vimeo-Einbettung (siehe build.py), kein Script nötig. */

  updateCounts();
})();
