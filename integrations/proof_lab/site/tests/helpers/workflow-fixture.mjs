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
  law_id:definition.law,grammar_certified:checked,node_trace:[],source_projection_complete:false,foundation_complete:false,
  source:{id:'user_text',text:request.input.text,revision:workflowHash(request.input.text)},context:request.input.context,
  reading:checked?{governor:'arrival',lexeme:'ab',ending:'waw',complement:'zayd',prefix:'جَاءَ ',word:'أَبُو',complement_text:'زَيْدٍ',start_byte:11,end_byte:21,grammatical_case:'raf',observed_case:'raf',convention:'common_letter_substitution',prerequisites:[],alternatives:[]}:null,
  orthographic_bridge:checked?{profile:'nabt.six-noun-exact-spelling.v1',raw:request.input.text,canonical:'جَاْءَ ءَبُوْ زَيْدِنْ',cells:[16,3,112,112,5,107,40,111,30,99],number:'64813690006973564080',raw_reconstruction_checked:true,canonical_projection_complete:true}:null,
  intended_sense_established:false,speaker_reference_established:false,world_truth_established:false,
  external_truth_established:false,tawatur_established:false,whole_arabic_complete:false,linguistic_rejection:false,
  residuals:['SOURCE_AUTHENTICITY_NOT_ESTABLISHED','RULE_INTERPRETATION_IS_AUTHORED','REFERENCE_INTENT_AND_WORLD_TRUTH_NOT_ESTABLISHED']
 });
 if(op==='six_noun_acquisition'&&checked){
  // Independently specified transport fixture; no Lean execution is claimed.
  result.source_review={sha256:'315e6c067d9bacded9661bef043594be90437b73f1f695842d1d087d0dac0b8e',authority:'synthetic transport fixture',passage_ids:['qatr_subject','qatr_six_inventory_case','alfiyya_idafa_non_speaker','alfiyya_variants','qatr_genitive']};
  result.native_receipt={schema:definition.law,law_id:definition.law,
   ...structuredClone(Object.fromEntries(['source','context','status','reading','grammar_certified','node_trace','foundation_complete','orthographic_bridge','intended_sense_established','external_truth_established','strict_language_accepted','whole_arabic_complete'].map(key=>[key,result[key]]))),
   source_projection:{status:'INCOMPLETE',alphabet_id:'nabt.a116.v1',number_domain:'nabt.foundation.projected-cells.bijective116.v1',cells:[16,112,5,40,111],number:'3254553764'},
   source_restored:true,unresolved:[]};
  const premise=(name,origin)=>({name,state:'affirmed',origin});
  const common=[premise('exact_source_interval','native_source_slice'),premise('declared_finite_profile','authored_profile_not_general_classification')];
  const leaf=[...common,premise('declared_lexical_slot_allowed','native_grammar')];
  const interfaces=premise('child_interfaces_match','native_grammar');
  const face=(category,state,position)=>({category,state,position,residual:[]});
  // Fixed transport-only specimen. The numerical examples are not a grammar oracle.
  const rows=[
   ['prefix','PREFIX_EXACT_V1',[],0,11,'جَاءَ ',[16,3,112],'229329',face('verbPhrase',0,0),['qatr_subject'],leaf],
   ['noun','NOUN_FULL_FORM_V1',[],11,21,'أَبُو',[112,5,107],'1521332',face('noun',1,1),['qatr_six_inventory_case','alfiyya_idafa_non_speaker','alfiyya_variants'],leaf],
   ['complement','COMPLEMENT_EXACT_V1',[],22,34,'زَيْدٍ',[40,111,30,99],'65507504',face('noun',2,2),['qatr_genitive'],leaf],
   ['idafa','IDAFA_EXACT_V1',['noun','complement'],11,34,'أَبُو زَيْدٍ',[112,5,107,40,111,30,99],'275458425390256',face('nounPhrase',1,1),['qatr_genitive','alfiyya_idafa_non_speaker'],[...common,interfaces,premise('ordered_noun_complement_children','native_grammar')]],
   ['sentence','SIX_NOUN_COMMON_LETTER_V1',['prefix','idafa'],0,34,request.input.text,[16,3,112,112,5,107,40,111,30,99],'64813690006973564080',face('verbalClause',1,0),['qatr_subject','qatr_six_inventory_case','alfiyya_idafa_non_speaker','alfiyya_variants'],[...common,interfaces]]
  ];
  for(const [node_id,rule_id,children,start_byte,end_byte,raw,output_cells,output_number,output_face,passage_ids,prerequisites]of rows){
   const predecessors=children.map(id=>result.node_trace.find(node=>node.node_id===id));
   result.node_trace.push({node_id,rule_id,children,start_byte,end_byte,raw,output_cells,output_number,output_face,passage_ids,prerequisites,
    law_id:definition.law,scope:'INSTALLED_EXACT_SPELLING_COMMON_LETTER_PROFILE',source:structuredClone(result.source),context:result.context,
    orthographic_profile:'nabt.six-noun-exact-spelling.v1',alphabet_id:'nabt.a116.v1',number_domain:'nabt.foundation.projected-cells.bijective116.v1',
    rule_source_review_sha256:result.source_review.sha256,input_cells:predecessors.map(node=>[...node.output_cells]),input_faces:predecessors.map(node=>structuredClone(node.output_face)),
    alternatives:[],unresolved:[],licensed:true});
  }
  result.native_receipt.node_trace=structuredClone(result.node_trace);
  result.request_sha256=workflowHash({source:result.source,context:result.context});
  result.receipt_sha256=workflowHash(result.native_receipt);result.executable_sha256='e'.repeat(64);
  Object.assign(claim,{id:definition.kind,authority:'NATIVE_CHECKED',source_review_sha256:result.source_review.sha256,
   ...structuredClone(Object.fromEntries(['source','context','reading','node_trace','request_sha256','receipt_sha256'].map(key=>[key,result[key]]))),
   unresolved_premises:[...result.residuals]});
 }
 const registry='a'.repeat(64),gateway={schema:'nabt.licensed-workflow-response.v1',status:result.status,workflow_status:checked?'SCOPED_CLAIMS_AVAILABLE':'NO_SCOPED_CLAIMS',operation:op,claims:checked?[{...claim,origin_path:'claims[0]'}]:[],native_checked:checked,strict_language_accepted:false,whole_arabic_complete:false,tawatur_established:false,world_truth_established:false,display_contract:{proof_source:'claims[*].proof',native_checked_is_not_blanket_proof:true},request_sha256:workflowHash(request),surface_id:definition.surface,registry_sha256:registry,result_sha256:workflowHash(result),result};
 return {schema:'nabt.proof-lab-result.v1',request_id:workflowId,code_sha:'f0d41d3c6320fe78ac31ce60411fbb3442dc8293',payload_sha256:'b'.repeat(64),mode:'licensed_workflow',status:'LICENSED_WORKFLOW_COMPLETE',all_arabic_complete:false,world_truth_established:false,native_sha256:null,registry_sha256:registry,workflow_request:structuredClone(request),workflow_request_sha256:workflowHash(request),gateway_result:gateway,gateway_result_json:wire(gateway),gateway_result_sha256:workflowHash(gateway),adapter_result_json:wire(result),migration_inventory:{schema:'nabt.interface-migration-inventory.v1',registry_sha256:registry,surface_count:1,states:{MIGRATED_SCOPED_NATIVE_ADAPTER:1},surfaces:[{surface_id:gateway.surface_id,migration_state:'MIGRATED_SCOPED_NATIVE_ADAPTER',pending_obligations:['NO_GENERAL_LANGUAGE_ACCEPTANCE'],whole_language_claim:false}],all_interfaces_migrated:false,whole_arabic_complete:false}};
}
