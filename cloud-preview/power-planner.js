'use strict';
const POWER_REFERENCES=[
  {key:'s19pro',name:'Antminer S19 Pro · 110T',watts:3250,source:'https://support.bitmain.com/hc/en-us/articles/900000261726-S19-Pro-Specifications'},
  {key:'s21hyd',name:'Antminer S21 Hyd. · 335T',watts:5360,source:'https://file12.bitmain.com/shop-product-s3/firmware/b27218d7-1eec-4907-83c7-28e9f8437890/2025/03/20/16/S21%20Hyd.%20User%20Guide-V4.0.14.pdf'}
];
function catalogPower(model){
  const text=String(model||'').toLowerCase().replace(/\b(bitmain|antminer)\b/g,'').replace(/\./g,'').replace(/\s+/g,' ').trim();
  if(/^s19 pro(?: 110\s*(?:t|th|th\/s))?$/.test(text))return {...POWER_REFERENCES[0],variantMissing:!text.includes('110')};
  const hydro=text.match(/^s21 (?:hyd|hydro)(?: (335|319|302)\s*(?:t|th|th\/s))?$/);
  if(hydro)return {...POWER_REFERENCES[1],name:'Antminer S21 Hyd. · '+(hydro[1]||'335')+'T',watts:hydro[1]?{335:5360,319:5104,302:4832}[hydro[1]]:5360,variantMissing:!hydro[1]};
  return null;
}
class PowerPlanner {
  constructor(){this.stations=new Map();this.overrides=new Map()}
  configure(site,input){
    if(['capacity','pf','target','auxKw','margin'].some(key=>input[key]===null||input[key]===undefined||String(input[key]).trim()===''))throw Error('Điền đủ thông số trạm và phụ tải.');
    const c={name:String(input.name||'').trim(),unit:input.unit,capacity:Number(input.capacity),pf:Number(input.pf),target:Number(input.target),auxKw:Number(input.auxKw),margin:Number(input.margin)};
    if(!c.name||c.name.length>80||!['kw','kva'].includes(c.unit)||!Number.isFinite(c.capacity)||c.capacity<=0||c.capacity>100000)throw Error('Nhập tên trạm và công suất hợp lệ.');
    if(!Number.isFinite(c.pf)||c.pf<=0||c.pf>1||!Number.isFinite(c.target)||c.target<=0||c.target>100||!Number.isFinite(c.margin)||c.margin<0||c.margin>100||!Number.isFinite(c.auxKw)||c.auxKw<0||c.auxKw>100000)throw Error('Kiểm tra hệ số công suất, mức tải, phụ tải phụ và dự phòng.');
    this.stations.set(site,c);return c;
  }
  setModel(site,model,watts){if(!model)throw Error('Thiếu model máy.');const key=site+'\0'+model;if(watts===''||watts===null){this.overrides.delete(key);return}const value=Number(watts);if(!Number.isFinite(value)||value<=0||value>100000)throw Error('Công suất máy cần lớn hơn 0 và không quá 100.000 W.');this.overrides.set(key,value)}
  power(site,d,now=Date.now()){
    const manual=this.overrides.get(site+'\0'+d.model),catalog=catalogPower(d.model),rated=manual??catalog?.watts??null;
    let measured=typeof d.power_w==='number'&&Number.isFinite(d.power_w)&&d.power_w>=0?d.power_w:null;
    let stale=false;const stamp=d.power_ts??d.power_timestamp;
    if(stamp!==undefined&&stamp!==null){const time=typeof stamp==='number'?(stamp<1e12?stamp*1000:stamp):Date.parse(stamp);stale=!Number.isFinite(time)||now-time>600000||time>now+60000;if(stale)measured=null}
    return {watts:rated===null?measured:Math.max(rated,measured??0),rated,measured,stale,catalog,source:manual!==undefined?'manual':rated!==null?'catalog':measured!==null?'reported':'unknown'};
  }
  evaluate(site,devices,racks,now=Date.now()){
    const ids=new Set(racks.filter(r=>r.site===site).flatMap(r=>r.slots).filter(Boolean));
    const assigned=devices.filter(d=>d.site===site&&ids.has(d.id)),rows=assigned.map(d=>({device:d,...this.power(site,d,now)}));
    const unknown=rows.filter(r=>r.rated===null),knownW=rows.reduce((sum,r)=>sum+(r.watts??0),0),config=this.stations.get(site)||null;
    const capacityKw=config?(config.unit==='kva'?config.capacity*config.pf:config.capacity):null;
    const limitKw=config?capacityKw*config.target/100:null;
    const loadKw=config?knownW/1000*(1+config.margin/100)+config.auxKw:knownW/1000;
    const remainingKw=config?limitKw-loadKw:null;
    return {site,rows,unknown,knownW,config,capacityKw,limitKw,loadKw,remainingKw,unplaced:devices.filter(d=>d.site===site&&!ids.has(d.id)).length,complete:!!config&&!unknown.length};
  }
  fit(report,watts){if(!report.complete||!Number.isFinite(watts)||watts<=0)return null;return Math.max(0,Math.floor((report.remainingKw*1000+1e-8)/(watts*(1+report.config.margin/100))))}
  clear(){this.stations.clear();this.overrides.clear()}
}
if(typeof module!=='undefined')module.exports={PowerPlanner,catalogPower,POWER_REFERENCES};
