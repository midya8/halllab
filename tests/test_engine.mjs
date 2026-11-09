import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {spawnSync} from 'node:child_process';import {analyze} from '../docs/engine.js';
const controls=JSON.parse(fs.readFileSync(new URL('../docs/controls.json',import.meta.url)));
test('complete reports agree with independent native matching and tuple checker',()=>{
 const inputs=controls.map(c=>c.input);let seed=1927;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2**32;};
 for(let k=0;k<160;k++){const m=Math.floor(random()*9),n=Math.floor(random()*7);inputs.push({values:m,domains:Array.from({length:n},()=>Array.from({length:m},(_,i)=>i).filter(()=>random()<.5))});}
 for(let a=0;a<8;a++)for(let b=0;b<8;b++)for(let c=0;c<8;c++)inputs.push({values:3,domains:[a,b,c].map(mask=>[0,1,2].filter(v=>mask>>v&1))});
 const script='import json,sys\nfrom halllab import analyze,verify\na=[analyze(d) for d in json.load(sys.stdin)]\nassert all(verify(r) for r in a)\nprint(json.dumps(a))';
 const p=spawnSync(process.env.PYTHON||'python',['-c',script],{input:JSON.stringify(inputs),encoding:'utf8',maxBuffer:32*1024*1024});assert.equal(p.status,0,p.stderr);
 const expected=JSON.parse(p.stdout),totals={reports:inputs.length,edges:0,supports:0,obstructions:0,hallSets:0,rounds:0};
 inputs.forEach((d,i)=>{let saved=JSON.stringify(d),r=analyze(d);assert.deepEqual(r,expected[i]);assert.equal(JSON.stringify(d),saved);totals.edges+=r.edges.length;totals.supports+=r.edges.filter(e=>e.supported).length;totals.obstructions+=r.edges.filter(e=>!e.supported).length;totals.hallSets+=r.hall_sets.length;totals.rounds+=r.pairwise_rounds.length;});console.log(totals);
});
test('strict input and boundary conventions',()=>{for(const d of [null,[],{}, {values:true,domains:[]},{values:2,domains:[[1,0]]},{values:1,domains:[[true]]},{values:2,domains:[[0,0]]},{values:8,domains:Array(7).fill([])}])assert.throws(()=>analyze(d));assert.equal(analyze({values:0,domains:[]}).solution_count,1);assert.equal(analyze(controls.at(-1).input).solution_count,20160);});
