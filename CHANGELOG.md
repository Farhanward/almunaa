# Changelog — almunaa

## 1.0.0 — 2026-07-05 (الترقية المؤسسية)

- **خدمة HTTP محلية**: `python -m almunaa.cli serve` — نقاط `/api/health` (مفتوحة) و`/api/version` و`/api/metrics` + نقاط النطاق.
- **Config مركزي عبر البيئة**: `almunaa/config.py` (متغيرات `ALMUNAA_*`).
- **Observability**: `almunaa/observability.py` — سجلات JSON بتدوير تلقائي + عدادات وp50/p95/p99.
- **مصادقة وحدود**: `X-API-Key` بمقارنة constant-time عند ضبط `ALMUNAA_API_KEY`، وحد حجم الطلب (413) مع تفريغ آمن للجسم.
- **تغليف**: `pyproject.toml` كامل مع entry point وأمر `version`.
- **توثيق تشغيل**: `docs/OPERATIONS.md`.
- **اختبارات enterprise**: config/metrics/auth/الخدمة عبر HTTP حقيقي على منفذ ephemeral.

## 0.1.0 — 2026-07-04

- المنتج الأولي + تحسين الجودة الإنتاجية الموثق في MASTER_REFERENCE.
