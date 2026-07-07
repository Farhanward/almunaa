# تقرير اختبار المناعة الواسع

- الملف: `C:\Projects\almunaa\data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl`
- السجلات المحمّلة: `942`
- مرات التكرار: `1`
- إجمالي الفحوص: `942`
- الأخطاء: `0`
- الزمن: `1.5417s`
- الإنتاجية: `611.01` فحص/ثانية

## الجودة

- Accuracy: `93.21%`
- Precision: `91.78%`
- Recall: `97.10%`
- Specificity: `87.69%`
- F1: `94.37%`
- Confusion: `TP=536 TN=342 FP=48 FN=16`

## الضغط والانهيار

- الحالة: `PASS`
- بلا استثناءات: `True`
- P99 أقل من 10ms: `False`
- P99 أقل من 25ms: `True`
- ذروة الذاكرة أقل من 128MB: `True`
- Latency mean/p95/p99/max: `1.6053 / 3.7151 / 10.8447 / 26.1004` ms
- Peak memory: `0.241` MB

## توزيع القرارات

- `QUARANTINE`: `583`
- `ALLOW`: `358`
- `BLOCK`: `1`

## أكثر القواعد عملاً

- `LEXICAL_MODEL_RISK`: `584`
- `PROMPT_OVERRIDE`: `141`
- `PROMPT_INJECTION`: `86`
- `CODE_EXECUTION_REQUEST`: `52`
- `PROMPT_ROLE_TAKEOVER`: `39`
- `SQUASHED_PROMPT_OVERRIDE`: `28`
- `TOOL_HIJACK_REQUEST`: `25`
- `JAILBREAK`: `13`
- `CONTEXT_EXFILTRATION`: `11`
- `PROMPT_LEAK`: `10`
- `HARMFUL_SECURITY_REQUEST`: `6`
- `PROMPT_EXTRACTION`: `4`
- `AR_PROMPT_INJECTION`: `3`
- `PRIVILEGED_AGENT_OPERATION`: `3`
- `INPUT_DESTRUCTIVE_INTENT`: `2`
