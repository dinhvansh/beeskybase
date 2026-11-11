/* Progressive table controls preserve row elements, handlers and API contracts. */
(()=>{
 const states=new WeakMap();let sequence=0,queued=false;
 const fold=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 function enhance(table){
  if(!table.tHead||!table.tBodies[0])return;
  let s=states.get(table);if(!s){
   const uid=++sequence,tool=document.createElement('div');tool.className='table-tools';
   tool.innerHTML=`<input type="search" aria-label="Tìm trong bảng ${uid}" placeholder="Tìm trong bảng…"><div class="pager"><span class="table-count" role="status"></span><button type="button" class="btn small" data-page="-1" aria-label="Trang trước">←</button><button type="button" class="btn small" data-page="1" aria-label="Trang sau">→</button></div>`;
   if(table.closest("main")?.querySelector("#miner-search"))tool.querySelector("input").hidden=true;
   const columns=document.createElement("details");columns.className="table-columns";const summary=document.createElement("summary");summary.textContent="Cột";columns.append(summary);const options=document.createElement("div");options.className="column-picker";columns.append(options);tool.append(columns);
   table.before(tool);s={table,tool,page:0,size:25,query:'',hiddenColumns:new Set(),sort:-1,dir:1,rows:[]};states.set(table,s);
   tool.querySelector('input').addEventListener('input',e=>{s.query=fold(e.target.value);s.page=0;draw(s)});
   tool.addEventListener('click',e=>{const b=e.target.closest('[data-page]');if(b){s.page+=Number(b.dataset.page);draw(s)}});
   Array.from(table.tHead.rows[0].cells).forEach((th,i)=>{if(!th.textContent.trim())return;const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=true;label.append(check,document.createTextNode(th.textContent));options.append(label);check.addEventListener('change',()=>{if(check.checked)s.hiddenColumns.delete(i);else s.hiddenColumns.add(i);columnsFor(s)});const b=document.createElement('button');b.className='sort-button';b.type='button';b.textContent=th.textContent+' ↕';b.setAttribute('aria-label','Sắp xếp '+th.textContent);th.replaceChildren(b);b.addEventListener('click',()=>{s.dir=s.sort===i?-s.dir:1;s.sort=i;s.page=0;Array.from(table.tHead.rows[0].cells).forEach(x=>x.removeAttribute('aria-sort'));th.setAttribute('aria-sort',s.dir===1?'ascending':'descending');draw(s)})});
  }
  const rows=Array.from(table.tBodies[0].rows);if(rows.length!==s.rows.length||rows.some(r=>!s.rows.includes(r))){s.rows=rows;draw(s)}
 }
 function columnsFor(s){Array.from(s.table.rows).forEach(r=>Array.from(r.cells).forEach((c,i)=>{c.hidden=s.hiddenColumns.has(i)}))}
 function draw(s){
  columnsFor(s);
  const rows=s.rows.filter(r=>fold(r.textContent).includes(s.query));if(s.sort>=0){const text=r=>r.cells[s.sort]?.textContent.trim()||'';rows.sort((a,b)=>text(a).localeCompare(text(b),undefined,{numeric:true})*s.dir);const fragment=document.createDocumentFragment();rows.forEach(r=>fragment.append(r));s.table.tBodies[0].append(fragment)}
  const pages=Math.max(1,Math.ceil(rows.length/s.size));s.page=Math.max(0,Math.min(s.page,pages-1));const visible=new Set(rows.slice(s.page*s.size,(s.page+1)*s.size));s.rows.forEach(r=>{r.hidden=!visible.has(r)});
  const emptyRows=rows.filter(r=>r.cells.length===1&&r.querySelector('.empty'));const count=rows.length-emptyRows.length;
  s.tool.querySelector('.table-count').textContent=`${count} dòng · ${s.page+1}/${pages}`;s.tool.querySelector('[data-page="-1"]').disabled=s.page===0;s.tool.querySelector('[data-page="1"]').disabled=s.page===pages-1;
 }
 function scan(){queued=false;document.querySelectorAll('table.data-table,.tablewrap>table,table.energy').forEach(enhance)}
 new MutationObserver(()=>{if(!queued){queued=true;queueMicrotask(scan)}}).observe(document.body,{childList:true,subtree:true});scan();
})();
