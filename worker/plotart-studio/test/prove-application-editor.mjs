import assert from 'node:assert/strict';
import vm from 'node:vm';
import { EDIT_JS } from '../src/application-revision-ui.js';
import { REVIEW_JS } from '../src/application-review-ui.js';
new Function(EDIT_JS);
new Function(REVIEW_JS);
console.log('PASS both generated browser scripts parse');
const handlers={},elements={};let reloads=0;
const location={hash:'',reload(){reloads++;}};
await vm.runInNewContext(EDIT_JS,{
  location,
  addEventListener(event,handler){handlers[event]=handler;},
  document:{getElementById(id){return elements[id]||=( {} );}}
},{timeout:1000});
location.hash='#PA-AP-261116-ABCDEF/'+'a'.repeat(64);
handlers.hashchange();
assert.equal(reloads,1);
console.log('PASS a renewed application link reloads an existing tab');
location.hash='#unrelated';handlers.hashchange();
assert.equal(reloads,1);
console.log('PASS unrelated fragments do not reload the page');
