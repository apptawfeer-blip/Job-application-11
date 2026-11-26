# -*- coding: utf-8 -*-
"""محتوى السيرة الذاتية (عربي + إنجليزي). المصدر المعتمد: النسخة العربية.
أي تعديل على السيرة يتم هنا ثم: python3 scripts/build_cv.py
العناصر التي تحمل phd=True تُحذف من نسخ NoPhD (للمدارس والجامعات).
"""

CONTACT = {
    "email": "amer.abdeljalil77@gmail.com",
    "phone_intl": "+962 78 018 9766",
    "orcid": "orcid.org/0009-0009-7349-4201",
}

AR = {
    "lang": "ar",
    "name": "عامر عبد الجليل السعايدة",
    "title": "أخصائي ومعلم تربية خاصة | منسق تعليم دامج | محاضر جامعي",
    "contact": f"عمّان، الأردن | \u2066{CONTACT['phone_intl']}\u2069 | {CONTACT['email']}",
    "orcid": f"ORCID: {CONTACT['orcid']}",
    "sections": [
        ("الملخص المهني", [
            {"p": "محاضر ومدرب في جامعة اليرموك وجامعة عمّان الأهلية وجامعة البتراء، ولي أبحاث منشورة في مجلات مصنفة في Scopus."},
            {"p": "أخصائي ومعلم تربية خاصة ومنسق تعليم دامج بخبرة تزيد على خمس سنوات في مدارس وزارة التربية والتعليم الأردنية، في دعم الطلبة ذوي صعوبات التعلم واضطراب طيف التوحد والإعاقات العقلية والسمعية والبصرية والحركية. متمرس في إعداد الخطط التربوية الفردية (IEP) والقياس والتشخيص وبرامج غرف المصادر وتعديل السلوك والتعليم الدامج. درّبت المعلمين العاديين ومعلمي التعليم الدامج، وحققت الدمج الكلي للطلبة ذوي الإعاقة لأول مرة في مدرسة حكومية."},
        ]),
        ("الخبرات المهنية", [
            {"h": "محاضر – الدبلوم العالي لإعداد المعلمين",
             "sub": "جامعة اليرموك، كلية العلوم التربوية – إربد، الأردن | 10/2025 – 07/2026",
             "bullets": [
                 "تدريس مساقات متخصصة في التربية الخاصة ضمن برنامج الدبلوم العالي لإعداد المعلمين.",
                 "الإشراف الأكاديمي والتدريب الميداني لمعلمي التربية الخاصة قبل الخدمة.",
                 "تدريب المعلمين على استراتيجيات التعليم الدامج والتربية الخاصة.",
             ]},
            {"h": "أخصائي تربية خاصة (عمل خاص)",
             "sub": "قطر | 01/2025 – 01/2026",
             "bullets": [
                 "تقديم خدمات تعليمية وعلاجية متخصصة للطلبة ذوي الاحتياجات الخاصة.",
                 "تصميم برامج تعليمية فردية لكل طالب.",
                 "العمل ضمن فريق متعدد التخصصات للوصول إلى أعلى مستوى ممكن مع الطالب.",
             ]},
            {"h": "منسق ومدرب التعليم الدامج ومعلم غرفة المصادر",
             "sub": "وزارة التربية والتعليم – السلط، الأردن | 04/2018 – 01/2025",
             "bullets": [
                 "تدريب المعلمين العاديين ومعلمي التعليم الدامج على التعامل مع الطلبة ذوي الإعاقات (العقلية، والتوحد، والسمعية، والبصرية، والحركية).",
                 "تصميم الخطط التربوية والتعليمية والعلاجية وتطبيق استراتيجيات تدريس تناسب البيئة الدامجة.",
                 "تحقيق الدمج الكلي للطلبة ذوي الإعاقة لأول مرة في مدرسة حكومية.",
                 "تخفيض نسبة التحاق الطلبة بغرفة المصادر بنسبة 10% (2018–2022) عبر طرق تدريس بديلة وإبداعية.",
                 "إعداد قوائم الطلبة المستهدفين بخدمات غرفة المصادر والتعليم الدامج.",
                 "تطبيق الاختبارات الرسمية وغير الرسمية لتحديد نقاط القوة والاحتياجات لدى كل طالب.",
                 "بناء الخطة التربوية الفردية (IEP) والخطة التعليمية لكل طالب.",
                 "إجراء دراسة علمية حول مشكلات التحاق الطلبة بغرفة المصادر والتعليم الدامج، وتقديم توصيات لإدارة المدرسة.",
             ]},
        ]),
        ("التعليم", [
            {"h": "دكتوراه في التربية الخاصة (قيد الدراسة)",
             "sub": "جامعة العلوم الإسلامية العالمية – عمّان، الأردن | 2025 – حتى الآن", "phd": True},
            {"h": "ماجستير في التربية الخاصة – التقدير: امتياز (85%)",
             "sub": "جامعة مؤتة – الأردن | 2018 – 2021",
             "bullets": ["عنوان الرسالة: «تقييم غرف المصادر للطلبة ذوي صعوبات التعلم من وجهة نظر المشرفين التربويين والمعلمين العاديين في الأردن»."]},
            {"h": "بكالوريوس في التربية الخاصة – التقدير: جيد جداً",
             "sub": "جامعة البلقاء التطبيقية – الأردن | 2011 – 2015"},
        ]),
        ("الأبحاث والمنشورات", [
            {"bullets": [
                "Co-author (2026). The Impact of Feedback Timing on L2 Writing Performance and Learner Perceptions: A Study of Jordanian College EFL Learners. Theory and Practice in Language Studies, 16(9). Scopus Q1. DOI: 10.17507/tpls.1609.33",
                "(2026). Personality Traits of Gifted Students at Ajloun Governorate. Multidisciplinary Science Journal. Scopus Q3.",
            ], "ltr": True},
            {"h": "أبحاث قيد النشر", "bullets": [
                "الجاهزية الرقمية لدى معلمي التربية الخاصة قبل الخدمة في ضوء متطلبات دمج التكنولوجيا في التعليم.",
                "القلق الرقمي والتشتت الرقمي وعلاقتهما بالتنبؤ بالتوجه نحو المستقبل لدى طلبة الدبلوم العالي لإعداد المعلمين في جامعة اليرموك.",
                "الضيق النفسي والأعراض الخارجية بين المقيمين الأردنيين في المجتمعات المضيفة للاجئين: دراسة مقطعية.",
            ]},
        ]),
        ("البرامج والورش التدريبية المقدمة (مدرب)", [
            {"bullets": [
                "تعديل السلوك للأطفال ذوي الإعاقة وصعوبات التعلم، وإعداد معلمي اضطراب طيف التوحد، وإعداد معلمي الظل، والخطط والبرامج التربوية – المبتكرون للإرشاد وإعادة التأهيل (06/2023 – 12/2023).",
                "دورات تدريبية قدمتها في جامعة عمّان الأهلية: مهارات وفنيات تعديل السلوك (12 ساعة، 07/2025)، وبروتوكولات التعامل مع ذوي الهمم (12 ساعة، 11/2024)، وكيفية التعامل مع ذوي الهمم في العمل الميداني (10 ساعات، 06/2024).",
                "ورشة فنيات تعديل السلوك – جامعة البتراء (الفصل الأول 2024/2025).",
                "ورشة تشتت الانتباه والنشاط الزائد (ADHD) لأولياء الأمور بأساليب تفاعلية – قاعة الرويال، عمّان (تقييم: ممتاز).",
                "محاضرة آلية السمع لطلبة البكالوريوس حول تشريح الأذن والوقاية من مشاكل السمع – جامعة عمّان الأهلية (تقييم: ممتاز).",
                "تطبيق برنامج MOBAK الحركي لأول مرة في الأردن على الطلبة ذوي الإعاقة العقلية البسيطة – مركز الأمل، جامعة مؤتة.",
            ]},
        ]),
        ("الدورات والشهادات", [
            {"bullets": [
                "شهادة مدرب مدربين (TOT) – كامبردج",
                "الرخصة الدولية لقيادة الحاسوب (ICDL) – كامبردج",
                "بيئات التعلم الداعمة (المادية والاجتماعية) – IREX",
                "مبادئ الذكاء الاصطناعي التوليدي في تعليم الصفوف الأولى – IREX",
                "القياس والتشخيص للتوحد – وزارة التنمية الاجتماعية",
                "التعليم الدامج – وزارة التربية والتعليم",
                "مبادرة القراءة والحساب (RAM) – وزارة التربية والتعليم",
                "ملف الطالب ذوي الاحتياجات الخاصة – الجمعية الأردنية للسمع والنطق الخيرية",
                "لغة الإشارة – مركز الاستشارات والتدريب، جامعة البلقاء التطبيقية",
                "اللغة الإنجليزية (المستويات 1–3) – المعهد الثقافي البريطاني",
                "إدارة الوقت وتحديد الأولويات – جامعة عمّان الأهلية",
            ]},
        ]),
        ("المهارات", [
            {"bullets": [
                "التربية الخاصة: صعوبات التعلم، اضطراب طيف التوحد، الإعاقة العقلية، التعليم الدامج، غرف المصادر",
                "التخطيط والتقييم: الخطط التربوية الفردية (IEP)، القياس والتشخيص، الاختبارات الرسمية وغير الرسمية، متابعة تقدم الطلبة",
                "التدريس: التعليم المتمايز، تعديل السلوك، إدارة الصف، معلم الظل",
                "العمل الجماعي: تدريب المعلمين، الفرق متعددة التخصصات، التواصل مع أولياء الأمور",
                "البحث والتقنية: البحث العلمي التربوي، النشر في مجلات Scopus، Microsoft Office، ICDL",
            ]},
        ]),
        ("اللغات", [
            {"bullets": ["العربية: اللغة الأم", "الإنجليزية"]},
        ]),
    ],
}

