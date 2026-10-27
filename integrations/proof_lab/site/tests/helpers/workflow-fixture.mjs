import {createHash} from 'node:crypto';
import '../../web/workflow-contract.js';
export const workflowId='11111111-1111-4111-8111-111111111111';
export const workflowRequests={
 six_noun_acquisition:{schema:'nabt.licensed-workflow-request.v1',op:'six_noun_acquisition',input:{text:'جَاءَ أَبُو زَيْدٍ',context:'مقام جديد غير محسوم'}},
 lexical_surface:{schema:'nabt.licensed-workflow-request.v1',op:'lexical_surface',input:{text:'عَيْنَ',context:'مقام جديد غير محسوم'}},
 discourse_boundary:{schema:'nabt.licensed-workflow-request.v1',op:'discourse_boundary',input:{text:'لم أر أسداً قط؛ وأقصد بالأسد الحيوان المعروف.',context:'مقام جديد غير محسوم',profile_id:'linguistic'}},
 source_inference:{schema:'nabt.licensed-workflow-request.v1',op:'source_inference',input:{source:'إن عرف زيد الحق سار زيد. عرف زيد الحق.',query:'هل سار زيد؟',scope:'مقام جديد غير محسوم'}}
};
export const workflowRequest=workflowRequests.lexical_surface;
const operationFixtures={
 six_noun_acquisition:{schema:'nabt.six-noun-acquisition-receipt.v1',status:'CHECKED_SIX_NOUN',kind:'SOURCE_BOUND_SIX_NOUN_CONSTRUCTION',law:'nabt.six-noun-acquisition.v1',surface:'tools.linguistic_truth.six_noun.acquire_six_noun'},
 lexical_surface:{schema:'nabt.witnessed-surface-receipt.v2',status:'DOCUMENTARY_FORM_MATCH',kind:'EXACT_WITNESSED_FORM_WITH_DECLARED_ANNOTATION',law:'nabt.lexical-surface-binding.v1',surface:'tools.linguistic_truth.surface.certify_surface'},
 discourse_boundary:{schema:'nabt.discourse-boundary-receipt.v1',status:'CHECKED_DISCOURSE_BOUNDARY',kind:'EXACT_DISCOURSE_BOUNDARY_AND_CUE_SLICE',law:'nabt.discourse-boundary-cue.v1',surface:'tools.linguistic_truth.discourse_boundary.acquire_discourse_boundary'},
 source_inference:{schema:'nabt.scoped-source-inference.v1',status:'SUPPORTED',kind:'SOURCE_BOUND_FINITE_INFERENCE',law:'nabt.licensed-inference.v1',surface:'tools.transport_adapters.certify_inference'}
};
const wire=globalThis.NabtWorkflowContract.canonical;
export const workflowHash=v=>createHash('sha256').update(typeof v==='string'?v:wire(v)).digest('hex');
export function workflowReport({checked=true,op='lexical_surface'}={}){
 const definition=operationFixtures[op],request=workflowRequests[op];
 if(!definition||!request)throw new Error('Unknown synthetic workflow fixture operation');
 const claim={kind:definition.kind,scope:'Explicit synthetic transport fixture, not native evidence.',proof:{law_id:definition.law,theorems:['Nabt.Example.transportFixture']}};
 const result={schema:definition.schema,status:checked?definition.status:'VERIFICATION_UNAVAILABLE',native_checked:checked,strict_language_accepted:false,claims:checked?[claim]:[]};
 if(op==='six_noun_acquisition')Object.assign(result,{
  law_id:definition.law,grammar_certified:checked,source_projection_complete:false,foundation_complete:false,
  source:{id:'user_text',text:request.input.text,revision:workflowHash(request.input.text)},context:request.input.context,
  reading:checked?{governor:'arrival',lexeme:'ab',ending:'waw',complement:'zayd',prefix:'جَاءَ ',word:'أَبُو',complement_text:'زَيْدٍ',start_byte:11,end_byte:21,grammatical_case:'raf',observed_case:'raf',convention:'common_letter_substitution',prerequisites:[],alternatives:[]}:null,
  orthographic_bridge:checked?{profile:'nabt.six-noun-exact-spelling.v1',raw:request.input.text,canonical:'جَاْءَ ءَبُوْ زَيْدِنْ',cells:[16,3,112,112,5,107,40,111,30,99],number:'64813690006973564080',raw_reconstruction_checked:true,canonical_projection_complete:true}:null,
  intended_sense_established:false,speaker_reference_established:false,world_truth_established:false,
  external_truth_established:false,tawatur_established:false,whole_arabic_complete:false,linguistic_rejection:false,
  residuals:['SOURCE_AUTHENTICITY_NOT_ESTABLISHED','RULE_INTERPRETATION_IS_AUTHORED','REFERENCE_INTENT_AND_WORLD_TRUTH_NOT_ESTABLISHED']
 });
 if(op==='six_noun_acquisition'&&checked){
  // Independently specified transport fixture; no Lean execution is claimed.
  result.source_review={sha256:'315e6c067d9bacded9661bef043594be90437b73f1f695842d1d087d0dac0b8e',authority:'synthetic transport fixture',passage_ids:[]};
  result.native_receipt={schema:definition.law,law_id:definition.law,
   ...structuredClone(Object.fromEntries(['source','context','status','reading','grammar_certified','foundation_complete','orthographic_bridge','intended_sense_established','external_truth_established','strict_language_accepted','whole_arabic_complete'].map(key=>[key,result[key]]))),
   source_projection:{status:'INCOMPLETE',alphabet_id:'nabt.a116.v1',number_domain:'nabt.foundation.projected-cells.bijective116.v1',cells:[16,112,5,40,111],number:'3254553764'},
   source_restored:true,unresolved:[]};
  result.request_sha256=workflowHash({source:result.source,context:result.context});
  result.receipt_sha256=workflowHash(result.native_receipt);result.executable_sha256='e'.repeat(64);
  Object.assign(claim,{id:definition.kind,authority:'NATIVE_CHECKED',source_review_sha256:result.source_review.sha256,
   ...structuredClone(Object.fromEntries(['source','context','reading','request_sha256','receipt_sha256'].map(key=>[key,result[key]]))),
   unresolved_premises:[...result.residuals]});
 }
 const registry='a'.repeat(64),gateway={schema:'nabt.licensed-workflow-response.v1',status:result.status,workflow_status:checked?'SCOPED_CLAIMS_AVAILABLE':'NO_SCOPED_CLAIMS',operation:op,claims:checked?[{...claim,origin_path:'claims[0]'}]:[],native_checked:checked,strict_language_accepted:false,whole_arabic_complete:false,tawatur_established:false,world_truth_established:false,display_contract:{proof_source:'claims[*].proof',native_checked_is_not_blanket_proof:true},request_sha256:workflowHash(request),surface_id:definition.surface,registry_sha256:registry,result_sha256:workflowHash(result),result};
 return {schema:'nabt.proof-lab-result.v1',request_id:workflowId,code_sha:'f0d41d3c6320fe78ac31ce60411fbb3442dc8293',payload_sha256:'b'.repeat(64),mode:'licensed_workflow',status:'LICENSED_WORKFLOW_COMPLETE',all_arabic_complete:false,world_truth_established:false,native_sha256:null,registry_sha256:registry,workflow_request:structuredClone(request),workflow_request_sha256:workflowHash(request),gateway_result:gateway,gateway_result_json:wire(gateway),gateway_result_sha256:workflowHash(gateway),adapter_result_json:wire(result),migration_inventory:{schema:'nabt.interface-migration-inventory.v1',registry_sha256:registry,surface_count:1,states:{MIGRATED_SCOPED_NATIVE_ADAPTER:1},surfaces:[{surface_id:gateway.surface_id,migration_state:'MIGRATED_SCOPED_NATIVE_ADAPTER',pending_obligations:['NO_GENERAL_LANGUAGE_ACCEPTANCE'],whole_language_claim:false}],all_interfaces_migrated:false,whole_arabic_complete:false}};
}
