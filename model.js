'use strict';
// Persisted schema is independent of the view. Patient IDs never come from names.
const EggModel=(()=>{
 const localDate=(d=new Date())=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
 const daily=()=>({well:false,asthma:false,changes:false,prepared:false});
 function patient(name='Новый пациент',dob=''){
  return {id:crypto.randomUUID(),name,dob,guideAcknowledged:false,daily:daily(),dailyDate:localDate(),question:false,reportQuestion:'',selectedDay:localDate(),assigned:false,paused:false,restricted:false,pauseReason:'',reactionAt:'',records:[],clinicalReviews:[],planHistory:[],course:null,
   plan:{id:crypto.randomUUID(),protocol:'',phenotype:'unclear',setting:'specialist',diagnosis:'',age:'',anaphylaxis:false,asthma:'unknown',fpiesSeverity:'unknown',lastReaction:'',clinicianConfirmed:false,recipeId:null,stage:1,start:'',minDays:'',fullRequired:'',immediateHours:'',delayedHours:'',initial:'',amount:'',goal:'',frequency:'',period:'',observe:'',protein:'',restart:'',contact:'',nextDecision:'',specialistPlan:'',allowedRecipes:[],route:''}};
 }
 const canHome=p=>['ige','delayed'].includes(p.phenotype)&&p.setting==='home'&&p.clinicianConfirmed&&!p.anaphylaxis&&['none','controlled'].includes(p.asthma)&&p.age!==''&&Number.isInteger(Number(p.age))&&Number(p.age)>=0&&!(p.phenotype==='ige'&&Number(p.age)>=6);
 function fresh(){const p=patient();return {app:'em-yaytso',schemaVersion:1,activePatientId:p.id,patients:[p]};}
 const fail=()=>{throw new Error('Файл не является корректной резервной копией ЕмЯйцо версии 1. Данные не изменены.');};
 const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
 const str=(x,max=4000)=>{if(typeof x!=='string'||x.length>max)fail();};
 const id=x=>{str(x,100);if(!/^[a-zA-Z0-9_-]+$/.test(x))fail();};
 const bool=x=>{if(typeof x!=='boolean')fail();};
 const num=(x,min,max,integer=false)=>{if(typeof x!=='number'||!Number.isFinite(x)||x<min||x>max||integer&&!Number.isInteger(x))fail();};
 function date(x,empty=false){if(empty&&x==='')return;str(x,10);if(!/^\d{4}-\d{2}-\d{2}$/.test(x)||!Number.isFinite(Date.parse(x+'T12:00:00Z'))||new Date(x+'T12:00:00Z').toISOString().slice(0,10)!==x||x<'1900-01-01'||x>localDate())fail();}
 function iso(x,empty=false){if(empty&&x==='')return;str(x,40);if(!/^\d{4}-\d\d-\d\dT/.test(x)||!Number.isFinite(Date.parse(x))||Date.parse(x)>Date.now()+60000)fail();}
 const one=(x,values)=>{if(!values.includes(x))fail();};
 function safeTree(x,depth=0){if(depth>14)fail();if(typeof x==='string'){str(x,10000);return;}if(x===null||typeof x==='boolean')return;if(typeof x==='number'){if(!Number.isFinite(x))fail();return;}if(Array.isArray(x)){if(x.length>100000)fail();x.forEach(v=>safeTree(v,depth+1));return;}if(!obj(x))fail();for(const [k,v]of Object.entries(x)){if(['__proto__','prototype','constructor'].includes(k))fail();safeTree(v,depth+1);}}
 const unique=items=>{const ids=new Set();for(const x of items){id(x.id);if(ids.has(x.id))fail();ids.add(x.id);}};
 function plan(p){if(!obj(p))fail();id(p.id);one(p.phenotype,['ige','delayed','fpies','eoe','unclear']);one(p.setting,['home','specialist']);one(p.asthma,['unknown','none','controlled','uncontrolled']);one(p.fpiesSeverity,['unknown','mild','severe']);bool(p.anaphylaxis);bool(p.clinicianConfirmed);num(p.stage,1,7,true);date(p.start,true);
  for(const k of ['protocol','diagnosis','lastReaction','initial','amount','goal','frequency','period','observe','protein','restart','contact','nextDecision','specialistPlan'])str(p[k]);
  for(const [k,max,integer]of [['age',120,true],['minDays',3650,true],['fullRequired',1000,true],['immediateHours',168,false],['delayedHours',720,false]])if(p[k]!=='')num(p[k],k==='fullRequired'?1:0,max,integer);
  if(!Array.isArray(p.allowedRecipes)||p.allowedRecipes.length>17)fail();const seen=new Set();for(const a of p.allowedRecipes){if(!obj(a))fail();id(a.recipeId);const r=recipes.find(r=>r.id===a.recipeId);if(!r||r.step!==p.stage||seen.has(r.id))fail();seen.add(r.id);str(a.start);str(a.schedule);if(!a.start.trim()||!a.schedule.trim())fail();}if(p.recipeId!==null&&!seen.has(p.recipeId))fail();
 }
 function context(c){if(!obj(c))fail();id(c.planId);if(c.courseId!==null)id(c.courseId);num(c.stage,1,7,true);str(c.recipeName);str(c.target);str(c.protein);str(c.start);str(c.schedule);for(const k of ['immediateHours','delayedHours'])if(c[k]!==''&&c[k]!==null)num(c[k],0,k==='immediateHours'?168:720);
  if(c.recipeId===null){if(c.metrics!==null)fail();return;}id(c.recipeId);str(c.recipeVersion,100);const r=recipes.find(r=>r.id===c.recipeId);if(!r||!obj(c.metrics))fail();const m=c.metrics;
  // Reject altered measurements in backups; future recipe versions require an explicit migration.
  for(const [key,value]of Object.entries({recipeId:r.id,recipeVersion:r.version,recipeName:r.name,stage:r.step,fullPortion:r.portion,fullUnits:r.fullUnits,unitGenitive:r.unitGenitive,estimatedProteinMg:r.estimatedProteinMg,measuredAllergenMg:r.measuredAllergenMg,measuredProteinMg:r.measuredProteinMg,approximate:r.approximate,metricsVersion:r.metricsVersion}))if(m[key]!==value)fail();if(c.recipeVersion!==r.version||c.stage!==r.step)fail();
 }
 function record(r){if(!obj(r))fail();id(r.id);date(r.date);str(r.time,5);if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(r.time))fail();iso(r.occurredAt);iso(r.updatedAt);context(r.context);one(r.kind,['intake','skip','observation']);one(r.symptom,['none','pending','symptom','danger','skip']);one(r.productClass,['standard','category']);for(const k of ['amount','unit','phase','batch','onset','note'])str(r[k]);for(const k of ['targetMet','recipeMatch','immediateDone','delayedDone'])bool(r[k]);if(r.kind==='skip'&&r.symptom!=='skip'||r.kind!=='skip'&&r.symptom==='skip')fail();if(r.productClass==='standard'){if(r.kind!=='intake'||!r.context.metrics||!obj(r.fraction))fail();num(r.fraction.numerator,1,1000,true);num(r.fraction.denominator,1,1000,true);}else if(r.fraction!==null)fail();}
 function validate(value){safeTree(value);if(!obj(value)||value.app!=='em-yaytso'||value.schemaVersion!==1||!Array.isArray(value.patients)||!value.patients.length||value.patients.length>100)fail();unique(value.patients);id(value.activePatientId);if(!value.patients.some(p=>p.id===value.activePatientId))fail();
  for(const p of value.patients){str(p.name,80);if(!p.name.trim())fail();date(p.dob,true);for(const k of ['guideAcknowledged','question','assigned','paused','restricted'])bool(p[k]);str(p.reportQuestion,1000);str(p.pauseReason);iso(p.reactionAt,true);date(p.dailyDate);date(p.selectedDay);if(!obj(p.daily))fail();for(const k of Object.keys(daily()))bool(p.daily[k]);plan(p.plan);if(!Array.isArray(p.records)||!Array.isArray(p.clinicalReviews)||!Array.isArray(p.planHistory))fail();unique(p.records);p.records.forEach(record);p.planHistory.forEach(plan);unique(p.clinicalReviews);if(p.assigned&&p.restricted===canHome(p.plan))fail();if(p.reactionAt&&!p.paused&&!p.clinicalReviews.some(r=>r.decision==='resume'&&Date.parse(r.recordedAt)>=Date.parse(p.reactionAt)))fail();
   for(const r of p.clinicalReviews){date(r.date);iso(r.recordedAt);str(r.clinician);str(r.note);one(r.decision,['pause','resume']);id(r.previousPlanId);if(r.decision==='resume'){id(r.recipeId);str(r.start);str(r.schedule);}}
   if(p.course!==null){if(!obj(p.course))fail();id(p.course.id);id(p.course.planId);id(p.course.recipeId);date(p.course.startDate);if(p.course.planId!==p.plan.id||p.course.recipeId!==p.plan.recipeId)fail();}
  }return structuredClone(value);
 }
 return {localDate,daily,patient,fresh,validate,date,canHome};
})();
if(typeof module!=='undefined')module.exports=EggModel;
