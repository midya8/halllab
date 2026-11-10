export function validate(data){
 if(!data||Array.isArray(data)||typeof data!=='object'||Object.keys(data).sort().join(',')!=='domains,values')throw Error('input needs exactly values and domains');
 const {values:m,domains:ds}=data;
 if(!Number.isInteger(m)||m<0||m>8)throw Error('values must be an integer in 0..8');
 if(!Array.isArray(ds)||ds.length>6)throw Error('domains must be a list of at most 6 lists');
 for(const row of ds)if(!Array.isArray(row)||row.some((v,k)=>!Number.isInteger(v)||v<0||v>=m||(k>0&&v<=row[k-1])))throw Error('domains must be sorted unique integer indices');
 return structuredClone(data);
}
export function alternating(input){
 const data=validate(input),ds=data.domains,n=ds.length,m=data.values,N=n+m,partials=[],solutions=[];
 // Complete assignment recursion is independent of Python augmenting matching.
 const visit=(i,a,used)=>{if(i===n){partials.push([...a]);if(!a.includes(null))solutions.push([...a]);return;}for(const v of [...ds[i],null])if(v===null||!used.has(v)){a.push(v);const next=new Set(used);if(v!==null)next.add(v);visit(i+1,a,next);a.pop();}};visit(0,[],new Set());
 const sizes=partials.map(a=>a.filter(v=>v!==null).length),size=sizes.reduce((a,b)=>Math.max(a,b),0),matching=partials[sizes.indexOf(size)],sat=solutions.length>0;
 const graph=Array.from({length:N},()=>[]),arcs=[];
 ds.forEach((row,i)=>row.forEach(v=>{const matched=matching[i]===v,source=matched?i:n+v,target=matched?n+v:i;graph[source].push(target);arcs.push({variable:i,value:v,source,target,matched});}));graph.forEach(r=>r.sort((a,b)=>a-b));
 const bfs=(g,starts)=>{const paths=new Map(starts.map(u=>[u,[u]])),queue=[...starts];for(const u of queue)for(const v of g[u])if(!paths.has(v)){paths.set(v,[...paths.get(u),v]);queue.push(v);}return paths;};
 const classes=g=>{const reached=g.map((_,i)=>bfs(g,[i])),remaining=new Set(g.map((_,i)=>i)),out=[];while(remaining.size){const i=Math.min(...remaining),group=[...remaining].filter(j=>reached[i].has(j)&&reached[j].has(i));out.push(group);for(const j of group)remaining.delete(j);}return out;};
 const components=classes(graph),free=Array.from({length:m},(_,v)=>v).filter(v=>!matching.includes(v)),starts=free.map(v=>n+v),paths=bfs(graph,starts),layers=[starts],seen=new Set(starts);
 while(true){const next=[...new Set(layers.at(-1).flatMap(u=>graph[u]).filter(v=>!seen.has(v)))].sort((a,b)=>a-b);layers.push(next);next.forEach(v=>seen.add(v));if(!next.length)break;}
 const expanded=graph.map(r=>[...r]);expanded.push([]);for(let v=0;v<m;v++)if(matching.includes(v))expanded[n+v].push(N);else expanded[N].push(n+v);
 const deficient=rows=>{for(let mask=1;mask<2**n;mask++){const variables=rows.map((_,i)=>i).filter(i=>mask&2**i),neighbors=[...new Set(variables.flatMap(i=>rows[i]))].sort((a,b)=>a-b);if(neighbors.length<variables.length)return{variables,neighbors,deficit:variables.length-neighbors.length};}throw Error('no Hall obstruction');};
 const filtered=ds.map(()=>[]),edges=[];
 ds.forEach((row,i)=>row.forEach(v=>{
  const supported=solutions.some(a=>a[i]===v),same=components.some(g=>g.includes(i)&&g.includes(n+v));
  const reason=!sat?'unsatisfiable':matching[i]===v?'base':same?'cycle':paths.has(n+v)?'free-path':'pruned';let walk=[],assignment=null,obstruction=null;
  if(supported){filtered[i].push(v);assignment=[...matching];if(reason==='cycle')walk=[n+v,...bfs(graph,[i]).get(n+v)];else if(reason==='free-path')walk=[...paths.get(n+v),i,n+matching[i]];
   for(let k=0;k+1<walk.length;k++)if(walk[k+1]<n)assignment[walk[k+1]]=walk[k]-n;
   if(!solutions.some(a=>JSON.stringify(a)===JSON.stringify(assignment))||assignment[i]!==v)throw Error('invalid flip');
  }else obstruction=deficient(ds.map((d,j)=>j===i?[v]:d.filter(w=>w!==v)));
  if(supported!==['base','cycle','free-path'].includes(reason))throw Error('graph disagrees with assignment recursion');
  edges.push({variable:i,value:v,supported,reason,walk,assignment,obstruction});
 }));
 return{schema:'halllab-alternating-v1',input:data,satisfiable:sat,maximum_size:size,matching,nodes:[...ds.map((_,i)=>'x'+i),...Array.from({length:m},(_,v)=>'v'+v)],arcs,components,free_values:free,reach_layers:layers,dummy_components:classes(expanded),obstruction:sat?null:deficient(ds),edges,filtered};
}
