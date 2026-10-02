import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';
import { GlobalFonts } from '@napi-rs/canvas';

const root = process.env.CLARO_REPO;
if (!root) throw new Error('Set CLARO_REPO to the repository root');
const skill = process.env.CLARO_PRESENTATIONS_SKILL;
const python = process.env.CLARO_RUNTIME_PYTHON;
const build = path.join(root, '.local/deck-build');
const output = path.join(root, 'submission');
const { resolvePresentationFont, applyPresentationChartFont, finalizePresentation } = await import(
  pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href
);
const fontDir = process.env.CLARO_FONT_DIR;
for (const weight of ['Regular', 'Bold']) {
 if (!GlobalFonts.registerFromPath(path.join(fontDir, `NotoSans-${weight}.ttf`), 'Noto Sans')) {
  throw new Error('Could not load bundled Noto Sans font');
 }
}
const font = resolvePresentationFont({fontFamily:'Noto Sans'});
const C = {navy:'#0B1932', white:'#F7FAFC', ink:'#14243B', teal:'#149F8E', mint:'#67E2C4', gray:'#587087', light:'#DCE9ED', muted:'#A4B7C8'};
const ppt = Presentation.create({slideSize:{width:1280,height:720}});
const json = async (p) => JSON.parse(await fs.readFile(path.join(root,p),'utf8'));
const fraud = await json('docs/evidence/ml-evaluation.json');
const language = await json('docs/evidence/language-evaluation.json');
const deployment = await json('submission/deployment.json');
const challenge = await json('docs/evidence/system-challenge-evaluation.json');
const regression = await json('docs/evidence/system-challenge-regression.json');

function text(slide, value, x,y,w,h,size=26,color=C.ink,bold=false,align='left') {
 const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 s.text=value;
 s.text.style={typeface:font,fontSize:size,color,bold,alignment:align,verticalAlignment:'top',autoFit:'none',wrap:'word',insets:{top:0,bottom:0,left:0,right:0}};
 return s;
}
function slide(title, number, dark=false) {
 const s=ppt.slides.add();s.background.fill=dark?C.navy:C.white;
 text(s,title,64,47,1152,100,44,dark?C.white:C.ink,true);
 text(s,`Claro  /  Factored 2026  /  ${number}`,64,672,1100,25,15,dark?C.muted:C.gray);
 return s;
}
function notes(s,content){s.speakerNotes.textFrame.setText(content);}
function chart(s,{x,y,w,h,categories,values,labels,max=1,format='0%',color=C.teal}){
 const c=s.charts.add('bar',{
  position:{left:x,top:y,width:w,height:h},categories,
  series:[{name:'Measured result',values:values.map(v=>Number(v.toPrecision(9))),fill:color,valuesFormatCode:format,
   points:categories.map((_,idx)=>({idx,fill:idx===0?'#8DA8B8':idx===1?C.teal:'#427D9A'})),
   dataLabelOverrides:labels?.map((v,idx)=>({idx,text:v,position:'outEnd',showValue:true,textStyle:{typeface:font,fontSize:20,fill:C.ink,bold:true}}))}],
  barOptions:{direction:'column',grouping:'clustered',gapWidth:90},hasLegend:false,
  chartFill:'none',chartLine:{fill:'none',width:0},plotAreaFill:'none',plotAreaLine:{fill:'none',width:0},
  xAxis:{textStyle:{typeface:font,fontSize:19,fill:C.gray},line:{fill:C.light,width:1}},
  yAxis:{min:0,max,numberFormatCode:format,textStyle:{typeface:font,fontSize:16,fill:C.gray},majorGridlines:{fill:C.light,width:1},line:{fill:'none',width:0}},
  dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:font,fontSize:20,fill:C.ink,bold:true}},
 });applyPresentationChartFont(c,{fontFamily:font});return c;
}
async function screenshot(s,name,position,alt,crop){
 const file=path.join(output,'assets',name);
 const image=s.images.add({blob:await fs.readFile(file),contentType:'image/jpeg',alt,fit:crop?'cover':'contain',position});
 if(crop) image.crop=crop;
}

