'use strict';
class MachineGroups {
  constructor(getDevices){this.getDevices=getDevices;this.groups=[];this.sequence=0}
  device(site,id){return this.getDevices().find(d=>d.site===site&&d.id===id)}
  list(site){return this.groups.filter(g=>g.site===site)}
  forDevice(d){return this.list(d.site).filter(g=>g.memberIds.includes(d.id))}
  model(d){if(['air','hydro','generic'].includes(d.visualModel))return d.visualModel;const name=d.model.toLowerCase();return /hydro|hydraulic/.test(name)?'hydro':/s19/.test(name)?'air':'generic'}
  labels(input){const labels=(Array.isArray(input)?input:String(input||'').split(',')).map(v=>String(v).trim()).filter(Boolean);const unique=[...new Map(labels.map(v=>[v.toLocaleLowerCase('vi'),v])).values()];if(unique.length>8||unique.some(v=>v.length>32))throw Error('Tối đa 8 nhãn, mỗi nhãn 32 ký tự.');return unique}
  setMetadata(site,id,{labels,visualModel}){const d=this.device(site,id);if(!d)throw Error('Máy không thuộc xưởng này.');if(!['auto','air','hydro','generic'].includes(visualModel))throw Error('Model 3D không hợp lệ.');const normalized=this.labels(labels);d.labels=normalized;d.visualModel=visualModel;return d}
  save(site,input){
    const old=input.id?this.list(site).find(g=>g.id===input.id):null;
    if(input.id&&!old)throw Error('Nhóm không thuộc xưởng này.');
    const name=String(input.name||'').trim(),type=input.type||'custom';
    if(!name||name.length>60)throw Error('Tên nhóm cần từ 1–60 ký tự.');
    if(this.list(site).some(g=>g.id!==old?.id&&g.name.toLocaleLowerCase('vi')===name.toLocaleLowerCase('vi')))throw Error('Tên nhóm đã tồn tại trong xưởng.');
    if(!['water','custom'].includes(type))throw Error('Loại nhóm không hợp lệ.');
    const cooler=String(input.cooler||'').trim(),circuit=String(input.circuit||'').trim(),notes=String(input.notes||'').trim();
    if(cooler.length>80||circuit.length>80||notes.length>400)throw Error('Bộ tản/đường nước tối đa 80 ký tự, ghi chú tối đa 400 ký tự.');
    const memberIds=[...new Set(input.memberIds||[])];if(memberIds.some(id=>!this.device(site,id)))throw Error('Chỉ chọn máy thuộc cùng xưởng.');
    const group={id:old?.id||'group-'+Date.now()+'-'+(++this.sequence),site,name,type,cooler,circuit,notes,memberIds};
    if(old)Object.assign(old,group);else this.groups.push(group);
    return old||group;
  }
  remove(site,id){const g=this.list(site).find(g=>g.id===id);if(!g)throw Error('Nhóm không thuộc xưởng này.');this.groups=this.groups.filter(g=>g.id!==id)}
  search(d){return [...(d.labels||[]),...this.forDevice(d).flatMap(g=>[g.name,g.cooler,g.circuit])].join(' ')}
}
if(typeof module!=='undefined')module.exports={MachineGroups};
