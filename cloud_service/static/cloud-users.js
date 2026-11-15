'use strict';
const registration={q:'',status:'',offset:0};
async function loadRegistrations(signal){
 const query=new URLSearchParams({q:registration.q,status:registration.status,offset:registration.offset,limit:25});
 const [users,summary]=await Promise.all([api('/platform/users?'+query,undefined,undefined,signal),api('/platform/overview',undefined,undefined,signal)]);
 return {users,summary};
}
function registrationPage(){
 const {users,summary}=cloud.data.registration;
 return head('Người dùng đăng ký','<button class="btn" data-refresh>Làm mới</button>')+
 `<div class="stats registration-stats">${[['Tài khoản',summary.users],['Chờ xác minh',summary.pending],['Đã khóa',summary.disabled]].map(([label,value])=>`<article class="stat"><div class="stat-top">${label}</div><div class="stat-number">${value}</div></article>`).join('')}</div>
 <form id="registration-filter" class="toolbar registration-filter"><div class="field"><label for="registration-query">Tên hoặc email</label><input id="registration-query" name="q" type="search" maxlength="120" value="${esc(registration.q)}" placeholder="Tìm người dùng"></div><div class="field"><label for="registration-status">Trạng thái</label><select id="registration-status" name="status">${[['','Tất cả'],['pending','Chờ xác minh'],['active','Đã xác minh'],['disabled','Đã khóa'],['superadmin','Super Admin']].map(([value,label])=>`<option value="${value}" ${registration.status===value?'selected':''}>${label}</option>`).join('')}</select></div><button class="btn" type="submit">Tìm kiếm</button></form>`+
 table(['Tài khoản','Trạng thái','Quyền','Ngày đăng ký',''],users.results.map(user=>`<tr><td><strong>${esc(user.name||'Chưa đặt tên')}</strong><small>${esc(user.email)}</small></td><td><span class="pill ${!user.active?'warn':user.verifiedAt?'ok':'neutral'}">${!user.active?'Đã khóa':user.verifiedAt?'Đã xác minh':'Chờ xác minh'}</span></td><td>${user.superadmin?'Super Admin':'Người dùng'}</td><td>${time(user.joinedAt)}</td><td>${user.superadmin?'<span class="muted">Tài khoản được bảo vệ</span>':`<button class="btn small" data-registration-user="${esc(user.id)}">Quản lý</button>`}</td></tr>`).join(''),'Không có tài khoản khớp bộ lọc.')+
 `<div class="toolbar"><span class="muted">${users.count?registration.offset+1:0}–${Math.min(registration.offset+25,users.count)} / ${users.count} tài khoản</span><div class="page-actions"><button class="btn" data-registration-page="prev" ${registration.offset===0?'disabled':''}>Trước</button><button class="btn" data-registration-page="next" ${registration.offset+25>=users.count?'disabled':''}>Sau</button></div></div>`;
}
function openRegistrationUser(id){
 const user=cloud.data.registration?.users.results.find(user=>user.id===id);
 if(!cloud.me.user.superadmin||!user||user.superadmin)return;
 dialog('Quản lý tài khoản',`<input type="hidden" name="userId" value="${esc(id)}"><p><strong>${esc(user.name)}</strong><br>${esc(user.email)}</p><div class="field"><label for="registration-action">Thao tác</label><select id="registration-action" name="action"><option value="${user.active?'disable':'enable'}">${user.active?'Khóa tài khoản':'Mở lại tài khoản'}</option><option value="revoke_sessions">Đăng xuất mọi phiên</option>${user.active&&!user.verifiedAt?'<option value="resend_verification">Gửi lại email xác minh</option>':''}</select></div>${field('reason','Lý do','text','','required minlength="3" maxlength="300"')}<p class="muted">Khóa tài khoản thu hồi các phiên đăng nhập. Dữ liệu xưởng được giữ lại.</p><p id="registration-error" class="auth-field-error" role="alert"></p>`,'registration-action','Xác nhận');
}
document.addEventListener('click',event=>{
 const button=event.target.closest('button');if(!button||!cloud.me?.user?.superadmin)return;
 if(button.dataset.registrationUser)openRegistrationUser(button.dataset.registrationUser);
 if(button.dataset.registrationPage){registration.offset=Math.max(0,registration.offset+(button.dataset.registrationPage==='next'?25:-25));action(()=>show({refreshSites:false}))}
});
document.addEventListener('submit',event=>{
 const form=event.target;
 if(!['registration-filter','registration-action'].includes(form.id))return;
 event.preventDefault();if(!cloud.me?.user?.superadmin)return;
 const values=Object.fromEntries(new FormData(form));
 if(form.id==='registration-filter'){registration.q=values.q.trim();registration.status=values.status;registration.offset=0;action(()=>show({refreshSites:false}));return}
 const button=event.submitter;if(button)button.disabled=true;
 (async()=>{try{
  const result=await api('/platform/users/'+values.userId+'/action',{action:values.action,reason:values.reason});
  $('#cloud-dialog').close();toast(result.message);await show({refreshSites:false});
 }catch(error){const message=$('#registration-error');if(message)message.textContent=error.message;else toast(error.message)}finally{if(button?.isConnected)button.disabled=false}})();
});
