import {validate as baseValidate} from './engine.js';
export function conflicts(raw){
 if(!raw||Array.isArray(raw)||typeof raw!=='object'||Object.keys(raw).sort().join(',')!=='domains,scopes,values')throw Error('input needs exactly values, domains and scopes');
 baseValidate({values:raw.values,domains:raw.domains});const n=raw.domains.length,scopes=raw.scopes;
 if(!Array.isArray(scopes)||scopes.length>6||scopes.some(s=>!Array.isArray(s)||s.some((i,j)=>!Number.isInteger(i)||i<0||i>=n||(j>0&&s[j-1]>=i)))||new Set(scopes.map(s=>JSON.stringify(s))).size!==scopes.length)throw Error('scopes: up to six distinct increasing index lists');
 const input=structuredClone(raw),m=scopes.length,size=1<<m,full=size-1,subsets=[];
 // Independently solve every subset by a recursive assignment walk with early rejection.
 for(let mask=0;mask<size;mask++){
  const chosen=Array.from({length:m},(_,k)=>k).filter(k=>mask>>k&1);let count=0,first=null;
  function walk(i,a){if(i===n){count++;if(first===null)first=[...a];return;}
   for(const v of input.domains[i]){a.push(v);if(chosen.every(k=>{const s=scopes[k].filter(j=>j<=i);return new Set(s.map(j=>a[j])).size===s.length;}))walk(i+1,a);a.pop();}}
  walk(0,[]);subsets.push({scopes:chosen,solution_count:count,assignment:first});
 }
 const cores=[];
 for(let mask=0;mask<size;mask++){const row=subsets[mask];if(!row.solution_count&&row.scopes.every(k=>subsets[mask^(1<<k)].solution_count))cores.push({scopes:row.scopes,deletions:row.scopes.map(k=>({removed:k,scopes:subsets[mask^(1<<k)].scopes,assignment:subsets[mask^(1<<k)].assignment}))});}
 const repairs=[];
 for(let removed=0;removed<size;removed++){const kept=full^removed,indices=subsets[removed].scopes;
  if(subsets[kept].solution_count&&indices.every(k=>!subsets[kept|(1<<k)].solution_count))repairs.push({removed:indices,kept:subsets[kept].scopes,assignment:subsets[kept].assignment,restorations:indices.map(k=>{const active=subsets[kept|(1<<k)].scopes;return {restored:k,scopes:active,core:cores.find(c=>c.scopes.every(j=>active.includes(j))).scopes};})});
 }
 return {schema:'halllab-conflicts-v1',input,background_satisfiable:subsets[0].solution_count>0,satisfiable:subsets[full].solution_count>0,subsets,cores,repairs};
}
