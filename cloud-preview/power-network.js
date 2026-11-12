'use strict';
class PowerNetwork {
  constructor(){this.cabinets=[];this.branches=[];this.feeds={};this.phases={};this.sources={};this.samples={};this.surges={}}
  cabinet(site,name,limitKw,id){name=String(name||'').trim();limitKw=Number(limitKw);if(!name||!Number.isFinite(limitKw)||limitKw<=0)throw Error('Nhập tên tủ và giới hạn kW hợp lệ.');id=id||'cab-'+Date.now()+'-'+Math.random().toString(36).slice(2,7);const old=this.cabinets.find(c=>c.id===id);if(old&&old.site!==site)throw Error('Tủ khác xưởng.');const item={id,site,name,limitKw};if(old)Object.assign(old,item);else this.cabinets.push(item);return item}
  branch(site,cabinet,name,phaseKw,id){const c=this.cabinets.find(c=>c.id===cabinet&&c.site===site);const limits=['A','B','C'].map(p=>Number(phaseKw[p]));if(!c||!String(name||'').trim()||limits.some(v=>!Number.isFinite(v)||v<=0))throw Error('Chọn tủ, tên nhánh và giới hạn kW từng pha.');id=id||'branch-'+Date.now()+'-'+Math.random().toString(36).slice(2,7);const old=this.branches.find(b=>b.id===id);if(old&&old.site!==site)throw Error('Nhánh khác xưởng.');const item={id,site,cabinet,name:String(name).trim(),phaseKw:Object.fromEntries(['A','B','C'].map((p,i)=>[p,limits[i]]))};if(old)Object.assign(old,item);else this.branches.push(item);return item}
  feed(site,rack,branch,phase){if(!['A','B','C','ABC'].includes(phase)||!this.branches.some(b=>b.site===site&&b.id===branch)||rack.site!==site)throw Error('Nguồn cấp kệ không hợp lệ.');this.feeds[rack.id]={site,branch,phase}}
  phase(site,device,phase){if(device.site!==site||!['A','B','C','ABC',''].includes(phase))throw Error('Pha máy không hợp lệ.');this.phases[device.id]=phase}
  evaluate(report,racks,now=Date.now()){
    const site=report.rows[0]?.device.site??report.site, alerts=[],loads=new Map(this.branches.filter(b=>b.site===site).map(b=>[b.id,{...b,load:{A:0,B:0,C:0},unknown:0}]));let unmapped=0;
    for(const row of report.rows){const d=row.device,rack=racks.find(r=>r.site===site&&r.slots.includes(d.id)),feed=this.feeds[rack?.id],branch=loads.get(feed?.branch),phase=this.phases[d.id]||feed?.phase;
      if(!branch||!phase){unmapped++;continue}if(/s21.*(?:hyd|hydro)/i.test(d.model)&&phase!=='ABC'){alerts.push({key:'hyd-'+d.id,text:d.ip+': S21 Hydro cần nguồn 3 pha ABC; kiểm tra đấu nối.'})}
      if(/s19 pro(?:\s|$)/i.test(d.model)&&phase==='ABC')alerts.push({key:'single-'+d.id,text:d.ip+': S19 Pro là tải 1 pha; chọn pha A/B/C thực tế cho máy, không chia đều ABC.'});
      if(row.rated===null)branch.unknown++;
      const kw=(row.watts??0)/1000*(1+(report.config?.margin||0)/100);for(const p of ['A','B','C'])if(phase===p||phase==='ABC')branch.load[p]+=kw/(phase==='ABC'?3:1);
    }
    if(report.config&&report.remainingKw<0)alerts.push({key:'station',text:'Trạm vượt tải mục tiêu '+(-report.remainingKw).toFixed(2)+' kW.'});
    if(report.unknown.length)alerts.push({key:'unknown',text:report.unknown.length+' máy chưa có công suất định mức xác nhận.'});
    if(unmapped)alerts.push({key:'unmapped',text:unmapped+' máy trong kệ chưa gán nhánh/pha; chưa kết luận tải nhánh.'});
    for(const b of loads.values()){for(const p of ['A','B','C'])if(b.load[p]>b.phaseKw[p])alerts.push({key:b.id+p,text:b.name+' · pha '+p+' vượt '+(b.load[p]-b.phaseKw[p]).toFixed(2)+' kW.'});const values=Object.values(b.load),avg=values.reduce((a,b)=>a+b,0)/3;b.imbalance=avg?Math.max(...values.map(v=>Math.abs(v-avg)))/avg*100:0;if(b.imbalance>20)alerts.push({key:b.id+'imbalance',text:b.name+': lệch tải pha '+b.imbalance.toFixed(1)+'% (ngưỡng 20%).'})}
    const cabinets=this.cabinets.filter(c=>c.site===site).map(c=>({...c,loadKw:[...loads.values()].filter(b=>b.cabinet===c.id).reduce((sum,b)=>sum+Object.values(b.load).reduce((a,v)=>a+v,0),0)}));for(const c of cabinets)if(c.loadKw>c.limitKw)alerts.push({key:c.id,text:c.name+' vượt giới hạn tủ '+(c.loadKw-c.limitKw).toFixed(2)+' kW.'});
    for(const d of report.rows.map(r=>r.device)){const key=site+'|'+d.id,stamp=d.power_ts??d.power_timestamp,ts=typeof stamp==='number'?(stamp<1e12?stamp*1000:stamp):Date.parse(stamp),w=d.power_w,prev=this.samples[key];if(Number.isFinite(ts)&&now-ts<=600000&&ts<=now+60000&&Number.isFinite(w)&&w>=0){if(prev&&ts>prev.ts&&prev.w>0&&w-prev.w>=100&&w>prev.w*1.2)this.surges[key]={ts,text:d.ip+': điện tăng '+((w/prev.w-1)*100).toFixed(0)+'% ('+prev.w+' → '+w+' W).'};if(!prev||ts>prev.ts)this.samples[key]={ts,w}}const surge=this.surges[key];if(surge&&now-surge.ts<600000)alerts.push({key:'surge-'+key,text:surge.text})}
    return {branches:[...loads.values()],cabinets,alerts,unmapped};
  }
}
if(typeof module!=='undefined')module.exports={PowerNetwork};
