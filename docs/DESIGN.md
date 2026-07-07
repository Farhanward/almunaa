# تصميم المناعة

## الهدف

حارس أمام الوكيل، لا أمام المخرج فقط. الفرق عن «الميزان»:

- الميزان يحكم صحة وأمان المخرج.
- المناعة تحرس دورة الوكيل كاملة: مدخلات، أدوات، ذاكرة، مخرجات.

## الطبقات

1. `input`: حقن أوامر، محاولة كشف system prompt، قلب الأولويات.
2. `tool_call`: أوامر مدمرة، Docker socket، تحميل وتنفيذ من الشبكة، وصول لملفات أسرار.
3. `memory`: تسميم ذاكرة أو تعليمات دائمة خبيثة.
4. `output`: تسريب أسرار، توجيه المستخدم لتعطيل الحماية، أو إفشاء مفاتيح.
5. `context`: مؤشرات تشغيلية مرافقة للحدث مثل `parent_process` و`child_process`.

## قواعد izaen المدمجة

استُخدمت قواعد آمنة من أرشيف ZEED كمصدر محلي:

- أدوات سرقة الاعتماديات: `mimikatz`, `invoke-mimikatz`, `sekurlsa`, `procdump`.
- مؤشرات C2 أو تجاوز ذاكرة: `meterpreter`, `cobalt strike`, `reflective_dll`, `amsi bypass`.
- أوامر PowerShell المشفرة: `-enc`, `-EncodedCommand`, `FromBase64String`.
- LOLBins لتحميل وتشغيل: `certutil -urlcache`, `regsvr32 /i:http`, `mshta http`, `rundll32 http`.
- تعطيل الاسترجاع: `vssadmin delete shadows`, `wmic shadowcopy delete`, `bcdedit /set recoveryenabled no`.
- عملية ويب تستدعي shell: `w3wp/nginx/apache/node` مع `cmd/powershell/bash`.

## القرارات

- `ALLOW`: لا مؤشرات.
- `REVIEW`: مؤشرات منخفضة/متوسطة.
- `QUARANTINE`: مؤشرات عالية، تحفظ الحمولات ولا تنفذ آلياً.
- `BLOCK`: مؤشرات حرجة مثل حذف شامل أو مفاتيح خاصة أو Docker socket مع أمر تدميري.

## وضعا التشغيل

1. **Rule-only**: سريع جداً ومحافظ. مناسب للبوابات التي تريد false positives قليلة جداً. آخر قياس على 15,919 سجل: precision 99.24% وp99 6.73ms، لكنه يفوّت هجمات مموّهة كثيرة.
2. **Hybrid**: يضيف نموذج Naive Bayes لفظي محلي مدرّب على بيانات إنترنت مفتوحة. مناسب لحراسة الوكلاء العامة. آخر قياس على 15,919 سجل: F1 98.06%، recall 98.38%، specificity 96.27%.

## اختبار الانهيار

بيانات الاختبار الكبيرة:

- المصدر: `neuralchemy/Prompt-injection-dataset` من Hugging Face.
- الحجم: 15,919 سجل.
- الملف: `data\benchmarks\neuralchemy_prompt_injection_full.events.jsonl`.
- ضغط نهائي: 47,757 فحص بتكرار 3، بدون أخطاء، ذروة ذاكرة 1.70MB، وp99 10.55ms. لا يوجد انهيار فعلي؛ فقط تحذير أن الوضع الهجين أبطأ من rule-only.

## المرحلة التالية

- ربط `/api/scan` و`/api/tool-gate`.
- دمج اختياري مع `C:\Projects\almeezan` لفحص المخرجات بعمق.
- توقيع Ed25519 لاحقاً بدل HMAC المحلي.
- سياسة سماح/منع حسب اسم الوكيل، بيئة التشغيل، ونوع الأداة.
