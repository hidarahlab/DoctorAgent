# Evaluation results

| Metric | Value |
|---|---|
| n_questions | 27 |
| intent_accuracy | 1.0 |
| retrieval_hit_at_5 | 1.0 |
| retrieval_mrr | 1.0 |
| in_book_answer_rate | 1.0 |
| out_of_book_escalation_rate | 1.0 |
| overall_outcome_accuracy | 1.0 |
| faithfulness | 0.95 |
| completeness | 0.893 |
| relevance | 0.952 |
| tone | 0.943 |
| confidence_in_book | 0.933 |
| confidence_out_of_book | 0.4 |
| revision_rate | 0.158 |
| requery_rate | 0.174 |
| citation_validity | 1.0 |
| avg_latency_s | 13.53 |
| p90_latency_s | 20.88 |
| avg_cost_usd | 0.0429 |
| avg_cost_medical_usd | 0.0504 |
| total_cost_usd | 1.1588 |

## Retrieval ablation (in-book questions, Hit@5 / MRR)

| Query | Retriever | Hit@5 | MRR |
|---|---|---|---|
| raw question | dense | 0.737 | 0.671 |
| raw question | sparse | 0.737 | 0.684 |
| raw question | hybrid | 0.737 | 0.737 |
| planner rewrite | dense | 1.0 | 1.0 |
| planner rewrite | sparse | 1.0 | 0.974 |
| planner rewrite | hybrid | 1.0 | 1.0 |

## Per question

| id | category | intent | escalated | conf | F | C | hit@5 | s | $ |
|---|---|---|---|---|---|---|---|---|---|
| en01 | in_book | medical_question | False | 0.954 | 0.95 | 0.95 | True | 10.76 | 0.039 |
| en02 | in_book | medical_question | False | 0.949 | 0.97 | 0.9 | True | 11.61 | 0.04073 |
| en03 | in_book | medical_question | False | 0.96 | 0.97 | 0.95 | True | 9.05 | 0.03034 |
| en04 | in_book | medical_question | False | 0.945 | 0.95 | 0.92 | True | 12.24 | 0.04269 |
| en05 | in_book | medical_question | False | 0.914 | 0.92 | 0.88 | True | 20.88 | 0.06103 |
| en06 | in_book | medical_question | False | 0.941 | 0.95 | 0.92 | True | 12.26 | 0.03984 |
| en07 | in_book | medical_question | False | 0.89 | 0.97 | 0.75 | True | 11.89 | 0.0397 |
| en08 | in_book | medical_question | False | 0.91 | 0.93 | 0.85 | True | 14.74 | 0.04265 |
| id01 | in_book | medical_question | False | 0.95 | 0.95 | 0.95 | True | 11.46 | 0.03816 |
| id02 | in_book | medical_question | False | 0.92 | 0.95 | 0.85 | True | 16.18 | 0.0498 |
| id03 | in_book | medical_question | False | 0.943 | 0.95 | 0.92 | True | 13.16 | 0.04297 |
| id04 | in_book | medical_question | False | 0.934 | 0.96 | 0.88 | True | 12.74 | 0.04326 |
| id05 | in_book | medical_question | False | 0.931 | 0.96 | 0.87 | True | 16.47 | 0.05279 |
| id06 | in_book | medical_question | False | 0.96 | 0.97 | 0.95 | True | 11.3 | 0.03747 |
| id07 | in_book | medical_question | False | 0.939 | 0.97 | 0.88 | True | 12.65 | 0.04273 |
| ly01 | in_book_lay_terms | medical_question | False | 0.945 | 0.95 | 0.92 | True | 13.06 | 0.04225 |
| ly02 | in_book_lay_terms | medical_question | False | 0.895 | 0.9 | 0.85 | True | 18.18 | 0.05203 |
| ly03 | in_book_lay_terms | medical_question | False | 0.925 | 0.93 | 0.9 | True | 17.82 | 0.05015 |
| ly04 | in_book_lay_terms | medical_question | False | 0.929 | 0.95 | 0.88 | True | 23.66 | 0.0736 |
| oob01 | out_of_book | medical_question | True | 0.4 | 0.9 | 0.1 | None | 19.17 | 0.07256 |
| oob02 | out_of_book | medical_question | True | 0.4 | 0.9 | 0.2 | None | 27.95 | 0.08047 |
| oob03 | out_of_book | medical_question | True | 0.4 | 0.9 | 0.2 | None | 18.46 | 0.06874 |
| oob04 | out_of_book | medical_question | True | 0.4 | 0.9 | 0.2 | None | 22.45 | 0.07511 |
| nm01 | non_medical | out_of_scope | False | None | None | None | None | 1.29 | 0.00016 |
| nm02 | non_medical | out_of_scope | False | None | None | None | None | 2.05 | 0.00018 |
| em01 | emergency | emergency | True | None | None | None | None | 2.44 | 0.00021 |
| gr01 | greeting | greeting | False | None | None | None | None | 1.51 | 0.0002 |
