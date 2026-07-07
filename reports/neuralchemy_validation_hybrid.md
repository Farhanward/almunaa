# تقرير اختبار المناعة الواسع

- الملف: `C:\Projects\almunaa\data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl`
- السجلات المحمّلة: `941`
- مرات التكرار: `1`
- إجمالي الفحوص: `941`
- الأخطاء: `0`
- الزمن: `1.5366s`
- الإنتاجية: `612.39` فحص/ثانية

## الجودة

- Accuracy: `93.73%`
- Precision: `92.64%`
- Recall: `96.63%`
- Specificity: `89.93%`
- F1: `94.59%`
- Confusion: `TP=516 TN=366 FP=41 FN=18`

## الضغط والانهيار

- الحالة: `PASS`
- بلا استثناءات: `True`
- P99 أقل من 10ms: `False`
- P99 أقل من 25ms: `True`
- ذروة الذاكرة أقل من 128MB: `True`
- Latency mean/p95/p99/max: `1.602 / 3.7821 / 10.8308 / 30.3774` ms
- Peak memory: `0.256` MB

## توزيع القرارات

- `QUARANTINE`: `557`
- `ALLOW`: `384`

## أكثر القواعد عملاً

- `LEXICAL_MODEL_RISK`: `556`
- `PROMPT_OVERRIDE`: `125`
- `PROMPT_INJECTION`: `74`
- `CODE_EXECUTION_REQUEST`: `35`
- `PROMPT_ROLE_TAKEOVER`: `34`
- `SQUASHED_PROMPT_OVERRIDE`: `28`
- `TOOL_HIJACK_REQUEST`: `28`
- `PROMPT_LEAK`: `11`
- `CONTEXT_EXFILTRATION`: `8`
- `JAILBREAK`: `7`
- `PROMPT_EXTRACTION`: `2`
- `HARMFUL_SECURITY_REQUEST`: `2`
- `AR_PROMPT_INJECTION`: `1`
