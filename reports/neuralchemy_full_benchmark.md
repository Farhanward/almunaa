# تقرير اختبار المناعة الواسع

- الملف: `C:\Projects\almunaa\data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl`
- السجلات المحمّلة: `15377`
- مرات التكرار: `1`
- إجمالي الفحوص: `15377`
- الأخطاء: `0`
- الزمن: `3.7612s`
- الإنتاجية: `4088.3` فحص/ثانية

## الجودة

- Accuracy: `46.51%`
- Precision: `99.53%`
- Recall: `15.31%`
- Specificity: `99.88%`
- F1: `26.54%`
- Confusion: `TP=1486 TN=5666 FP=7 FN=8218`

## الضغط والانهيار

- الحالة: `PASS`
- بلا استثناءات: `True`
- P99 أقل من 10ms: `True`
- ذروة الذاكرة أقل من 128MB: `True`
- Latency mean/p95/p99/max: `0.2187 / 0.3702 / 1.2439 / 5.3493` ms
- Peak memory: `0.597` MB

## توزيع القرارات

- `ALLOW`: `13884`
- `QUARANTINE`: `1487`
- `BLOCK`: `6`

## أكثر القواعد عملاً

- `PROMPT_OVERRIDE`: `1163`
- `PROMPT_INJECTION`: `650`
- `PROMPT_ROLE_TAKEOVER`: `260`
- `TOOL_HIJACK_REQUEST`: `156`
- `PROMPT_LEAK`: `87`
- `CONTEXT_EXFILTRATION`: `55`
- `JAILBREAK`: `37`
- `INPUT_DESTRUCTIVE_INTENT`: `6`
