const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const names={chat:"聊天",work:"协作",debate:"深入讨论"};
const paths={
chat:'<path d="M21 11a8 8 0 0 1-8 8H9l-6 3 2-6a8 8 0 1 1 16-5Z"/>',
history:'<path d="M3 11a9 9 0 1 1 3 7M3 4v7h7M12 7v5l3 2"/>',
file:'<path d="M14 2H4v20h16V8L14 2Zm0 0v6h6M8 13h8M8 17h6"/>',
settings:'<path d="M12 3v3m0 12v3M3 12h3m12 0h3M6 6l2 2m8 8 2 2M6 18l2-2m8-8 2-2"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
power:'<path d="M12 2v10M5 5a9 9 0 1 0 14 0"/>',
send:'<path d="m3 3 18 9-18 9 3-9-3-9ZM6 12h15"/>',
edit:'<path d="m16 3 5 5-12 12-6 1 1-6zM14 5l5 5"/>',
copy:'<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
spark:'<path d="m12 3 2 7 7 2-7 2-2 7-2-7-7-2 7-2z"/>',
arrow:'<path d="M5 12h14m-5-5 5 5-5 5"/>',
search:'<circle cx="10" cy="10" r="7"/><path d="m16 16 5 5"/>',
plan:'<path d="M9 5h12M9 12h12M9 19h12M3 4l1 1 2-2M3 11l1 1 2-2M3 18l1 1 2-2"/>'
};
const icon=n=>'<svg viewBox="0 0 24 24" aria-hidden="true">'+(paths[n]||paths.chat)+'</svg>';
// 两个原创的小伙伴，仅用于首页，不借用模型品牌图标。
const buddy=actor=>'<svg class="buddy '+actor+'" viewBox="0 0 80 84" aria-hidden="true">'+(actor==='codex'?'<rect x="9" y="13" width="62" height="62" rx="19" fill="#DEB393"/><path d="M16 21q10-8 21-5" stroke="#F2D2B5" stroke-width="3" fill="none"/>':'<path d="M11 65C0 40 19 11 43 14C68 12 85 41 71 66C59 83 20 85 11 65" fill="#C9BDDE"/><path d="M20 26q8-8 18-8" stroke="#E6DDF2" stroke-width="3" fill="none"/>')+'<ellipse cx="33" cy="44" rx="2.8" ry="4" fill="#584F48"/><ellipse cx="49" cy="44" rx="2.8" ry="4" fill="#584F48"/><path d="M38 55q4 3 8 0" stroke="#776A60" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>';
$$("[data-icon]").forEach(e=>e.innerHTML=icon(e.dataset.icon));
const token=new URLSearchParams(location.hash.slice(1)).get("token")||"";
history.replaceState(null,"",location.pathname);
const state={view:"workspace",config:null,items:[],session:null,mode:"chat",recipient:"both",job:null,renameId:null,branchIndex:null,models:[]};
let toastTimer,pollTimer,pingTimer,polling=false,sending=false;
async function api(path,body){
 const response=await fetch(path,{method:body===undefined?"GET":"POST",headers:{"X-DualMind-Token":token,...(body===undefined?{}:{"Content-Type":"application/json"})},...(body===undefined?{}:{body:JSON.stringify(body)})});
 const data=await response.json();if(!response.ok)throw Error(data.error||"本地服务暂时不可用");return data;
}

