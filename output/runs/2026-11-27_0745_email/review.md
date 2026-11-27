# Review: 2026-11-27_0745_email (independent reviewer)

Checked for all 34 messages (30 ready + reserves 31-34): selection.json, research.json, texts.json, verify.json and scripts/cv_content.py, plus `log_tool.py check` for every email and name, and a domain/name match against the desk queue (`output/runs/_sync/desk/queue`, 118 docs) and the ledger.
- Duplicates: none in the log, the ledger or the desk queue.
- NoPhD: every school uses `cv=NoPhD` and never mentions a PhD. The only `Full` CVs are centres 23 and 24, which say "طالب دكتوراه". That is allowed for centres. Centres 1 and 33 use NoPhD, which is the conservative choice.
- Language: EN for international schools. EN for id 1 because the vacancy is advertised in English. AR for local centres 23, 24 and 33. Every EN message has subject_ar/body_ar.
- Achievements: each one matches cv_content.py and opens with one of Achieved/Led/Managed/Delivered (or حققت/قدت/أدرت/قدّمت).
- Style: no em/en dashes, no "not only…but", no salesy words. Each message is 5 lines (EN) or 6 lines (AR). Each opens with "I am Amer Abdeljalil" or "أنا عامر عبد الجليل". Each has one descriptive org fact backed by research.json. Qatar appears only as "worked in Qatar", with no duration or year.

| id | org | verdict | note |
|---|---|---|---|
| 1 | Dubai Center for Special Needs | FIXED | Vacancy title "Class Teacher (Special Needs)" is used as advertised, in the subject and the body (priority). Removed "with students with autism, learning difficulties and intellectual disabilities" from the Qatar sentence (EN + body_ar) because the CV's Qatar role does not list these groups. hr@ is the address the careers page asks for. The ad requires CDA registration and prefers UAE experience. |
| 2 | Oryx International School | PASS | reception@ is the only email on the site. Vacancies page exists. |
| 3 | Beta Cambridge School | PASS | registrar@ is the admissions inbox (no recruitment email on the site). |
| 4 | Intl School of Choueifat Doha | FIXED | "Dear The International School…" changed to "Dear International School…". Generic inbox; SABIS hires through its careers portal. |
| 5 | United School International | PASS | Official recruitment email. |
| 6 | Al Khor International School | PASS | recruitment@ is from the site. The school prefers applications through its portal or TES. |
| 7 | Qatar International School | PASS | The school usually requires QTS, so a reply is less likely. |
| 8 | ISL Qatar | PASS | General mail@ (no recruitment email). |
| 9 | American School of Doha | PASS | reception@ is on the old domain (the site moved to asd.sch.qa). MX check ok. Hiring is mainly through the portal or job fairs. |
| 10 | Ideal Indian School | PASS | hr@ is from the careers page. |
| 11 | Shantiniketan Indian School | PASS | |
| 12 | Hartford American School | PASS | Current vacancies are not in SEN. |
| 13 | SEK International School Qatar | PASS | FLAG: admissions@ is a parents' admissions inbox. SEK jobs site recommended. |
| 14 | Vision International School | PASS | inquiries@ is on the new domain from the site. |
| 15 | Alpha Cambridge School | PASS | registrar@ inbox. |
| 16 | Cambridge School Doha | FIXED | "Dear The Cambridge School…" changed to "Dear Cambridge School…". FLAG: feedback@tcsqatar.com is a parent feedback inbox (the only email on the site). The user should decide to keep it or exclude it. |
| 17 | Jordanian International School(s) | PASS | EN used because the school is classed international, although it also has a National Program. The user may prefer AR. The email comes from the directory and is not shown on the site. |
| 18 | American Community School Amman | PASS | The email comes from the directory and is not shown on the site. |
| 19 | Cambridge High School Amman | PASS | |
| 20 | One World International School Riyadh | PASS | FLAG: admissions inbox from the directory. |
| 21 | Dome International Schools | PASS | Official hrm@. |
| 22 | American International School Riyadh | PASS | join_us@ is the official address. |
| 23 | إثراء السلوك (Behaviour Enrichment) | PASS | Centre, so Full CV and the doctoral-student mention are allowed. hr@ is on the site. |
| 24 | مركز الابتسامة | PASS | Centre run by the Indian Association in Sharjah with an English site. AR follows the local rule; the user may prefer EN. |
| 25 | American School of Kuwait | FIXED | "Dear The American School…" changed to "Dear American School…". The school requires certified teachers. |
| 26 | Kuwait American School | PASS | Posts for 2026-27 are filled; the CV will be kept for future openings. |
| 27 | Al Shomoukh International | PASS | hr@ is from the site. |
| 28 | Indian School Nizwa | PASS | careers@ is from the site. |
| 29 | American School of Bahrain | PASS | jobs@ is the official address. No SEN vacancy. |
| 30 | Al Hekma International School | PASS | Duplicate rows were checked and only one message is used. |
| 31 (reserve) | Step One International School | PASS | FLAG: admissions inbox from the directory. |
| 32 (reserve) | Philippine International School Qatar | PASS | The school serves the Filipino community, so a reply is less likely. |
| 33 (reserve) | Future Centre for Special Needs | PASS | AR + NoPhD. frc@ is from the site. |
| 34 (reserve) | Iqra'a American School | PASS | contact@ general inbox. |

FAIL ids to drop: none. Flagged for the user's decision (not failed): 16 (parent feedback inbox); 13, 20 and 31 (admissions inboxes).

RESULT: PASS
