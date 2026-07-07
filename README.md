# المناعة — Agent Immunity Gateway

`almunaa` هو تنفيذ أول لفكرة «المناعة»: حارس محلي للوكلاء يفحص:

- مدخلات المستخدم ضد حقن الأوامر.
- استدعاءات الأدوات ضد الاختطاف وتجاوز الصلاحيات.
- المخرجات ضد تسريب الأسرار.
- الذاكرة ضد التسميم.
- سياق الحدث ضد مؤشرات تشغيلية مثل عملية ويب تستدعي shell.

تم تعزيز قواعد التشغيل من أرشيف ZEED:
`C:\Users\FARHAN\Desktop\ZEED_GOLD_2026-06-29.zip`
وتحديداً مفاهيم `izaen` حول أنماط YARA/Sigma الخفيفة.

القرار يكون:

- `ALLOW`: آمن.
- `REVIEW`: يحتاج مراجعة.
- `QUARANTINE`: يُحجر ولا ينفّذ آلياً.
- `BLOCK`: ممنوع.

يعمل بلا تبعيات خارجية.

يوجد أيضاً وضع هجين اختياري يستخدم نموذجاً لفظياً محلياً خفيفاً:
`models\almunaa_lexical_guard.json`.

## تشغيل سريع

```powershell
cd C:\Projects\almunaa
python -m almunaa.cli scan --input examples\prompt_injection.json
python -m almunaa.cli scan --input examples\risky_tool_call.json
python -m almunaa.cli scan --input examples\encoded_powershell.json
python -m almunaa.cli scan --input examples\web_shell_child.json
python -m almunaa.cli verify-ledger
python -m unittest discover -s tests -v
```

## اختبار واسع من الإنترنت

تم جلب مجموعة `neuralchemy/Prompt-injection-dataset` من Hugging Face:

- المسار الخام: `data\external\neuralchemy_prompt_injection_full.jsonl`
- مسار أحداث الاختبار: `data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl`
- العدد: 15,919 سجل، منها 9,914 حقن/خطر و6,005 آمنة.

الأوامر:

```powershell
python -m almunaa.cli download-dataset --dataset neuralchemy-full
python -m almunaa.cli train-model --input data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl --out models\almunaa_lexical_guard.json
python -m almunaa.cli batch --input data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl --out reports\neuralchemy_full_rule_only.md --format md
python -m almunaa.cli batch --input data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl --model models\almunaa_lexical_guard.json --out reports\neuralchemy_full_hybrid.md --format md
python -m almunaa.cli stress --input data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl --model models\almunaa_lexical_guard.json --repeat 3 --out reports\neuralchemy_stress_hybrid.md --format md
```

آخر نتائج:

- Rule-only على 15,919 سجل: F1 = 39.82%، precision = 99.24%، recall = 24.90%، p99 = 6.73ms.
- Hybrid على كامل المجموعة: F1 = 98.06%، precision = 97.75%، recall = 98.38%، specificity = 96.27%.
- Hybrid على split=test فقط: F1 = 94.37%، recall = 97.10%.
- Stress: 47,757 فحص، 0 أخطاء، peak memory = 1.70MB، p99 = 10.55ms، ولا يوجد انهيار فعلي.
- تحقق إنتاجي 2026-07-04: `python -m unittest discover -s tests -v` => 11/11 ناجحة، و`python -m almunaa.cli verify-ledger` => ledger verified بعدد 5 سجلات.

## تحسين إنتاجي 2026-07-04

كان الحجر الصحي ينقّح الحدث نفسه، لكن سجل التدقيق والـ findings المحفوظة قد تحتفظ ببريد أو مفتاح خام إذا جاء التسريب داخل مخرجات الوكيل. تم تعديل مسار الحفظ بحيث:

- `quarantine/*.json` يحفظ الحدث والـ findings بعد تنقيح الأسرار.
- `ledger/almunaa-ledger.jsonl` يحفظ payload منقحاً مع بقاء hash-chain/HMAC قابلاً للتحقق.
- نتيجة الفحص اللحظية تبقى مفصلة للبرنامج المستدعي، بينما الملفات طويلة العمر لا تتحول إلى مخزن أسرار.

اختبار `test_persisted_ledger_and_quarantine_redact_secret_evidence` يثبت أن `sk_live_*` والبريد الإلكتروني لا يظهران في ملفات الحجر أو السجل، وأن السجل يبقى `verified`.

## صيغة الحدث

```json
{
  "kind": "tool_call",
  "agent": "carbonflow-agent",
  "content": "docker rm -f $(docker ps -aq)",
  "tool": {
    "name": "shell",
    "command": "docker rm -f $(docker ps -aq)"
  },
  "context": {
    "user": "owner",
    "session": "demo"
  }
}
```

## الملفات

- `almunaa/core.py`: محرك القرار.
- `almunaa/policy.py`: أنماط الهجوم والسياسات.
- `almunaa/quarantine.py`: حفظ الحمولات الخطرة مع تنقيح.
- `almunaa/ledger.py`: سجل حوادث hash-chain/HMAC.
- `almunaa/batch.py`: تقييم JSONL وقياسات جودة/ضغط.
- `almunaa/datasets.py`: تنزيل وتحويل بيانات Hugging Face.
- `almunaa/lexical_model.py`: نموذج Naive Bayes محلي اختياري.
- `almunaa/cli.py`: واجهة أوامر.

## قواعد مفعلة

- Prompt injection وكشف تعليمات النظام.
- طلبات كشف الأسرار ومفاتيح API.
- أوامر حذف تدميرية أو وصول Docker socket.
- تحميل وتنفيذ مباشر من الشبكة.
- PowerShell مشفر أو `FromBase64String`.
- مؤشرات Mimikatz/Sekurlsa/Procdump وC2.
- تعطيل النسخ الظلية أو خيارات الاسترجاع.
- عملية ويب تستدعي `cmd`/`powershell`/`bash`.

## مراجع تصميمية

- OWASP LLM01:2025 Prompt Injection.
- OWASP LLM Top 10: مخاطر الإفصاح، المخرجات غير المعقمة، Excessive Agency.
- NIST AI RMF / Generative AI Profile لفكرة إدارة المخاطر المستمرة.

## التشغيل المؤسسي (Enterprise) — v1.0.0

- **خدمة مناعة HTTP**: `python -m almunaa.cli serve` → `POST /api/scan-event {AgentEvent}` يعيد `ALLOW/REVIEW/QUARANTINE/BLOCK` مع findings.
- **بلا كتابة افتراضياً**: أضف `"record": true` لتسجيل الحادثة في ledger/quarantine المنقحين.
- **الوضع الهجين يحمل مرة واحدة** عند الإقلاع (`ALMUNAA_MODEL`، افتراضي `models\almunaa_lexical_guard.json`).
- **نقاط فحص**: `/api/health` (مفتوح) · `/api/version` · `/api/metrics`.
- **تهيئة عبر البيئة**: متغيرات `ALMUNAA_*` — انظر `docs/OPERATIONS.md`.
- **مصادقة**: `ALMUNAA_API_KEY` → ترويسة `X-API-Key`. **سجلات JSON**: `logs\almunaa.service.jsonl`.
