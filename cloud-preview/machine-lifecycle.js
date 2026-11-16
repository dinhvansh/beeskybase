'use strict';
class MachineLifecycle {
  constructor(getDevices,getRacks){this.getDevices=getDevices;this.getRacks=getRacks}
  location(id){for(const rack of this.getRacks()){const index=rack.slots.indexOf(id);if(index>=0)return {rack,index}}return null}
  update(site,id,{status,notes,detach=false,expected=null}){
    const device=this.getDevices().find(d=>d.id===id&&d.site===site);
    if(!device)throw Error('Máy không thuộc xưởng này.');
    if(!['active','broken','repair','retired'].includes(status))throw Error('Tình trạng không hợp lệ.');
    const text=String(notes||'').trim();if(text.length>500)throw Error('Ghi chú tối đa 500 ký tự.');
    const position=this.location(id);
    if(detach&&(!position||position.rack.site!==site||!expected||expected.rackId!==position.rack.id||expected.index!==position.index))throw Error('Vị trí máy đã thay đổi. Mở lại chi tiết máy để tháo.');
    const old=position?{rackId:position.rack.id,index:position.index}:null;
    device.maintenanceState=status;device.maintenanceNotes=text;
    if(detach){position.rack.slots[position.index]=null;device.lastRackPosition=old}
    return {device,removed:detach,old};
  }
}
if(typeof module!=='undefined')module.exports={MachineLifecycle};
