---
name: taqdeem
description: روتين "تقديم" اليومي لعامر السعايدة – تقديم السيرة على جهات الأردن والخليج. استخدمها عندما يكتب المستخدم "تقديم ايميل [عدد]" أو "تقديم واتس [عدد]" أو "تقديم بحث [دولة]" أو "تقديم حالة" أو "تقديم سيرة" أو "تقديم" وحدها. الإيميل = المستخدم يراجع ويعدّل في "مكتب الإرسال" ويضغط "أضف لطابور الإرسال"، وClaude يرسل المعتمد تلقائياً كل ساعة ضمن الحد اليومي. Use also for the hourly auto-send run، الواتساب = طابور رسائل لإضافة Chrome.
---

# مهارة "تقديم"

هذه المهارة تجمع كل ما بُني في هذا المستودع منذ البداية: قوائم الجهات، السير الأربع، السجلات، المسودات، الواتساب، اللوحة. اقرأ `CLAUDE.md` أولاً، فقواعده كلها سارية هنا.

## قواعد لا تُكسر
1. **الإرسال التلقائي فقط لما وافق عليه المستخدم.** مكتب الإرسال: https://claude.ai/artifact/BoV5qMq37yJHyVii75FZ53
   - Claude يضع الرسائل في طابور المكتب بالحالة `ready`. المستخدم يراجع كل رسالة ويعدّلها ويضغط **"أضف لطابور الإرسال"** ← الحالة `approved`. هذه الضغطة هي الموافقة الصريحة على تلك الرسالة بعينها (المستلم + الموضوع + النص + اسم المرفق ظاهرة له في المكتب).
   - المهمة المجدولة كل ساعة (`trig_01LQ8qmiAfGi5ZWKD6sgGPMW`، الدقيقة 58، داخل هذه الجلسة لأنها تحمل ربط Gmail) ترسل `approved` فقط عبر `mcp__Gmail__send_message`، ليلاً ونهاراً، حتى `daily_max` (30) في `config/settings` بالمكتب.
   - ممنوع إرسال أي رسالة ليست `approved`، أو تجاوز الحد اليومي، أو الإرسال وقت `paused: true`. الرد والتحويل محظوران في `.claude/settings.json`.
2. **الواتساب لا يُرسل من هنا.** الناتج ملف طابور فقط (`docs/whatsapp_queue_format.md`) والمستخدم يضغط إرسال من إضافته.
3. **لا تكرار:** الاختيار يتم عبر `pipeline.py select` فقط (يستبعد السجل والدفتر والعمود 14)، ثم `log_tool.py check` لكل جهة.
4. **لا دكتوراه للمدارس والجامعات:** نسخة السيرة `NoPhD` (ملف `_S`) واسم المرفق الظاهر دائماً `Amer_AlSaaideh_CV_Arabic.pdf` / `Amer_AlSaaideh_CV_English.pdf`.
5. **لا معلومات مخترعة:** كل إنجاز من `scripts/cv_content.py` فقط، وكل معلومة عن الجهة من مصدر علني (موقعها أو رابط المصدر في ملف الدولة). إن لم تجد معلومة حقيقية اكتب سطراً عاماً صادقاً عن نوع الجهة.
6. **مهارة humanizer إلزامية** (`humanizer:humanizer`) على كل رسالة وإيميل قبل المراجعة.
7. **الحصة اليومية** من `config/sending_policy.json`. إن طلب المستخدم أكثر من `remaining_today` أو كان `backlog_days ≥ 3` ← نبّهه واقترح العدد المناسب، ولا تتجاوز إلا بموافقة صريحة.
8. **كل تعثر** (خطأ أو موافقة ناقصة) ← `python3 scripts/issues_tool.py add ...` فوراً، ويُعرض في الملخص.
9. **commit + push** بعد كل تشغيل على الفرع `claude/job-application-profile-nj3oqj`.

