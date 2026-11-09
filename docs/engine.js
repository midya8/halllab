// Independent exhaustive partial assignments, not the native augmenting-path solver.
export function validate(data) {
  if (!data || Array.isArray(data) || typeof data!=='object' || Object.keys(data).sort().join(',')!=='domains,values') throw Error('input needs exactly values and domains');
  const {values:m,domains:ds}=data;
  if (!Number.isInteger(m)||m<0||m>8||!Array.isArray(ds)||ds.length>6) throw Error('values 0..8; at most 6 domains');
  for(const d of ds) if(!Array.isArray(d)||d.some((v,i)=>!Number.isInteger(v)||v<0||v>=m||(i>0&&d[i-1]>=v))) throw Error('domains must be strictly increasing integer indices');
  return structuredClone(data);
}
export function analyze(raw) {
  const data=validate(raw),ds=data.domains,n=ds.length;
  let best=-1,matching=[],count=0;
  const support=ds.map(d=>d.map(()=>null));
  function visit(i,used,a){
    if(i===n){
      if(used.size>best){best=used.size;matching=[...a];}
      if(used.size===n){count++;a.forEach((v,j)=>{let k=ds[j].indexOf(v);if(support[j][k]===null)support[j][k]=[...a];});}
      return;
    }
    for(const v of ds[i]) if(!used.has(v)){used.add(v);a.push(v);visit(i+1,used,a);a.pop();used.delete(v);}
    a.push(null);visit(i+1,used,a);a.pop();
  }
  visit(0,new Set(),[]);
  function halls(rows){
    const out=[];
    for(let mask=1;mask<2**n;mask++){
      const variables=Array.from({length:n},(_,i)=>i).filter(i=>(mask&(2**i))!==0);
      const neighbors=[...new Set(variables.flatMap(i=>rows[i]))].sort((a,b)=>a-b);
      if(neighbors.length<=variables.length)out.push({variables,neighbors,deficit:variables.length-neighbors.length});
    }
    return out;
  }
  const edges=[],filtered=ds.map(()=>[]);
  ds.forEach((d,i)=>d.forEach((v,k)=>{
    const assignment=support[i][k],supported=assignment!==null;
    if(supported)filtered[i].push(v);
    const fd=ds.map((r,j)=>j===i?[v]:r.filter(w=>w!==v));
    edges.push({variable:i,value:v,supported,assignment,obstruction:supported?null:halls(fd).find(h=>h.deficit>0)});
  }));
  const rounds=[structuredClone(ds)];
  while(true){
    const old=rounds.at(-1);
    const next=old.map((d,i)=>d.filter(v=>old.every((r,j)=>i===j||r.some(w=>w!==v))));
    rounds.push(next);if(JSON.stringify(next)===JSON.stringify(old))break;
  }
  return {schema:'halllab-v1',input:data,satisfiable:best===n,maximum_size:best,matching,solution_count:count,hall_sets:halls(ds),edges,filtered,pairwise_rounds:rounds};
}
