# تقرير اختبار المناعة الواسع

- الملف: `C:\Projects\almunaa\data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl`
- السجلات المحمّلة: `15919`
- مرات التكرار: `1`
- إجمالي الفحوص: `15919`
- الأخطاء: `0`
- الزمن: `15.2248s`
- الإنتاجية: `1045.6` فحص/ثانية

## الجودة

- Accuracy: `53.11%`
- Precision: `99.24%`
- Recall: `24.90%`
- Specificity: `99.68%`
- F1: `39.82%`
- Confusion: `TP=2469 TN=5986 FP=19 FN=7445`

## الضغط والانهيار

- الحالة: `PASS`
- بلا استثناءات: `True`
- P99 أقل من 10ms: `True`
- P99 أقل من 25ms: `True`
- ذروة الذاكرة أقل من 128MB: `True`
- Latency mean/p95/p99/max: `0.925 / 1.9359 / 6.7092 / 21.9105` ms
- Peak memory: `0.71` MB

## توزيع القرارات

- `ALLOW`: `13431`
- `QUARANTINE`: `2481`
- `BLOCK`: `7`

## أكثر القواعد عملاً

- `PROMPT_OVERRIDE`: `2628`
- `PROMPT_INJECTION`: `1419`
- `CODE_EXECUTION_REQUEST`: `884`
- `PROMPT_ROLE_TAKEOVER`: `636`
- `SQUASHED_PROMPT_OVERRIDE`: `443`
- `TOOL_HIJACK_REQUEST`: `391`
- `PROMPT_LEAK`: `216`
- `CONTEXT_EXFILTRATION`: `142`
- `JAILBREAK`: `106`
- `HARMFUL_SECURITY_REQUEST`: `65`
- `PROMPT_EXTRACTION`: `60`
- `PRIVILEGED_AGENT_OPERATION`: `24`
- `INPUT_DESTRUCTIVE_INTENT`: `14`
- `AR_PROMPT_INJECTION`: `4`
