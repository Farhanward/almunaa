from __future__ import annotations

import re

from .models import AgentEvent, ThreatFinding
from .normalization import text_variants
from .text import compact, mask_secret


Rule = tuple[str, str, str, str, re.Pattern[str]]


INPUT_RULES: list[Rule] = [
    ("PROMPT_INJECTION", "input", "high", "حقن أوامر", re.compile(r"\b(ignore|disregard|override)\b.{0,80}\b(system|developer|instructions?)\b", re.I)),
    ("PROMPT_OVERRIDE", "input", "high", "تجاوز تعليمات سابقة", re.compile(r"\b(ignore|forget|disregard|bypass|override|break|violate)\b.{0,120}\b(previous|prior|above|system|developer|policy|policies|rules|instructions?|guardrails?|constraints?)\b", re.I)),
    ("PROMPT_ROLE_TAKEOVER", "input", "high", "استبدال دور الوكيل", re.compile(r"\b(you are now|act as|pretend to be|developer mode|god mode|root mode|sudo mode|no restrictions?|without restrictions?)\b", re.I)),
    ("PROMPT_LEAK", "input", "high", "طلب كشف تعليمات", re.compile(r"\b(system prompt|developer message|hidden instructions|reveal your prompt)\b", re.I)),
    ("CONTEXT_EXFILTRATION", "input", "high", "طلب استخراج سياق أو أسرار", re.compile(r"\b(print|show|reveal|dump|export|exfiltrate|leak)\b.{0,120}\b(system prompt|developer message|hidden prompt|context|memory|secrets?|api keys?|tokens?|credentials?)\b", re.I)),
    ("TOOL_HIJACK_REQUEST", "input", "high", "طلب اختطاف أداة", re.compile(r"\b(use|call|invoke|run|execute)\b.{0,100}\b(tool|function|shell|terminal|cmd|powershell|bash|docker)\b", re.I)),
    ("INPUT_DESTRUCTIVE_INTENT", "input", "critical", "طلب تنفيذ تدميري", re.compile(r"\b(rm\s+-rf\s+/|docker\s+rm\s+-f|format\s+[a-z]:|vssadmin\s+delete\s+shadows|wmic\s+shadowcopy\s+delete)\b", re.I)),
    ("HARMFUL_SECURITY_REQUEST", "input", "high", "طلب أمني ضار", re.compile(r"\b(hack|exploit|exfiltrate|steal|leak|spy|phish|ransomware|malware|backdoor|keylogger|credential|database)\b.{0,160}\b(passwords?|credentials?|private data|sensitive information|government database|people|victim|target|payload|xss|sql injection)\b", re.I)),
    ("CODE_EXECUTION_REQUEST", "input", "high", "طلب تنفيذ كود خطر", re.compile(r"\b(import\s+os|subprocess|os\.system|popen|eval\s*\(|exec\s*\()\b.{0,160}\b(whoami|id|/etc/passwd|cmd|powershell|bash|curl|wget|rm\s+-rf)\b", re.I)),
    ("PRIVILEGED_AGENT_OPERATION", "input", "high", "طلب صلاحية وكيل عالية", re.compile(r"\b(admin access|privileged[_ -]?operation|temporary admin|root access|sudo access|next agent)\b.{0,160}\b(use|execute|override|bypass|payload|operation)\b", re.I)),
    ("AR_PROMPT_INJECTION", "input", "high", "حقن أوامر بالعربية", re.compile(r"(تجاهل|تجاوز|اكسر|عطّل).{0,70}(تعليمات|النظام|السياسة|الحماية)")),
    ("AR_CONTEXT_EXFILTRATION", "input", "high", "طلب استخراج سياق أو أسرار بالعربية", re.compile(r"(اكشف|اعرض|اطبع|استخرج|سرّب).{0,90}(تعليمات|النظام|السياق|الذاكرة|الأسرار|اسرار|المفاتيح|التوكن|توكن)")),
    ("AR_SECRET_LEAK_REQUEST", "input", "high", "طلب كشف أسرار", re.compile(r"(اكشف|اعرض|اطبع|استخرج).{0,70}(مفاتيح|اسرار|أسرار|توكن|كلمات المرور|كلمة المرور)")),
    ("JAILBREAK", "input", "high", "محاولة jailbreak", re.compile(r"\b(DAN mode|jailbreak|unfiltered|do anything now|always answer|never refuse|do not refuse|no safety|uncensored)\b", re.I)),
    ("INDIRECT_PROMPT_INJECTION", "input", "high", "حقن أوامر غير مباشر", re.compile(r"\b(this (?:document|email|webpage|file) says|instructions? for the assistant|assistant must|model must|begin system prompt|end system prompt)\b", re.I)),
    ("PROMPT_EXTRACTION", "input", "high", "استخراج prompt أو هوية النموذج", re.compile(r"\b(repeat|print|reveal|show|dump)\b.{0,120}\b(words above|prompt above|system prompt|you are chatgpt|knowledge cutoff|training data|training completion)\b", re.I)),
    ("SQUASHED_PROMPT_OVERRIDE", "input", "high", "حقن أوامر مضغوط", re.compile(r"(ignore|bypass|override|forget)(all)?(previous|prior|system|developer|safety|instructions|directives|rules|guardrails)|(safetysuspended|bypasssafety|ignoresafety|withoutrestrictions)", re.I)),
]