## الأوامر

| الأمر | الناتج |
|---|---|
| `تقديم ايميل N` | N مسودة Gmail مخصصة من دول مختلفة + تقرير مراجعة + تحديث الملفات واللوحة |
| `تقديم واتس N` | طابور N رسالة واتساب (`output/whatsapp/queue_*.json/.csv`) + مراجعة + تحديث |
| `تقديم بحث [دولة]` | توسيع/إثراء قوائم الجهات (إيميل، واتساب، صفحات تواصل) |
| `تقديم حالة` | مزامنة المرسَل والردود والارتدادات + اللوحة + ما يحتاج تدخلك (بدون إنشاء شيء) |
| `تقديم سيرة` | تعديل `cv_content.py` ← `build_cv.py` ← عرض PDF للمراجعة |
| `تقديم` وحدها | اسأل: إيميل أم واتس، وكم؟ (اعرض الحصة المتاحة لكل قناة) |

إن لم يذكر N: اقترح `remaining_today` من `quota`.

## خط العمل (تقديم ايميل / تقديم واتس)

أنشئ مهمة (TaskCreate) لكل مرحلة. **لا تُعلَّم أي مهمة completed إلا بعد PASS من المراجع.** كل مرحلة ينفذها مساعد مستقل (Agent) بتعليمات مكتوبة كاملة، لأن المساعد يبدأ بلا سياق.

### Helper-0: التحقق المسبق
```
git pull --ff-only origin claude/job-application-profile-nj3oqj
```
- المكتب: `ArtifactData list collection=queue out_dir=output/runs/_sync/desk` ← `pipeline.py sync-desk --dir output/runs/_sync/desk` (يسجّل ما ضغط عليه المستخدم "أرسلتها").
- إيميل (تحقق إضافي): ابحث في Gmail `in:sent newer_than:14d` ← احفظ `[{to,date,subject}]` في `output/runs/_sync/sent.json` ← `pipeline.py sync-sent --file ...`
- ارتدادات: `from:mailer-daemon newer_than:14d` ← استخرج الإيميلات المرتدة ← `sync-bounces --file ...`
- ردود: رسائل واردة من إيميلات موجودة في `output/pipeline_ledger.json` ← `sync-replies --file ...`
- واتساب: `pipeline.py sync-wa`
- `pipeline.py quota --channel email|whatsapp` ← إن كان `stop: true` توقف وأبلغ المستخدم.

### Helper-1: الاختيار
```
python3 scripts/pipeline.py select --channel email|whatsapp --count N
```
يطبع مسار التشغيل `output/runs/<stamp>_<channel>/`. ثم لكل جهة: `python3 scripts/log_tool.py check --email ... --phone ... --name ...`، وأي تطابق يُحذف من `selection.json` ويُستبدل.

### Helper-2: البحث للتخصيص + نبذة الجهة
لكل جهة: افتح موقعها (`website`) أو رابط المصدر (`source`) واستخرج:
- **معلومة حقيقية واحدة** للتخصيص في الرسالة (برنامج، فئة يخدمونها، منهج، فرع، رسالة الجهة).
- **نبذة بالعربية** (2–3 جمل) يراها المستخدم في مكتب الإرسال قبل الموافقة: ما الجهة، من تخدم (أعمار/إعاقات/مراحل)، أهم خدماتها، وأي معلومة لافتة (سنة التأسيس، فروع، اعتماد) فقط إن ذكرها مصدر. + 2–4 نقاط قصيرة.
- **فحص سريع:** هل موقع الجهة ونطاق إيميلها يعملان؟ هل الجهة فعلاً ضمن المجال؟ أي شك يُكتب في `warn` فيظهر للمستخدم كتنبيه في المكتب.
احفظ في `research.json`: `[{id, fact, about, facts: [...], url, limited, warn}]`. إن تعذّر: جملة صادقة مما هو معروف (النوع + المدينة) و`limited: true`، ولا تخمّن. `desk-export` يضع النبذة تلقائياً في المكتب (`about`, `about_facts`, `about_url`). أدوات مساعدة: `scripts/research/enrich.py`, `scripts/research/pw_fetch.js` (حوّل http إلى https).

