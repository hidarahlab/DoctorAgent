# Evaluation results

| Metric | Value |
|---|---|
| n_questions | 27 |
| intent_accuracy | 1.0 |
| retrieval_hit_at_5 | 0.947 |
| retrieval_mrr | 0.947 |
| in_book_answer_rate | 0.947 |
| out_of_book_escalation_rate | 1.0 |
| overall_outcome_accuracy | 0.963 |
| faithfulness | 0.95 |
| completeness | 0.898 |
| relevance | 0.949 |
| tone | 0.936 |
| confidence_in_book | 0.934 |
| confidence_out_of_book | 0.4 |
| revision_rate | 0.368 |
| requery_rate | 0.217 |
| citation_validity | 1.0 |
| avg_latency_s | 15.39 |
| p90_latency_s | 23.32 |
| avg_cost_usd | 0.0469 |
| avg_cost_medical_usd | 0.0551 |
| total_cost_usd | 1.2674 |

## Retrieval ablation (in-book questions, Hit@5 / MRR)

| Query | Retriever | Hit@5 | MRR |
|---|---|---|---|
| raw question | dense | 0.737 | 0.629 |
| raw question | sparse | 0.737 | 0.649 |
| raw question | hybrid | 0.684 | 0.684 |
| planner rewrite | dense | 1.0 | 1.0 |
| planner rewrite | sparse | 1.0 | 0.939 |
| planner rewrite | hybrid | 0.947 | 0.947 |

## Per question

| id | category | intent | escalated | conf | F | C | hit@5 | s | $ |
|---|---|---|---|---|---|---|---|---|---|
| en01 | in_book | medical_question | False | 0.948 | 0.95 | 0.93 | True | 13.13 | 0.04001 |
| en02 | in_book | medical_question | False | 0.958 | 0.97 | 0.93 | True | 12.09 | 0.03824 |
| en03 | in_book | medical_question | False | 0.96 | 0.97 | 0.95 | True | 10.39 | 0.033 |
| en04 | in_book | medical_question | False | 0.948 | 0.95 | 0.93 | True | 17.1 | 0.05868 |
| en05 | in_book | medical_question | False | 0.91 | 0.9 | 0.9 | True | 23.23 | 0.06668 |
| en06 | in_book | medical_question | False | 0.941 | 0.95 | 0.92 | True | 11.21 | 0.03789 |
| en07 | in_book | medical_question | False | 0.87 | 0.95 | 0.75 | True | 15.04 | 0.04423 |
| en08 | in_book | medical_question | False | 0.929 | 0.95 | 0.88 | True | 13.72 | 0.03942 |
| id01 | in_book | medical_question | False | 0.95 | 0.95 | 0.95 | True | 19.59 | 0.05765 |
| id02 | in_book | medical_question | False | 0.92 | 0.95 | 0.85 | True | 15.71 | 0.05219 |
| id03 | in_book | medical_question | True | 0.4 | 0.95 | 0.1 | False | 23.32 | 0.06895 |
| id04 | in_book | medical_question | False | 0.945 | 0.97 | 0.9 | True | 13.94 | 0.04293 |
| id05 | in_book | medical_question | False | 0.929 | 0.95 | 0.88 | True | 17.1 | 0.05346 |
| id06 | in_book | medical_question | False | 0.96 | 0.97 | 0.95 | True | 12.37 | 0.04138 |
| id07 | in_book | medical_question | False | 0.933 | 0.95 | 0.88 | True | 14.3 | 0.04498 |
| ly01 | in_book_lay_terms | medical_question | False | 0.945 | 0.97 | 0.9 | True | 18.85 | 0.05587 |
| ly02 | in_book_lay_terms | medical_question | False | 0.919 | 0.93 | 0.88 | True | 22.4 | 0.06594 |
| ly03 | in_book_lay_terms | medical_question | False | 0.935 | 0.95 | 0.9 | True | 17.57 | 0.05041 |
| ly04 | in_book_lay_terms | medical_question | False | 0.914 | 0.92 | 0.88 | True | 31.12 | 0.07544 |
| oob01 | out_of_book | medical_question | True | 0.4 | 0.9 | 0.2 | None | 18.05 | 0.06956 |
| oob02 | out_of_book | medical_question | True | 0.4 | 0.95 | 0.2 | None | 24.11 | 0.0747 |
| oob03 | out_of_book | medical_question | True | 0.4 | 0.95 | 0.2 | None | 19.19 | 0.07274 |
| oob04 | out_of_book | medical_question | True | 0.4 | 0.95 | 0.2 | None | 24.65 | 0.08232 |
| nm01 | non_medical | out_of_scope | False | None | None | None | None | 1.32 | 0.00017 |
| nm02 | non_medical | out_of_scope | False | None | None | None | None | 2.18 | 0.00018 |
| em01 | emergency | emergency | True | None | None | None | None | 2.31 | 0.0002 |
| gr01 | greeting | greeting | False | None | None | None | None | 1.57 | 0.0002 |
