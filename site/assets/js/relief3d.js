/* Vederea 3D a zonei Domogled: relief rotibil + straturi care se pornesc și se opresc.
   Date: assets/date/relief/relief.json și straturi3d.json (din site-src/relief3d.py).
   three.js r128 de pe cdnjs, OrbitControls de pe jsDelivr. Pornește singur când secțiunea ajunge pe ecran. */
(function(){
  var THREE_URL='https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
  var ORBIT_URL='https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js';
  var ZC={'Protecție strictă':'#e08a6a','Protecție integrală':'#9c7bb0','Conservare durabilă':'#f2e27a','Conservare durabilă – parcele limitrofe':'#f0b860','Dezvoltare durabilă':'#7aa6d8'};
  // ordinea de desenare = de jos în sus
  var LAYERS=[
    {id:'zonare',  nume:'Zonare PMI 2025',            on:false, sw:'linear-gradient(90deg,#e08a6a 50%,#9c7bb0 50%)'},
    {id:'pante',   nume:'Pante peste 45° (inaccesibil pe jos)', on:false, sw:'#555'},
    {id:'incendiu',nume:'Incendiul din 2026 (aug. → oct.)', on:false, sw:'linear-gradient(90deg,#fcd34d,#b91c1c)'},
    {id:'parcele', nume:'Parcelar silvic (u.a.)',      on:false, sw:'#3a3a3a', line:1},
    {id:'drumuri', nume:'Drumuri vechi de exploatare', on:false, sw:'#6b3d12', line:1},
    {id:'trasee',  nume:'Trasee turistice',            on:true,  sw:'#1f5fa8', line:1},
    {id:'parc',    nume:'Limita parcului',             on:false, sw:'#2C5F2D', line:1},
    {id:'contur',  nume:'Zona Domogled',               on:true,  sw:'#d21923', line:1},
    {id:'repere',  nume:'Repere',                      on:true,  sw:'#fff', pt:1},
    {id:'elicopter',nume:'Puncte pentru elicopter (propuse)', on:true, sw:'#e8710a', pt:1}
  ];
  function load(src){return new Promise(function(ok,err){var s=document.createElement('script');s.src=src;s.onload=ok;s.onerror=function(){err(new Error(src))};document.head.appendChild(s);});}
  function json(u){return fetch(u).then(function(r){if(!r.ok)throw new Error(u);return r.json();});}
  function img(u){return new Promise(function(ok,err){var i=new Image();i.onload=function(){ok(i)};i.onerror=err;i.src=u;});}
  function webgl(){try{var c=document.createElement('canvas');return !!(c.getContext('webgl')||c.getContext('experimental-webgl'));}catch(e){return false;}}

  document.querySelectorAll('.r3d').forEach(function(box){
    var btn=box.querySelector('.r3d-start'), stage=box.querySelector('.r3d-stage'), msg=box.querySelector('.r3d-msg'), started=false;
    function go(){
      if(started) return; started=true;
      if(!webgl()){msg.textContent='Browserul acesta nu poate afișa modele 3D (WebGL). Imaginea statică rămâne valabilă.';return;}
      if(btn){btn.disabled=true;btn.textContent='Se încarcă modelul 3D…';}
      var root=box.getAttribute('data-root')||'';
      Promise.all([load(THREE_URL).then(function(){return load(ORBIT_URL);}),json(root+'assets/date/relief/relief.json'),json(root+'assets/date/relief/straturi3d.json')])
        .then(function(r){start(box,root,r[1],r[2]);})
        .catch(function(){started=false;if(btn){btn.disabled=false;btn.textContent='Încearcă din nou';}msg.textContent='Modelul 3D nu s-a putut încărca. Verificați conexiunea la internet.';});
    }
    if(btn) btn.addEventListener('click',go);
    stage.addEventListener('click',function(e){if(!started&&e.target.tagName==='IMG')go();});
    if('IntersectionObserver' in window){var io=new IntersectionObserver(function(en){if(en[0].isIntersecting){io.disconnect();go();}},{threshold:0.35});io.observe(stage);}
  });

  function start(box,root,D,S){
    var T=window.THREE, stage=box.querySelector('.r3d-stage');
    box.classList.add('on'); stage.innerHTML=''; stage.tabIndex=0; stage.setAttribute('aria-label','Model 3D al zonei Domogled. Săgețile rotesc modelul, + și − apropie.');
    var bin=atob(D.h), n=D.nx*D.ny, H=new Float32Array(n);
    for(var i=0;i<n;i++) H[i]=(bin.charCodeAt(2*i)|(bin.charCodeAt(2*i+1)<<8))/65535*D.dif_nivel_m;
    var W=D.latime_m/1000, L=D.inaltime_m/1000, vex=1.5;

    var renderer=new T.WebGLRenderer({antialias:true});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2)); renderer.outputEncoding=T.sRGBEncoding;
    stage.appendChild(renderer.domElement);
    var scene=new T.Scene(); scene.background=new T.Color(0xe9efe4);
    var cam=new T.PerspectiveCamera(40,1.6,0.05,100);
    scene.add(new T.HemisphereLight(0xffffff,0x4a5a3a,0.85));
    var sun=new T.DirectionalLight(0xffffff,0.6); sun.position.set(-6,8,-5); scene.add(sun);
    var geo=new T.PlaneGeometry(W,L,D.nx-1,D.ny-1); geo.rotateX(-Math.PI/2);
    var pos=geo.attributes.position;
    function relief(){for(var i=0;i<n;i++) pos.setY(i,H[i]/1000*vex); pos.needsUpdate=true; geo.computeVertexNormals();}
    relief();

    // textura = fond + straturile pornite, desenate pe un canvas
    var cv=document.createElement('canvas'); cv.width=S.w; cv.height=S.h; var cx=cv.getContext('2d');
    var tex=new T.CanvasTexture(cv); tex.encoding=T.sRGBEncoding; tex.anisotropy=renderer.capabilities.getMaxAnisotropy();
    var mat=new T.MeshLambertMaterial({map:tex}); scene.add(new T.Mesh(geo,mat));
    var fonduri={}, fond='satelit', on={}; LAYERS.forEach(function(l){on[l.id]=l.on;});
    function path(rings){cx.beginPath();rings.forEach(function(r){cx.moveTo(r[0],r[1]);for(var i=2;i<r.length;i+=2)cx.lineTo(r[i],r[i+1]);cx.closePath();});}
    function fill(polys,col,a){cx.globalAlpha=a;cx.fillStyle=col;polys.forEach(function(p){path(p);cx.fill('evenodd');});cx.globalAlpha=1;}
    function stroke(ls,col,w,dash){cx.strokeStyle=col;cx.lineWidth=w;cx.setLineDash(dash||[]);cx.lineJoin='round';cx.lineCap='round';
      ls.forEach(function(r){cx.beginPath();cx.moveTo(r[0],r[1]);for(var i=2;i<r.length;i+=2)cx.lineTo(r[i],r[i+1]);cx.stroke();});cx.setLineDash([]);}
    function fireCol(d){var t=(new Date(d)-new Date('2026-08-20'))/(new Date('2026-10-15')-new Date('2026-08-20'));t=Math.max(0,Math.min(1,t));
      var a=[252,211,77],b=[185,28,28];return 'rgb('+a.map(function(v,i){return Math.round(v+(b[i]-v)*t)}).join(',')+')';}
    var X=S.straturi;
    function draw(){
      if(fonduri[fond]) cx.drawImage(fonduri[fond],0,0,S.w,S.h); else {cx.fillStyle='#dfe6d8';cx.fillRect(0,0,S.w,S.h);}
      if(on.zonare) Object.keys(X.zonare).forEach(function(k){fill(X.zonare[k],ZC[k]||'#888',0.45);});
      if(on.pante) fill(X.pante,'#3b3b3b',0.55);
      if(on.incendiu) X.incendiu.forEach(function(f){fill(f.p,fireCol(f.data),0.8);});
      if(on.parcele) stroke(X.parcele,'rgba(30,30,30,.75)',1.6);
      if(on.drumuri) {stroke(X.drumuri,'rgba(255,255,255,.8)',7);stroke(X.drumuri,'#6b3d12',4);}
      if(on.trasee) X.trasee.forEach(function(t){stroke(t.l,'rgba(255,255,255,.85)',7);stroke(t.l,'#1f5fa8',4,t.oficial?null:[10,10]);});
      if(on.parc) {stroke(X.parc,'rgba(255,255,255,.85)',7);stroke(X.parc,'#2C5F2D',4,[16,12]);}
      if(on.contur) {stroke(X.contur,'#fff',9);stroke(X.contur,'#d21923',5);}
      tex.needsUpdate=true;
    }
    draw();
    img(root+'assets/img/relief/textura-satelit.jpg').then(function(i){fonduri.satelit=i;draw();});

    // etichete
    var tags=[];
    function tagset(arr,cls,grp){arr.forEach(function(r){var s=document.createElement('span');s.className='r3d-tag '+cls;s.textContent=r[0];stage.appendChild(s);tags.push({el:s,x:r[1]/1000,z:r[2]/1000,h:r[3],g:grp,dy:cls==='heli'?'8px':'-100%'});});}
    tagset(D.repere,'','repere'); tagset(S.elicopter,'heli','elicopter');
    var nord=document.createElement('div'); nord.className='r3d-n'; nord.setAttribute('aria-hidden','true'); nord.innerHTML='<b>N</b>'; stage.appendChild(nord);

    var ctl=new T.OrbitControls(cam,renderer.domElement);
    ctl.enableDamping=true; ctl.dampingFactor=0.08; ctl.minDistance=1.5; ctl.maxDistance=24;
    ctl.maxPolarAngle=1.38; ctl.screenSpacePanning=false; ctl.autoRotateSpeed=1.2; ctl.rotateSpeed=0.9;
    function reset(){var k=Math.max(1,1.15/(cam.aspect||1.6)); cam.position.set(-6.5*k,6.2*k,8.5*k); ctl.target.set(0,0.45,0); ctl.update();}
    function orbit(dAz,dPol,f){var off=cam.position.clone().sub(ctl.target), s=new T.Spherical().setFromVector3(off);
      s.theta+=dAz; s.phi=Math.max(0.12,Math.min(ctl.maxPolarAngle,s.phi+dPol)); s.radius=Math.max(ctl.minDistance,Math.min(ctl.maxDistance,s.radius*(f||1)));
      off.setFromSpherical(s); cam.position.copy(ctl.target).add(off); ctl.update();}

    var bar=box.querySelector('.r3d-bar'); bar.hidden=false;
    bar.addEventListener('click',function(e){
      var b=e.target.closest('button'); if(!b) return; var a=b.getAttribute('data-a');
      if(a==='st') orbit(-Math.PI/8,0); else if(a==='dr') orbit(Math.PI/8,0);
      else if(a==='sus') orbit(0,-0.15); else if(a==='jos') orbit(0,0.15);
      else if(a==='plus') orbit(0,0,0.8); else if(a==='minus') orbit(0,0,1.25);
      else if(a==='auto'){ctl.autoRotate=!ctl.autoRotate;b.setAttribute('aria-pressed',ctl.autoRotate);}
      else if(a==='vex'){vex=vex===1?1.5:(vex===1.5?2:1);b.textContent='Relief ×'+String(vex).replace('.',',');relief();}
      else if(a==='reset'){ctl.autoRotate=false;var ab=bar.querySelector('[data-a=auto]');if(ab)ab.setAttribute('aria-pressed','false');reset();}
      else if(a==='ecran'){try{if(document.fullscreenElement)document.exitFullscreen();else box.requestFullscreen();}catch(err){}}
    });
    stage.addEventListener('keydown',function(e){var k=e.key,h=true;
      if(k==='ArrowLeft')orbit(-Math.PI/16,0);else if(k==='ArrowRight')orbit(Math.PI/16,0);else if(k==='ArrowUp')orbit(0,-0.08);else if(k==='ArrowDown')orbit(0,0.08);
      else if(k==='+'||k==='=')orbit(0,0,0.85);else if(k==='-')orbit(0,0,1.18);else h=false; if(h)e.preventDefault();});

    // panoul de straturi
    var pan=box.querySelector('.r3d-layers'); pan.hidden=false; if(stage.clientWidth<600) pan.open=false;
    var html='<fieldset><legend>Fond</legend>'+[['satelit','Satelit'],['topo','Topografic'],['fara','Fără fond']].map(function(f){
      return '<label><input type="radio" name="r3d-fond" value="'+f[0]+'"'+(f[0]===fond?' checked':'')+'> '+f[1]+'</label>';}).join('')+'</fieldset>';
    html+='<fieldset><legend>Straturi</legend>'+LAYERS.slice().reverse().map(function(l){
      return '<label><input type="checkbox" data-l="'+l.id+'"'+(l.on?' checked':'')+'> <i class="'+(l.line?'ln':(l.pt?'pt':''))+'" style="background:'+l.sw+'"></i>'+l.nume+'</label>';}).join('')+'</fieldset>';
    html+='<div class="r3d-zc">'+Object.keys(ZC).map(function(k){return '<span><i style="background:'+ZC[k]+'"></i>'+k+'</span>';}).join('')+'</div>';
    pan.querySelector('.r3d-lbody').innerHTML=html;
    function zc(){pan.querySelector('.r3d-zc').hidden=!on.zonare;} zc();
    pan.addEventListener('change',function(e){var t=e.target;
      if(t.name==='r3d-fond'){fond=t.value; if(fond==='topo'&&!fonduri.topo) img(root+'assets/img/relief/textura-topo.jpg').then(function(i){fonduri.topo=i;draw();}); draw(); return;}
      var id=t.getAttribute('data-l'); if(!id) return; on[id]=t.checked; zc(); draw();});

    function size(){var w=stage.clientWidth,h=stage.clientHeight; if(!w||!h) return; renderer.setSize(w,h,false); cam.aspect=w/h; cam.updateProjectionMatrix();}
    var ro=new ResizeObserver(size); ro.observe(stage); size(); reset();
    var visible=true;
    if('IntersectionObserver' in window){var io=new IntersectionObserver(function(en){visible=en[0].isIntersecting;}); io.observe(stage);}
    var v=new T.Vector3();
    (function loop(){
      requestAnimationFrame(loop); if(!visible) return;
      ctl.update(); renderer.render(scene,cam);
      var w=stage.clientWidth,h=stage.clientHeight;
      tags.forEach(function(t){v.set(t.x,t.h/1000*vex+0.06,t.z).project(cam);
        var ok=on[t.g]&&v.z<1&&Math.abs(v.x)<1.05&&Math.abs(v.y)<1.05; t.el.style.display=ok?'':'none';
        if(ok) t.el.style.transform='translate('+((v.x+1)/2*w)+'px,'+((1-v.y)/2*h)+'px) translate(-50%,'+t.dy+')';});
      var az=Math.atan2(cam.position.x-ctl.target.x,cam.position.z-ctl.target.z);
      nord.style.transform='rotate('+(az*180/Math.PI)+'deg)';
    })();
  }
})();
