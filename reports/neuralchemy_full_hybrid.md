# تقرير اختبار المناعة الواسع

- الملف: `C:\Projects\almunaa\data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl`
- السجلات المحمّلة: `15919`
- مرات التكرار: `1`
- إجمالي الفحوص: `15919`
- الأخطاء: `0`
- الزمن: `25.2022s`
- الإنتاجية: `631.65` فحص/ثانية

## الجودة

- Accuracy: `97.58%`
- Precision: `97.75%`
- Recall: `98.38%`
- Specificity: `96.27%`
- F1: `98.06%`
- Confusion: `TP=9753 TN=5781 FP=224 FN=161`

## الضغط والانهيار

- الحالة: `PASS`
- بلا استثناءات: `True`
- P99 أقل من 10ms: `False`
- P99 أقل من 25ms: `True`
- ذروة الذاكرة أقل من 128MB: `True`
- Latency mean/p95/p99/max: `1.5502 / 3.5782 / 10.6829 / 30.2672` ms
- Peak memory: `0.718` MB

## توزيع القرارات

- `QUARANTINE`: `9970`
- `ALLOW`: `5942`
- `BLOCK`: `7`

## أكثر القواعد عملاً

- `LEXICAL_MODEL_RISK`: `9963`
- `PROMPT_OVERRIDE`: `1568`
- `PROMPT_INJECTION`: `795`
- `CODE_EXECUTION_REQUEST`: `626`
- `SQUASHED_PROMPT_OVERRIDE`: `441`
- `PROMPT_ROLE_TAKEOVER`: `367`
- `TOOL_HIJACK_REQUEST`: `238`
- `PROMPT_LEAK`: `127`
- `CONTEXT_EXFILTRATION`: `86`
- `JAILBREAK`: `67`
- `PROMPT_EXTRACTION`: `37`
- `HARMFUL_SECURITY_REQUEST`: `36`
- `PRIVILEGED_AGENT_OPERATION`: `18`
- `INPUT_DESTRUCTIVE_INTENT`: `7`
- `AR_PROMPT_INJECTION`: `4`
