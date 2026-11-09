import {analyze as local,validate as baseValidate} from './engine.js';
export function overlaps(raw){
 if(!raw||Array.isArray(raw)||typeof raw!=='object'||Object.keys(raw).sort().join(',')!=='domains,scopes,values')throw Error('input needs exactly values, domains and scopes');
 baseValidate({values:raw.values,domains:raw.domains});const n=raw.domains.length,scopes=raw.scopes;
 if(!Array.isArray(scopes)||scopes.length>6||scopes.some(s=>!Array.isArray(s)||s.some((i,j)=>!Number.isInteger(i)||i<0||i>=n||(j>0&&s[j-1]>=i)))||new Set(scopes.map(s=>JSON.stringify(s))).size!==scopes.length)throw Error('scopes: up to six distinct increasing index lists');
 const data=structuredClone(raw);let ds=structuredClone(data.domains);const rounds=[];
 while(true){const constraints=scopes.map(s=>local({values:data.values,domains:s.map(i=>ds[i])})),next=ds.map(d=>[...d]);scopes.forEach((s,k)=>s.forEach((i,j)=>{next[i]=next[i].filter(v=>constraints[k].filtered[j].includes(v));}));rounds.push({domains:ds,constraints,next_domains:next});if(JSON.stringify(next)===JSON.stringify(ds))break;ds=next;}
 let count=0;const bins=scopes.map(()=>0),first=new Map();
 function walk(i,a){if(i<n){for(const v of data.domains[i]){a.push(v);walk(i+1,a);a.pop();}return;}
  const k=scopes.findIndex(s=>new Set(s.map(j=>a[j])).size!==s.length);if(k>=0){bins[k]++;return;}count++;a.forEach((v,j)=>{const key=j+':'+v;if(!first.has(key))first.set(key,[...a]);});}
 walk(0,[]);const global=data.domains.map(()=>[]),edges=[];
 data.domains.forEach((d,i)=>d.forEach(v=>{const assignment=first.get(i+':'+v)??null,supported=assignment!==null;if(supported)global[i].push(v);edges.push({variable:i,value:v,local:ds[i].includes(v),supported,assignment});}));
 return {schema:'halllab-overlaps-v1',input:data,rounds,local_domains:ds,local_consistent:ds.every(d=>d.length>0)&&rounds.at(-1).constraints.every(r=>r.satisfiable),satisfiable:count>0,solution_count:count,rejection_counts:bins,global_domains:global,edges};
}
