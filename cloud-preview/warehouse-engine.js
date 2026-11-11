'use strict';
// Layout coordinates are preview grid units, not measured physical dimensions.
class WarehouseEngine {
  constructor(getRacks){this.getRacks=getRacks;this.sites=new Map();this.history=[];this.sequence=0}
  site(id){
    if(!this.sites.has(id))this.sites.set(id,{active:'floor-1',floors:[{id:'floor-1',name:'Tầng 1',width:40,depth:24}]});
    return this.sites.get(id);
  }
  floors(site){return this.site(site).floors}
  floor(site,id=this.site(site).active){return this.floors(site).find(f=>f.id===id)}
  racks(site,floor=this.site(site).active){return this.getRacks().filter(r=>r.site===site&&r.placement?.floorId===floor)}
  footprint(r,rotation=0){return rotation%180===0?{width:r.cols*1.18+.65,depth:1.7}:{width:1.7,depth:r.cols*1.18+.65}}
  normalize(p){
    if(!p||!Number.isFinite(p.x)||!Number.isFinite(p.z)||!Number.isFinite(p.rotation)||p.rotation%90!==0)throw Error('Vị trí hoặc góc xoay không hợp lệ.');
    return {floorId:p.floorId,x:Math.round(p.x*2)/2,z:Math.round(p.z*2)/2,rotation:((p.rotation%360)+360)%360};
  }
  check(r,p){
    const f=this.floor(r.site,p.floorId);if(!f)return 'Tầng không thuộc xưởng này.';
    const size=this.footprint(r,p.rotation);
    if(Math.abs(p.x)+size.width/2>f.width/2-.5||Math.abs(p.z)+size.depth/2>f.depth/2-.5)return 'Kệ vượt ra ngoài sàn xưởng.';
    const hit=this.racks(r.site,p.floorId).find(other=>{if(other.id===r.id)return false;const b=this.footprint(other,other.placement.rotation);return Math.abs(p.x-other.placement.x)<(size.width+b.width)/2+.5&&Math.abs(p.z-other.placement.z)<(size.depth+b.depth)/2+.5});
    return hit?'Vị trí trùng hoặc quá sát '+hit.name+'. Giữ khoảng cách giữa các kệ.':'';
  }
  space(r,floorId){
    const f=this.floor(r.site,floorId);if(!f)throw Error('Không tìm thấy tầng.');
    const step=Math.ceil((r.cols*1.18+1.15)*2)/2;
    for(let z=0;z<=f.depth;z+=3)for(const zz of z?[z,-z]:[0])for(let offset=0;offset<f.width;offset+=step)for(const x of offset?[-offset,offset]:[0]){const p=this.normalize({floorId,x,z:zz,rotation:0});if(!this.check(r,p))return p}
    throw Error('Tầng này không còn chỗ cho kệ. Tạo tầng khác hoặc điều chỉnh bố trí.');
  }
  sync(site){
    this.site(site);
    for(const r of this.getRacks().filter(r=>r.site===site))if(!r.placement){r.placement=this.space(r,this.site(site).active)}
  }
  select(site,id){if(!this.floor(site,id))throw Error('Không tìm thấy tầng.');this.site(site).active=id}
  addFloor(site,name,width=40,depth=24){
    name=String(name||'').trim();if(!name||name.length>60)throw Error('Nhập tên tầng từ 1–60 ký tự.');
    if(this.floors(site).some(f=>f.name.toLocaleLowerCase('vi')===name.toLocaleLowerCase('vi')))throw Error('Tên tầng đã tồn tại.');
    if(this.floors(site).length>=12)throw Error('Bản duyệt hỗ trợ tối đa 12 tầng mỗi xưởng.');
    if(!Number.isInteger(width)||!Number.isInteger(depth)||width<16||depth<12||width>100||depth>100)throw Error('Sàn cần rộng 16–100 và sâu 12–100 ô lưới.');
    const f={id:'floor-'+Date.now()+'-'+(++this.sequence),name,width,depth};this.floors(site).push(f);this.select(site,f.id);return f;
  }
  renameFloor(site,id,name){const f=this.floor(site,id);name=String(name||'').trim();if(!f||!name||name.length>60)throw Error('Tên tầng không hợp lệ.');if(this.floors(site).some(other=>other.id!==id&&other.name.toLocaleLowerCase('vi')===name.toLocaleLowerCase('vi')))throw Error('Tên tầng đã tồn tại.');f.name=name}
  removeFloor(site,id){if(this.floors(site).length===1)throw Error('Xưởng phải có ít nhất một tầng.');if(this.racks(site,id).length)throw Error('Chuyển các kệ sang tầng khác trước khi xóa.');if(!this.floor(site,id))throw Error('Không tìm thấy tầng.');const s=this.site(site);s.floors=s.floors.filter(f=>f.id!==id);if(s.active===id)s.active=s.floors[0].id}
  move(rackId,next){
    const r=this.getRacks().find(r=>r.id===rackId);if(!r)throw Error('Không tìm thấy kệ.');
    const p=this.normalize(next),error=this.check(r,p);if(error)throw Error(error);
    if(JSON.stringify(r.placement)===JSON.stringify(p))return false;
    this.history.push({rackId,site:r.site,before:{...r.placement},after:{...p}});r.placement=p;return true;
  }
  undo(site){
    const h=this.history.at(-1);if(!h||h.site!==site)throw Error('Không có thay đổi bố trí để hoàn tác.');
    const r=this.getRacks().find(r=>r.id===h.rackId);if(!r||JSON.stringify(r.placement)!==JSON.stringify(h.after))throw Error('Bố trí đã thay đổi, không thể hoàn tác bước này.');
    const error=this.check(r,h.before);if(error)throw Error(error);
    r.placement={...h.before};this.history.pop();this.select(site,r.placement.floorId);return r;
  }
}
if(typeof module!=='undefined')module.exports={WarehouseEngine};