TOOL_RULES: list[Rule] = [
    ("DESTRUCTIVE_COMMAND", "tool_call", "critical", "أمر تدميري", re.compile(r"\b(rm\s+-rf\s+/|docker\s+rm\s+-f|docker\s+system\s+prune|format\s+[a-z]:|Remove-Item\b.+-Recurse|del\s+/s)\b", re.I)),
    ("NETWORK_TO_SHELL", "tool_call", "high", "تنفيذ من الشبكة مباشرة", re.compile(r"\b(curl|wget|iwr|Invoke-WebRequest)\b.+\b(bash|sh|iex|Invoke-Expression|python\s+-c)\b", re.I)),
    ("DOCKER_SOCKET", "tool_call", "critical", "وصول Docker socket", re.compile(r"(/var/run/docker\.sock|docker\.sock)", re.I)),
    ("SECRET_FILE_ACCESS", "tool_call", "high", "وصول لملفات أسرار", re.compile(r"(/vault/secrets/[^\s;&|]+|\.env\b|credentials\.json|id_rsa|private_key|\.ssh/config)", re.I)),
    ("PRIVILEGE_CHANGE", "tool_call", "high", "تغيير صلاحيات", re.compile(r"\b(chmod\s+777|chown\s+root|sudoers|Set-ExecutionPolicy)\b", re.I)),
]

IZAEN_THREAT_RULES: list[Rule] = [
    (
        "IZAEN_CREDENTIAL_TOOL",
        "tool_call",
        "critical",
        "أداة سرقة اعتماديات",
        re.compile(r"\b(invoke-mimikatz|mimikatz|sekurlsa|procdump(?:64)?(?:\.exe)?)\b", re.I),
    ),
    (
        "IZAEN_C2_PAYLOAD",
        "tool_call",
        "critical",
        "حمولة C2 أو تجاوز ذاكرة",
        re.compile(r"\b(meterpreter|cobalt\s*strike|reflective[_-]?dll|amsi\s*bypass)\b", re.I),
    ),
    (
        "IZAEN_ENCODED_POWERSHELL",
        "tool_call",
        "high",
        "PowerShell مشفر أو مخفي",
        re.compile(r"\b(powershell(?:\.exe)?|pwsh(?:\.exe)?)\b.{0,120}(?:-(?:enc|encodedcommand)\b|frombase64string\b)|\bfrombase64string\b", re.I),
    ),
    (
        "IZAEN_SCRIPT_DOWNLOAD",
        "tool_call",
        "high",
        "تحميل وتنفيذ مشبوه",
        re.compile(r"\b(downloadstring|certutil\s+-urlcache|regsvr32\b.{0,80}/i:https?://|mshta\s+https?://|rundll32\b.{0,80}https?://)\b", re.I),
    ),
    (
        "IZAEN_RECOVERY_TAMPER",
        "tool_call",
        "critical",
        "تعطيل الاسترجاع أو النسخ الظلية",
        re.compile(r"\b(vssadmin\s+delete\s+shadows|wmic\s+shadowcopy\s+delete|bcdedit\s+/set\s+recoveryenabled\s+no)\b", re.I),
    ),
    (
        "IZAEN_WEB_SHELL_CHILD",
        "tool_call",
        "high",
        "عملية ويب تستدعي shell",
        re.compile(r"\b(nginx|apache|httpd|iis|w3wp|node)\b.{0,120}\b(cmd(?:\.exe)?|powershell(?:\.exe)?|pwsh(?:\.exe)?|bash|sh)\b", re.I),
    ),
]