### Helper-3: الكتابة (+ humanizer)
اكتب `texts.json` في مجلد التشغيل.

**إيميل:** كل عنصر:
```json
{"id":1,"lang":"AR|EN","cv":"Full|NoPhD","subject":"...","paras":["...","..."],"items":["...","..."],"after":["..."]}
```
- اللغة والنسخة: من ملف الدولة (عمودا 12 و13) مع قواعد CLAUDE.md. مدرسة/جامعة ← `NoPhD` دائماً.
- البنية: تحية باسم الجهة ← من أنا والمسمى المناسب لنوع الجهة ← سطر عن الجهة نفسها (من research) ← 2–3 إنجازات في `items` تبدأ بأفعال الصورة: **Achieved / Led / Improved / Managed / Delivered** = **حققت / قدت / حسّنت / أدرت / قدّمت** ← السيرة مرفقة واستعداد للمقابلة. التوقيع يُضاف آلياً من `output/drafts/signature.json`، فلا تكتبه.
- إنجازات مسموحة (من السيرة فقط): تحقيق الدمج الكلي لأول مرة في مدرسة حكومية؛ تدريب المعلمين (TOT – كامبردج)؛ إعداد وتنفيذ IEP؛ إدارة غرف المصادر؛ القياس والتشخيص؛ تعديل السلوك؛ محاضر في جامعة اليرموك والدبلوم العالي لإعداد المعلمين؛ أبحاث منشورة في Scopus؛ عمل في قطر. "طالب دكتوراه" فقط لغير المدارس والجامعات.
- الموضوع قصير ومحدد، مثال: `طلب توظيف – أخصائي تربية خاصة | عامر السعايدة` / `Application – Special Education Teacher | Amer AlSaaideh`.
- 4–6 أسطر نص (بدون القائمة والتوقيع). بلا كلمات سبام (مجاني، عاجل، فرصة ذهبية، !!!، guaranteed، urgent، free) وبلا شرطات طويلة (—).

- **رسائل الإنجليزي:** أضف لكل عنصر `subject_ar` و`body_ar` = ترجمة عربية أمينة بنفس الفقرات والنقاط، لا تضيف ولا تحذف. تظهر للمستخدم في المكتب تحت النص للفهم فقط، والرسالة تُرسل بالإنجليزية.

**واتساب:** كل عنصر `{"id":1,"lang":"AR|EN","cv":"Full|NoPhD","text":"..."}` في 2–4 أسطر، مختلفة عن بعضها (لا نسخ متطابقة، فهي إشارة سبام لواتساب)، تذكر اسم الجهة.

ثم **حمّل مهارة `humanizer:humanizer` وطبّقها على كل نص**: احذف "ليس فقط... بل"، الثلاثيات المصطنعة، المبالغة، الافتتاحيات المسرحية، الخواتيم المكررة، الشرطات الطويلة.

### Helper-4: الإنشاء
**إيميل (مكتب الإرسال):** لا تُنشأ مسودات Gmail من Claude.
```
python3 scripts/pipeline.py desk-export --run <run> --start <آخر n في الطابور + 1>
```
ثم اكتب الملفات إلى طابور المكتب: `ArtifactData batch` على `https://claude.ai/artifact/BoV5qMq37yJHyVii75FZ53` بإدخالات `{op:"set", collection:"queue", doc_id, file_path}` من `output/desk/export/_index.json` (حتى 50 في الدفعة). لمعرفة آخر `n`: `ArtifactData list collection=queue`.
- الحصة اليومية والفواصل في وثيقة `config/settings` بالمكتب (`daily_max`, `gap_min`, `gap_max`, `window`) وتُحدَّث بـ `ArtifactData update` إن تغيّرت `config/sending_policy.json`.
- السير مرفوعة كأصول في المكتب (`output/desk/assets.json`). بعد إعادة بناء السير (`build_cv.py`) ارفعها من جديد (`Artifact publish asset:true file_paths`) وحدّث الروابط في `assets.json` ثم أعد التصدير.
- طريقة Gmail القديمة (`pipeline.py build` + `create_draft` + `record`) تبقى احتياطاً فقط إن طلبها المستخدم.