// 1. Data-backed problem and focused customer-service scope.
{
 const s=ppt.slides.add();s.background.fill=C.navy;
 text(s,'Claro',64,46,760,105,86,C.white,true);
 text(s,'Banking support with\nverified outcomes',64,173,730,150,51,C.white,true);
 text(s,'Spanish and Portuguese transaction support\nwith confirmed cases for human review',67,351,730,90,27,C.muted);
 text(s,'4.43M',890,167,320,78,64,C.mint,true);
 text(s,'transactions audited',893,251,320,36,24,C.white);
 text(s,'42',890,337,280,78,64,C.mint,true);
 text(s,'distinct customer utterances\nin organizer transcripts',893,419,320,75,24,C.white);
 text(s,'We keep organizer analysis, authored language scenarios and public demo fixtures separate.',67,542,1120,75,27,C.white);
 text(s,'Factored AI & Data Hackathon 2026  /  Team nicoceron',67,669,1100,30,17,C.muted);
 notes(s,'Problem and scope: 23,495,188 organizer synthetic rows across 13 tables. Exactly 4,425,008 transaction rows. 171,321 transcripts contain only 42 distinct customer text strings, with no demonstrated Portuguese coverage or trustworthy dispute-intent labels. Source: docs/DATA_FINDINGS.md and docs/evidence/data-profile-summary.json. Focus on transaction support and confirmed dispute intake rather than inventing aligned dialogue labels. Public examples and policies are independently team-authored fixtures.');
}
// 2. Actual product evidence and workflow.
{
 const s=slide('Customer evidence and verified cases',2);
 await screenshot(s,'customer-case.jpg',{left:64,top:173,width:776,height:453},'Actual Claro customer demo with transaction evidence and a sandbox case proposal');
 text(s,'1  Understand',880,178,330,43,27,C.teal,true);
 text(s,'Ask for the transaction\nwhen the request is unclear.',880,225,330,77,23);
 text(s,'2  Show the evidence',880,323,330,43,27,C.teal,true);
 text(s,'Preserve amount, currency,\nstatus and historical source.',880,370,330,77,23);
 text(s,'3  Confirm and verify',880,468,330,43,27,C.teal,true);
 text(s,'Create one sandbox case.\nRead it back before success.',880,515,330,77,23);
 notes(s,'Screenshot: real running Claro UI, team-authored synthetic fixtures. Workflow: trusted test session, scoped record tools, exact versioned synthetic policy retrieval, a separate confirmation endpoint, atomic case commit, read-back verification, analyst queue. No real money movement, refunds or card blocking. Sources: README.md, docs/OPERATIONS.md, src/factored_banking/api.py and workflow.py.');
}
// 3. Native editable architecture diagram.
{
 const s=slide('Permissions and actions stay in service code',3,true);
 text(s,'The model advises the workflow. It cannot select an identity or execute a banking action.',64,147,1150,55,25,C.muted);
 const node=(label,x,y,w=230)=>{const n=s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:96},fill:'#132A44',line:{fill:'#365067',width:1.2}});n.text=label;n.text.style={typeface:font,fontSize:24,bold:true,color:C.white,alignment:'center',verticalAlignment:'middle',insets:{left:12,right:12,top:12,bottom:12}};return n;};
 const a=node('ES / PT browser',64,243);const b=node('Scoped sessions\nand record tools',364,243);const c=node('Local language\nclassifier',664,243);const d=node('Deterministic\nworkflow',964,243);
 const e=node('Receipt and\nanalyst queue',364,450);const f=node('SQLite commit\nand read-back',664,450);const g=node('Explicit case\nconfirmation',964,450);
 const link=(from,to,fromSide='right',toSide='left')=>s.shapes.connect(from,to,{kind:'straight',fromSide,toSide,line:{fill:C.mint,width:2},tail:{type:'triangle',width:'med',length:'med'}});
 link(a,b);link(b,c);link(c,d);link(d,g,'bottom','top');link(g,f,'left','right');link(f,e,'left','right');
 text(s,'Exact fixture facts\nVersioned demo policies',64,454,245,88,23,C.muted);
 text(s,'Opaque sessions + CSRF     Customer/workspace isolation     Idempotent confirmed writes',64,592,1140,58,24,C.white);
 notes(s,'Diagram objects and connectors are native/editable. Online sequence shows logical responsibility boundaries, not an exhaustive call graph. Public personas issue scoped sandbox identities, not bank customer authentication. Native SQLite persistence uses one worker, with reserved idempotency fingerprint before case side effect and fresh-connection read-back before receipt. Separate private DuckDB data/training jobs never serve organizer raw rows. Sources: docs/OPERATIONS.md, api.py, store.py, workflow.py.');
}
// 4. Independent numerical fraud experiment.
{
 const s=slide('Fraud candidates did not earn release',4);
 text(s,'4,425,008 validated transactions',64,161,565,50,29,C.teal,true);
 text(s,'Contracts, quarantine and source hashes\nStrictly prior customer/currency history\nTwo full runs with identical feature bytes',64,223,540,126,24);
 text(s,'Temporal evaluation',64,380,520,40,27,C.teal,true);
 text(s,'Train before January 2026\nCalibrate January, select February\nTest March through the June snapshot',64,430,535,113,24);
 text(s,'451,823 test transactions / 409 fraud labels',650,156,565,52,25,C.ink,true);
 text(s,'Average precision',650,203,565,35,21,C.gray);
 const ms=fraud.metrics.test;
 chart(s,{x:642,y:242,w:567,h:300,categories:['Constant','Logistic','CatBoost'],values:[ms.constant.average_precision,ms.logistic.average_precision,ms.catboost.average_precision],labels:['0.000905','0.000942','0.000938'],max:0.0011,format:'0.0000'});
 text(s,'4 / 409',670,567,230,60,42,C.teal,true);
 text(s,'fraud labels reached at 1% review\ncapacity by each learned candidate',880,569,330,63,21,C.ink);
 text(s,'Synthetic retrospective labels. Demo fixtures receive no fraud probability.',64,619,580,45,19,C.gray);
 notes(s,'Exact held-out results in docs/evidence/ml-evaluation.json and docs/ML_REPORT.md. Logistic AP0.0009415226700474275, CatBoost AP0.0009380975559168019, constant0.0009052217350599682. At1% review capacity:4,519 reviewed,4TP/4,515FP for either learned model. Training population3,735,596; fitted deterministic sample471,012 including all3,712positives, inverse-propensity negative weights8. Candidate promotion fixed on February before test. Excludes supplied fraud_score, target, current snapshots and future/simultaneous history. Full-snapshot feasibility diagnostics preceded temporal evaluation, so no externally blind claim. No learned promotion. Runtime organizer-domain population prior is explicitly not personalized. Public fixtures are out of domain. No prevented-loss or production-accuracy claim.');
}
// 5. Honest component and fresh system comparison.
{
 const s=slide('Measured language and workflow results',5);
 const languageSystems=['keyword_rules','tfidf_logistic','gemma3_4b_local'].map(k=>language.systems[k]);
 const challengeSystems=['keyword_rules','tfidf_logistic'].map(k=>challenge.systems[k]);
 const afterFix=regression.systems.tfidf_logistic;
 text(s,'Intent classification',64,151,550,43,29,C.teal,true);
 text(s,'140 frozen authored cases / macro-F1',64,194,550,37,22,C.gray);
 chart(s,{x:61,y:253,w:545,h:287,categories:['Rules','Local ML','Gemma 3'],values:languageSystems.map(v=>v.macro_f1),labels:languageSystems.map(v=>v.macro_f1.toFixed(3)),max:1,format:'0.0'});
 text(s,'First workflow challenge',668,151,545,43,29,C.teal,true);
 text(s,'70 independent-agent cases / correct outcomes',668,194,545,60,22,C.gray);
 chart(s,{x:663,y:253,w:545,h:287,categories:['Rules','Local ML'],values:challengeSystems.map(v=>v.outcome_accuracy),labels:challengeSystems.map(v=>`${v.correct_outcomes} / ${v.cases}`),max:1,format:'0%'});
 text(s,'117/140 exact labels correct',65,553,550,45,25,C.ink,true);
 text(s,'28/30 required handoffs on first pass',668,553,540,45,25,C.ink,true);
 text(s,'Authored synthetic cases, without independent human language review.',64,607,1145,30,20,C.gray);
 text(s,`After correcting cancellation: ${afterFix.correct_outcomes}/${afterFix.cases} outcomes and ${afterFix.verified_handoffs}/${afterFix.required_handoffs} handoffs in a regression replay.`,64,637,1145,28,19,C.gray);
 notes(s,'Sources: docs/LANGUAGE_EVALUATION.md, docs/SYSTEM_EVALUATION.md, docs/evidence/language-evaluation.json, system-challenge-evaluation.json. Component: training196/development56/test140 balanced synthetic cases, frozen semantic groups. Local ML TF-IDF/logistic117/140 macroF10.8230; rules65/140 F10.4207; local Gemma3 4B115/140 F10.8045. Small ML/Gemma difference is not claimed significant. Fresh system first pass61/70 versus43/70. Learned ES31/35, PT30/35, required verified handoffs28/30, unnecessary proposals4/70. Labels/translations are assistant-authored without independent human/native-language review. Author saw earlier workflow code, so not externally blinded. Model API spend0 excludes electricity/hardware/hosting. First-pass workflow sources remain immutable; later fixes are regression, not untouched validation.');
}
// 6. Product review and explicit deployment/production boundary.
{
 const s=slide('Demo and the route to a bank integration',6,true);
 await screenshot(s,'analyst-case.jpg',{left:64,top:167,width:570,height:336},'Cropped detail of actual Claro analyst case evidence',{left:0.46,top:0.25,right:0.02,bottom:0.425});
 text(s, deployment.verified ? 'Verified deployed demo' : 'Deployment verification pending',64,515,590,42,26,C.mint,true);
 text(s,deployment.verified?deployment.url:'A working URL will replace this line after verification.',64,563,590,77,20,C.white);
 text(s,'Deliberate trade-offs',690,164,520,43,29,C.mint,true);
 text(s,'Single worker and SQLite\nSimple deployment. Free-host restarts\ncan reset sandbox state.',690,225,510,121,24,C.white);
 text(s,'Local model, no remote model calls\nPortable CPU inference. Synthetic tests\nlimit claims about real customer demand.',690,370,510,121,24,C.white);
 text(s,'Before real customers',690,511,510,39,26,C.mint,true);
 text(s,'Bank identity, approved policies, durable\nstorage and independent ES/PT review.',690,558,515,82,24,C.white);
 notes(s,'Repository: https://github.com/nicoceron/factored-hackathon-2026-nicoceron . Deployed URL only appears as verified when submission/deployment.json verified=true, supplied after root verifies live service. Until then the editable deck clearly states pending. Screenshot is a real running sandbox UI with team fixtures. Free-host filesystem may reset. Source docs/OPERATIONS.md and submission/deployment.json. Next deployment gates include independent labels/language review, real bank entitlements/MFA, approved jurisdiction/product policies, durable transactional data, monitored rollout, privacy/retention controls and operational human staffing. No real-bank operation or production readiness certification.');
}

await fs.mkdir(build,{recursive:true});
const draft=path.join(build,'candidate.pptx');
await(await PresentationFile.exportPptx(ppt)).save(draft);
for(let i=0;i<6;i++){
 const s=ppt.slides.items[i];
 const blob=await ppt.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
 const layout=await s.export({format:'layout'});
 await fs.writeFile(path.join(build,`slide-${i+1}.layout.json`),await layout.text());
}
const final=path.join(root,'.local/deck-finalized',`Claro-${Date.now()}.pptx`);
const receipt=await finalizePresentation({workspaceDir:path.join(root,'.local'),candidatePath:draft,finalPath:final,
 pythonExecutable:python,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
 explicitTotalSlideCount:6,requiredNativeChartOwnerSlides:[4,5],requiredNativeTableOwnerSlides:[],
 materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[font]},
 verifyArtifactToolImport:true,receiptPath:path.join(build,`validation-${Date.now()}.json`)});
await fs.copyFile(final,path.join(output,'Claro-Hackathon-2026.pptx'));
await fs.writeFile(path.join(build,'build-summary.json'),JSON.stringify({font,slideCount:6,final,receipt},null,2));
console.log(JSON.stringify({font,final,slideCount:6}));
