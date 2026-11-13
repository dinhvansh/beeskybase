import {mount} from '../cloud-preview/rack3d/scene.js';
const body=document.querySelector('#screen-body');let cleanup=()=>{},mode='3d';
function enhance(){
 const warehouse=body.querySelector('.warehouse');if(!warehouse||body.querySelector('.view-switch'))return;cleanup();
 const toolbar=document.createElement('div');toolbar.className='view-switch';toolbar.innerHTML='<span>XƯỞNG MẪU · S19 PRO / S21 HYDRO</span><div role="group" aria-label="Góc nhìn xưởng"><button data-mode="2d" aria-pressed="false">2D</button><button data-mode="3d" aria-pressed="true">3D</button></div>';body.prepend(toolbar);
 const host=document.createElement('div');host.className='warehouse-3d';warehouse.after(host);
 const floor={id:'demo',name:'Tầng 1',width:20,depth:16};
 const devices=new Map(),racks=[];
 for(let n=0;n<3;n++){
  const rack={id:'rack-'+n,name:['A01 · MÁY GIÓ','A02 · MÁY NƯỚC','A03 · HỖN HỢP'][n],zone:'MINH HỌA',rows:2,cols:3,placement:{x:(n-1)*5,z:n===1?-2:1,rotation:0,floorId:'demo'},slots:[]};
  for(let i=0;i<6;i++){const id='miner-'+(n*6+i),kind=n===0?'air':n===1?'hydro':i%2?'air':'hydro';rack.slots.push(id);devices.set(id,{id,kind,ip:'192.168.1.'+(21+n*6+i),temp:kind==='air'?62:48,offline:false,maintenanceState:'active'});}racks.push(rack);
 }
 const colors={bg:'#eaf0ed',frame:'#6d8278',shelf:'#d8e1dc',fan:'#36483f',floor:'#e1e8e3',labelBg:'#f5f9f6',text:'#304c3b',brand:'#d7b85c',normal:'#83b895',selected:'#6ea8b9',offline:'#89918c',critical:'#cc7562',warm:'#d2ad61',empty:'#becbc1',grid:'#90a59a'};
 let instance;const noop=()=>{};
 const api={colors,floor,floors:[floor],allFloors:false,modelBase:'../cloud-preview/assets/models/',animateFans:true,racks:()=>racks,device:id=>devices.get(id),visualModel:d=>d.kind,mode:()=> 'inspect',edit:()=>false,effects:()=>!document.body.classList.contains('still'),query:()=>'',matches:()=>new Set(),selectedRack:()=>null,selectRack:noop,pending:()=>null,dragged:()=>null,hover:noop,move:noop,moveRack:noop,validateRack:()=>'',position:(r,i)=>r.name+' / '+(i+1),status:message=>{host.dataset.status=message},inspect:(r,i)=>window.dispatchEvent(new CustomEvent('marketing-miner-select',{detail:Number(r.slots[i].split('-')[1])}))};
 try{instance=mount(host,api);instance.view('perspective');host.dataset.renderer='workshop';}catch(error){host.textContent='Không mở được 3D. Chuyển sang 2D để xem máy.';host.dataset.status=error.message;mode='2d';}
 function sync(){instance?.setEffects(mode==='3d'&&!document.body.classList.contains('still'));}
 function switchMode(value){mode=value;warehouse.hidden=value==='3d';host.hidden=value==='2d';toolbar.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===value)));const note=body.querySelector('.map-hint');if(note)note.textContent=value==='3d'?'Model máy & kệ dùng chung với ứng dụng · Kéo để xoay · Chọn máy để xem chi tiết · Hiệu ứng đào minh họa':'Bấm một ô máy để xem worker, hiệu suất và thao tác.';sync();}
 toolbar.querySelectorAll('button').forEach(b=>b.onclick=()=>switchMode(b.dataset.mode));switchMode(mode);
 addEventListener('marketing-motion',sync);
 cleanup=()=>{removeEventListener('marketing-motion',sync);instance?.dispose()};
}
new MutationObserver(()=>{if(!body.querySelector('.warehouse'))cleanup();else enhance()}).observe(body,{childList:true});enhance();
