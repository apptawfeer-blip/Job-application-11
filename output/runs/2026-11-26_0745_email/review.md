# Review: 2026-11-26 runs 0745 + 0755 (29 desk messages)

Independent reviewer. Sources: export JSONs, selection/research/texts of both runs, scripts/cv_content.py, docs/style_edits_log.md, output/pipeline_ledger.json, the desk queue snapshot in output/runs/_sync/desk/queue, and `log_tool.py check` per message.

**Result: 26 PASS, 3 FAIL.**

Checks run on all 29 messages, all clean:
- `log_tool.py check`: no match for every message. But see the two queue duplicates below.
- cv_url matches lang+cv for every message. All NoPhD ones (schools, QF entities, RIA) use the _S blobs. No دكتوراه/PhD/doctor in subject/body/body_ar of any NoPhD message.
- send_name is clean and matches lang everywhere.
- No long dashes (— or –), no "ليس فقط", no "من الأردن", no spam words, no surname in body paragraphs. Every EN message has subject_ar/body_ar.
- Status: 28 are `ready`, and 2026-11-26-0745-email-06 is `reserve`. None are `approved`.

| doc_id | verdict | notes / fix |
|---|---|---|
| 2026-11-26-0745-email-01 | PASS | MADA. Fact supported. TOT, Yarmouk and the "under publication" digital-readiness research are all in the CV. |
| 2026-11-26-0745-email-03 | PASS | QISH is a therapy clinic, not a school, so Full/PhD is OK. Facts supported. Warn mentions English may suit better. Kept AR per the user's rule for local bodies. |
| 2026-11-26-0745-email-04 | PASS | Facts supported. Optional: the warn is stale. It advises switching to contact@ilctherapy.com, which is already the `to` (fix in review_fixes.json). |
| 2026-11-26-0745-email-05 | PASS | The sign language course (Al-Balqa Consulting & Training Center) is in the CV. Fact supported. |
| 2026-11-26-0745-email-06 | PASS (reserve) | Rehab medical center, so Full is OK. Warn: website is down and the email comes only from Edarabia, so bounce risk is medium. |
| 2026-11-26-0745-email-08 | PASS | School, NoPhD, Arabic_S. Fact supported. |
| 2026-11-26-0745-email-09 | PASS | Fact (Muscat, 2014, autism) supported. The autism assessment course from MOSD is in the CV. |
| 2026-11-26-0745-email-10 | **FAIL** | **Duplicate.** HOPE Qatar, info@hope-qatar.org, is already on the desk as b01-33 with status `approved`. The ledger also has it (batch_01, drafted, Targets_Qatar row 129). `log_tool check` misses it only because it is not sent yet. Fix: drop it and do not add it to the queue. Promote the reserve -06 if a replacement is wanted. Mark Targets_Qatar row 146 as a duplicate/contacted. |
| 2026-11-26-0745-email-11 | PASS | Treated as a school, so NoPhD, Arabic_S. Fact (1999, ABA/TEACCH) supported. |
| 2026-11-26-0745-email-12 | **FAIL** | **Duplicate.** Awsaj Academy, awsajacademy@qf.org.qa, is already on the desk as b01-31 with status `approved`. The ledger also has it (batch_01, Targets_Qatar row 125). Fix: drop it and do not add it to the queue. Mark Targets_Qatar row 569 as a duplicate/contacted. (Text, language, CV and translation were otherwise correct.) |
| 2026-11-26-0745-email-13 | PASS | No fact about the org. Research is limited (only "Duhail, Doha"), and leaving it out is acceptable and honest. Achievements are in the CV. |
| 2026-11-26-0745-email-15 | PASS | Special education center, so Full is OK. Fact (licensed by MoE, 40+ students integrated) supported by research. |
| 2026-11-26-0745-email-17 | PASS | Thesis topic, the 10% reduction and the study recommendations are all in the CV. Fact supported. |
| 2026-11-26-0745-email-19 | PASS | British-curriculum special needs school, so EN + English_S. MOBAK and IEP are in the CV. Translation is faithful. |
| 2026-11-26-0745-email-20 | PASS | Fact supported. Achievements are in the CV. |
| 2026-11-26-0745-email-21 | PASS | Fact (under MOSD, in Seeb) supported. |
| 2026-11-26-0745-email-22 | PASS | QF school, so EN + English_S. Fact (ages 3–21, severe/complex needs) supported. Translation is faithful. Optional: the warn still says "المدخل الحالي AR/Full يحتاج تعديل", which is stale (fix in JSON). |
| 2026-11-26-0745-email-23 | PASS | International school, so EN + English_S. Fact (Hamala, 3–18) supported. Warn: the address is the admissions inbox. |
| 2026-11-26-0745-email-24 | PASS | QF, so EN + English_S. Fact supported. Yarmouk teaching and field supervision are in the CV. Translation is faithful. |
| 2026-11-26-0745-email-27 | PASS | Fact (2008, under Shafallah, ID/DD) supported. Note: this is a local chapter of Best Buddies International. AR is defensible (local NGO under Shafallah), but the user could be asked. |
| 2026-11-26-0745-email-28 | PASS | No fact about the org (research limited). Warn: the site looks like a nursery and may be outdated. Text is accurate. |
| 2026-11-26-0745-email-29 | PASS | School, NoPhD, Arabic_S. No fact about the org (limited). Email source is the Yusr government directory. Warn shown. |
| 2026-11-26-0745-email-31 | PASS | International (Indian curriculum) school, so EN + English_S. Fact supported. Translation is faithful. |
| 2026-11-26-0755-email-01 | PASS | HMC hospital department, so Full/PhD is OK. Fact supported. Warn: this is a patient-services inbox, and hiring usually goes through the HMC portal. |
| 2026-11-26-0755-email-02 | PASS | IB school, so EN + English_S. Fact supported. Warn: the address is the admissions inbox. |
| 2026-11-26-0755-email-03 | PASS | Fact (Inclusion & Learning Support team, IEPs) supported by the official page. Translation is faithful. |
| 2026-11-26-0755-email-05 | **FAIL** | **CV accuracy.** Bullet: "Delivered behaviour modification training programmes … including the preparation of shadow teachers." In the CV these are two separate programmes. Fix (body): "Delivered training programmes in behaviour modification for children with disabilities and learning difficulties, and in shadow teacher preparation." Fix (body_ar): "قدّمت برامج تدريبية في تعديل السلوك للأطفال ذوي الإعاقة وصعوبات التعلم، وفي إعداد معلمي الظل." |
| 2026-11-26-0755-email-07 | PASS | Fact (Salwa, 1978, ages 4–18, 75+ countries) supported. Sent to the HR email that the careers page names. |
| 2026-11-26-0755-email-08 | PASS | No fact about the org (limited). Text is accurate. Warn: the address is a registrar inbox. |

Process note: `log_tool.py check` only covers sent rows. Selection should also exclude emails already in `pipeline_ledger.json` or in the desk queue with status ready/approved/reserve. That is how HOPE Qatar and Awsaj slipped in through duplicate rows in Targets_Qatar (129/146 and 125/569).

## Final
- 0745-10 HOPE و0745-12 Awsaj: استُبعدتا (مكررتان مع b01-33 وb01-31).
- 0755-05: صُحّح النص حسب الاقتراح.
- النتيجة النهائية: PASS لـ 27 رسالة (26 ready + 1 reserve) ووُضعت في المكتب.
