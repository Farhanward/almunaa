# تقرير اختبار المناعة الواسع

- الملف: `C:\Projects\almunaa\data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl`
- السجلات المحمّلة: `15377`
- مرات التكرار: `1`
- إجمالي الفحوص: `15377`
- الأخطاء: `0`
- الزمن: `13.7917s`
- الإنتاجية: `1114.94` فحص/ثانية

## الجودة

- Accuracy: `52.26%`
- Precision: `99.25%`
- Recall: `24.54%`
- Specificity: `99.68%`
- F1: `39.35%`
- Confusion: `TP=2381 TN=5655 FP=18 FN=7323`

## الضغط والانهيار

- الحالة: `PASS`
- بلا استثناءات: `True`
- P99 أقل من 10ms: `True`
- ذروة الذاكرة أقل من 128MB: `True`
- Latency mean/p95/p99/max: `0.869 / 1.8056 / 6.5507 / 19.2376` ms
- Peak memory: `0.713` MB

## توزيع القرارات

- `ALLOW`: `12978`
- `QUARANTINE`: `2393`
- `BLOCK`: `6`

## أكثر القواعد عملاً

- `PROMPT_OVERRIDE`: `2580`
- `PROMPT_INJECTION`: `1400`
- `CODE_EXECUTION_REQUEST`: `832`
- `PROMPT_ROLE_TAKEOVER`: `615`
- `SQUASHED_PROMPT_OVERRIDE`: `429`
- `TOOL_HIJACK_REQUEST`: `366`
- `PROMPT_LEAK`: `208`
- `CONTEXT_EXFILTRATION`: `135`
- `JAILBREAK`: `101`
- `HARMFUL_SECURITY_REQUEST`: `65`
- `PROMPT_EXTRACTION`: `56`
- `PRIVILEGED_AGENT_OPERATION`: `21`
- `INPUT_DESTRUCTIVE_INTENT`: `12`
- `AR_PROMPT_INJECTION`: `1`
