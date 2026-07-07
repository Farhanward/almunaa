# تقرير اختبار المناعة الواسع

- الملف: `C:\Projects\almunaa\data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl`
- السجلات المحمّلة: `15919`
- مرات التكرار: `3`
- إجمالي الفحوص: `47757`
- الأخطاء: `0`
- الزمن: `73.7904s`
- الإنتاجية: `647.2` فحص/ثانية

## الجودة

- Accuracy: `97.58%`
- Precision: `97.75%`
- Recall: `98.38%`
- Specificity: `96.27%`
- F1: `98.06%`
- Confusion: `TP=29259 TN=17343 FP=672 FN=483`

## الضغط والانهيار

- الحالة: `PASS`
- بلا استثناءات: `True`
- P99 أقل من 10ms: `False`
- P99 أقل من 25ms: `True`
- ذروة الذاكرة أقل من 128MB: `True`
- Latency mean/p95/p99/max: `1.5142 / 3.5279 / 10.5246 / 31.8484` ms
- Peak memory: `1.692` MB

## توزيع القرارات

- `QUARANTINE`: `29910`
- `ALLOW`: `17826`
- `BLOCK`: `21`

## أكثر القواعد عملاً

- `LEXICAL_MODEL_RISK`: `29889`
- `PROMPT_OVERRIDE`: `4704`
- `PROMPT_INJECTION`: `2385`
- `CODE_EXECUTION_REQUEST`: `1878`
- `SQUASHED_PROMPT_OVERRIDE`: `1323`
- `PROMPT_ROLE_TAKEOVER`: `1101`
- `TOOL_HIJACK_REQUEST`: `714`
- `PROMPT_LEAK`: `381`
- `CONTEXT_EXFILTRATION`: `258`
- `JAILBREAK`: `201`
- `PROMPT_EXTRACTION`: `111`
- `HARMFUL_SECURITY_REQUEST`: `108`
- `PRIVILEGED_AGENT_OPERATION`: `54`
- `INPUT_DESTRUCTIVE_INTENT`: `21`
- `AR_PROMPT_INJECTION`: `12`
