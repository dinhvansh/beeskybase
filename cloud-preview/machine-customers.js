'use strict';
class MachineCustomers {
  constructor(getDevices){this.getDevices=getDevices;this.customers=[];this.sequence=0}
  list(site){return this.customers.filter(c=>c.site===site)}
  create(site,name){name=String(name||'').trim();if(!name||name.length>100)throw Error('Tên khách cần từ 1–100 ký tự.');if(this.list(site).some(c=>c.name.toLocaleLowerCase('vi')===name.toLocaleLowerCase('vi')))throw Error('Khách đã có trong danh sách. Chọn khách đã tạo.');const customer={id:'customer-'+Date.now()+'-'+(++this.sequence),site,name};this.customers.push(customer);return customer}
  assign(site,id,customerId){const d=this.getDevices().find(d=>d.id===id&&d.site===site);if(!d)throw Error('Máy không thuộc xưởng này.');const customer=customerId?this.list(site).find(c=>c.id===customerId):null;if(customerId&&!customer)throw Error('Khách không thuộc xưởng này.');d.customerId=customer?.id||null;d.customerOwner=customer?.name||'';return d}
  name(d){return this.list(d.site).find(c=>c.id===d.customerId)?.name||''}
  importLegacy(){for(const d of this.getDevices()){if(!d.customerOwner||d.customerId)continue;const name=d.customerOwner.trim();if(!name)continue;const existing=this.list(d.site).find(c=>c.name.toLocaleLowerCase('vi')===name.toLocaleLowerCase('vi'));this.assign(d.site,d.id,(existing||this.create(d.site,name)).id)}}
  clear(){this.customers=[];this.sequence=0}
}
if(typeof module!=='undefined')module.exports={MachineCustomers};
