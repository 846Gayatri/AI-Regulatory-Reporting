# Periodic Adverse Drug Experience Report (PADER)

**Generated:** {{ generated_date }}

---

{% for name, content in sections.items() %}
{{ content }}
{% if not loop.last %}
---
{% endif %}
{% endfor %}

---

*This report was generated automatically by the GenAR PADER pipeline. All data is derived from Individual Case Safety Reports (ICSRs) submitted during the reporting period.*
