# تشغيل وكيل "تقديم" في مكان جديد

## 1) ما في هذه الحزمة
| المسار | الوظيفة |
|---|---|
| `CLAUDE.md` | كل القواعد (يُقرأ تلقائياً عند فتح المجلد في Claude Code) |
| `.claude/skills/taqdeem/SKILL.md` | مهارة "تقديم" + أسلوب عامر |
| `.claude/settings.json` | الصلاحيات (إرسال Gmail مسموح، الرد/التحويل ممنوع) |
| `scripts/` | كل الأدوات (pipeline, log_tool, targets_tool, build_cv, ...) |
| `config/sending_policy.json` | الحد المتدرّج، أوزان الدول، الفواصل |
| `cv/` | السير الأربع PDF + الشهادات + الأصول |
| `docs/` | سجل تعديلات الأسلوب وصيغة طابور الواتساب |
| `output/` | السجل والدفتر وملفات الجهات (ضروري لمنع التكرار) |
| `setup_new_agent/triggers/*.txt` | نصوص المهام المجدولة الثلاث |

## 2) الخطوات
1. أنشئ ريبو GitHub جديد **Private** وفارغ، وارفع محتوى الحزمة إليه (أو اطلب من Claude رفعه).
2. افتح جلسة Claude Code جديدة على الريبو الجديد (claude.ai/code أو التطبيق).
3. وصّل **Gmail** (amer.abdeljalil77@gmail.com) من Settings → Connectors في حساب Claude.
4. تأكد: `pip install openpyxl reportlab` ثم `python3 scripts/pipeline.py stats` يعمل.
5. أنشئ المهام المجدولة: اطلب من Claude في الجلسة الجديدة:
   "أنشئ 3 مهام مجدولة من ملفات setup_new_agent/triggers بنفس التوقيت وغيّر اسم الفرع إلى فرع الريبو الجديد".
   - الإرسال كل ساعة: `CRON_TZ=Asia/Amman 58 * * * *` (داخل الجلسة)
   - تجهيز الصباح: `CRON_TZ=Asia/Amman 43 7 * * *` (داخل الجلسة)
   - تقديم حالة: `CRON_TZ=Asia/Amman 0 10 * * *` (جلسة جديدة كل مرة)
6. **أوقف المهام القديمة** في الجلسة الحالية حتى لا يرسل وكيلان معاً (اطلب ذلك من Claude هنا).

## 3) مكتب الإرسال ولوحة المتابعة
- مكتب الإرسال: https://claude.ai/artifact/BoV5qMq37yJHyVii75FZ53
- لوحة المتابعة: https://claude.ai/artifact/K72UnkftTqSLYjh8jq43ZP
- يعملان من أي جلسة بنفس حساب Claude. الطابور محفوظ فيهما، لا شيء يضيع.
- إن كان حساب Claude مختلفاً: انشر `output/desk/index.html` من جديد كـ Artifact وحدّث الروابط في CLAUDE.md وSKILL.md ونصوص المهام.

## 4) استبدال الفرع
النصوص والملفات تذكر الفرع `claude/job-application-profile-nj3oqj` والريبو `apptawfeer-blip/Job-application-11`. في الريبو الجديد استبدلهما باسم الريبو/الفرع الجديد (Claude يستطيع ذلك بأمر واحد).

## 5) القواعد الذهبية (لا تتغير)
- لا إرسال إلا لرسالة `approved` بضغطة المستخدم. لا واتساب قبل موافقته على كل رسالة.
- لا رد ولا تحويل نيابة عنه. لا دكتوراه للمدارس والجامعات. لا معلومة مخترعة.
