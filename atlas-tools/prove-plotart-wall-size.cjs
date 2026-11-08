'use strict';
const assert=require('node:assert/strict');
const tool=require('../plotart/assets/plotart-wall-size.js');
let count=0;function check(name,fn){fn();count++;console.log('PASS '+name);}
check('200 cm furniture gives 133–150 cm range',()=>{let r=tool.measure(tool.defaults);assert.equal(r.low,133);assert.equal(r.high,150);assert.equal(r.valid,true);assert.equal(r.fits,true);});
check('furniture and artwork use the same centimetre geometry',()=>{let r=tool.measure({...tool.defaults,reference:240,width:160,height:100});assert.equal(r.wallWidth,340);assert.equal(r.x,90);assert.equal(r.y,65);assert.equal((r.wallWidth-2*r.x)/240,160/240);});
check('portrait work keeps its actual height and width',()=>{let r=tool.measure({...tool.defaults,width:100,height:140});assert.equal(r.y,25);assert.equal(r.fits,true);});
check('oversize clear-wall work is identified',()=>{let r=tool.measure({...tool.defaults,mode:'wall',reference:100,width:120});assert.equal(r.wallWidth,100);assert.equal(r.fits,false);});
check('insufficient height above furniture is identified',()=>{assert.equal(tool.measure({...tool.defaults,room:180,height:140}).fits,false);});
check('clear-wall layout centres vertically',()=>{let r=tool.measure({...tool.defaults,mode:'wall',reference:300,width:100,height:80});assert.equal(r.x,100);assert.equal(r.y,90);});
for(const [key,value]of [['reference',''],['width','abc'],['height',Infinity],['room',99],['width',0],['reference',1001],['mode','<script>'],['theme','url(https://bad.invalid)']])check('reject invalid '+key+' '+value,()=>assert.equal(tool.measure({...tool.defaults,[key]:value}).valid,false));
check('fractional centimetres are preserved to one decimal place',()=>{assert.equal(tool.measure({...tool.defaults,width:120.55}).state.width,120.6);});
check('share link round-trips all dimensions and colour',()=>{let s={mode:'wall',reference:320,room:270,width:101.5,height:142.3,theme:'green'};assert.deepEqual(tool.decode(tool.encode(s)),s);});
check('malicious fragment cannot change controls or create markup',()=>{assert.deepEqual(tool.decode('#mode=%3Cscript%3E&theme=bad&width=1e99'),tool.defaults);});
check('unrelated fragment parameters are ignored',()=>{assert.deepEqual(tool.decode('#email=private%40example.com&redirect=https%3A%2F%2Fbad.invalid'),tool.defaults);});
console.log('WALL SIZE CALCULATIONS · '+count+' checks passed');
