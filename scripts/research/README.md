# أدوات البحث عن الجهات (Research tools)

تُشغَّل من مجلد مؤقت (scratchpad) وتُخرج JSON بصيغة `{"targets":[...], "unreachable":[...]}` ثم تُستورد بـ
`python3 scripts/targets_tool.py import --country <Country> --file <json>` (يمنع التكرار ويُثري الصفوف الموجودة).

| الأداة | المصدر | الدول |
|---|---|---|
| `mj_scrape.py out.json` | madaresonajo.com (مدارس، مراكز تربية خاصة، جامعات، تدريب) | الأردن |
| `ed_scrape.py <country-slug> out.json` | edarabia.com (مدارس، جامعات، تدريب، SEN) | كل الدول |
| `yello.py <host> <cats> out.json` ثم `y2imp.py in out` | أدلة الصفحات الصفراء: jordanyp.com, saudiayp.com, yello.ae, qataryello.com, kuwaityello.com, omanyp.com, bahrainyellow.com | كل الدول |
| `dh_scrape.py <last_page> outdir` | disability-hub.com Arab World Directory (يفك تشفير الإيميلات) | الخليج |
| `parse_sayidaty.py in.html out.json` | دليل سيدتي لمراكز ذوي الاحتياجات | السعودية |
| `build_import.py <country-slug> out.json in1.json ...` | يحوّل مخرجات madaresona/edarabia لصيغة الاستيراد | — |
| `enrich.py in.json out.json` | يزور موقع كل جهة وصفحة "اتصل بنا" لاستخراج الإيميل/الهاتف/واتساب | — |
| `txt.py file.html [marker] [len]` | عرض نص صفحة للفحص اليدوي | — |

لإثراء الصفوف الناقصة: `targets_tool.py export-missing --country X --file miss.json` ← `enrich.py miss.json enr.json` ← `import`.

مصادر استُخدمت أيضاً (يدوياً عبر البحث): QNL (قطر)، منصة حياة/تواصل (السعودية)، abadc.com.sa (دليل الاحتياجات الخاصة – عدة دول)، specialneedsuae.com، مواقع وأدلة متفرقة (موثقة في عمود "مصدر المعلومة").