function toast(text,error=false){const el=$("#toast");el.textContent=text;el.hidden=false;el.classList.toggle("error",error);clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.hidden=true,6000);}
const busy=()=>Boolean(state.job?.running);
const date=value=>new Date(value).toLocaleDateString("zh-CN",{month:"2-digit",day:"2-digit"});
const inline=text=>esc(text).replace(/\u0060([^\u0060]+)\u0060/g,"<code>$1</code>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
async function copy(text){if(!text)return toast("还没有可复制的结果");try{await navigator.clipboard.writeText(text);toast("已复制");}catch{toast("无法访问剪贴板，可以选中文字复制或导出会话",true);}}
function markdown(text){
 const box=document.createElement("div");box.className="markdown";const lines=String(text).split("\n");let i=0;
 while(i<lines.length){
  const line=lines[i];
  if(line.startsWith("\u0060\u0060\u0060")){
   const language=line.slice(3).trim(),code=[];i++;while(i<lines.length&&!lines[i].startsWith("\u0060\u0060\u0060"))code.push(lines[i++]);if(i<lines.length)i++;
   const block=document.createElement("div");block.className="code-block";const top=document.createElement("div");top.className="code-top";
   const label=document.createElement("span");label.textContent=language||"代码";const button=document.createElement("button");button.textContent="复制代码";button.onclick=()=>copy(code.join("\n"));top.append(label,button);
   const pre=document.createElement("pre"),content=document.createElement("code");content.textContent=code.join("\n");pre.append(content);block.append(top,pre);box.append(block);continue;
  }
  if(i+1<lines.length&&line.includes('|')&&/^\s*\|?\s*:?-{3,}/.test(lines[i+1])){
   const cells=value=>value.trim().replace(/^\||\|$/g,'').split('|');
   const wrap=document.createElement('div');wrap.className='table-wrap';const table=document.createElement('table');
   const head=document.createElement('tr');cells(line).forEach(c=>{const th=document.createElement('th');th.innerHTML=inline(c.trim());head.append(th);});table.append(head);i+=2;
   while(i<lines.length&&lines[i].includes('|')&&lines[i].trim()){const row=document.createElement('tr');cells(lines[i++]).forEach(c=>{const td=document.createElement('td');td.innerHTML=inline(c.trim());row.append(td);});table.append(row);}
   wrap.append(table);box.append(wrap);continue;
  }
  if(/^\s*>/.test(line)){const quote=document.createElement('blockquote');quote.innerHTML=inline(line.replace(/^\s*>\s?/,''));box.append(quote);i++;continue;}
  const heading=line.match(/^(#{1,6})\s+(.+)/);
  if(heading){const el=document.createElement("h"+Math.min(4,heading[1].length+1));el.innerHTML=inline(heading[2]);box.append(el);i++;continue;}
  if(/^\s*([-*]|\d+[.)])\s+/.test(line)){
   const list=document.createElement(/^\s*\d/.test(line)?"ol":"ul");
   while(i<lines.length&&/^\s*([-*]|\d+[.)])\s+/.test(lines[i])){const li=document.createElement("li");li.innerHTML=inline(lines[i++].replace(/^\s*([-*]|\d+[.)])\s+/,""));list.append(li);}box.append(list);continue;
  }
  if(!line.trim()){i++;continue;}
  const paragraph=[];
  while(i<lines.length&&lines[i].trim()&&!/^#{1,6}\s/.test(lines[i])&&!lines[i].startsWith("\u0060\u0060\u0060")&&!/^\s*([-*]|\d+[.)])\s+/.test(lines[i]))paragraph.push(lines[i++]);
  const p=document.createElement("p");p.innerHTML=inline(paragraph.join("\n"));box.append(p);
 }
 return box;
}
function latestResult(session){const current=[];for(const m of [...(session?.messages||[])].reverse()){if(m.speaker==="你")break;current.unshift(m);}return current.filter(m=>m.kind==="report").at(-1)?.text||current.filter(m=>m.kind==="reply").map(m=>m.speaker+"\n"+m.text).join("\n\n");}
async function exportSession(id){
 if(!id)return toast("发送消息后可以导出会话");
 try{const response=await fetch("/api/export/"+id,{headers:{"X-DualMind-Token":token}});if(!response.ok)throw Error((await response.json()).error);
 const url=URL.createObjectURL(await response.blob()),link=document.createElement("a");link.href=url;link.download="DualMind-"+id.slice(0,8)+".md";link.click();setTimeout(()=>URL.revokeObjectURL(url),10000);toast("会话已导出");}catch(e){toast(e.message,true);}
}
function renderSidebar(){
 $("#history-count").textContent=state.items.length;
 $("#recent-sessions").innerHTML=state.items.slice(0,9).map(s=>'<button class="recent-item '+(s.id===state.session?.id?"selected":"")+'" data-session="'+s.id+'" title="'+esc(s.title)+'">'+(s.pinned?'⌖ ':'')+esc(s.title)+'</button>').join("")||'<div class="recent-empty">这里会留下每一次好思路。</div>';
 $$("[data-session]",$("#recent-sessions")).forEach(el=>el.onclick=()=>openSession(el.dataset.session));
 const configured=state.config?.gemini.configured;
 $("#provider-status").innerHTML='<span class="status-dot '+(configured?"":"off")+'"></span>'+(configured?"Gemini 已配置":"Gemini 待配置");
 $("#version").textContent=state.config?.version||"0.3";$("#test-badge").hidden=!state.config?.test_mode;
 $$(".nav-item").forEach(el=>el.classList.toggle("active",el.dataset.view===state.view));
}
async function refreshHistory(){const data=await api("/api/sessions");state.items=data.items;renderSidebar();if(data.skipped)toast("跳过 "+data.skipped+" 条无法读取的历史，原文件已保留",true);}
function navigate(view){saveDraft();state.view=view;$("#page-label").textContent={workspace:"工作空间",history:"会话记录",reports:"分析报告",settings:"模型设置",guide:"使用指南"}[view];renderSidebar();({workspace:renderWorkspace,history:renderHistory,reports:renderReports,settings:renderSettings,guide:renderGuide}[view])();}
async function stopTask(){try{state.job=(await api("/api/stop",{})).job;updateConversation();}catch(e){toast(e.message,true);}}
async function pollJob(){
 if(polling)return;polling=true;
 try{const job=(await api("/api/job")).job;if(job){const changed=JSON.stringify(job)!==JSON.stringify(state.job),finished=state.job?.running&&!job.running;state.job=job;
 if(changed){if(state.session?.id===job.session.id)state.session=job.session;updateConversation();updateControls();if(state.view==="settings")$("#save-settings").disabled=busy();if(finished){toast(job.outcome,job.outcome!=="完成"&&!job.outcome.startsWith("已停止"));await refreshHistory();if(state.view==="history")renderHistory();if(state.view==="reports")renderReports();}}}
 }catch(e){if(busy())toast("连接暂时中断；不会重复发送请求，请稍后重新打开应用",true);}finally{polling=false;}
}
const heading=(title,sub,extra="")=>'<div class="page-heading"><div><div class="eyebrow">YOUR SHARED SPACE</div><h1>'+title+'</h1><p>'+sub+'</p></div>'+extra+'</div>';
function renderReports(){
 const items=state.items.filter(s=>s.report_count);
 $("#page").innerHTML='<div class="content-page">'+heading("分析报告","共识、分歧与下一步，整理在一起。",'<span class="badge">保留不同意见</span>')+'<div class="session-grid">'+(items.map(s=>tile(s,true)).join("")||'<div class="empty-state">'+icon("file")+'<h3>让思路慢慢形成结论。</h3><p>在工作空间选择“讨论”，完成后报告会出现在这里。<br>普通聊天和协作不会额外调用模型生成报告。</p><button class="button" id="start-discussion">开始一个讨论 '+icon("arrow")+'</button></div>')+'</div></div>';
 bindTiles();if($("#start-discussion"))$("#start-discussion").onclick=()=>{newSession();state.mode="debate";updateControls();updatePanel();};
}
async function openReport(id){
 try{const session=await api("/api/session/"+id),report=session.messages.filter(m=>m.kind==="report").at(-1);if(!report)return toast("这条会话尚未形成报告");
 $("#page").innerHTML='<div class="content-page">'+heading(esc(session.title),"最新综合报告 · "+date(session.created))+'<div class="report-actions"><button id="back-reports" class="button">← 所有报告</button><button id="copy-report" class="button">'+icon("copy")+'复制报告</button><button id="export-report" class="button">'+icon("download")+'导出完整会话</button><button id="continue-report" class="button primary">接着聊 '+icon("arrow")+'</button></div><div class="report-note">由 Gemini 汇总。模型共识不代表事实已验证，重要结论仍需证据支持。</div><article class="report-detail" id="report-body"></article></div>';
 $("#report-body").append(markdown(report.text));$("#back-reports").onclick=renderReports;$("#copy-report").onclick=()=>copy(report.text);$("#export-report").onclick=()=>exportSession(id);$("#continue-report").onclick=()=>openSession(id);
 }catch(e){toast(e.message,true);}
}
function showRename(id,title){if(!id)return toast("发送消息后可以给会话改名");state.renameId=id;$("#rename-title").value=title;$("#rename-dialog").showModal();$("#rename-title").focus();}
$("#rename-form").onsubmit=async e=>{e.preventDefault();try{const session=await api("/api/rename",{id:state.renameId,title:$("#rename-title").value});if(state.session?.id===session.id)state.session=session;$("#rename-dialog").close();await refreshHistory();updateConversation();toast("标题已保存");}catch(error){toast(error.message,true);}};
$("#cancel-rename").onclick=()=>$("#rename-dialog").close();
$$("[data-view]").forEach(el=>el.onclick=()=>navigate(el.dataset.view));$("#new-session").onclick=newSession;
$(".brand").onclick=e=>{e.preventDefault();navigate("workspace");};$("#all-history").onclick=()=>navigate("history");$("#provider-status").onclick=()=>navigate("settings");
$("#exit-app").onclick=async()=>{try{await api("/api/shutdown",{});$("#page").innerHTML='<div class="content-page">'+heading("已退出 DualMind","已完成的内容保留在本机。可以关闭这个窗口。")+'</div>';clearInterval(pollTimer);clearInterval(pingTimer);}catch(e){toast(e.message,true);}};
async function boot(){
 try{state.config=await api("/api/config");await refreshHistory();state.job=(await api("/api/job")).job;
 if(state.job?.running){state.session=state.job.session;state.mode=state.job.mode;}else{const last=storage.get("last-session");if(last&&state.items.some(s=>s.id===last)){state.session=await api("/api/session/"+last);state.mode=state.session.mode;}}navigate("workspace");
 pollTimer=setInterval(pollJob,900);pingTimer=setInterval(()=>api("/api/ping").catch(()=>{}),20000);if(state.config.warning)toast(state.config.warning,true);
 }catch(e){$("#page").innerHTML='<div class="content-page">'+heading("暂时无法连接本地服务","请双击项目中的启动DualMind.cmd 重新打开。")+'<div class="key-status">'+esc(e.message)+'</div></div>';}
}

// v0.4 interface: build on the existing API, Markdown reader and report views.
Object.assign(paths,{
 trash:'<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/>',
 pin:'<path d="M9 3h6l-1 6 4 4H6l4-4-1-6M12 13v8"/>',
 fork:'<circle cx="6" cy="5" r="2"/><circle cx="18" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><path d="M6 7v10M18 7v2c0 4-12 2-12 6"/>',
 moon:'<path d="M20 15a9 9 0 0 1-11-11 9 9 0 1 0 11 11Z"/>',
 menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
 attach:'<path d="m8 12 6-6a3 3 0 0 1 4 4L9 19a5 5 0 0 1-7-7l10-10"/>'
});
$$('[data-icon]').forEach(el=>el.innerHTML=icon(el.dataset.icon));
const storage={
 get(key,fallback=''){try{return localStorage.getItem('dualmind-'+key)||fallback;}catch{return fallback;}},
 set(key,value){try{localStorage.setItem('dualmind-'+key,value);}catch{}},
 remove(key){try{localStorage.removeItem('dualmind-'+key);}catch{}}
};
try{state.models=JSON.parse(storage.get('models','[]'));if(!Array.isArray(state.models))state.models=[];}catch{}
let confirmAction=null,searchTimer;
function confirmActionDialog(title,detail,action){
 confirmAction=action;$('#confirm-title').textContent=title;$('#confirm-detail').textContent=detail;$('#confirm-dialog').showModal();
}
$('#confirm-cancel').onclick=()=>$('#confirm-dialog').close();
$('#confirm-form').onsubmit=async e=>{e.preventDefault();const action=confirmAction;confirmAction=null;$('#confirm-dialog').close();if(action)await action();};
function saveDraft(){const input=$('#message-input');if(input)storage.set('draft-'+(state.session?.id||'new'),input.value);}
function fitInput(){const input=$('#message-input');if(input){input.style.height='auto';input.style.height=Math.min(160,Math.max(55,input.scrollHeight))+'px';}}
function setTheme(theme){
 storage.set('theme',theme);document.documentElement.dataset.theme=theme==='dark'||(theme==='system'&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';
 if($('#theme-choice'))$('#theme-choice').value=theme;
}
$('#theme-toggle').onclick=()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark');
$('#sidebar-toggle').onclick=()=>$('.app-shell').classList.toggle('sidebar-collapsed');
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if(storage.get('theme','system')==='system')setTheme('system');});
async function openSession(id){try{saveDraft();const session=await api('/api/session/'+id);state.session=session;state.mode=session.mode;state.branchIndex=null;state.recipient='both';storage.set('last-session',id);state.view='workspace';renderSidebar();$('#page-label').textContent='工作空间';renderWorkspace();}catch(e){toast(e.message,true);}};
function newSession(){saveDraft();state.session=null;state.mode='chat';state.recipient='both';state.branchIndex=null;storage.remove('last-session');state.view='workspace';$('#page-label').textContent='工作空间';renderSidebar();renderWorkspace();$('#message-input').focus();};
function workspaceAction(id,name,label){return '<button class="icon-button" id="'+id+'" aria-label="'+label+'" title="'+label+'">'+icon(name)+'</button>';}
function renderWorkspace(){
 $('#page').innerHTML='<div class="workspace"><div class="conversation"><div class="conversation-head"><div class="conversation-heading"><div class="eyebrow">YOUR SHARED SPACE</div><h1 id="conversation-title"></h1></div><div class="icon-actions">'+
 [['rename-session','edit','重命名会话'],['pin-session','pin','置顶或取消置顶'],['fork-session','fork','复制会话'],['copy-result','copy','复制最新结果'],['export-session','download','导出会话'],['delete-session','trash','删除会话']].map(a=>workspaceAction(...a)).join('')+'</div></div>'+
 '<div class="messages" id="message-list"><div class="chat-column" id="message-content"></div></div><div class="composer-wrap"><div class="chat-column"><button class="jump-bottom" id="jump-bottom" hidden>↓ 回到最新消息</button><div id="config-notice"></div><div id="branch-notice"></div><div class="composer-models" id="composer-models"></div><form class="composer" id="composer">'+
 '<textarea id="message-input" aria-label="发送给 AI 的消息" placeholder="和两位 AI 聊聊，或者一起做点什么…" maxlength="12000" rows="3"></textarea><div class="composer-toolbar"><div class="mode-switch">'+Object.entries(names).map(([key,label])=>'<button type="button" data-mode="'+key+'">'+label+'</button>').join('')+
 '<button type="button" id="attach-text" class="icon-button" aria-label="添加文本文件" title="添加文本文件">'+icon('attach')+'</button><input id="text-file" type="file" hidden accept=".txt,.md,.py,.js,.ts,.json,.csv,.java,.html,.css,.sql,.yml,.yaml,.xml,.log"></div>'+
 '<div class="send-area"><select class="round-select" id="round-select" aria-label="讨论轮数"><option value="1">1 轮</option><option value="2">2 轮</option><option value="3">3 轮</option></select><select class="recipient-select" id="recipient" aria-label="选择回复的模型"><option value="both">两位 AI</option><option value="codex">Codex</option><option value="gemini">Gemini</option></select><kbd>Ctrl ↵</kbd><button type="button" class="stop-button" id="stop-task" hidden>停止</button><button type="submit" class="send-button" id="send-message" aria-label="发送消息">'+icon('send')+'</button></div></div></form><div class="composer-meta"><span id="call-budget"></span><span>Enter 发送 · Shift+Enter 换行</span></div></div></div></div></div>';
 $('#round-select').value=String(state.config.settings.rounds);$('#recipient').value=state.recipient;$('#message-input').value=storage.get('draft-'+(state.session?.id||'new'));
 $$('[data-mode]').forEach(el=>el.onclick=()=>{state.mode=el.dataset.mode;state.branchIndex=null;updateControls();});
 $('#recipient').onchange=e=>{state.recipient=e.target.value;updateControls();};$('#round-select').onchange=updateControls;
 $('#composer').onsubmit=send;$('#message-input').oninput=()=>{fitInput();saveDraft();};
 $('#message-input').onkeydown=e=>{if(e.key==='Enter'&&!e.isComposing&&!e.shiftKey){e.preventDefault();send(e);}};
 $('#rename-session').onclick=()=>showRename(state.session?.id,state.session?.title);
 $('#pin-session').onclick=()=>manageSession('pin',state.session?.id);$('#fork-session').onclick=()=>manageSession('fork',state.session?.id);$('#delete-session').onclick=()=>deleteSession(state.session?.id);
 $('#copy-result').onclick=()=>copy(latestResult(state.session));$('#export-session').onclick=()=>exportSession(state.session?.id);$('#stop-task').onclick=stopTask;
 $('#attach-text').onclick=()=>$('#text-file').click();$('#text-file').onchange=e=>{if(e.target.files[0])attachText(e.target.files[0]);e.target.value='';};
 $('#composer').ondragover=e=>{e.preventDefault();$('#composer').classList.add('drop-active');};$('#composer').ondragleave=()=>$('#composer').classList.remove('drop-active');
 $('#composer').ondrop=e=>{e.preventDefault();$('#composer').classList.remove('drop-active');if(e.dataTransfer.files[0])attachText(e.dataTransfer.files[0]);};
 $('#jump-bottom').onclick=()=>{$('#message-list').scrollTop=$('#message-list').scrollHeight;};
 $('#message-list').onscroll=()=>{$('#jump-bottom').hidden=$('#message-list').scrollHeight-$('#message-list').scrollTop-$('#message-list').clientHeight<150;};
 renderModelChips();updateConversation(true);updateControls();fitInput();
};
async function attachText(file){
 if(!/\.(txt|md|py|js|ts|json|csv|java|html|css|sql|yml|yaml|xml|log)$/i.test(file.name)||file.size>65536)return toast('请添加 64 KB 以内的文本或代码文件',true);
 const input=$('#message-input'),text=await file.text(),addition='\n\n文件：'+file.name+'\n'+text;
 if(input.value.length+addition.length>12000)return toast('文件与消息合计超过 12000 字，请选取需要讨论的部分',true);
 input.value+=addition;fitInput();saveDraft();input.focus();toast('文本已加入消息，发送后才会交给模型');
}
function renderModelChips(){
 if(state.view!=='workspace')return;const s=state.config.settings;
 $('#composer-models').innerHTML='<label class="model-chip"><span>● Codex</span> <select id="quick-codex" class="recipient-select" aria-label="快速切换 Codex 模型"></select></label><label class="model-chip gemini"><span>● Gemini</span> <select id="quick-gemini" class="recipient-select" aria-label="快速切换 Gemini 模型"></select></label><button class="model-chip" id="interaction-toggle" title="切换同轮互动方式">'+(s.interaction==='independent'?'各自回答':'一起聊')+' ⇄</button>';
 $('#quick-gemini').innerHTML=[...new Set([s.gemini_model,...state.models])].map(name=>'<option value="'+esc(name)+'">'+esc(name)+'</option>').join('')+'<option value="__settings">更多模型…</option>';
 $('#quick-gemini').value=s.gemini_model;$('#quick-gemini').disabled=busy();
 $('#quick-gemini').onchange=async e=>{if(e.target.value==='__settings')return navigate('settings');await quickConfig({gemini_model:e.target.value});};
 $('#quick-codex').innerHTML='<option value="">CLI 默认</option>'+[...new Set([s.codex_model,...(state.config.codex_models||[])])].filter(Boolean).map(name=>'<option value="'+esc(name)+'">'+esc(name)+'</option>').join('')+'<option value="__settings">手动填写…</option>';$('#quick-codex').value=s.codex_model||'';$('#quick-codex').disabled=busy();$('#quick-codex').onchange=e=>e.target.value==='__settings'?navigate('settings'):quickConfig({codex_model:e.target.value});$('#interaction-toggle').disabled=busy();
 $('#interaction-toggle').onclick=()=>quickConfig({interaction:s.interaction==='independent'?'together':'independent'});
}
async function quickConfig(update){try{state.config=await api('/api/config',update);renderModelChips();updateControls();toast('已切换，下一条消息使用新设置');}catch(e){toast(e.message,true);renderModelChips();}}
function updateControls(){
 if(state.view!=='workspace')return;const debate=state.mode==='debate';if(debate)state.recipient='both';
 $$('[data-mode]').forEach(el=>{el.classList.toggle('active',el.dataset.mode===state.mode);el.disabled=busy();});
 $('#recipient').value=state.recipient;$('#recipient').disabled=debate||busy();$('#round-select').hidden=!debate;$('#round-select').disabled=busy();
 $('#send-message').disabled=busy()||sending;$('#stop-task').hidden=!busy();
 const count=debate?Number($('#round-select').value)*2+1:state.recipient==='both'?2:1;
 $('#call-budget').textContent=busy()?state.job.status:'本次最多 '+count+' 次调用 · '+(debate?'独立思考，再自然讨论':state.config.settings.interaction==='independent'?'两位分别回答':'同伴可以接着补充');
 $('#config-notice').innerHTML=(!state.config.gemini.configured&&state.recipient!=='codex')?'<div class="config-notice"><span>先配置 Gemini，或选择只让 Codex 回答。</span><button id="go-config" type="button">前往设置 ↗</button></div>':'';
 if($('#go-config'))$('#go-config').onclick=()=>navigate('settings');
 $('#branch-notice').innerHTML=state.branchIndex!==null?'<div class="branch-notice"><span>编辑后会创建新分支，原会话保留。</span><button id="cancel-branch" type="button">取消</button></div>':'';
 if($('#cancel-branch'))$('#cancel-branch').onclick=()=>{state.branchIndex=null;updateControls();};
 ['pin-session','fork-session','delete-session','rename-session'].forEach(id=>$('#'+id).disabled=!state.session||busy());
 if($('#quick-gemini'))$('#quick-gemini').disabled=busy();if($('#quick-codex'))$('#quick-codex').disabled=busy();if($('#interaction-toggle'))$('#interaction-toggle').disabled=busy();
};
function updatePanel(){} // Explanations live in the guide, not beside the conversation.
function updateConversation(forceBottom=false){
 if(state.view!=='workspace')return;$('#conversation-title').textContent=state.session?.title||'新的共同工作空间';
 const scroll=$('#message-list'),box=$('#message-content'),nearBottom=scroll.scrollHeight-scroll.scrollTop-scroll.clientHeight<150,oldScroll=scroll.scrollTop;box.replaceChildren();
 if(!state.session?.messages?.length){
  box.innerHTML='<div class="welcome"><div class="welcome-emblem">'+buddy('codex')+'<span class="buddy-link">＋</span>'+buddy('gemini')+'</div><div class="eyebrow">THINK BETTER, TOGETHER</div><h2>多一种思路，<em>多一点可能。</em></h2><p>聊聊日常，碰一碰想法，或者一起把事情做好。<br>Codex 和 Gemini 都在，节奏由你来定。</p><div class="suggestions">'+
  [['chat','chat','随便聊聊','不用结论，也不用辩论。','今天有点累，陪我聊聊吧。'],['work','plan','一起做点事','计划、写作、代码，都可以。','一起帮我想一个周末能完成的小项目。'],['debate','spark','多想一个角度','重要选择，听听不同看法。','请帮我比较两种学习路线，我会先提供背景。']].map(([mode,ico,title,sub,prompt])=>'<button class="suggestion" data-prompt="'+esc(prompt)+'" data-prompt-mode="'+mode+'">'+icon(ico)+'<strong>'+title+'</strong><small>'+sub+'</small></button>').join('')+'</div><p class="welcome-note">@Codex 或 @Gemini 可以单独点名。你的消息才会推进对话。</p></div>';
  $$('[data-prompt]',box).forEach(el=>el.onclick=()=>{state.mode=el.dataset.promptMode;$('#message-input').value=el.dataset.prompt;fitInput();saveDraft();$('#message-input').focus();updateControls();});
 }else state.session.messages.forEach((m,index)=>{
  const user=m.speaker==='你',el=document.createElement('article');el.className='message '+(user?'user-message ':'')+(m.kind==='error'?'error':'');
  const meta=document.createElement('div');meta.className='message-meta';meta.innerHTML='<span class="avatar '+(user?'user':m.speaker==='Gemini'?'gemini':'')+'">'+(user?'我':m.speaker==='Gemini'?'G':'C')+'</span><span class="speaker">'+esc(m.speaker)+'</span>'+(m.model?'<span class="model-label">'+esc(m.model)+'</span>':'')+(state.session.mode==='debate'?'<span class="message-stage">'+esc(m.stage)+'</span>':'');
  const actions=document.createElement('div');actions.className='message-actions';
  const copyButton=document.createElement('button');copyButton.className='message-copy';copyButton.textContent='复制';copyButton.onclick=()=>copy(m.text);actions.append(copyButton);
  if(state.session.mode!=='debate'){const action=document.createElement('button');action.className='message-copy';action.textContent=user?'编辑':'重新生成';action.disabled=busy();action.onclick=()=>user?editMessage(index):regenerate(index);actions.append(action);}
  meta.append(actions);const card=document.createElement('div');card.className='message-card';card.append(markdown(m.text));el.append(meta,card);box.append(el);
 });
 if(busy()&&state.job.session.id===state.session?.id){const pending=document.createElement('div');pending.className='pending';pending.setAttribute('role','status');pending.innerHTML='<span class="pending-dot"></span><span>'+esc(state.job.status)+'</span>';box.append(pending);}
 scroll.scrollTop=forceBottom||nearBottom?scroll.scrollHeight:oldScroll;
};
function editMessage(index){state.branchIndex=index;$('#message-input').value=state.session.messages[index].text;$('#message-input').focus();fitInput();saveDraft();updateControls();}
function regenerate(index){
 let userIndex=index;while(userIndex>=0&&state.session.messages[userIndex].speaker!=='你')userIndex--;if(userIndex<0)return;
 const actor=state.session.messages[index].speaker.toLowerCase();
 confirmActionDialog('重新生成这条回复？','只调用 '+state.session.messages[index].speaker+' 一次，并创建新分支，原会话保留。',()=>submitMessage(state.session.messages[userIndex].text,actor,userIndex));
}
async function send(event){
 event?.preventDefault();if(busy()||sending)return;let text=$('#message-input').value.trim(),recipient=state.recipient;if(!text)return toast('先写一条消息');
 const mention=text.match(/^@(Codex|Gemini)\b\s*/i);if(mention&&state.mode!=='debate'){recipient=mention[1].toLowerCase();text=text.slice(mention[0].length).trim();}
 if(!text)return toast('点名后写上你想说的话');await submitMessage(text,recipient,state.branchIndex);
};
async function submitMessage(text,recipient,branchIndex=null){
 if(busy()||sending)return;sending=true;updateControls();const originalSession=state.session?.id||'new';
 try{const payload={text,mode:state.mode,recipient,rounds:Number($('#round-select').value),session_id:state.session?.id||null};if(branchIndex!==null)payload.branch_index=branchIndex;
  const data=await api('/api/send',payload);state.job=data.job;state.session=data.job.session;state.branchIndex=null;storage.remove('draft-'+originalSession);storage.set('last-session',state.session.id);$('#message-input').value='';fitInput();updateConversation(true);await refreshHistory();if(!state.job.running)toast(state.job.outcome);
 }catch(e){toast(e.message,true);}finally{sending=false;updateControls();}
}
async function manageSession(action,id){
 if(!id)return toast('发送消息后可以管理会话');
 try{const result=await api('/api/'+action,{id});if(action==='fork'){await refreshHistory();return openSession(result.id);}if(action==='pin'&&state.session?.id===id)state.session=result;await refreshHistory();if(state.view==='history')renderHistory();else if(state.view==='reports')renderReports();else updateConversation();toast(action==='restore'?'会话已恢复':'已更新');}catch(e){toast(e.message,true);}
}
function deleteSession(id){
 if(!id)return;const title=state.items.find(s=>s.id===id)?.title||state.session?.title||'会话';
 confirmActionDialog('删除这段会话？','“'+title+'”会移入回收站，可以恢复。',async()=>{try{saveDraft();await api('/api/delete',{id});storage.remove('draft-'+id);if(state.session?.id===id){state.session=null;state.branchIndex=null;storage.remove('last-session');}if(state.job?.session.id===id)state.job=null;await refreshHistory();if(state.view==='workspace')renderWorkspace();else navigate(state.view);toast('已移入回收站');}catch(e){toast(e.message,true);}});
}
function tile(s,report=false){return '<article class="session-tile"><button class="tile-open" data-open="'+s.id+'" data-report="'+report+'"><div class="tile-top"><span class="mode-badge">'+(s.pinned?'⌖ ':'')+(report?'分析报告':names[s.mode])+'</span><span class="tile-date">'+date(s.created)+'</span></div><h3>'+esc(s.title)+'</h3><p>'+esc(s.preview)+'</p></button><div class="tile-footer"><span>'+s.reply_count+' 条 AI 回复'+(s.report_count?' · '+s.report_count+' 份报告':'')+'</span><div class="tile-actions">'+[['pin',s.pinned?'取消置顶':'置顶'],['edit','重命名'],['download','导出'],['trash','删除']].map(([name,label])=>'<button data-action="'+name+'" data-id="'+s.id+'" aria-label="'+label+' '+esc(s.title)+'" title="'+label+'">'+icon(name)+'</button>').join('')+'</div></div></article>';};
function bindTiles(){
 $$('[data-open]',$('#page')).forEach(el=>el.onclick=()=>el.dataset.report==='true'?openReport(el.dataset.open):openSession(el.dataset.open));
 $$('[data-action]',$('#page')).forEach(el=>el.onclick=()=>{const id=el.dataset.id;({pin:()=>manageSession('pin',id),edit:()=>showRename(id,state.items.find(s=>s.id===id)?.title),download:()=>exportSession(id),trash:()=>deleteSession(id)})[el.dataset.action]();});
};
function renderHistory(){
 $('#page').innerHTML='<div class="content-page">'+heading('会话记录','找到旧思路，也给新思路留一点空间。','<button class="button" id="trash-view">'+icon('trash')+'回收站</button>')+'<div class="stats">'+[['全部会话',state.items.length],['AI 回复',state.items.reduce((n,s)=>n+s.reply_count,0)],['分析报告',state.items.reduce((n,s)=>n+s.report_count,0)]].map(([label,count])=>'<div class="stat"><small>'+label+'</small><b>'+count+'</b></div>').join('')+'</div><div class="search-row"><label class="search-field">'+icon('search')+'<input id="history-search" aria-label="搜索会话" placeholder="搜索标题或对话全文…" maxlength="200"></label><select id="history-filter" class="filter-select" aria-label="筛选会话模式"><option value="">全部模式</option><option value="chat">聊天</option><option value="work">协作</option><option value="debate">深入讨论</option></select></div><div class="session-grid" id="history-grid"></div></div>';
 let matches=state.items,requestId=0;
 const draw=()=>{if(!$('#history-grid'))return;const mode=$('#history-filter').value;$('#history-grid').innerHTML=matches.filter(s=>!mode||s.mode===mode).map(s=>tile(s)).join('')||'<div class="empty-state">'+icon('history')+'<h3>还没有匹配的会话</h3><p>新建一段聊天，或者换个关键词试试。</p></div>';bindTiles();};
 $('#history-search').oninput=()=>{const current=++requestId;clearTimeout(searchTimer);searchTimer=setTimeout(async()=>{try{const query=$('#history-search')?.value;if(query===undefined)return;const data=await api('/api/search',{query});if(current===requestId&&state.view==='history'&&$('#history-grid')){matches=data.items;draw();}}catch(e){toast(e.message,true);}},220);};
 $('#history-filter').onchange=draw;$('#trash-view').onclick=renderTrash;draw();
};
async function renderTrash(){
 try{const data=await api('/api/trash');$('#page').innerHTML='<div class="content-page">'+heading('回收站','删除的会话仍保存在本机，可随时恢复。','<button class="button" id="back-history">← 会话记录</button>')+(data.items.map(s=>'<div class="trash-row"><strong>'+esc(s.title)+'</strong><button class="button" data-restore="'+s.id+'">恢复会话</button></div>').join('')||'<div class="empty-state">回收站是空的。</div>')+'</div>';$('#back-history').onclick=renderHistory;$$('[data-restore]').forEach(el=>el.onclick=async()=>{await manageSession('restore',el.dataset.restore);await renderTrash();});}catch(e){toast(e.message,true);}
}
function renderSettings(){
 const c=state.config,s=c.settings;
 $('#page').innerHTML='<div class="content-page">'+heading('模型设置','把连接配置好，然后安心聊天。','<span class="badge">本机保存</span>')+'<div class="settings-grid"><div><form id="settings-form"><section class="setting-card"><h2><span class="avatar gemini">G</span>Gemini<span class="badge">'+(c.gemini.configured?'已配置':'待配置')+'</span></h2><label class="field-label" for="api-key">API Key</label><input class="field" id="api-key" type="password" autocomplete="off" spellcheck="false" placeholder="'+(c.gemini.configured?'已保存，留空保留原 Key':'粘贴 Google AI Studio 的 API Key')+'"><p class="help">只交给本机后端，Windows 加密保存；页面不会回显 Key。</p><div class="key-status">'+esc(c.gemini.error||('配置来源：'+c.gemini.source))+'</div><label class="field-label" for="gemini-model">当前模型</label><input class="field" id="gemini-model" value="'+esc(s.gemini_model)+'" required spellcheck="false"><div class="model-picker"><select class="field" id="model-list" aria-label="可用 Gemini 模型"><option value="">选择已获取的模型…</option>'+state.models.map(name=>'<option value="'+esc(name)+'">'+esc(name)+'</option>').join('')+'</select><button type="button" class="button" id="fetch-models">保存并获取列表</button></div><p class="help" id="model-note">获取列表不生成回答。列表不保证模型对当前账号可用或有免费额度；不会自动换模型或重试。</p><label class="field-label" for="gemini-proxy">本地代理（可选）</label><input class="field" id="gemini-proxy" value="'+esc(s.gemini_proxy||'')+'" placeholder="例如 http://127.0.0.1:7897"><p class="help">只影响 Gemini。Clash 用户可填写本机 HTTP/混合端口；留空使用启动环境，保存后立即生效。</p></section><section class="setting-card"><h2><span class="avatar">C</span>Codex</h2><label class="field-label" for="codex-model">模型名称（可选）</label><input class="field" id="codex-model" list="codex-options" value="'+esc(s.codex_model||'')+'" placeholder="留空使用 Codex CLI 当前默认模型" spellcheck="false"><datalist id="codex-options">'+(c.codex_models||[]).map(name=>'<option value="'+esc(name)+'">').join('')+'</datalist><p class="help">沿用 ChatGPT 登录，不需要 OpenAI API Key。填写 CLI 支持的模型名称；能否使用取决于账号与 CLI 版本。</p><div class="key-status">'+(c.codex.configured?'CLI 已找到；登录与额度由 Codex 账号决定。':'未找到 CLI，请按使用指南安装并登录。')+'</div></section><section class="setting-card"><h2>'+icon('settings')+'对话偏好</h2><label class="field-label" for="interaction">两位 AI 如何回应</label><select class="field" id="interaction"><option value="together">一起聊 · 第二位可以接着第一位补充</option><option value="independent">各自回答 · 同轮互不影响</option></select><p class="help">一起聊每次仍最多两次调用；你发送才继续。深入讨论的首轮始终独立。</p><div class="field-row"><div><label class="field-label" for="default-rounds">默认讨论轮数</label><select class="field" id="default-rounds"><option value="1">1 轮</option><option value="2">2 轮</option><option value="3">3 轮</option></select></div><div><label class="field-label" for="timeout">单次超时（秒）</label><input class="field" id="timeout" type="number" min="10" max="600" value="'+s.timeout+'" required></div></div><div class="save-row"><button class="button primary" id="save-settings" type="submit">保存配置</button><small>保存不会生成回答</small></div></section></form><section class="setting-card"><h2>'+icon('moon')+'外观</h2><label class="field-label" for="theme-choice">主题</label><select class="field" id="theme-choice"><option value="system">跟随系统</option><option value="light">浅色 · 暖白</option><option value="dark">深色 · 墨灰</option></select><p class="help">高亮保留暖橙和淡紫，正文保持清晰。</p></section></div><aside class="settings-aside"><section class="setting-card"><h2>'+icon('history')+'本地数据</h2><p class="help">会话、回收站与配置保存在这里。换设备前可导出重要会话。</p><div class="path-note">'+esc(c.data_dir)+'</div></section><section class="setting-card"><h2>'+icon('chat')+'浏览器打开</h2><p class="help">服务运行后，在浏览器打开这个地址。</p><div class="local-address"><code>'+esc(location.origin)+'/</code><button class="button" id="copy-address" type="button">复制地址</button></div></section><section class="info-box"><h3>第一次连接</h3><p>1. 安装 Codex CLI 并用 ChatGPT 登录。<br>2. 在 Google AI Studio 获取 Key，粘贴并保存。<br>3. 先只选 Gemini 发送一句话，确认可用。</p><p>模型和配额以服务提供方为准。地区受限、模型繁忙与配额错误会分别显示。</p><button class="button" id="open-guide">完整使用指南 ↗</button></section></aside></div></div>';
 $('#default-rounds').value=String(s.rounds);$('#interaction').value=s.interaction||'together';$('#theme-choice').value=storage.get('theme','system');$('#save-settings').disabled=busy();$('#fetch-models').disabled=busy();
 $('#copy-address').onclick=()=>copy(location.origin+'/');$('#open-guide').onclick=()=>navigate('guide');$('#model-list').onchange=e=>{if(e.target.value)$('#gemini-model').value=e.target.value;};$('#theme-choice').onchange=e=>setTheme(e.target.value);
 $('#settings-form').onsubmit=async e=>{e.preventDefault();await saveSettings();};
 $('#fetch-models').onclick=async()=>{const button=$('#fetch-models');button.disabled=true;button.textContent='正在获取…';
  try{if(!await saveSettings(false))return;const data=await api('/api/models',{});state.models=data.models;storage.set('models',JSON.stringify(state.models));$('#model-list').innerHTML='<option value="">选择可用模型…</option>'+state.models.map(name=>'<option value="'+esc(name)+'">'+esc(name)+'</option>').join('');$('#model-note').textContent='已获取 '+state.models.length+' 个文本模型，选择后点“保存配置”。实际可用性与配额以调用结果为准。';toast('模型列表已更新');}
  catch(e){toast(e.message,true);}finally{if(button.isConnected){button.disabled=false;button.textContent='保存并获取列表';}}
 };
};
async function saveSettings(notify=true){
 const button=$('#save-settings');button.disabled=true;
 try{state.config=await api('/api/config',{api_key:$('#api-key').value,gemini_model:$('#gemini-model').value,gemini_proxy:$('#gemini-proxy').value,codex_model:$('#codex-model').value,interaction:$('#interaction').value,timeout:Number($('#timeout').value),rounds:Number($('#default-rounds').value)});$('#api-key').value='';renderSidebar();if(notify){renderSettings();toast('配置已保存');}return true;}catch(e){toast(e.message,true);return false;}finally{if(button.isConnected)button.disabled=busy();}
}
function renderGuide(){
 $('#page').innerHTML='<div class="content-page">'+heading('一起用好 DualMind','模型连接、工作方式与快捷操作，都放在这里。')+'<div class="guide-grid">'+[
 ['先连接，再聊天','<p><b>Codex：</b>安装官方 CLI，运行 codex login，用已有 ChatGPT 账号登录。</p><p><b>Gemini：</b>用 Google AI Studio 获取 API Key，在模型设置里保存。不要把 Key 粘贴到对话中。</p><p>初次先选一个模型发一句短消息，配额和支持地区以提供方规则为准。</p>'],
 ['像群聊一样，也能各自思考','<p><b>聊天：</b>自然接话，不套分析模板。第二位可以看到第一位本轮回复。</p><p><b>协作：</b>一起做计划、写作、分析和产出代码。</p><p><b>深入讨论：</b>首轮独立，之后交换具体看法，最后生成五部分报告。</p><p>切到“各自回答”，可以避免同轮答案互相影响。</p>'],
 ['常用操作','<ul><li>Enter 发送，Shift+Enter 换行，Ctrl+Enter 也能发送；输入法选词时不会发送。</li><li>消息以 @Codex 或 @Gemini 开头，可以单独点名。</li><li>Ctrl+Shift+O 新建会话；Ctrl+K 打开历史搜索。</li><li>消息和代码可以复制，会话可导出 Markdown。</li><li>文本文件可拖进输入框，只加入文本，不执行代码；单文件不超过 64 KB，消息合计不超过 12000 字。</li><li>草稿在当前浏览器自动保存。</li></ul>'],
 ['会话与模型管理','<p>置顶、重命名、全文搜索、导出、复制会话都不调用模型。</p><p>删除会移入本地回收站，可以恢复；编辑消息或重新生成会创建新分支，保留原会话。</p><p>模型设置可获取 Gemini 列表，或手动填写两位模型的名称；新设置用于下一条消息，历史保留原模型标签。</p>'],
 ['你掌握调用节奏','<p>单独点名最多一次，两位一起最多两次；深入讨论为 2 × 轮数 + 1 次，最多三轮。</p><p>没有无限互聊、自动重试或暗中切换模型。停止会阻止后续调用；已发出的 Gemini 请求可能等到返回或超时。</p><p>上下文保留最近 12 条、约 16000 字，长任务请重申关键背景；共识也需要事实核查。</p>'],
 ['连接问题怎么处理','<p><b>400 地区限制：</b>检查出口和支持条件。</p><p><b>404：</b>模型可能未开放或退役。</p><p><b>429：</b>配额或频率限制。</p><p><b>503 high demand：</b>模型繁忙，稍后只重新生成 Gemini，避免重复调用 Codex。</p><p>Clash 用户可在设置中填写本机 HTTP/混合代理，保存即生效。</p>']
 ].map(([title,body])=>'<section class="setting-card"><h2>'+title+'</h2>'+body+'</section>').join('')+'</div></div>';
}
$('#rename-form').onsubmit=async e=>{e.preventDefault();try{const session=await api('/api/rename',{id:state.renameId,title:$('#rename-title').value});if(state.session?.id===session.id)state.session=session;$('#rename-dialog').close();await refreshHistory();if(state.view==='history')renderHistory();else if(state.view==='reports')renderReports();else updateConversation();toast('标题已保存');}catch(e){toast(e.message,true);}};
$('#new-session').onclick=()=>newSession();
$('#exit-app').onclick=()=>confirmActionDialog('退出 DualMind？',busy()?'当前任务将停止，已完成的内容保留。':'历史与设置保留在本机。',async()=>{try{saveDraft();await api('/api/shutdown',{});$('#page').innerHTML='<div class="content-page">'+heading('已退出 DualMind','可以关闭这个窗口。')+'</div>';clearInterval(pollTimer);clearInterval(pingTimer);}catch(e){toast(e.message,true);}});
document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.shiftKey&&e.key.toLowerCase()==='o'){e.preventDefault();newSession();}if(e.ctrlKey&&e.key.toLowerCase()==='k'){e.preventDefault();navigate('history');$('#history-search').focus();}});
window.addEventListener('beforeunload',saveDraft);
boot();
