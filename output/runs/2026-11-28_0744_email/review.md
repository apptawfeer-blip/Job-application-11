OVERALL: PASS

# Independent review: 2026-11-28_0744_email (17 items)

Checked: duplicates (`log_tool.py check` for every email incl. secondary ones, plus email/domain/name grep in `output/pipeline_ledger.json` and `output/runs/_sync/desk/queue/*.json`, 152 files), PhD/doctorate words, every achievement against `scripts/cv_content.py`, org fact against `research.json`, opening/name rules, language, em dash/"!"/spam/humanizer tells, "worked in Qatar" without year/duration, length, email plausibility.

Global results: no duplicate found for any item. No em dash, en dash or "!" anywhere. No "2025"/"a year" with Qatar. "AlSaaideh/السعايدة" appears only in the subject line (template convention), never in the body. Every body is greeting + one paragraph + 2 bullets + closing line (4 to 6 lines). All schools are NoPhD with no PhD wording; the only PhD mention is item 14 (government body, cv Full, once).

| id | org | result | notes / fixes |
|---|---|---|---|
| 1 | Al Manar International School (Qatar) | PASS | Fact matches research (Common Core, KG to high school). Email is the branch general contact, not HR; careers page states local hiring only and uses an online form. |
| 4 | Global Academy International - Muaither (Qatar) | PASS | FIX: bullet "Led a research study" changed to "Conducted a research study" (CV says conducted), and body_ar "قدت دراسة" changed to "أجريت دراسة". Email recruitment@ is the better address from research (file had Lusail branch email). |
| 5 | Cardiff International School (Qatar) | PASS | Note: admissions@ address (admissions-only). ADHD workshop bullet matches CV. |
| 6 | Newton British Academy - Barwa City (Qatar) | PASS | Note: registrar address, not recruitment; group careers portal exists. Same group as a Newton entry (id 8) not in this run. |
| 7 | Brilliant Indian International School (Qatar) | PASS | Email corrected by research to info@ (file had malformed "Addressinfo@"). Phone numbers in selection look malformed (+9742044930039); not used for email. CBSE school, lower hiring odds. |
| 9 | Nord Anglia International School Al Khor (Qatar) | PASS | Selection has two emails; pipeline sends to the first (admissions.naisak@, admissions-only). Facts taken from Edarabia/search (site blocked). |
| 10 | Galileo International School (Qatar) | PASS | FIX: body_ar added "الهندي" to match "Central Board of Secondary Education" translation. Email enquiry@galileois.com is on the official site (galileo-is.com) per research. |
| 12 | French School of Amman (Jordan) | PASS | Note: secretaire@ (first of two) is a secretariat address; site empty, facts from Edarabia. School may require French. EN accepted as international school. |
| 13 | Modern American School (Jordan) | PASS | Email recruiting@ from employment page (better than admissions@). |
| 14 | General Secretariat for Special Education (Saudi, government) | PASS | AR, cv Full, PhD student mentioned once (allowed for non-school). Fact is the descriptive LRE regulation from moe.gov.sa. Note: government hiring is usually for nationals; low odds. |
| 17 | Emirates Down Syndrome Association (UAE) | PASS | AR local association, NoPhD kept as selected (no PhD wording). Services listed match research facts. Note: website address is Dubai (Al Qusais) while file says Abu Dhabi; city not mentioned in text, so no conflict. |
| 18 | Creative Children International School (Kuwait) | PASS | pr@ address (public relations), still the published one. Behaviour modification courses bullet matches CV certificates. |
| 19 | Indian Educational School (Bhavans, Kuwait) | PASS | Email HR@ from the school's published staff recruitment policy (replaces chairman@). CBSE school, lower odds. |
| 20 | International French School of Muscat (LFIM, Oman) | PASS | Email direction@ (management) from research. Al-Mubtakiroun bullet matches CV. May require French. |
| 21 | International School of Choueifat - Muscat (Oman) | PASS | info@ address. Not a duplicate of the queued ISC Doha message (different school/country/domain). |
| 22 | Riffa Views International School (Bahrain) | PASS | Note: admissions@ address (admissions-only). |
| 23 | Talent International and the Infant School (Bahrain) | PASS | admin.riffa@ general address. |

Fixes applied directly in texts.json: item 4 (EN bullet + body_ar), item 10 (body_ar). No emails, cv versions or languages were changed.
