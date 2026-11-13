import * as T from 'three';

// Decorative activity only: no balances, payouts or mining commands are generated.
export function miningEffects(scene,slots,host,api,render){
  const leds=[],coins=[],water=[],fans=[];
  const blue=new T.Color(api.colors.selected);
  const coinCanvas=document.createElement('canvas');coinCanvas.width=128;coinCanvas.height=128;
  const ctx=coinCanvas.getContext('2d');ctx.fillStyle='#facc15';ctx.beginPath();ctx.arc(64,64,55,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#fff0a3';ctx.lineWidth=4;ctx.stroke();ctx.fillStyle='#694d08';ctx.font='bold 76px Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('₿',64,67);
  const coinMap=new T.CanvasTexture(coinCanvas);coinMap.colorSpace=T.SRGBColorSpace;
  const hashCanvas=document.createElement('canvas');hashCanvas.width=256;hashCanvas.height=80;const hashCtx=hashCanvas.getContext('2d');hashCtx.fillStyle=api.colors.normal;hashCtx.font='bold 38px monospace';hashCtx.textAlign='center';hashCtx.fillText('+ HASH',128,52);const hashMap=new T.CanvasTexture(hashCanvas);hashMap.colorSpace=T.SRGBColorSpace;
  const dotGeo=new T.SphereGeometry(.028,6,4);
  const byRack=new Map();
  slots.forEach((slot,index)=>{
    const d=slot.userData.d;if(!d)return;
    const led=new T.Mesh(dotGeo,new T.MeshBasicMaterial({color:d.offline?api.colors.offline:api.colors.normal,transparent:true}));led.position.set(.4,.36,.59);slot.add(led);leds.push({mesh:led,online:!d.offline&&(!d.maintenanceState||d.maintenanceState==='active'),phase:index*.7,slot});
    if(d.offline||(d.maintenanceState&&d.maintenanceState!=='active'))return;
    if(api.animateFans&&api.visualModel(d)==='air'){
      for(const y of [-.2,.2]){
        const rotor=new T.Group();rotor.position.set(0,y,.57);slot.add(rotor);
        const material=new T.MeshStandardMaterial({color:0x64716d,metalness:.4,roughness:.5,transparent:true,opacity:.75});
        for(let blade=0;blade<5;blade++){
          const arm=new T.Group();arm.rotation.z=blade*Math.PI*2/5;
          const mesh=new T.Mesh(new T.PlaneGeometry(.06,.12),material);mesh.position.y=.07;mesh.rotation.z=.3;arm.add(mesh);rotor.add(arm);
        }
        fans.push({mesh:rotor,slot,phase:index*.5});
      }
    }
    if(!byRack.has(slot.userData.r.id))byRack.set(slot.userData.r.id,[]);byRack.get(slot.userData.r.id).push(slot);
    if(api.visualModel(d)==='hydro'){
      for(let j=0;j<3;j++){const dot=new T.Mesh(dotGeo,new T.MeshBasicMaterial({color:blue,transparent:true,opacity:.8}));slot.add(dot);water.push({mesh:dot,phase:j/3,slot})}
    }
  });
  // A small fixed budget keeps large farms readable and avoids per-frame allocations.
  for(const rackSlots of [...byRack.values()].slice(0,9)){
    for(let j=0;j<3;j++){
      const slot=rackSlots[Math.min(j*3,rackSlots.length-1)];
      const sprite=new T.Sprite(new T.SpriteMaterial({map:j===1?hashMap:coinMap,color:0xffffff,transparent:true,opacity:0,depthWrite:false}));sprite.scale.set(j===1 ? 1.3 : .65,j===1 ? .4 : .65,1);slot.parent.add(sprite);coins.push({mesh:sprite,slot,phase:j/3});
    }
  }
  if(!leds.length)dotGeo.dispose();if(!coins.length){coinMap.dispose();hashMap.dispose()}
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let enabled=api.enabled(),visible=true,disposed=false,raf=0,last=0,elapsed=0;
  function update(t){
    const ids=api.query()?api.matches():null,show=slot=>!ids||ids.has(slot.userData.d.id);
    leds.forEach(({mesh,online,phase,slot})=>{mesh.material.opacity=online&&enabled&&show(slot) ? .65+.35*Math.sin(t*2+phase) : 1});
    fans.forEach(({mesh,slot,phase})=>{mesh.visible=show(slot);mesh.rotation.z=t*16+phase});
    water.forEach(({mesh,phase,slot})=>{mesh.visible=enabled&&show(slot);const p=(t*.35+phase)%1;mesh.position.set(.34,p*.65-.3,.6);mesh.material.opacity=Math.sin(p*Math.PI)});
    coins.forEach(({mesh,slot,phase})=>{const p=(t*.23+phase)%1;mesh.visible=enabled&&show(slot);mesh.position.copy(slot.position);mesh.position.y+=.6+p*2.2;mesh.position.x+=Math.sin(p*Math.PI*2+phase)*.12;mesh.position.z+=.75;mesh.material.opacity=Math.sin(p*Math.PI)*.95;mesh.material.rotation=Math.sin(t+phase)*.12});
  }
  function tick(now){raf=0;if(disposed)return;if(!enabled||reduced.matches||!visible||document.hidden){sync();return}if(now-last>=1000/30){elapsed+=Math.min((now-last)/1000,.1);last=now;update(elapsed);render();host.dataset.effectFrames=String((+host.dataset.effectFrames||0)+1)}raf=requestAnimationFrame(tick)}
  function sync(){cancelAnimationFrame(raf);raf=0;update(elapsed);host.dataset.effects=enabled?(reduced.matches?'reduced':document.hidden||!visible?'paused':'running'):'off';render();if(enabled&&!reduced.matches&&visible&&!document.hidden){last=performance.now();raf=requestAnimationFrame(tick)}}
  const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;sync()});observer.observe(host);
  document.addEventListener('visibilitychange',sync);reduced.addEventListener('change',sync);
  sync();
  return {setEnabled(value){enabled=value;sync()},refresh(){update(elapsed)},dispose(){disposed=true;cancelAnimationFrame(raf);observer.disconnect();document.removeEventListener('visibilitychange',sync);reduced.removeEventListener('change',sync)}};
}
