export const REVIEW_JS = String.raw`/* Founder-only application review enhancement; injected into the existing authenticated Review Desk.
   No automatic emails or invitations. Pending change-request/resubmission workflow is not enabled. */
(() => {
  const ref=(location.pathname.match(/^\/admin\/applications\/(PA-AP-\d{6}-[0-9A-F]{6})$/)||[])[1];
  if(!ref)return;
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const endpoint='/api/admin/applications/'+ref+'/review';
  let installed=false;
  async function api(method,body){
    const r=await fetch(endpoint,{method,credentials:'same-origin',headers:{'X-Studio':'1',...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined});
    const d=await r.json();if(!r.ok||!d.ok)throw Error(d.error||'Request failed');return d.review;
  }
  async function mount(){
    if(installed)return;
    const decision=[...document.querySelectorAll('h2')].find(h=>h.textContent.trim()==='Decision');
    if(!decision)return;
    installed=true;
    const box=document.createElement('section');box.className='st-card';box.style.marginTop='18px';
    box.innerHTML='<h2>Application review</h2><p id="gar-status" class="st-muted">Loading application status…</p><label for="gar-notes">Private review notes</label><textarea id="gar-notes" rows="4" maxlength="4000" style="width:100%;box-sizing:border-box"></textarea><label for="gar-reason">Internal decision reason (optional)</label><textarea id="gar-reason" rows="2" maxlength="2000" style="width:100%;box-sizing:border-box"></textarea><div class="st-row" style="margin-top:12px;flex-wrap:wrap"><button type="button" class="st-btn" data-gar="under_review">Save review</button><button type="button" class="st-btn st-btn--solid" data-gar="accepted">Accept</button><button type="button" class="st-btn" data-gar="declined">Decline</button></div><p class="st-muted">Contact Artist and secure resubmission will appear here once email delivery and update access are configured. Accepting does not invite the artist or send an email.</p><p id="gar-error" role="alert"></p>';
    decision.parentElement.appendChild(box);
    try{
      let current=await api('GET');
      const status=box.querySelector('#gar-status'),notes=box.querySelector('#gar-notes'),reason=box.querySelector('#gar-reason'),error=box.querySelector('#gar-error');
      notes.value=current.review_notes||'';reason.value=current.decision_reason||'';
      const render=()=>{status.textContent='Current status: '+current.status;const final=['accepted','declined','withdrawn'].includes(current.status);box.querySelectorAll('[data-gar]').forEach(b=>b.disabled=final);};
      render();
      box.querySelectorAll('[data-gar]').forEach(btn=>btn.addEventListener('click',async()=>{
        const next=btn.dataset.gar;
        if(next!=='under_review'&&!confirm('Record '+next+' for '+current.artist_name+'? No email will be sent.'))return;
        error.textContent='';box.querySelectorAll('[data-gar]').forEach(b=>b.disabled=true);
        try{await api('POST',{expected_status:current.status,status:next,notes:notes.value,reason:reason.value});current=await api('GET');render();}
        catch(e){error.textContent=e.message;render();}
      }));
    }catch(e){box.querySelector('#gar-status').textContent='Review unavailable: '+e.message;box.querySelectorAll('button').forEach(b=>b.disabled=true);}
  }
  const observer=new MutationObserver(()=>{if(!installed)mount();});
  observer.observe(document.documentElement,{childList:true,subtree:true});mount();
})();`;
