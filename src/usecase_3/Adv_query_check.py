from src.usecase_3.reranker_fin import process_inputs,compute_logits
import json

def main():
    with open('adversial_queries.json',"r",encoding="utf-8") as f:
        data= json.load(f)

    test_cases = data['test_cases']
    testcase_neg=[case for case in test_cases if case.get('pattern')=="negation"]
    testcase_key=[case for case in test_cases if case.get('pattern')=="keyword_trap"]
    testcase_const=[case for case in test_cases if case.get('pattern')=="constraint_swap"]

    neg_logit_diff_list=[]
    key_logit_diff_list=[]
    const_logit_diff_list=[]
    accuracy_per_pattern_list=[]


    for pattern_list in [testcase_neg,testcase_key,testcase_const]:
        correct=0
        incorrect=0
        for case in pattern_list:
            pattern= case['pattern']
            query= case['query']
            candidates=case['candidates']

            docs=[c['text'] for c in candidates]
            

            inputs=process_inputs(query,docs)

            logits= compute_logits(inputs)


            logit_diff=logits[0]-logits[1]
            if(logit_diff>0): pred =1
            else: pred=0
            if(pred==candidates[0]['label']): correct=correct+1
            else:incorrect=incorrect+1

            if(pattern_list==testcase_neg):
                neg_logit_diff_list.append(logit_diff)

            elif(pattern_list==testcase_key):
                key_logit_diff_list.append(logit_diff)

            else:
                const_logit_diff_list.append(logit_diff)

            
        accuracy_per_pattern= (correct/(correct+incorrect))*100
        accuracy_per_pattern_list.append(accuracy_per_pattern)


    avg_logit_diff_per_pattern=[sum(i)/len(i) for i in [neg_logit_diff_list,key_logit_diff_list,const_logit_diff_list]]

    print(f"Average logit difference per pattern (negation,keyword_trap,constraint_swap){avg_logit_diff_per_pattern}")
    print(f"Accuracy per pattern (negation,keyword_trap,constraint_swap):{accuracy_per_pattern_list}%")
            # per_case_logits=[]

            # for c in candidates:
            #     abstract= c['text']
            #     input= process_inputs(query,abstract)
            #     if(c['doc_id']=="true_doc"):
            #         true_logit=compute_logits(input)
            #         per_case_logits.append(true_logit)
            #     else:
            #         decoy_logit=compute_logits(input)
            #         per_case_logits.append(decoy_logit)


            #     logit_diff= true_logit-decoy_logit
            #     print(logit_diff)

if __name__ == "__main__":
    main()




