import {analyze} from './engine.js';
const $=id=>document.getElementById(id),controls=await fetch('controls.json').then(r=>r.json());let report=null;
const fmt=a=>a.length?a.map(v=>'v'+v).join(', '):'∅',xs=a=>a.map(i=>'x'+i).join(', ')||'∅';
function options(id,items){$(id).replaceChildren(...items.map((text,i)=>{const o=document.createElement('option');o.value=i;o.textContent=text;return o;}));$(id).disabled=items.length===0;}
function graph(edge){
 const {domains:ds,values:m}=report.input,n=ds.length,h=Math.max(1,n,m)*47+36,ns='http://www.w3.org/2000/svg';
 const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 460 ${h}`);svg.setAttribute('role','img');svg.setAttribute('aria-label','Original domains; green selected matching, purple inspected edge');
 const yy=(i,k)=>30+(i+.5)*(h-50)/Math.max(1,k);
 const assignment=edge?.assignment||report.matching;
 ds.forEach((d,i)=>d.forEach(v=>{const line=document.createElementNS(ns,'line');const selected=edge&&edge.variable===i&&edge.value===v;const matched=assignment[i]===v;Object.entries({x1:72,y1:yy(i,n),x2:388,y2:yy(v,m),stroke:selected?'#c9b7ff':matched?'#87e6b6':'#3d465c','stroke-width':selected?5:matched?3:1,'stroke-dasharray':selected&&!edge.supported?'6 4':'none'}).forEach(([k,v])=>line.setAttribute(k,v));svg.append(line);}));
 for(const [k,x,p] of [[n,52,'x'],[m,408,'v']])for(let i=0;i<k;i++){const c=document.createElementNS(ns,'circle');c.setAttribute('cx',x);c.setAttribute('cy',yy(i,k));c.setAttribute('r',19);c.setAttribute('fill','#252d41');c.setAttribute('stroke','#7c88a5');svg.append(c);const t=document.createElementNS(ns,'text');t.setAttribute('x',x);t.setAttribute('y',yy(i,k)+5);t.setAttribute('text-anchor','middle');t.textContent=p+i;svg.append(t);}
 if(n===0){const t=document.createElementNS(ns,'text');t.setAttribute('x',20);t.setAttribute('y',25);t.textContent='Empty variable scope';svg.append(t);}
 $('graph').replaceChildren(svg);
}
function renderEdge(){const e=report.edges[Number($('edge').value)];if(!e){$('edge-status').textContent='No original edges to inspect.';$('edge-proof').textContent='No edge certificate needed.';$('forced').textContent='';graph(null);return;}
 $('edge-status').textContent=`x${e.variable} = v${e.value}: ${e.supported?'SUPPORTED':'BLOCKED'}`;
 if(e.supported){$('edge-proof').textContent='Complete injective assignment\n'+e.assignment.map((v,i)=>`x${i}=v${v}`).join(' · ');$('forced').textContent='Every variable is assigned; all values differ. This assignment includes the inspected edge.';}
 else{const h=e.obstruction;$('edge-proof').textContent=`Forced Hall obstruction\nS = {${xs(h.variables)}}\nN(S) = {${fmt(h.neighbors)}}\n${h.variables.length} variables > ${h.neighbors.length} values\ndeficit = ${h.deficit}`;$('forced').textContent=`Force x${e.variable}=v${e.value}; remove v${e.value} from every other domain. The certificate refers to these residual domains: `+report.input.domains.map((d,j)=>`x${j}:{${fmt(j===e.variable?[e.value]:d.filter(v=>v!==e.value))}}`).join(' · ');}
 graph(e);
}
function renderHall(){const h=report.hall_sets[Number($('hall').value)];$('hall-proof').textContent=h?`S = {${xs(h.variables)}}\nN(S) = {${fmt(h.neighbors)}}\n|S| = ${h.variables.length}; |N(S)| = ${h.neighbors.length}\ndeficit = ${h.deficit} (${h.deficit?'DEFICIENT: no full assignment':'TIGHT: no contradiction'})`:'No nonempty tight or deficient original subset. Every nonempty subset has slack.';}
function renderRound(){let i=Number($('round').value);$('round-proof').textContent=report.pairwise_rounds[i].map((d,j)=>`x${j}: {${fmt(d)}}`).join('\n')||'Empty scope: fixed point.';}
function run(){try{report=analyze(JSON.parse($('input').value));window.hallReport=report;$('error').textContent='';$('output').hidden=false;$('download').disabled=false;
 $('status').textContent=report.satisfiable?'A distinct assignment exists.':'No distinct assignment exists.';
 $('count').textContent=report.solution_count.toLocaleString('en-US');$('size').textContent=report.maximum_size+' / '+report.input.domains.length;$('retained').textContent=report.filtered.flat().length+' / '+report.edges.length;$('pairwise').textContent=report.pairwise_rounds.at(-1).flat().length;
 $('matching').textContent='Chosen maximum matching: '+(report.matching.map((v,i)=>`x${i} → ${v===null?'unmatched':'v'+v}`).join(' · ')||'empty assignment');
 options('edge',report.edges.map(e=>`x${e.variable} = v${e.value} / ${e.supported?'supported':'blocked'}`));
 const firstBlocked=report.edges.findIndex(e=>!e.supported);if(firstBlocked>=0)$('edge').value=firstBlocked;
 options('hall',report.hall_sets.map(h=>`{${xs(h.variables)}} / ${h.deficit?'deficit '+h.deficit:'tight'}`));
 options('round',report.pairwise_rounds.map((_,i)=>i===0?'0 / original':i===report.pairwise_rounds.length-1?`${i} / repeated fixed point`:`${i} / synchronous pruning`));$('round').value=report.pairwise_rounds.length-1;
 $('domains').replaceChildren(...report.input.domains.map((d,i)=>{const tr=document.createElement('tr');for(const text of ['x'+i,fmt(d),fmt(report.pairwise_rounds.at(-1)[i]),fmt(report.filtered[i])]){const td=document.createElement('td');td.textContent=text;tr.append(td);}return tr;}));
 $('report').value=JSON.stringify(report,null,2);renderEdge();renderHall();renderRound();
 }catch(e){report=null;window.hallReport=null;$('output').hidden=true;$('download').disabled=true;$('report').value='';$('graph').replaceChildren();$('error').textContent=e.message;}}
options('control',controls.map(c=>c.name));function choose(){const c=controls[Number($('control').value)];$('input').value=JSON.stringify(c.input,null,2);$('why').textContent=c.why;run();}
$('control').onchange=choose;$('run').onclick=run;$('edge').onchange=renderEdge;$('hall').onchange=renderHall;$('round').onchange=renderRound;$('input').oninput=()=>{report=null;window.hallReport=null;$('output').hidden=true;$('download').disabled=true;$('report').value='';$('graph').replaceChildren();$('why').textContent='Edited input; analyze to generate a new report.';};
$('download').onclick=()=>{if(!report)return;const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='halllab-report.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};choose();