MEMORY_RULES: list[Rule] = [
    ("MEMORY_POISONING", "memory", "high", "تسميم ذاكرة", re.compile(r"(تذكر دائما|always remember|from now on).{0,120}(تجاهل|ignore|override|لا تطبق|disable)", re.I)),
    ("PERSISTENT_SECRET", "memory", "high", "تخزين سر في الذاكرة", re.compile(r"(احفظ|store|remember).{0,80}(password|secret|api key|token|كلمة المرور|توكن|مفتاح)", re.I)),
]

OUTPUT_RULES: list[Rule] = [
    ("API_KEY_LEAK", "output", "critical", "تسريب مفتاح API", re.compile(r"\b(?:sk|sk_live|sk_test|sk-ant|pplx|ghp|xoxb|AKIA)[A-Za-z0-9_\-]{12,}\b")),
    ("PRIVATE_KEY_LEAK", "output", "critical", "تسريب مفتاح خاص", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("EMAIL_LEAK", "output", "medium", "تسريب بريد", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("DISABLE_GUARDRAILS", "output", "high", "تعليمات تعطيل الحماية", re.compile(r"(عطل الحماية|disable guardrails|turn off safety|bypass security)", re.I)),
]


def _rules_for(event: AgentEvent) -> list[Rule]:
    rules = []
    if event.kind in {"input", "prompt"}:
        rules.extend(INPUT_RULES)
    elif event.kind == "tool_call":
        rules.extend(TOOL_RULES)
        rules.extend(IZAEN_THREAT_RULES)
        rules.extend(INPUT_RULES)
    elif event.kind == "memory":
        rules.extend(MEMORY_RULES)
        rules.extend(INPUT_RULES)
    elif event.kind == "output":
        rules.extend(OUTPUT_RULES)
    else:
        rules.extend(INPUT_RULES)
        rules.extend(TOOL_RULES)
        rules.extend(IZAEN_THREAT_RULES)
        rules.extend(MEMORY_RULES)
        rules.extend(OUTPUT_RULES)
    return rules


def scan_policy(event: AgentEvent) -> list[ThreatFinding]:
    findings: list[ThreatFinding] = []
    variants = text_variants(event.scan_text())
    for code, layer, severity, title, pattern in _rules_for(event):
        seen_evidence: set[str] = set()
        for variant_name, text in variants:
            for match in pattern.finditer(text):
                evidence = match.group(0)
                if "KEY" in code or "SECRET" in code or "PASSWORD" in code:
                    evidence = mask_secret(evidence)
                evidence = compact(evidence)
                evidence_key = f"{code}:{evidence.lower()}"
                if evidence_key in seen_evidence:
                    continue
                seen_evidence.add(evidence_key)
                if variant_name != "original":
                    evidence = compact(f"{variant_name}: {evidence}")
                detail = f"رُصد نمط {title} في طبقة {layer}."
                if variant_name == "decoded_base64":
                    detail += " تم اكتشافه بعد فك Base64."
                elif variant_name == "normalized":
                    detail += " تم اكتشافه بعد تطبيع النص."
                findings.append(
                    ThreatFinding(
                        code=code,
                        layer=layer,
                        severity=severity,
                        title=title,
                        detail=detail,
                        evidence=evidence,
                    )
                )
    return findings
