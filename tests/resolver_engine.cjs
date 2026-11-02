const {test}=require('node:test');
const assert=require('node:assert/strict');
const R=require('../custom/js/scoreboard-resolver.js');
test('unconfirmed rank labels follow current row position rather than tied intermediate score rank',()=>{
 const e=R.create(fixture()),a=R.announcements(e);
 const label=id=>{const rows=e.ranking(),i=rows.findIndex(r=>r.team.id===id);return R.rankLabel(rows[i].rank,i+1,a.isConfirmed(id));};
 assert.equal(label('v'),'2');assert.equal(label('u'),'1');
 a.step();a.step();a.step();assert.equal(label('v'),'2');
 a.step();assert.equal(label('v'),'2');assert.equal(label('u'),'1');
 a.undo();assert.equal(label('v'),'2');
 assert.equal(R.rankLabel(3,4,false),'4');assert.equal(R.rankLabel(3,4,true),'3');
});
test('announcement visits and confirms every team including teams without frozen submissions',()=>{
 const e=R.create(fixture()),a=R.announcements(e);
 assert.equal(a.next().team.id,'v');assert.equal(a.next().kind,'reveal');
 a.step();a.step();a.step();
 assert.equal(a.next().team.id,'v');assert.equal(a.next().kind,'confirm');assert.equal(a.isConfirmed('v'),false);
 assert.equal(a.step().kind,'confirm');assert.equal(a.isConfirmed('v'),true);
 assert.equal(a.next().team.id,'u');assert.equal(a.next().kind,'confirm');
 a.step();assert.equal(a.next(),null);assert.equal(a.isConfirmed('u'),true);
 assert.equal(a.undo(),true);assert.equal(a.next().team.id,'u');assert.equal(a.isConfirmed('u'),false);
 a.undo();assert.equal(a.next().team.id,'v');assert.equal(a.isConfirmed('v'),false);
 a.undo();assert.equal(a.next().kind,'reveal');assert.equal(a.next().cell.shown,2);
 assert.equal(e.ranking()[1].score.solved,0);
});
test('all-zero scoreboard still has one manual confirmation per participant',()=>{
 const f=fixture();f.submissions=[];f.judgements=[];f.scoreboard.rows.forEach(r=>{r.rank=1;r.score={num_solved:0,total_time:0};});
 const a=R.announcements(R.create(f));assert.equal(a.next().team.id,'v');assert.equal(a.next().kind,'confirm');
 a.step();assert.equal(a.next().team.id,'u');a.step();assert.equal(a.next(),null);
 assert.equal(a.undo(),true);assert.equal(a.next().team.id,'u');
 const reset=R.announcements(R.create(f));assert.equal(reset.isConfirmed('v'),false);assert.equal(reset.next().team.id,'v');
});
test('announcement defers a moved team and never confirms it while submissions remain',()=>{
 const f=fixture();f.teams=[{id:'u',name:'U'},{id:'v',name:'Z'},{id:'w',name:'Y'}];f.scoreboard.rows=[{team_id:'v',rank:1,score:{num_solved:2,total_time:371}},{team_id:'u',rank:2,score:{num_solved:1,total_time:10}},{team_id:'w',rank:3,score:{num_solved:0,total_time:0}}];
 f.submissions=[f.submissions[0],{id:'2',team_id:'v',problem_id:'a',contest_time:'3:01:00'},{id:'3',team_id:'v',problem_id:'b',contest_time:'3:10:00'}];f.judgements=f.judgements.slice(0,3);f.judgements.forEach(j=>j.judgement_type_id='AC');
 const e=R.create(f),a=R.announcements(e);assert.equal(a.next().team.id,'v');
 const moved=a.step();assert.equal(moved.beforePosition,3);assert.equal(moved.afterPosition,2);
 assert.equal(a.isConfirmed('v'),false);assert.equal(a.isVisited('v'),true);assert.equal(a.isVisited('u'),false);assert.equal(a.next().team.id,'w');assert.equal(a.next().kind,'confirm');
 a.step();assert.equal(a.isConfirmed('w'),true);assert.equal(a.next().team.id,'v');assert.equal(a.next().problem.id,'b');
 a.step();assert.equal(a.next().team.id,'u');assert.equal(a.next().kind,'confirm');
 a.step();assert.equal(a.next().team.id,'v');assert.equal(a.next().kind,'confirm');a.step();
 assert.equal(a.next(),null);assert.equal(e.validate().ok,true);
});
test('undo and reset restore unvisited masking independently of rank confirmation',()=>{
 const a=R.announcements(R.create(fixture()));assert.equal(a.isVisited('v'),false);
 a.step();assert.equal(a.isVisited('v'),true);a.step();a.undo();assert.equal(a.isVisited('v'),true);
 a.undo();assert.equal(a.isVisited('v'),false);
 const reset=R.announcements(R.create(fixture()));assert.equal(reset.isVisited('v'),false);assert.equal(reset.isConfirmed('v'),false);
});
function fixture(){return {contest:{name:'TEST',scoreboard_type:'pass-fail',duration:'4:00:00',scoreboard_freeze_duration:'1:00:00',penalty_time:20},problems:[{id:'a',label:'A',name:'A'},{id:'b',label:'B',name:'B'}],teams:[{id:'u',name:'U'},{id:'v',name:'V'}],scoreboard:{rows:[{team_id:'u',rank:1,score:{num_solved:1,total_time:10}},{team_id:'v',rank:2,score:{num_solved:1,total_time:241}}]},judgementTypes:[{id:'AC',solved:true,penalty:false},{id:'WA',solved:false,penalty:true},{id:'CE',solved:false,penalty:false}],submissions:[{id:'1',team_id:'u',problem_id:'a',contest_time:'0:10:00'},{id:'2',team_id:'v',problem_id:'b',contest_time:'3:01:00'},{id:'3',team_id:'v',problem_id:'b',contest_time:'3:11:00'},{id:'4',team_id:'v',problem_id:'b',contest_time:'3:21:00'}],judgements:[{id:'j1',submission_id:'1',valid:true,end_time:'2026-01-01T00:00:00Z',judgement_type_id:'AC'},{id:'j2',submission_id:'2',valid:true,end_time:'2026-01-01T00:01:00Z',judgement_type_id:'WA'},{id:'j3',submission_id:'3',valid:true,end_time:'2026-01-01T00:02:00Z',judgement_type_id:'WA'},{id:'j4',submission_id:'4',valid:true,end_time:'2026-01-01T00:03:00Z',judgement_type_id:'AC'}]};}
test('one step reveals one attempt; success scores submitted time plus penalties',()=>{const e=R.create(fixture());assert.equal(e.next().team.id,'v');let s=e.step();assert.equal(s.attempt,1);assert.equal(s.accepted,false);e.step();s=e.step();assert.equal(s.attempt,3);assert.equal(s.accepted,true);assert.equal(e.ranking()[1].score.total,241);assert.equal(e.next(),null);assert.equal(e.validate().ok,true);e.undo();assert.equal(e.next().cell.shown,2);});
test('negative, late, ignored and unknown-team submissions are excluded',()=>{const f=fixture();for(const [id,time,team,valid] of [['n','-0:01:00','u',true],['late','4:00:00','u',true],['bad','0:01:00','u',false],['unknown','0:02:00','x',true]]){f.submissions.push({id,team_id:team,problem_id:'b',contest_time:time,valid});f.judgements.push({id:'j'+id,submission_id:id,valid:true,end_time:'2026-01-01T01:00:00Z',judgement_type_id:'AC'});}const e=R.create(f);assert.equal(e.validate().ok,true);assert.equal(e.total,3);});
test('compile error counts as an attempt but adds no penalty',()=>{const f=fixture();f.judgements[1].judgement_type_id='CE';f.scoreboard.rows[1].score.total_time=221;const e=R.create(f);assert.equal(e.validate().ok,true);e.step();e.step();assert.equal(e.step().attempt,3);assert.equal(e.ranking()[1].score.total,221);});
test('unfinished latest judgement blocks opening; invalid rejudgement is ignored',()=>{const f=fixture();f.judgements.push({id:'new',submission_id:'4',valid:false,end_time:'2026-01-02T00:00:00Z',judgement_type_id:'WA'});assert.equal(R.create(f).validate().ok,true);f.judgements.push({id:'pending',submission_id:'4',valid:true,end_time:null,start_time:'2026-01-03T00:00:00Z'});assert.throws(()=>R.create(f),/채점/);});
test('official score mismatch is detected before any reveal',()=>{const f=fixture();f.scoreboard.rows[1].score.total_time=999;assert.equal(R.create(f).validate().ok,false);});
test('right-hand totals follow current revealed score through success and undo',()=>{const e=R.create(fixture());assert.match(R.frame(),/desktop-scoreboard/);let score=e.ranking().find(r=>r.team.id==='v').score;assert.equal(R.totals(score),'<td class="scorenc kr-total-solved">0</td><td class="scorett kr-total-time">0</td>');e.step();e.step();e.step();score=e.ranking().find(r=>r.team.id==='v').score;assert.match(R.totals(score),/>1<\/td>.*>241<\/td>/);e.undo();score=e.ranking().find(r=>r.team.id==='v').score;assert.match(R.totals(score),/>0<\/td>.*>0<\/td>/);});
test('duration parser handles negative and long contest times',()=>{assert.equal(R.seconds('-214:00:39.481'),-770439.481);assert.equal(R.seconds('27:01:02'),97262);assert.throws(()=>R.seconds('oops'));});
test('prefreeze unsuccessful attempts remain visible without pending counts',()=>{const c={accepted:false,attempts:3,shown:0,events:[]};assert.equal(R.presentation(c).label,'−3');assert.equal(R.presentation(c).state,'wrong');c.events=[{}];assert.equal(R.presentation(c).label,'−3');assert.equal(R.presentation(c).state,'pending');assert.equal(R.presentation(c).detail,'');});
test('public presentation contains only scoreboard heading and table, not controls or commentary',()=>{const html=R.frame();assert.match(html,/<h1>스코어보드<\/h1>/);assert.match(html,/<table/);assert.doesNotMatch(html,/<button|<select|<p\b|운영자|결과 발표|Space|Enter|건 공개|다시 불러오기/);assert.doesNotMatch(R.presentation({attempts:0,accepted:false,shown:0,events:[{},{}]}).detail,/건/);});
test('unfinished in-window run after an AC still blocks the snapshot',()=>{const f=fixture();f.submissions.push({id:'later',team_id:'u',problem_id:'a',contest_time:'3:30:00'});f.judgements.push({id:'laterj',submission_id:'later',valid:true,start_time:'2026-01-04T00:00:00Z',end_time:null});assert.throws(()=>R.create(f),/채점/);});
test('moves a successful last row up and defers its remaining problem',()=>{const f=fixture();f.teams=[{id:'u',name:'U'},{id:'v',name:'Z'},{id:'w',name:'Y'}];f.scoreboard.rows.push({team_id:'w',rank:3,score:{num_solved:0,total_time:0}});f.submissions=f.submissions.slice(0,2);f.submissions[1].problem_id='a';f.judgements=f.judgements.slice(0,2);f.judgements[1].judgement_type_id='AC';f.submissions.push({id:'5',team_id:'v',problem_id:'b',contest_time:'3:20:00'},{id:'6',team_id:'w',problem_id:'b',contest_time:'3:30:00'});f.judgements.push({id:'j5',submission_id:'5',valid:true,end_time:'2026-01-01T01:00:00Z',judgement_type_id:'AC'},{id:'j6',submission_id:'6',valid:true,end_time:'2026-01-01T01:00:01Z',judgement_type_id:'WA'});const e=R.create(f);assert.equal(e.next().team.id,'v');assert.equal(e.next().problem.id,'a');const moved=e.step();assert.equal(moved.beforePosition,3);assert.equal(moved.afterPosition,2);assert.equal(e.next().team.id,'w');e.step();assert.equal(e.next().team.id,'v');assert.equal(e.next().problem.id,'b');});
