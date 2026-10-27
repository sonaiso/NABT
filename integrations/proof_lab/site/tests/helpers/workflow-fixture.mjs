import {createHash} from 'node:crypto';
import '../../web/workflow-contract.js';
export const workflowId='11111111-1111-4111-8111-111111111111';
export const workflowRequests={
 lexical_surface:{schema:'nabt.licensed-workflow-request.v1',op:'lexical_surface',input:{text:'عَيْنَ',context:'مقام جديد غير محسوم'}},
 discourse_boundary:{schema:'nabt.licensed-workflow-request.v1',op:'discourse_boundary',input:{text:'لم أر أسداً قط؛ وأقصد بالأسد الحيوان المعروف.',context:'مقام جديد غير محسوم',profile_id:'linguistic'}},
 source_inference:{schema:'nabt.licensed-workflow-request.v1',op:'source_inference',input:{source:'إن عرف زيد الحق سار زيد. عرف زيد الحق.',query:'هل سار زيد؟',scope:'مقام جديد غير محسوم'}}
};
export const workflowRequest=workflowRequests.lexical_surface;
const operationFixtures={
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
 const registry='a'.repeat(64),gateway={schema:'nabt.licensed-workflow-response.v1',status:result.status,workflow_status:checked?'SCOPED_CLAIMS_AVAILABLE':'NO_SCOPED_CLAIMS',operation:op,claims:checked?[{...claim,origin_path:'claims[0]'}]:[],native_checked:checked,strict_language_accepted:false,whole_arabic_complete:false,tawatur_established:false,world_truth_established:false,display_contract:{proof_source:'claims[*].proof',native_checked_is_not_blanket_proof:true},request_sha256:workflowHash(request),surface_id:definition.surface,registry_sha256:registry,result_sha256:workflowHash(result),result};
 return {schema:'nabt.proof-lab-result.v1',request_id:workflowId,code_sha:'f0d41d3c6320fe78ac31ce60411fbb3442dc8293',payload_sha256:'b'.repeat(64),mode:'licensed_workflow',status:'LICENSED_WORKFLOW_COMPLETE',all_arabic_complete:false,world_truth_established:false,native_sha256:null,registry_sha256:registry,workflow_request:structuredClone(request),workflow_request_sha256:workflowHash(request),gateway_result:gateway,gateway_result_json:wire(gateway),gateway_result_sha256:workflowHash(gateway),adapter_result_json:wire(result),migration_inventory:{schema:'nabt.interface-migration-inventory.v1',registry_sha256:registry,surface_count:1,states:{MIGRATED_SCOPED_NATIVE_ADAPTER:1},surfaces:[{surface_id:gateway.surface_id,migration_state:'MIGRATED_SCOPED_NATIVE_ADAPTER',pending_obligations:['NO_GENERAL_LANGUAGE_ACCEPTANCE'],whole_language_claim:false}],all_interfaces_migrated:false,whole_arabic_complete:false}};
}
