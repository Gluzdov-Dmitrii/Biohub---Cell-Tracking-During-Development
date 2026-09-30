# Biohub: baseline и проверка публичных CV, 21 сентября 2026

## Проверенные ориентиры

| Ориентир | Число | Интерпретация |
|---|---:|---|
| Наш EXP214 gapfix90 | 0.7427291486246141 | Development-adapted reciprocal embryo OOF,175 полных роликов; текущий воспроизводимый локальный ориентир |
| Его альтернативный local graph | 0.7132851517671771 | Те же модели/когорта, другой графовый алгоритм |
| Наш подтверждённый public лучший | 0.947 | Live API COMPLETE, ref56243810, Zhehao P26 v1; это не CV |
| Текущий лидер public LB | 0.974 | Live API Sergio Alvarez; следующие0.973/0.970; ни наличие открытых весов, ни локальный CV из ранга не следуют |
| Наш чисто классический EXP002 | 0.826 LB / 0.7409785635 local175 | LB подтверждён API; EXP222 теперь воспроизвёл фиксированный baseline на той же175когорте, процесс завершён |
| Наш EXP001 sanity | 0.143 | Live API COMPLETE, ref55686043, простой nearest-neighbor baseline |
| Старый reciprocal DL detector + registered Hungarian | 0.615980 |183 ролика, иной detector/cohort/selection; это физический линкер поверх DL, не классический end-to-end baseline |

Live receipts: `work/biohub_public_audit_20260921/our_submissions.json`, `leaderboard.json`. Исторический183 audit: `reports/SUBMISSION_CV_MATRIX.md`. Его выбор checkpoint/threshold уже использовал другие фильмы target-эмбриона, поэтому это тоже не независимый финальный unseen-embryo test. Нельзя сравнивать0.826 LB с0.7427 CV как победу классики.

«Физический baseline» здесь означает обнаружение blob/DoG и связывание в физических координатах с ограничениями движения, а не механистическую симуляцию тканей или физический верхний предел score. В EXP002 действительно выбирается detector=blob; присутствующая в файле U-Net helper не используется. Источник `kaggle_notebooks/exp002_rule_based/biohub-rule-based-baseline.py`.

Официальный исходный baseline организаторов — TemporalUNet3D с temporal attention + node transformer, sparse supervision. README говорит о3epoch training опубликованного starter, без заявленного сопоставимого175-score: https://github.com/royerlab/kaggle-cell-tracking-competition .

## Что проверялось сейчас

Kaggle API:100 верхних notebooks по scoreDescending,100 последних (157 уникальных в объединении),32 поисковых OOF результата и выборки CV/validation/classical. Также datasets по OOF/fold/checkpoint/CV/LOEO/validation. Это целевой аудит, не доказательство отсутствия любого неизвестного публичного или частного решения. Сортировка по score не возвращает само число score; заголовки0.948/0.95 не считать API-подтверждением.

Сохранены исходники/версии/SHA восьми notebooks и небольшие результатные отчёты пяти из них. Notebook-код не исполнялся. Снимки source иногда не содержат outputs; фактические local числа ниже получены отдельно из опубликованных run logs. API source metadata и list lastRunTime могут расходиться; версии и файлы зафиксированы отдельно.

