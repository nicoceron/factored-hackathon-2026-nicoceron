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
const workflow = await json('docs/evidence/system-evaluation-v2.json').catch(() => null);
const segments = await json('docs/evidence/service-segment-evaluation.json').catch(() => null);
const currentRegression = await json('docs/evidence/system-challenge-regression-v2.json').catch(() => null);
const chatWorkflow = await json('docs/evidence/chat-system-regression.json').catch(() => null);
const chatChallenge = await json('docs/evidence/chat-challenge-regression.json').catch(() => null);
const chatSegments = await json('docs/evidence/chat-service-segment-regression.json').catch(() => null);

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
 const file=path.join(output,'demo-assets',name);
 let frame={...position};
 if(crop){
  const ratio=(1488*(1-crop.left-crop.right))/(1038*(1-crop.top-crop.bottom));
  const width=Math.min(position.width,position.height*ratio),height=width/ratio;
  frame={left:position.left+(position.width-width)/2,top:position.top+(position.height-height)/2,width,height};
 }
 // A fit mode recomputes the source rectangle; explicit native crops use the declared rectangle.
 const image=s.images.add({blob:await fs.readFile(file),contentType:'image/jpeg',alt,...(crop?{}:{fit:'contain'}),position:frame});
 if(crop)image.crop=crop;
}

