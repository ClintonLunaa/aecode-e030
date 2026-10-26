
export default function({data:d,parentElement:root,setStateValue}){
 const host=root.querySelector("#structural-explorer");
 if(!host||!d)return;
 if(host._cleanup)host._cleanup();
 let mode=d.focus.mode, floor=d.focus.floor, phase=0, amplitude=1, perspective=true, forces=false, playing=false, raf=0, last=0, frames=0;
 const colors=["#2563EB","#D97706","#059669"], fmt=(x,n=2)=>Number(x).toFixed(n);
 const qs=s=>host.querySelector(s);
 const y=i=>300-i*45;
 host.innerHTML=[
 '<section class="bench" aria-label="Inspector estructural interactivo">',
 '<header class="benchbar"><div><span class="eyebrow">INSPECTOR ESTRUCTURAL</span><h2>Mesa de análisis modal</h2></div>',
 '<div class="mode-tabs" role="group" aria-label="Modo de vibración">',
 [1,2,3].map(m=>'<button type="button" class="mode" data-mode="'+m+'" aria-label="Seleccionar modo '+m+'">M'+m+'</button>').join(""),
 '</div></header>',
 '<div class="workspace"><div class="scene">',
 '<div class="view-toolbar"><div class="view-switch" role="group" aria-label="Proyección ilustrativa"><button id="view-volume" aria-pressed="true">Volumen</button><button id="view-front" aria-pressed="false">Alzado</button></div><button id="show-forces" aria-pressed="false">Ver fuerzas</button></div>',
 '<div class="scene-meta"><span>FORMA MODAL RELATIVA</span><b id="mode-period"></b></div>',
 '<svg id="structure" viewBox="0 0 360 365" role="img" aria-label="Proyección ilustrativa de los modos suministrados. Las dimensiones en planta son esquemáticas; no es un modelo FEM">',
 '<defs><pattern id="grid" width="22" height="22" patternUnits="userSpaceOnUse"><path d="M22 0H0V22" fill="none" stroke="#243750" stroke-width=".6"/></pattern></defs>',
 '<rect width="360" height="365" fill="url(#grid)"/>',
 '<rect id="level-band" x="20" width="285" height="38" rx="7" fill="#70c9ff" opacity=".09"/>',
 '<g id="ghost" stroke="#5c7190" stroke-width="1" stroke-dasharray="3 4" opacity=".55"></g>',
 '<g id="deformed"></g><path d="M55 310H275" stroke="#8ca3bc" stroke-width="2"/>',
 '<text x="60" y="342" fill="#a9bad0" font-size="10">PROYECCIÓN ILUSTRATIVA · NO FEM</text>',
 '<g id="level-hits"></g></svg>',
 '<div class="motion"><button id="play" type="button" aria-label="Reproducir forma modal">Reproducir</button><button id="reset" type="button">Reiniciar</button><span id="clock"></span></div>',
 '<label class="phase-label">Fase del ciclo <input id="phase" aria-label="Fase del ciclo" type="range" min="0" max="1" step=".001" value="0"></label>',
 '<label class="phase-label"><span>Escala visual</span><input id="amplitude" aria-label="Escala visual de la forma" type="range" min="0.5" max="2" step="0.1" value="1"><output id="amplitude-value">1.0×</output></label>',
 '<p class="scene-foot">Forma modal relativa · reproducción ralentizada ×8.<br>Proyección y amplitud ilustrativas; no son geometría ni desplazamientos de diseño. Flechas: fuerzas modales con signo, escala relativa.</p>',
 '</div><div class="readout">',
 '<div class="selection-label"><span>SELECCIÓN ACTIVA</span><span id="mode-badge"></span></div>',
 '<h3 id="floor-title" aria-live="polite"></h3><p class="hint">Selecciona un nivel en el esquema o en la tabla.</p>',
 '<div class="readout-grid"><div><span>Fuerza modal</span><strong id="force"></strong></div><div><span>Cortante modal</span><strong id="shear"></strong></div><div><span>Masa del nivel</span><strong id="mass"></strong></div><div><span>Cortante 25/75</span><strong id="combined"></strong></div></div>',
 '<table aria-label="Respuesta por nivel del modo activo"><thead><tr><th>Nivel</th><th>F (kN)</th><th>V (kN)</th></tr></thead><tbody id="level-table"></tbody></table>',
 '<div class="equation"><span>CÁLCULO DE LA FUERZA</span><p>Fᵢᵣ = mᵢ · φᵢᵣ · Γᵣ · Saᵣ</p><code id="substitution"></code></div>',
 '<p class="readout-foot">Valores espectrales del escenario ejecutado; no son fuerzas instantáneas de la animación.</p>',
 '</div></div>',
 '<footer class="bench-footer"><span id="focus-summary"></span><span>Períodos y modos ingresados · caso académico</span></footer></section>'
 ].join("");
 let ghost="";
 for(let i=0;i<=5;i++)ghost+='<path d="M100 '+y(i)+'H195"/>';
 ghost+='<path d="M100 '+y(0)+'V'+y(5)+'M195 '+y(0)+'V'+y(5)+'"/>';
 qs("#ghost").innerHTML=ghost;
 qs("#level-hits").innerHTML=[1,2,3,4,5].map(i=>'<g role="button" tabindex="0" class="level-hit" data-floor="'+i+'" aria-label="Seleccionar piso '+i+'"><rect x="25" y="'+(y(i)-19)+'" width="320" height="38" fill="transparent"/><text x="298" y="'+(y(i)+4)+'" fill="#b8c9dd" font-size="12">P'+i+'</text><text x="298" y="'+(y(i)+17)+'" fill="#93a9c3" font-size="9">'+fmt(i*d.h,1)+' m</text></g>').join("");
 function draw(){
  const c=colors[mode-1], offsets=[0,...d.phiNormalized.map(row=>row[mode-1]*Math.sin(2*Math.PI*phase)*35*amplitude)];
  let shapes="";
  const depth=perspective?42:0, lift=perspective?-22:0, left=98, right=192;
  // Depth is an illustrative projection only; no plan dimensions or torsion are inferred.
  shapes+='<path d="M'+left+' 300L'+(left+depth)+' '+(300+lift)+'H'+(right+depth)+'L'+right+' 300Z" fill="#45647d" opacity=".25"/>';
  for(let side of [left,right]){
   if(perspective)shapes+='<polyline points="'+offsets.map((x,i)=>(side+x+depth)+","+(y(i)+lift)).join(" ")+'" fill="none" stroke="'+c+'" opacity=".35" stroke-width="1.5"/>';
   shapes+='<polyline points="'+offsets.map((x,i)=>(side+x)+","+y(i)).join(" ")+'" fill="none" stroke="'+c+'" stroke-width="2.5"/>';
  }
  for(let i=1;i<=5;i++){
   const x=left+offsets[i], z=y(i), active=i===floor;
   shapes+='<path d="M'+x+' '+z+'L'+(x+depth)+' '+(z+lift)+'H'+(right+offsets[i]+depth)+'L'+(right+offsets[i])+' '+z+'Z" fill="'+(active?'#79d7e8':c)+'" fill-opacity="'+(active?'.30':'.07')+'" stroke="'+(active?'#a0f0ec':c)+'" stroke-width="'+(active?'2':'1')+'"/>';
   shapes+='<path d="M'+x+' '+z+'H'+(right+offsets[i])+'" stroke="'+(active?'#d5fbec':c)+'" stroke-width="'+(active?4:2)+'"/>';
   shapes+='<circle cx="'+(right+offsets[i])+'" cy="'+z+'" r="'+(active?5:2.5)+'" fill="'+(active?'#d5fbec':c)+'"/>';
   if(forces){
    const value=d.F[i-1][mode-1], max=Math.max(...d.F.map(row=>Math.abs(row[mode-1])),1e-12), len=value/max*34, ax=55;
    shapes+='<path d="M'+ax+' '+z+'h'+len+'m'+(-Math.sign(len)*5)+' -3l'+(Math.sign(len)*5)+' 3l'+(-Math.sign(len)*5)+' 3" stroke="#f3bb72" fill="none" stroke-width="2"/>';
   }
  }
  qs("#deformed").innerHTML=shapes;qs("#level-band").setAttribute("y",y(floor)-19);qs("#ghost").style.opacity=perspective?".18":".5";
  qs("#phase").value=phase;qs("#clock").textContent="t = "+fmt(phase*d.periods[mode-1],4)+" s";
  host.dataset.phase=String(phase);host.dataset.frameCount=String(frames);
 }
 function paint(){
  const i=floor-1,m=mode-1,c=colors[m];
  host.style.setProperty("--mode",c);
  host.querySelectorAll("[data-mode]").forEach(b=>{const active=Number(b.dataset.mode)===mode;b.classList.toggle("active",active);b.setAttribute("aria-pressed",String(active));});
  qs("#mode-period").textContent="T"+mode+" = "+fmt(d.periods[m],3)+" s";
  qs("#mode-badge").textContent="MODO "+mode+" · "+fmt(d.participation[m],1)+"% masa";qs("#mode-badge").style.color="#294d81";
  qs("#floor-title").textContent="Piso "+floor+" / "+fmt(floor*d.h,2)+" m";
  qs("#force").textContent=fmt(d.F[i][m])+" kN";qs("#shear").textContent=fmt(d.V[i][m])+" kN";
  qs("#mass").textContent=fmt(d.masses[i])+" t";qs("#combined").textContent=fmt(d.Vcomb[i])+" kN";
  qs("#substitution").textContent=fmt(d.masses[i],3)+" × "+fmt(d.phiRaw[i][m],4)+" × "+fmt(d.gamma[m],4)+" × "+fmt(d.Sa[m],4)+" = "+fmt(d.F[i][m])+" kN";
  qs("#level-table").innerHTML=[5,4,3,2,1].map(n=>'<tr class="'+(n===floor?"chosen":"")+'"><td><button type="button" data-floor="'+n+'" aria-label="Ver respuesta del piso '+n+'">P'+n+'</button></td><td>'+fmt(d.F[n-1][m])+'</td><td>'+fmt(d.V[n-1][m])+'</td></tr>').join("");
  qs("#focus-summary").textContent="Piso "+floor+" · Modo "+mode+" · selección aplicada a las figuras";
  host.dataset.mode=String(mode);host.dataset.floor=String(floor);host.dataset.firma=d.firma;
  bindFloors();draw();
 }
 function stop(){playing=false;cancelAnimationFrame(raf);qs("#play").textContent="Reproducir";qs("#play").setAttribute("aria-label","Reproducir forma modal");}
 function select(nextMode,nextFloor){
  stop();mode=nextMode;floor=nextFloor;paint();
  setStateValue("selection",{mode,floor});
 }
 function bindFloors(){
  host.querySelectorAll("[data-floor]").forEach(b=>{
   b.onclick=()=>select(mode,Number(b.dataset.floor));
   if(b.tagName.toLowerCase()==="g")b.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();select(mode,Number(b.dataset.floor));}};
  });
 }
 host.querySelectorAll("[data-mode]").forEach(b=>b.onclick=()=>select(Number(b.dataset.mode),floor));
 qs("#play").onclick=()=>{
  if(playing){stop();return;}
  playing=true;last=performance.now();qs("#play").textContent="Pausar";qs("#play").setAttribute("aria-label","Pausar forma modal");
  function frame(now){if(!playing)return;phase=(phase+(now-last)/(1000*d.periods[mode-1]*8))%1;last=now;frames++;draw();raf=requestAnimationFrame(frame);}
  raf=requestAnimationFrame(frame);
 };
 qs("#view-volume").onclick=()=>{perspective=true;qs("#view-volume").setAttribute("aria-pressed","true");qs("#view-front").setAttribute("aria-pressed","false");draw();};
 qs("#view-front").onclick=()=>{perspective=false;qs("#view-volume").setAttribute("aria-pressed","false");qs("#view-front").setAttribute("aria-pressed","true");draw();};
 qs("#show-forces").onclick=()=>{forces=!forces;qs("#show-forces").setAttribute("aria-pressed",String(forces));qs("#show-forces").textContent=forces?"Ocultar fuerzas":"Ver fuerzas";draw();};
 qs("#amplitude").oninput=e=>{amplitude=Number(e.target.value);qs("#amplitude-value").textContent=fmt(amplitude,1)+"×";draw();};
 qs("#reset").onclick=()=>{stop();phase=0;draw();};
 qs("#phase").oninput=e=>{stop();phase=Number(e.target.value);draw();};
 paint();
 host._cleanup=()=>{playing=false;cancelAnimationFrame(raf);};
 return ()=>host._cleanup?.();
}