| Публичный кандидат | Найденное доказательство | Почему не заменяет наш baseline |
|---|---|---|
| evgendvorkin/biohub-0-942-lb-proxy-score-0-9417 v31 | Run log:8 train movies, base proxy0.9490, selected0.9511 после7 вариантов | Те же публичные pretrained weights; фильмы не исключены из их обучения. Отбор постпроцессинга на этой же небольшой выборке. Заголовок0.9417 не совпадает с текущим log |
| leolin05/biohub-0-935-reproduction-audit-and-validation v4 | Run log:4 train movies, proxy0.9379 |2/prefix, отбор с делениями; public secondary SHA обучался на всех199train. Это не OOF весов |
| yusuketogashi/clean-approach-lightweight-local-cv-no-hack v106 |8 train movies, фиксированные публичные веса; встроена ссылка на прежний0.8792197451 | Smoke/local proxy, без доказанного исключения validation из обучения detector; прежнее число не текущий OOF |
| arnav170/biohub-reid3s v1 | Leave-one-volume-out OOF AUC для дополнительного edge re-ID HistGradientBoosting | Неполный уровень pipeline: не embryo-disjoint final graph OOF; базовые public detectors прежние. Снимок RUNNING |
| andnyu/biohub-density-adaptive-0-948-reproduction v1 | TemporalUNet public weights+DeepCenter+DivNet; runtime validator выключен |0.948 в названии, нет сопоставимого CV. Код пригоден для изучения, численное превосходство local не установлено |
| rishabhr0y/biohub-greenfield-seed-a-resume-e10-e13-v2 v4 | Реальный training receipt:13epochs, checkpoint SHA7e2a0772…,124train/32dev/39holdout,4public excluded | `official_cv_score=null`, `promotable=false`, CV-inference выключен. Movie roles сами по себе не доказывают embryo-disjoint разделение. Интересная независимая линия, не готовый победитель |
| yiyu0716/biohub-official-seed42-bs8-fold0-t4-submit v15 | Single fold0 test inference, statusERROR | Нет численного CV/полного provenance; fallback выбора первого checkpoint |
| codezzzsleep/biohub-095-owned-validation v1 | Исходник содержит hub приt=-1000, координатах-10000 и искусственные forks | Исключён; название owned-validation не подтверждает валидность конечного графа |

Подробности четырёх источников: `reports/BIOHUB_PUBLIC_CV_AUDIT_PART_20260921.md`. Все первичные исходники, receipts и logs: `work/biohub_public_audit_20260921/`.

## Отдельные готовые fold weights

Готовые CV/fold weights **существуют**. `horaz0/biohub-top-cv-0803-artifact` в названии содержит0.8031, но README и manifest заявляют **0.8135597342657821 на199роликах**. Это основной новый кандидат для воспроизведения. Код разделяет эмбрионы корректно и run_cv использует соответствующую единственную fold-модель. Однако train.py явно выбирает лучшие эпохи на том же outer fold (10/20/30/40/50; выбранные50/20); итоговый per-movie report/predictions отсутствует в опубликованном пакете; custom metric parity не проверено. Следовательно, это selected development-CV, не независимое доказательство превосходства. Наш0.7427 тоже development-adapted: преимущество нашего числа сейчас в воспроизводимости точным scorer на фиксированной175когорте, а не в абсолютной независимости от разработки.

`horaz0/biohub-cfg-embryo-cv-last-folds` содержит fixed-last50 обеих folds без опубликованного score — полезный контроль. `rudispresence/biohub-loeo-fold0-fixed-final-checkpoint` явно фиксирует128train/71test,3epochs,fixed_final; reciprocal fold1 опубликован отдельно, но полный парный training provenance/score не найден. Подробное доказательство и ссылки: `reports/BIOHUB_READY_WEIGHTS_AUDIT_20260921.md`.

Следующий приоритет: SHA-проверенная репродукция horaz0 на наших175роликах, каждый target только своей held-out моделью, исходные параметры и официальный scorer; fixed-last50 отдельным контролем. Нельзя использовать final twofold ensemble на train для OOF: одна из его составляющих видела target-эмбрион. До воспроизведения честный ответ: потенциально сильнее — да; уже доказанно сильнее и надёжнее — пока нет.

Авторская заметка Pilkwang описывает корректный fixed100epoch embryo-OOF и прямо отличает его от alltrain оценки, но опубликованного завершённого числа и комплекта OOF weights в этой заметке не найдено: https://pilkwangkim.github.io/posts/BioHub-Cell-Tracking-Working-Note-2-OOF-Structural-Diagnostics/ .

## Удалённая работа

EXP221 завершён epoch24 обеих веток, leases RELEASED; лучший source proxy0.9366348671→0.9376560530, это не CV tracking. Source graph gate готовится отдельно. Грок в сохранённой сессии проверяет план; shell запускает основной агент через lease-aware launcher, не context-only Grok worker. Все тяжёлые расчёты удалённые.

EXP222 full175 завершён за28.71min: классика0.7409785635 vsDL0.7427291486;44b6 классика0.717281 vsDL0.805207;6bba классика0.745326 vsDL0.731806. Это фиксированный development-бенчмарк на одной когорте. Разные детекции не позволяют приписать разницу одному линкеру. Нельзя выбрать алгоритм по target-эмбриону задним числом и назвать новый результат честным OOF. Детали reports/EXP222_CLASSICAL_FULL175_RESULT_20260921.md.