**واتساب:**
```
python3 scripts/pipeline.py wa-queue --run <run>
```

### الإرسال التلقائي (المهمة المجدولة كل ساعة)
1. `git pull`. احذف `output/runs/_sync/desk`، ثم `ArtifactData list collection=queue query.limit=1000` و`get config/settings` على المكتب، كلاهما بـ `out_dir=output/runs/_sync/desk`.
2. `python3 scripts/pipeline.py send-plan --dir output/runs/_sync/desk` ← `output/desk/outbox/plan.json`. يحسب: المرسل اليوم (بتوقيت الأردن)، المتبقي من `daily_max`، والساعات الباقية، فيختار 1–2 رسالة بحسب الأقدم موافقةً. إن كان `send_now: 0` أو `paused` ← انتهِ.
3. لكل عنصر: `mcp__Gmail__send_message` بـ `to=[to]`, `subject`, `htmlBody`, `body`, `attachments=[{content: attachment, filename, mimeType: "application/pdf"}]` (المرفق مرجع `sha256:` لملف السيرة الصحيح، و`filename` هو الاسم النظيف). ثم `ArtifactData update queue/<doc_id>` بـ `{status: "sent", sent_at: "YYYY-MM-DDTHH:MM:SS" (الأردن), gmail_id}`، ثم `delete_draft` لـ `old_draft_id` إن وُجد. بين رسالتين 2–5 دقائق (`sleep` في الخلفية).
4. فشل الإرسال ← `{status: "failed", error}` + `issues_tool.py add`، بلا إعادة تلقائية.
5. الارتدادات: `search_threads from:mailer-daemon newer_than:2d` ← الإيميل المرتد في الطابور يصبح `failed/bounce` + `pipeline.py sync-bounces`. أكثر من 5% من آخر 50 ← `config/settings {paused: true}` + `issues_tool`.
6. أعد قراءة الطابور ثم `pipeline.py sync-desk --dir output/runs/_sync/desk` (يسجّل في applications_log وملفات الدول) ثم `pipeline.py stats` ثم commit/push. سطر واحد للمستخدم: كم أُرسل وكم بقي اليوم وأي خطأ.

### Reviewer: المراجع المستقل
مساعد جديد **لم يشارك** في المراحل السابقة. يقرأ `selection.json`, `research.json`, `texts.json`, `drafts.json`/`queue.json` و`scripts/cv_content.py` و`output/applications_log.xlsx`، ويتحقق من:
- [ ] لا جهة موجودة مسبقاً في السجل أو الدفتر (`log_tool.py check`).
- [ ] العدد ≤ الحصة (أو بموافقة مسجلة)، والجهات من أكثر من دولة إن أمكن.
- [ ] مدرسة/جامعة ← `cv = NoPhD` ولا كلمة "دكتوراه/PhD/doctoral" في النص.
- [ ] اسم المرفق الظاهر بلا `_S` ولا "NoPhD".
- [ ] كل إنجاز موجود في السيرة، ومعلومة الجهة لها رابط في `research.json`.
- [ ] الإيميل/الرقم مطابق لملف الدولة؛ الرقم بصيغة دولية.
- [ ] اللغة مناسبة لنوع الجهة.
- [ ] لا كلمات سبام، لا شرطات طويلة، لا علامات كتابة آلية (humanizer).
- [ ] الطول: إيميل 4–6 أسطر، واتساب 2–4.
- [ ] (إيميل) كل الرسائل موجودة في طابور المكتب (`ArtifactData list queue`) بالحالة `ready` (لا تُوضع `approved` أبداً من Claude)، ومعها `cv_url` صحيح للنسخة (`_S` للمدارس والجامعات) و`send_name` نظيف.
يكتب `review.md` بنتيجة لكل عنصر: **PASS** أو **FAIL + السبب**. أي FAIL ← يعاد للكاتب ثم مراجعة جديدة، أو يُحذف العنصر (وإن كانت مسودة: `delete_draft`) ويُسجَّل.

