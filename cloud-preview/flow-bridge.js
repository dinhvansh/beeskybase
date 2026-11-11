'use strict';
// Preserve the reviewed workflow schema, validation and simulation engine.
const legacyBuilderView=builderView;
let selectedFlowNode='trigger',flowEditorId=null;
function flowNodeModels(w){
 const items=[{id:'trigger',kind:'trigger',category:'Kích hoạt',title:w.trigger==='schedule'?'Theo lịch':w.trigger==='discovered'?'Phát hiện máy mới':'Khi đạt điều kiện',detail:flowSummary(w)},
 {id:'scope',kind:'scope',category:'Phạm vi',title:siteName(w.site),detail:`${scopeDevices(w).length} máy · ${w.rack==='all'?'Tất cả rack':racksFor(w.site).find(r=>r.id===w.rack)?.name||'Rack'} · ${w.model==='all'?'Tất cả model':w.model}`},
 ...w.actions.map((a,i)=>({id:'action-'+i,kind:'action',category:'Action '+(i+1),title:actionCatalog[a.type].name,detail:a.type==='webhook'?(a.url||'Chưa đặt URL nhận'):a.type==='thermal'?`Mục tiêu ${a.target??75}°C · Quạt tối đa ${a.fanMax??100}%`:a.type==='pool'?(a.poolUrl||'Chưa đặt pool'):'Cần agent điều khiển'}))];
 return items.map((data,i)=>({id:data.id,type:'bee',position:w.canvas?.[data.id]||{x:(Math.floor(i/2)%2?1-i%2:i%2)*330+30,y:Math.floor(i/2)*220+65},data:{...data,number:String(i+1).padStart(2,'0'),input:i%2===0?'Top':Math.floor(i/2)%2?'Right':'Left',output:i%2===1?'Bottom':Math.floor(i/2)%2?'Left':'Right'},selected:data.id===selectedFlowNode}));
}
builderView=function(w){
 if(flowEditorId!==w.id){flowEditorId=w.id;selectedFlowNode='trigger'}
 const nodes=flowNodeModels(w);if(!nodes.some(n=>n.id===selectedFlowNode))selectedFlowNode='scope';
 const template=document.createElement('template');template.innerHTML=legacyBuilderView(w);
 const panels=template.content.querySelectorAll('.ops-node');
 const index=selectedFlowNode==='trigger'?0:selectedFlowNode==='scope'?1:2+Number(selectedFlowNode.split('-')[1]);
 return `<form id="ops-flow-form" class="bee-flow-form">${opsTitle('Workflow',opsButton('Đóng','flow-close','',false,'close')+'<button class="btn primary" type="submit">'+icon('check')+'Lưu bản nháp</button>')}<div class="ops-builder-meta"><div class="field"><label for="flow-name">Tên workflow</label><input id="flow-name" name="flow-name" value="${esc(w.name)}" maxlength="100" required aria-label="Tên workflow"></div><span class="pill warn">${flowReadiness(w)}</span></div><div class="bee-flow-workspace"><div id="bee-flow-canvas" class="bee-flow-canvas" aria-label="Sơ đồ workflow"></div><aside class="bee-flow-inspector" aria-label="Cấu hình khối đã chọn">${panels[index]?.outerHTML||''}</aside></div><div class="bee-flow-help"><span>Kéo khối để bố trí · Cuộn để zoom · Chọn khối để sửa</span><span>Chạy tuần tự theo dây nối · Bản duyệt chưa thực thi</span></div></form>`;
};
window.beeFlowBridge={
 select(id){captureFlow();selectedFlowNode=id;render()},
 position(id,position){if(ops.editing){ops.editing.canvas??={};ops.editing.canvas[id]=position}},
 viewport(viewport){if(ops.editing)ops.editing.viewport=viewport},
 positions(nodes){nodes.forEach(n=>this.position(n.id,n.position))}
};
const preFlowRender=render;
management.push(['ai-reports','monitor','AI & MCP']);titles['ai-reports']='AI & MCP';
function aiReportsView(){return opsTitle('AI & MCP')+`<div class="ops-context"><span class="pill warn">Chưa cấu hình kết nối</span><span>Quyền báo cáo riêng theo xưởng</span></div><section class="panel" style="padding:20px;margin-bottom:16px"><h2 style="font-size:16px">Kết nối AI để lập báo cáo</h2><p class="ops-note">Backend cloud đã có endpoint <code>/mcp</code>. Bản giao diện này chưa nối backend và chưa cấp quyền cho ứng dụng AI nào.</p><dl class="ops-kv"><div><dt>Kết nối</dt><dd>MCP · Streamable HTTP</dd></div><div><dt>Quyền</dt><dd>Chỉ đọc báo cáo</dd></div><div><dt>Phạm vi</dt><dd>Các xưởng được chủ xưởng cho phép</dd></div><div><dt>Bảo mật</dt><dd>Khóa riêng · Có hạn dùng · Thu hồi được</dd></div></dl><a class="btn" href="mcp-reporting.md" target="_blank" rel="noopener">Hướng dẫn kết nối</a></section><div class="panel table-panel"><table class="data-table"><thead><tr><th>DỮ LIỆU AI CÓ THỂ ĐỌC</th><th>CÔNG CỤ</th></tr></thead><tbody>${[['Tổng quan các xưởng được phép','list_farms'],['Sức khỏe và hashrate máy','list_miners'],['Sự kiện gần nhất','list_events'],['Lịch sử hashrate','get_hashrate_history'],['Điện năng và chi phí ước tính','get_energy_report']].map(([name,tool])=>`<tr><td>${name}</td><td><code>${tool}</code></td></tr>`).join('')}</tbody></table></div>`}
render=function(){window.unmountBeeFlow?.();if(location.hash==='#/ai-reports'){route='ai-reports';$('#app').innerHTML=shell(aiReportsView());document.title='AI & MCP · BeeSky Cloud'}else preFlowRender();const element=$('#bee-flow-canvas');if(element&&ops.editing)window.mountBeeFlow(element,{nodes:flowNodeModels(ops.editing),viewport:ops.editing.viewport})};
document.addEventListener('click',e=>{const button=e.target.closest('[data-ops]');if(!button||!ops.editing)return;const action=button.dataset.ops,index=+button.dataset.id;if(action==='action-add'){selectedFlowNode='action-'+ops.editing.actions.length;delete ops.editing.viewport}if(action==='action-up')selectedFlowNode='action-'+Math.max(0,index-1);if(action==='action-remove')selectedFlowNode='action-'+Math.max(0,index-1)},true);
render();