EN = {
    "lang": "en",
    "name": "Amer Abdeljalil AlSaaideh",
    "title": "Special Education Specialist & Teacher | Inclusive Education Coordinator | University Lecturer",
    "contact": f"Amman, Jordan | {CONTACT['phone_intl']} | {CONTACT['email']}",
    "orcid": f"ORCID: {CONTACT['orcid']}",
    "sections": [
        ("Professional Summary", [
            {"p": "Lecturer and trainer at Yarmouk University, Al-Ahliyya Amman University and the University of Petra, with research published in Scopus-indexed journals."},
            {"p": "Special Education Specialist and Teacher and Inclusive Education Coordinator with more than five years of experience in Jordanian Ministry of Education schools, supporting students with learning disabilities, Autism Spectrum Disorder (ASD), and intellectual, hearing, visual and physical disabilities. Experienced in Individualized Education Plans (IEPs), assessment and diagnosis, resource room programs, behavior modification and inclusive education. Trained general and inclusion teachers, and achieved full inclusion of students with disabilities for the first time in a public school."},
        ]),
        ("Professional Experience", [
            {"h": "Lecturer – Higher Diploma in Teacher Preparation",
             "sub": "Yarmouk University, Faculty of Educational Sciences – Irbid, Jordan | 10/2025 – 07/2026",
             "bullets": [
                 "Taught specialized special education courses in the Higher Diploma in Teacher Preparation program.",
                 "Provided academic supervision and field training for pre-service special education teachers.",
                 "Trained teachers on inclusive education and special education strategies.",
             ]},
            {"h": "Special Education Specialist (Private Practice)",
             "sub": "Qatar | 01/2025 – 01/2026",
             "bullets": [
                 "Delivered specialized educational and therapeutic services for students with special needs.",
                 "Designed individualized learning programs for each student.",
                 "Worked within a multidisciplinary team to help each student reach the highest possible level.",
             ]},
            {"h": "Inclusive Education Coordinator & Trainer and Resource Room Teacher",
             "sub": "Ministry of Education – Al-Salt, Jordan | 04/2018 – 01/2025",
             "bullets": [
                 "Trained general and inclusion teachers to work with students with disabilities (intellectual, autism, hearing, visual and physical).",
                 "Designed educational, instructional and therapeutic plans and applied teaching strategies suited to the inclusive environment.",
                 "Achieved full inclusion of students with disabilities for the first time in a public school.",
                 "Reduced resource room enrollment by 10% (2018–2022) through alternative and creative teaching methods.",
                 "Prepared lists of students eligible for resource room and inclusive education services.",
                 "Administered formal and informal assessments to identify each student's strengths and needs.",
                 "Built the Individualized Education Plan (IEP) and instructional plan for each student.",
                 "Conducted a research study on problems of student enrollment in resource rooms and inclusive education, and submitted recommendations to school management.",
             ]},
        ]),
        ("Education", [
            {"h": "PhD in Special Education (in progress)",
             "sub": "The World Islamic Sciences and Education University (WISE) – Amman, Jordan | 2025 – Present", "phd": True},
            {"h": "Master of Arts in Special Education – Grade: Excellent (85%)",
             "sub": "Mutah University – Jordan | 2018 – 2021",
             "bullets": ["Thesis: “Evaluation of Resource Rooms for Students with Learning Disabilities from the Perspective of Educational Supervisors and General Teachers in Jordan.”"]},
            {"h": "Bachelor of Arts in Special Education – Grade: Very Good",
             "sub": "Al-Balqa Applied University – Jordan | 2011 – 2015"},
        ]),
        ("Research and Publications", [
            {"bullets": [
                "Co-author (2026). The Impact of Feedback Timing on L2 Writing Performance and Learner Perceptions: A Study of Jordanian College EFL Learners. Theory and Practice in Language Studies, 16(9). Scopus Q1. DOI: 10.17507/tpls.1609.33",
                "(2026). Personality Traits of Gifted Students at Ajloun Governorate. Multidisciplinary Science Journal. Scopus Q3.",
            ]},
            {"h": "Research Under Review", "bullets": [
                "Digital Readiness of Pre-service Special Education Teachers in Light of Technology Integration Requirements in Education.",
                "Digital Anxiety and Digital Distraction and Their Relationship to Predicting Future Orientation among Higher Diploma in Teacher Preparation Students at Yarmouk University.",
                "Psychological Distress and Externalizing Symptoms among Jordanian Residents in Refugee-Hosting Communities: A Cross-Sectional Study.",
            ]},
        ]),
        ("Training Programs and Workshops Delivered (Trainer)", [
            {"bullets": [
                "Behavior modification for children with disabilities and learning difficulties; Autism Spectrum Disorder teacher preparation; shadow teacher preparation; educational plans and programs – Al-Mubtakiroun for Counseling and Rehabilitation (06/2023 – 12/2023).",
                "Training courses delivered at Al-Ahliyya Amman University: Behavior Modification Skills and Techniques (12 hours, 07/2025); Protocols for Dealing with People of Determination (12 hours, 11/2024); Dealing with People of Determination in Fieldwork (10 hours, 06/2024).",
                "Behavior Modification Techniques workshop – University of Petra (first semester 2024/2025).",
                "ADHD workshop for parents using interactive methods – Royal Hall, Amman (rated Excellent).",
                "Lecture for undergraduate students on the hearing mechanism, ear anatomy and preventing hearing problems – Al-Ahliyya Amman University (rated Excellent).",
                "Implemented the MOBAK motor skills program for the first time in Jordan with students with mild intellectual disability – Al-Amal Center, Mutah University.",
            ]},
        ]),
        ("Courses and Certifications", [
            {"bullets": [
                "Train-the-Trainer (TOT) – Cambridge",
                "International Computer Driving Licence (ICDL) – Cambridge",
                "Supportive Learning Environments (Physical and Social) – IREX",
                "Generative AI Principles in Early Grades Education – IREX",
                "Autism Assessment and Diagnosis – Ministry of Social Development",
                "Inclusive Education – Ministry of Education",
                "Reading and Arithmetic Initiative (RAM) – Ministry of Education",
                "Special Needs Student File – Jordanian Hearing and Speech Charitable Society",
                "Sign Language – Consulting and Training Center, Al-Balqa Applied University",
                "English Language (Levels 1–3) – British Council",
                "Time Management and Prioritization – Al-Ahliyya Amman University",
            ]},
        ]),
        ("Skills", [
            {"bullets": [
                "Special Education: Learning Disabilities, Autism Spectrum Disorder, Intellectual Disability, Inclusive Education, Resource Rooms",
                "Planning and Assessment: Individualized Education Plans (IEP), Assessment and Diagnosis, Formal and Informal Testing, Student Progress Monitoring",
                "Instruction: Differentiated Instruction, Behavior Modification, Classroom Management, Shadow Teaching",
                "Teamwork: Teacher Training, Multidisciplinary Teams, Parent Communication",
                "Research and Technology: Educational Research, Publishing in Scopus Journals, Microsoft Office, ICDL",
            ]},
        ]),
        ("Languages", [
            {"bullets": ["Arabic: Native", "English"]},
        ]),
    ],
}