### الإغلاق
```
python3 scripts/pipeline.py mark --run <run>
python3 scripts/pipeline.py stats
python3 scripts/targets_tool.py stats
git add -A && git commit -m "تقديم <channel> <N> – <run>" && git push -u origin claude/job-application-profile-nj3oqj
```
ثم أعد نشر اللوحة (Artifact) من `output/dashboard/index.html` إلى نفس الرابط المحفوظ في `output/dashboard/artifact_url.txt`.

### الملخص للمستخدم (قصير)
1. ما أُنجز: N مسودة/رسالة، التوزيع على الدول، نتيجة المراجع.
2. **ما يحتاج تدخلك:**
   - رسائل في مكتب الإرسال تنتظر مراجعتك وضغطة "أضف لطابور الإرسال" (رابط المكتب). بعدها الإرسال تلقائي كل ساعة حتى 30 يومياً، ليلاً ونهاراً.
   - رسائل واتساب جاهزة في الطابور، بفاصل 3–6 دقائق.
   - ردود وصلت (أولوية!) وارتدادات.
   - العناصر المفتوحة في `python3 scripts/issues_tool.py list`.
   - أي طلب تجاوز حصة.
3. رابط اللوحة.

## تقديم بحث [دولة]
- `targets_tool.py stats` لمعرفة الدول الأقل متبقياً.
- مصادر جديدة: `scripts/research/README.md` و`sources_tool.py` (سجل كل مصدر: نجح/جزئي/فشل).
- إثراء: `targets_tool.py export-missing` ← `research/enrich.py` ← `targets_tool.py import`.
- واتساب: `targets_tool.py whatsapp --country X`، ومسح المواقع `export-web` ← `research/wa_scan.py` ← `apply-scan`.
- كل صف له رابط مصدر علني. المصادر المتعذرة ← ورقة "تعذر الوصول" + issues_tool، وأبلغ المستخدم ليساعد.

## تقديم حالة
Helper-0 فقط + `stats` + نشر اللوحة + الملخص. لا إنشاء مسودات.

## تقديم سيرة
عدّل `scripts/cv_content.py` (العربية مرجع والإنجليزية ترجمة مطابقة) ← `python3 scripts/build_cv.py` ← حوّل صفحات PDF لصور وتحقق من الشكل ← أرسل الملفات للمستخدم (SendUserFile) ← انتظر موافقته قبل استخدامها في مسودات جديدة. المسودات القديمة تبقى بالسيرة القديمة ما لم يطلب إعادة إنشائها.

## الحصص (من config/sending_policy.json)
| | أسبوع 1 | أسبوع 2 | أسبوع 3 | بعدها | سقف | فاصل | نافذة |
|---|---|---|---|---|---|---|---|
| إيميل | 30 | 30 | 30 | 30 | 30 | 1–2 كل ساعة | 24 ساعة |
| واتساب | 10 | 15 | 20 | 20 | 25 | 3–6 د | 09:00–15:00 |
أيام العمل: الأحد–الخميس. إيقاف الإيميل إذا الارتدادات > 5% من آخر 50. تخفيف الواتساب إذا الردود < 5% بعد 50 رسالة (السقف الشهري للرسائل غير المُجاب عليها).