// 1. Data-backed problem and focused customer-service scope.
{
 const s=ppt.slides.add();s.background.fill=C.navy;
 text(s,'Claro',64,46,760,105,86,C.white,true);
 text(s,'Banking support with\nverified outcomes',64,173,730,150,51,C.white,true);
 text(s,'Immediate Spanish and Portuguese chat\nwith verified cases for human review',67,351,730,90,27,C.muted);
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
 const s=slide('One conversation from inquiry to follow-up',2);
 await screenshot(s,'chat-confirm-es.jpg',{left:64,top:173,width:776,height:453},'Actual local Claro chat and explicit case confirmation retaining the specific customer report',{left:495/1488,top:240/1038,right:(1488-995)/1488,bottom:(1038-805)/1038});
 text(s,'1  Start in chat',880,178,330,43,27,C.teal,true);
 text(s,'Automatic ES/PT language.\nClarify the transaction in chat.',880,225,330,77,23);
 text(s,'2  Confirm and verify',880,323,330,43,27,C.teal,true);
 text(s,'Commit one sandbox case.\nRead it back before success.',880,370,330,77,23);
 text(s,'3  Persist follow-up',880,468,330,43,27,C.teal,true);
 text(s,'Ask a specific question.\nReply in the same composer.',880,515,330,77,23);
 notes(s,'Screenshot: current local Claro chat captured with CUA at http://127.0.0.1:8096 on October 4, 2026 America/Bogota, team-authored synthetic fixtures and external providers disabled. The UI creates a trusted sandbox session without persona or language selectors. ES/PT detection never changes customer identity. Exact references narrow validated authorized records and ambiguity prompts clarification. The customer report preserves specific redacted allegations through transaction clarification and is labeled unverified; permitted record facts remain separate. Customer sees the text before confirming. Atomic case commit and fresh read-back precede the receipt. The reviewer route is /?review=1. The owning customer answers a persisted question in the same composer. Case events remain scoped and idempotent. No real money movement, refunds or card blocking. Sources: docs/SYSTEM_EVALUATION.md, docs/OPERATIONS.md, api.py, privacy.py, store.py and workflow.py.');
}
// 3. Native editable architecture diagram.
{
 const s=slide('Permissions and actions stay in service code',3,true);
 text(s,'Optional providers are implemented and mock-tested. Live inference remains unverified.',64,147,1150,55,25,C.muted);
 const node=(label,x,y,w=230)=>{const n=s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:96},fill:'#132A44',line:{fill:'#365067',width:1.2}});n.text=label;n.text.style={typeface:font,fontSize:24,bold:true,color:C.white,alignment:'center',verticalAlignment:'middle',insets:{left:12,right:12,top:12,bottom:12}};return n;};
 const a=node('ES / PT browser',64,243);const b=node('Scoped sessions\nand record tools',364,243);const c=node('Jev or local\nrouting',664,243);const d=node('Deterministic\nworkflow',964,243);
 const e=node('Case history\nand follow-up',364,450);const f=node('SQLite commit\nand read-back',664,450);const g=node('Explicit case\nconfirmation',964,450);
 const link=(from,to,fromSide='right',toSide='left')=>s.shapes.connect(from,to,{kind:'straight',fromSide,toSide,line:{fill:C.mint,width:2},tail:{type:'triangle',width:'med',length:'med'}});
 link(a,b);link(b,c);link(c,d);link(d,g,'bottom','top');link(g,f,'left','right');link(f,e,'left','right');
 text(s,'Optional DeepSeek Flash\nphrasing with constrained\nfacts and local fallback',64,450,272,106,22,C.muted);
 text(s,'Opaque sessions + CSRF     Customer/workspace isolation     Idempotent confirmed writes',64,592,1140,58,24,C.white);
 notes(s,'Diagram objects/connectors are native and editable. Sequence shows responsibility boundaries, not an exhaustive call graph. Optional Jev one-shot classification and DeepSeek Flash composition are implemented and tested using mocked transports. Live provider inference has not been verified. No claimed provider accuracy or actual spend. Classifier never chooses identity or performs tools. Composer receives minimized permitted context and cannot replace authoritative financial facts, case receipts or policy actions. Provider attempts, validated token usage, tariff estimates, unknown cost and budget reservations are separately accounted. Public personas are sandbox identities. SQLite uses reserved idempotency fingerprints and fresh read-back. Private DuckDB jobs never serve organizer raw rows. Sources: docs/AI_PROVIDERS.md, docs/OPERATIONS.md, api.py, providers.py, privacy.py, store.py, workflow.py.');
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
 const selectedWorkflow=chatWorkflow || workflow || await json('docs/evidence/system-evaluation.json');
 const workflowSystems=['keyword_rules','tfidf_logistic'].map(k=>selectedWorkflow.systems[k]);
 const learnedWorkflow=selectedWorkflow.systems.tfidf_logistic;
 text(s,'Intent classification',64,151,550,43,29,C.teal,true);
 text(s,'140 frozen authored cases / macro-F1',64,194,550,37,22,C.gray);
 chart(s,{x:61,y:247,w:545,h:277,categories:['Rules','Local ML','Gemma 3'],values:languageSystems.map(v=>v.macro_f1),labels:languageSystems.map(v=>v.macro_f1.toFixed(3)),max:1,format:'0.0'});
 text(s,chatWorkflow?'Current chat regression':workflow?'Historical v1.1 workflow':'Historical v1.0 workflow',668,151,545,43,29,C.teal,true);
 text(s,'140 exposed cases / correct regression outcomes',668,194,545,60,22,C.gray);
 chart(s,{x:663,y:247,w:545,h:277,categories:['Rules','Local ML'],values:workflowSystems.map(v=>v.outcome_accuracy),labels:workflowSystems.map(v=>`${v.correct_outcomes} / ${v.cases}`),max:1,format:'0%'});
 text(s,'Historical intent labels: 117/140',65,537,550,45,25,C.ink,true);
 text(s,chatWorkflow?`${learnedWorkflow.handoffs_preserving_reference_request}/${learnedWorkflow.required_handoffs} handoffs; ${learnedWorkflow.incorrect_outcomes} workflow errors`:workflow?`${learnedWorkflow.handoffs_preserving_reference_request}/${learnedWorkflow.required_handoffs} handoffs preserve the request`:'Request-preservation recheck pending',668,537,540,60,24,C.ink,true);
 const selectedSegments=chatSegments || segments;
 const perSegment=selectedSegments?Object.values(selectedSegments.systems.tfidf_logistic.strata).map(v=>v.correct_outcomes):[];
 const segmentText=selectedSegments&&new Set(perSegment).size===1?`${chatSegments?'Current':'Historical'} six status/currency strata: ${perSegment[0]}/140 each. Same authored utterances.`:'Six controlled status/currency strata. Current replay pending.';
 text(s,segmentText,64,597,1145,32,21,C.gray);
 text(s,chatWorkflow?'Stronger case grounding scorer. Exposed authored regressions, no independent human review.':'Authored tests, no independent human review. New 70-case provider challenge unscored.',64,633,1145,28,20,C.gray);
 notes(s,`Sources: docs/LANGUAGE_EVALUATION.md, docs/SYSTEM_EVALUATION.md and aggregate evidence. Component train196/development56/test140 uses frozen semantic groups. Local TF-IDF/logistic117/140 macroF10.8230; rules65/140 F10.4207; local Gemma3 4B115/140 F10.8045. Small ML/Gemma difference is not claimed significant. Workflow figure is ${chatWorkflow?'current v3 chat regression with a stronger case-lookup scorer':workflow?'historical v1.1 request-preservation regression':'historical v1.0 pending current recheck'}. Current v3 requires the returned exact persisted case, localized status, timestamp, supporting case evidence and pending question. Independently reading the endpoint is insufficient. The scorer differs from v1.1, so old and new correctness percentages are not directly comparable. Original labels remain unchanged, including two CASE-009 requests for a nonexistent seeded case, recorded as fixture/reference mismatches rather than silently relabeled successes. Current safe automated resolutions: ${learnedWorkflow.safe_automated_resolutions}/${learnedWorkflow.in_scope_cases}. Current incorrect outcomes: ${learnedWorkflow.incorrect_outcomes}; unnecessary proposals: ${learnedWorkflow.unnecessary_handoff_proposals}. Language slices and all errors are published. First untouched challenge remains61/70 learned versus43/70 rules, with28/30 required transfers. Separate exposed regression ${chatChallenge?.systems.tfidf_logistic.correct_outcomes || currentRegression?.systems.tfidf_logistic.correct_outcomes || regression.systems.tfidf_logistic.correct_outcomes}/70 follows fixes; it is never relabeled blind. Source-matched current files are docs/evidence/chat-system-regression.json and docs/evidence/chat-challenge-regression.json. Historical v1.1 sources remain preserved. ${chatSegments?'Current':'Historical v1.1'} six strata contain140 unique utterances and70 semantic pairs, counterbalanced ES/PT,840replays/system. These are selected-transaction status/currency groups, not demographic fairness. All labels/translations are assistant-authored without independent human/native-language review. Fresh prospective70 is frozen but unscored. Zero offline provider attempts do not establish free provider inference. No hardware/hosting or representative customer cost claim.`);
}
// 6. Product review and explicit deployment/production boundary.
{
 const s=slide('Demo and the route to a bank integration',6,true);
 await screenshot(s,'chat-history-pt.jpg',{left:64,top:167,width:570,height:405},'Current local Claro reviewer case with the persisted report, question, reply and closure',{left:699/1488,top:447/1038,right:(1488-1441)/1488,bottom:(1038-933)/1038});
 text(s, deployment.verified ? 'Prior v1.1 hosted demo' : 'Deployment verification pending',64,583,590,35,23,C.mint,true);
 text(s,deployment.verified?deployment.url:'A working URL will replace this line after verification.',64,625,590,40,16,C.white);
 text(s,'Deliberate trade-offs',690,164,520,43,29,C.mint,true);
 text(s,'Single worker and SQLite\nSimple deployment. Free-host restarts\ncan reset sandbox state.',690,225,510,121,24,C.white);
 text(s,'Optional external models\nUsage and tariff estimates are logged.\nLive provider results are still unverified.',690,370,510,121,24,C.white);
 text(s,'Before real customers',690,511,510,39,26,C.mint,true);
 text(s,'Bank identity, approved policies, durable\nstorage and independent ES/PT review.',690,558,515,82,24,C.white);
 notes(s,'Repository: https://github.com/nicoceron/factored-hackathon-2026-nicoceron . Public URL is tied to the prior v1.1 commit and verification date in submission/deployment.json. The current chat redesign is local and has not been deployed. Reviewer access is /?review=1 and customer chat is /. Current local screenshots do not independently prove that a newer branch is deployed. Optional Jev/DeepSeek adapters are implemented/mocked but live inference remains unverified pending authorized metered use. External tariff estimates are not invoice spend. Screenshot is a declared geometry crop of the current local reviewer timeline. Its Spanish interface retains the original Spanish report plus Portuguese question and reply; the filename does not imply a Portuguese-only interface. Screenshot was captured with CUA at http://127.0.0.1:8096 on October 4, 2026 America/Bogota using team fixtures and disabled providers. Free-host filesystem may reset. Sources: docs/AI_PROVIDERS.md, docs/OPERATIONS.md and submission/deployment.json. Real-bank requirements include approved identity/entitlements/MFA/policies, durable data, monitored rollout, privacy controls, independent ES/PT review and staffing. Organizer submission is intentionally outside requested scope. No real-bank operation or production safety certification.');
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
