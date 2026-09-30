# Biohub: reciprocal CV и public LB — 2026-09-28

## Правило чтения таблиц

В столбце **reciprocal CV (единые протокол и метрика)** числом без оговорки стоит только pooled score на одной когорте 175 роликов (59 `44b6` + 116 `6bba`), с reciprocal обучением по эмбрионам и проверенным **текущим organizer scorer**. Pooled score вычисляется из общих sufficient statistics, а не средним двух направлений. `н/с` означает, что для точной *подаваемой* версии такой CV не установлен. `ист.` обозначает исторический scorer или старый состав графов; число приведено для инвентаря, но не подставляется в регрессию с текущими CV. `proxy` и source-inner/один target movie не считаются reciprocal CV.

Даже численно сопоставимый score здесь является **development estimate**, потому что два эмбриона и их target-метрики многократно использовались в разработке. `EXP209` имеет наиболее чистое исходное embryo-disjoint происхождение, но его восстановленный current-scorer граф не byte-identical исходному. Для неизвестных hidden embryo точный продакшн-роутинг `EXP212/219/233` и Horaz E10 не имеет отдельного reciprocal CV. Поэтому разность public LB − local CV не является универсальной калибровкой или прогнозом private LB.

## A. Текущий organizer scorer: reciprocal 175

| модель | данные/эпохи/роутинг | reciprocal CV (единые протокол и метрика) | public LB | ref |
| --- | --- | ---: | ---: | ---: |
| EXP209, frozen fold policy [C1] | 175; source44b6→6bba 116, source6bba→44b6 59; centroid forward + EXP191 reverse | 0.6815218332750073 | — | — |
| EXP212 v5, продакшн EXP209 [C1,L1] | Те же fold-модели; unknown-embryo selector отличается от известного reciprocal роутинга | **н/с** (компонент EXP209: 0.6815218333) | 0.718 | 56181132 |
| EXP214 gapfix90, public graph [C2] | source44b6 primary 90 / secondary 60; reciprocal 175 | 0.7427291486246141 | — | — |
| EXP234, source-selected threshold [C3] | Те же 175; фиксированный threshold по source-inner, затем reciprocal target | 0.7426705533442897 | — | — |
| EXP227+236 Horaz E10 [C4] | Scratch 10 эпох; source-only checkpoint/threshold; reciprocal 116+59 | 0.7488419428035248 | — | — |
| HORAZ_LOCAL_E10 submitted v2 [C4,L2] | Те же E10 fold-веса; known-prefix reciprocal, unknown-prefix ensemble без своего CV | **н/с** (известные префиксы: 0.7488419428) | 0.873 | 56615970 |
| Horaz all199 E10 [L6] | Все 199 размеченных фильмов, seed3407, 10 эпох, одна full-data модель на каждый runtime test movie; без reciprocal-роутинга | **н/с** (обучение на обоих эмбрионах, holdout отсутствует) | 0.910 | 56651474 |
| EXP219 Frontier90 [C2,L3] | Продакшн EXP214; один source на runtime movie, unknown-prefix source6bba | **н/с** (известные префиксы: 0.7427291486) | 0.922 | 56277173 |
| EXP233 Frontier90 reproduction [C2,L3] | Точный EXP219; unknown-prefix selector не проверен reciprocal CV | **н/с** (известные префиксы: 0.7427291486) | 0.922 | 56512954 |
| x138 исходный [X1,L2] | Public primary+secondary UNet, DeepCenter, V1284; train/epoch/split отдельных компонентов не доказаны | н/с; x138 LOEO закрыт без полного reciprocal результата | 0.953 | 56520437 |
| x162 safe reproduction [X1,L2] | Тот же видимый root CSV, защитные runtime guards; отдельного end-to-end LOEO нет | н/с | 0.953 | 56611843 |
| x163 subvoxel [X2] | x162 + дробные координаты при той же topology; train proxy не является CV | н/с | 0.940 | 56628634 |

Строки с `н/с (компонент ...)` **не образуют измеренную CV↔LB пару**. В частности, EXP219 имеет reciprocal известным префиксам `0.7427291` и public `0.922`, тогда как Horaz E10 имеет более высокий reciprocal `0.7488419`, но более низкий public `0.873`. Порядок **не сохраняется**. На скрытом Kaggle-тесте все фильмы проходят ветку `unknown-embryo`, которую reciprocal CV с известным эмбрионом не проверяет. Horaz source-only E10 `0.7488419 → 0.873` (разность `+0.1241581`) и EXP209/212 `0.6815218 → 0.718` (`+0.0364782`) являются лишь сопоставлениями родственных, но не тождественных runtime-политик; из них нельзя вывести поправку к x138 или прогноз private LB. All199 E10 повысил public на `0.037` относительно source-only Horaz до `0.910`, но не имеет собственного holdout CV и не достиг порога `0.940`; это не устанавливает private-порядок. У x138 публичные `0.953` реальны; reciprocal CV всей сборки отсутствует, а LOEO закрыт по решению пользователя до дедлайна.

## B. Другие полные reciprocal 175: историческая метрика/состояние

В этом блоке `ист.` означает **не текущий подтверждённый organizer-score для данного графа**; исторический full175 scorer, selected epoch на target или позднее использование cohort делают ранжирование относительно блока A методологически ограниченным. Ниже сохранены все найденные отдельные full175 arms, в том числе отвергнутые. `—` в LB значит отсутствует подтверждённая public-подача именно этой версии.

| модель | данные/эпохи/роутинг | reciprocal CV (единые протокол и метрика) | public LB | ref |
| --- | --- | ---: | ---: | ---: |
| EXP192 raw common base [H1] | 175; ранние reciprocal scratch checkpoints, без поздних graph fixes | ист. 0.6102569076 | — | — |
| EXP190 short-track [H1] | Те же 175; min-track filter | ист. 0.6725934215 | — | — |
| EXP191 gap-pruned reverse [H1] | Те же 175; reverse DeepCenter gap/prune | ист. 0.6742747999 | — | — |
| EXP195 frozen composition [H1] | Те же 175; frozen forward/reverse composition | ист. 0.6739734043 | — | — |
| EXP201 local flow [H1] | Те же 175; local-flow forward | ист. 0.6730398381 | — | — |
| EXP202 flow + EXP195 [H1] | Те же 175; local-flow forward + EXP195 reverse | ист. 0.6745779981 | — | — |
| EXP206 centroid + EXP195 [H1] | Те же 175; centroid forward `(2,5,5)` | ист. 0.6784542971 | — | — |
| EXP209 alternative reverse [H2] | Те же 175; forward `(3,5,5)` + EXP195 reverse | ист. 0.6812194523 | — | — |
| EXP209 both centroids [H2] | Те же 175; source-selected centroid в двух направлениях | ист. 0.6802263871 | — | — |
| EXP210 safety veto [H2] | Те же 175; label-free pruning veto, отвергнут | ист. 0.6782048153 | — | — |
| EXP214 60/60 public graph [H3] | Reciprocal 175; primary/secondary 60/60 | ист. 0.7361519350 | — | — |
| EXP214 60/60 local graph [H3] | Те же detector, собственный local graph | ист. 0.7123439370 | — | — |
| EXP214 gapfix90 local graph [H3] | Reciprocal 175; 90/60, local graph | ист. 0.7132851518 | — | — |
| EXP217 full-source44 public [H4] | EXP214 target44 + full60 source44→target6bba | ист. 0.7368554865 | — | — |
| EXP217 full-source44 local [H4] | Тот же mixed fold, local graph | ист. 0.7073277838 | — | — |
| EXP218 short-track rescue [H5] | EXP214 90/60 public + conservative rescue; score точно тот же | ист. 0.7427291486 | — | — |
| EXP222 fixed classical [H6,L4] | DoG + physical Hungarian, без обучаемых весов; те же 175 | ист. 0.7409785635 | 0.826¹ | 55686045 |
| EXP223 Horaz selected50/20 [H7] | 175; fold0 e50, fold1 e20; epoch выбран с outer-target feedback | ист. 0.7949879415 | — | — |
| EXP223 Horaz fixed-last50 [H7] | 175; оба fold e50, тот же decoder | ист. 0.7386985046 | — | — |
| EXP228 Horaz 0.5/0.5 [H8] | 175; source44 selected+last 0.5/0.5, reverse reference | ист. 0.7759164900 | — | — |

¹ Public `0.826` принадлежит EXP002, исходному классическому notebook. EXP222 проверил его алгоритм на 175 и сохранил source functions/config, но перепаковал исполнение; это **родственная**, а не byte-exact submitted-model CV↔LB пара.

### Отдельный ранний reciprocal audit: 183 ролика

Здесь 63 `44b6` + 120 `6bba`, другой decoder и старые одноseed fold-веса. Это реальные reciprocal сравнения механизмов, но не та же cohort/версия моделей, что в A–B; `н/с` в общем CV столбце сохраняет эту границу ([P1]).

| модель | данные/эпохи/роутинг | reciprocal CV (единые протокол и метрика) | public LB | ref |
| --- | --- | ---: | ---: | ---: |
| EXP050/051 greedy learned edges [P1] | 183; reciprocal single-seed audit; локально 0.481198 | н/с: другая когорта | — | — |
| EXP050/051 registered Hungarian [P1] | Те же 183; локально 0.615980 | н/с: другая когорта | — | — |
| EXP050/051 registered + 10% tie-break [P1] | Те же 183; локально 0.616747 | н/с: другая когорта | — | — |

## C. LB-only account inventory

Ниже каждый **отличающийся scored ref** из сохранённой полной account-истории до 2026-09-21 и позднего API readback. Повтор одной и той же версии (`56165686`/`56165700`) показан одной строкой; ошибки, `PENDING`, пустые scores и неотправленные локальные опыты не являются LB evidence. Во всех строках этого блока CV `н/с`: названия/параметры взяты из account description, а точный reciprocal current-organizer CV подаваемой версии не доказан. Каждая строка ссылается на свой API receipt: [L5] — account snapshot 2026-09-21, [L2] — более поздний full API readback (включая пропущенные snapshot ref `56258574` и `56222165`). Исключение x163 — [X2]. Поле эпох/роутинга оставлено `не установлен`, где receipt его не даёт.

| модель | данные/эпохи/роутинг | reciprocal CV (единые протокол и метрика) | public LB | ref |
| --- | --- | ---: | ---: | ---: |
| Edge relink candidate v2 [L7] | Публичное семейство x138; дополнительный learned edge cache и другое связывание, не новый detector | н/с | 0.955 | 56641911 |
| Guarded ILP Hybrid v1 [L7] | Публичное семейство x138; иной graph repair в компонентах разногласий | н/с | 0.953 | 56649090 |
| EXP232 [L2] | P26 RUNTIME PROXY SWEEP 20260924 | н/с | 0.947 | 56514480 |
| EXP225 [L2] | P26 FIXED TIGHT55 v2 20260922 | н/с | 0.946 | 56464735 |
| Public 0.942 reproduction [L2] | threshold 0.96; эпохи/роутинг не установлены | н/с | 0.942 | 56258574 |
| CM215-S2 [L5] | FOCUS3D-HEDGE v1 20260915 | н/с | 0.839 | 56243993 |
| CM215-S1 [L5] | ZHEHAO-P26 v1 20260915 | н/с | 0.947 | 56243810 |
| Official UNet+Transformer+ILP [L2] | baseline v4; T4/CSV compatibility fixes | н/с | 0.810 | 56222165 |
| PUB-LITE-20260914 [L5] | UNION_REPAIRED v25 | н/с | 0.946 | 56220339 |
| PUB-LITE-20260913 [L5] | SUBVOXEL v23 | н/с | 0.935 | 56205220 |
| PUB-LITE-20260913 [L5] | ENSEMBLE v22 | н/с | 0.946 | 56204898 |
| PUB-LITE-20260912 [L5] | SECTTA1 DIV20 v21 | н/с | 0.946 | 56187070 |
| PUB-LITE-20260912 [L5] | COMPACT47 v20 | н/с | 0.946 | 56177715 |
| PUB-LITE v17 repeat [L5] | Center-TTA; две отправки одной версии v17 | н/с | 0.943 | 56165686, 56165700 |
| PUB-LITE-20260911 [L5] | CENTER-TTA v14 | н/с | 0.943 | 56158487 |
| PUB-LITE-20260910 [L5] | R4 factorized center v9 | н/с | 0.942 | 56143472 |
| EXP027 [L5] | W1 Zebrahub-initialized fine-tune full inference | н/с | 0.616 | 56095320 |
| EXP128 [L5] | W1-D3-S14 weak learned tie-break | н/с | 0.938 | 56071282 |
| EXP126 [L5] | W1-D2-S05 QRZ Gap5 capped dim rescue | н/с | 0.940 | 56045360 |
| EXP125 [L5] | W1-D2-S04 Flex v20 temporal agreement | н/с | 0.940 | 56045327 |
| EXP124 [L5] | W1-D2-S03 count calibration det090 | н/с | 0.911 | 56045303 |
| EXP123 [L5] | W1-D1-S04-ALT QRZ DC025-only | н/с | 0.942 | 56029401 |
| EXP122 [L5] | W1-D1-S05 clean low-overlap grouped confidence | н/с | 0.941 | 56028644 |
| EXP121 [L5] | W1-D1-S03 X54 single-factor | н/с | 0.938 | 56028627 |
| EXP120 [L5] | W1-D1-S02 analytica LB 0.941 | н/с | 0.941 | 56028590 |
| EXP119 [L5] | W1-D1-S01 fresh adaptive association | н/с | 0.941 | 56028571 |
| EXP118 [L5] | RETRY EXP116 system error | н/с | 0.931 | 56008261 |
| EXP117 [L5] | detector threshold 09375 | н/с | 0.912 | 56004193 |
| EXP115 [L5] | tomako conservative | н/с | 0.935 | 56004182 |
| EXP114 [L5] | arnav 0940e | н/с | 0.940 | 56004172 |
| EXP113 [L5] | nusrati 0940 v3 | н/с | 0.940 | 56004160 |
| EXP111 [L5] | EMA velocity relinker | н/с | 0.934 | 55973141 |
| EXP110 [L5] | V19C sister14 geometry | н/с | 0.939 | 55973135 |
| EXP109 [L5] | V19B safe div max9 | н/с | 0.939 | 55973125 |
| EXP108 [L5] | nusrati exact 0938 v1 | н/с | 0.938 | 55973111 |
| EXP107 [L5] | agreement gated dual seed | н/с | 0.931 | 55952843 |
| EXP106 [L5] | C42 PU appearance detector | н/с | 0.933 | 55952836 |
| EXP105 [L5] | C41 temporal detector | н/с | 0.933 | 55952831 |
| EXP104 [L5] | nusrati current v10 frontier | н/с | 0.936 | 55952820 |
| EXP103 [L5] | cloud current v1 exact reproduction | н/с | 0.935 | 55952817 |
| EXP102 [L5] | verified attributed 0935 division policy | н/с | 0.934 | 55941369 |
| EXP101 [L5] | verified C39 learned marginal verifier | н/с | 0.931 | 55941357 |
| EXP100 [L5] | verified C37 temporal dim rescue | н/с | 0.933 | 55941347 |
| EXP099 [L5] | verified C36 adaptive detection child | н/с | 0.933 | 55940151 |
| EXP098 [L5] | verified C35 clean fallback detection frontier | н/с | 0.934 | 55931493 |
| EXP093 [L5] | verified C33 public0933 topology anchor | н/с | 0.933 | 55907915 |
| EXP089 [L5] | controlled half-weight EMA interpolation | н/с | 0.924 | 55882683 |
| EXP092 [L5] | offline finetuned linker D4 hedge | н/с | 0.900 | 55882642 |
| EXP091 [L5] | division-heavy full inference hedge | н/с | 0.926 | 55882203 |
| EXP090 [L5] | edge threshold 040 association probe | н/с | 0.928 | 55882198 |
| EXP088 [L5] | full four-frame EMA motion challenger | н/с | 0.926 | 55882197 |
| EXP-087 [L5] | own controlled SDW90 detector-weight090 v1 | н/с | 0.926 | 55859147 |
| EXP-086 [L5] | source-attributed Anvith bidirectional fusion v1 | н/с | 0.928 | 55858614 |
| EXP-085 [L5] | source-attributed Evgen current 0928 v15 | н/с | 0.928 | 55858612 |
| EXP-084 [L5] | source-attributed SDW85 detector-weight085 v1 | н/с | 0.929 | 55858609 |
| EXP-083 [L5] | source-attributed clean Stephen frontier v1 | н/с | 0.931 | 55858606 |
| EXP-082 [L5] | source-attributed track-length08 sensitivity control v1 | н/с | 0.923 | 55836074 |
| EXP-081 [L5] | source-attributed full-velocity relink v1 | н/с | 0.926 | 55836071 |
| EXP-080 [L5] | source-attributed SDW75 detector-mixture extrapolation v1 | н/с | 0.928 | 55836067 |
| EXP-079 [L5] | source-attributed Flex best-epoch2 division-veto v22 | н/с | 0.928 | 55836064 |
| EXP-078 [L5] | source-attributed SDW70 det-weight070 v1 | н/с | 0.928 | 55836059 |
| EXP-075 [L5] | historical best harmonic frontier v11 not v12 | н/с | 0.927 | 55808638 |
| EXP-076 [L5] | secondary-edge-weight-025 harmonic controlled probe v1 | н/с | 0.923 | 55808636 |
| EXP-074 [L5] | Anhad harmonic directional-division frontier v21 | н/с | 0.927 | 55808576 |
| EXP-073 [L5] | SDW60 detection-weight-060 harmonic frontier v1 | н/с | 0.927 | 55808574 |
| EXP-072 [L5] | controlled harmonic reverse-weight-020 v1 | н/с | 0.918 | 55781468 |
| EXP-071 [L5] | bidirectional-harmonic weight-040 diversity v4 | н/с | 0.923 | 55781467 |
| EXP-070 [L5] | high-frontier retention-sensitive clean v1 | н/с | 0.926 | 55781466 |
| EXP-069R [L5] | full-inference harmonic-fusion v11 resubmit | н/с | 0.926 | 55781326 |
| EXP-068R [L5] | full-inference min-cost-flow v2 resubmit | н/с | 0.884 | 55781325 |
| EXP-067 [L5] | General-V8 continuation-guard orthogonal tracker hedge | н/с | 0.919 | 55761031 |
| EXP-066 [L5] | clean 0.926 division-sub frontier reproduction | н/с | 0.926 | 55761018 |
| EXP-065 [L5] | clean 0.927 harmonic-divergence frontier reproduction | н/с | 0.924 | 55761017 |
| EXP-028 [L5] | DeepCenter safe-division threshold 0.08 controlled LB probe | н/с | 0.919 | 55732720 |
| EXP-039 [L5] | independent secondary checkpoint controlled LB probe | н/с | 0.906 | 55732718 |
| EXP-007 [L5] | shared-node D4 association-TTA probe | н/с | 0.900 | 55732491 |
| EXP-008 [L5] | detector-diverse three-UNet flip-TTA tracker | н/с | 0.917 | 55732259 |
| EXP-005 [L5] | clean harmonic frontier exact 0.920 parent reproduction | н/с | 0.920 | 55719392 |
| EXP-055 [L5] | hidden-compatible intensity coordinates plus registered relink | н/с | 0.893 | 55706857 |
| EXP-054 [L5] | hidden-compatible registered motion relink | н/с | 0.905 | 55705721 |
| EXP-006 [L5] | harmonic dual-seed guarded division frontier | н/с | 0.919 | 55687578 |
| EXP-003 [L5] | clean single-seed UNet transformer ILP | н/с | 0.908 | 55686657 |
| EXP-004 [L5] | dual-seed logit blend DeepCenter | н/с | 0.912 | 55686487 |
| EXP-001 [L5] | nearest-neighbor sanity | н/с | 0.143 | 55686043 |


## Что исключено из CV и как использовать сопоставление

- Ранний reciprocal audit на 183 роликах приведён отдельно: его локальные значения не являются CV точных public dual-seed checkpoints ([P1]).
- EXP207 D4 `0.7604641105` — 24 development movies; EXP221/224 `0.808.../0.810...` — source8; EXP227 source-inner epoch10 `0.8114014924` против epoch20 `0.8068424889` на тех же 8 фильмах, EXP236 epoch10 `0.8458659188` — source-inner; x138/x163 восьми-TRAIN `0.945193/0.948346` и четыре visible train-copy `0.918/0.921` — train proxy. Ни одно не является reciprocal 175 CV ([P2], [P3], [X2]).
- Единственный fold0 target movie в x138 secondary LOEO дал `0.5568805892`, но это одна компонентная модель, один исторически target-exposed movie и не собранный x138 ([X3]). Число нельзя ставить против x138 public `0.953`.
- Public score относится к Kaggle hidden public split, а CV к локальным двум эмбрионам. Сильное расхождение Horaz E10 с public и провал x163 относительно положительного TRAIN proxy показывают, что линейную поправку или порядок private моделей по этим строкам оценивать нельзя. Для private выбора нужны парные embryo-level holdouts всех используемых компонентов и стабильность, а не максимальная публичная цифра.

## Источники по строкам

- [C1] `reports/exp209_reconstructed_scorer_v1_readonly_verify_20260927.json`; `reports/EXP209_COMPACT_CHECKPOINT_20260912.md`. [L1] `reports/exp212_live_state_20260912.json`, `reports/exp213_all_submissions_20260912.json`.
- [C2] `reports/EXP214_GAPFIX_RESULT_20260914.md`; current metric replay `reports/exp234_current_organizer_score_verified_20260927.json`. [C3] `reports/exp234_current_organizer_score_verified_20260927.json`.
- [C4] `reports/EXP227_EXP236_CURRENT175_POOLED_CHECK_ONLY_20260927.md`, `reports/exp227_exp236_current175_pooled_20260927.json`. [L2] `work/lb_pair_20260927/pair_live_full_api.json`, `work/lb_pair_20260927/pair_final_scores.json`.
- [L6] `work/horaz-full-dispatch-20260928/e10/terminal.json`, `work/horaz-full-runtime-20260928/candidate_e10/candidate_manifest.json`, `work/horaz-full-runtime-20260928/candidate_e10/clean_output_audit_v1.json`, `work/horaz-full-runtime-20260928/candidate_e10/api_scored_e10_56651474.json`.
- [L3] `reports/EXP219_LB_DIAGNOSTIC_20260916.md`, `work/lb_pair_20260927/pair_live_full_api.json`; `EXPERIMENTS.md` entry for EXP233 (2026-09-24). [X1] `reports/X138_CURRENT_20260926.md`; [X2] `reports/X138_X163_PREPOST_20260928.md`, `work/x163_independent/submission_api_complete_56628634.json`. [X3] `EXPERIMENTS.md` 2026-09-28 one-movie secondary result and `reports/X138_LOEO_FOLD0_PROOF_PREP_20260927.md`.
- [H1] `reports/EXP192_UNTOUCHED_POOLED_OOF_RESULT_20260912.md`; [H2] `reports/POOLED_OOF_FRONTIER_20260912.md`; [H3] `reports/EXP214_GAPFIX_RESULT_20260914.md`; [H4] `reports/EXP217_FULL60_SOURCE44_TARGET6BBA_RESULT_20260915.md`; [H5] `reports/EXP218_SHORT_TRACK_RESCUE_RESULT_20260915.md`; [H6] `reports/EXP222_CLASSICAL_FULL175_RESULT_20260921.md`; [H7] `reports/EXP223_OFFICIAL_RESULT_20260922.md`; [H8] `reports/EXP228_OFFICIAL_DIAGNOSTIC_RESULT_20260926.md`.
- [L4] `reports/SUBMISSION_CV_MATRIX.md` (EXP002/ref) и полный account snapshot [L5] `work/biohub_public_audit_20260921/our_submissions.json`. [P1] `reports/SUBMISSION_CV_MATRIX.md`; [P2] `reports/EXP207_D4_FEATURE_TTA_RESULT_20260912.md`, `reports/BIOHUB_VERIFIED_CV_SUMMARY_20260921.md`; [P3] `reports/exp227_source_checkpoint_selection_20260927.json`, `reports/exp227_source_graph10_score_20260927.json`, `reports/exp227_source_graph20_score_20260927.json`, `reports/exp236_source_graph10_score_20260927.json`.
- [L7] `work/final-pair-audit-20260929/live_api.json`, `reports/FINAL_PAIR_REASSESSMENT_20260929.md`; scored refs `56641911` и `56649090`.

## Первоначальное правило финального выбора (история)

| слот | кандидат | риск private shake-up |
| --- | --- | --- |
| 1 | **x162**, ref `56611843`, public `0.953`; этот слот фиксирован. | **Повышенный, плохо измеримый:** безопасное runtime-воспроизведение x138 имеет подтверждённый public score, но честного reciprocal CV всей сборки нет. |
| 2, если Horaz full-data E10 public ≥ `0.940` | **Horaz all199 E10**, ref `56651474`; фактический public `0.910`, условие не выполнено. | **Средний–повышенный:** reciprocal E10 `0.7488419` проверяет архитектурную линию с двумя disjoint fold-моделями, но не новую all199 модель; public тест может содержать train twins. |
| 2, если Horaz full-data E10 public < `0.940` или валидный score не получен к сроку | **EXP232 P26**, ref `56514480`, public `0.947`. | **Высокий/неизмеренный:** нет подтверждённого reciprocal current-organizer CV подаваемой версии; более высокий public score не доказывает private перенос. |

**Результат первоначального правила:** E10 `0.910 < 0.940`, поэтому получалась пара x162 + EXP232 P26. Пользователь позднее заменил её решением ниже. Порог `0.940` был явным правилом выбора, а не CV↔LB калибровкой.

## Актуальная финальная пара после уточнения пользователя 2026-09-29

| слот | кандидат | риск private shake-up |
| --- | --- | --- |
| 1, публичный форк | **Edge relink candidate v2**, ref `56641911`, public `0.955` | **Высокий/плохо измеримый:** новое связывание осмысленно использует дополнительные learned edge probabilities, но обученные детекторы публичного семейства общие, честного reciprocal CV точной сборки нет. |
| 2, наша локальная линия | **Horaz all199 E10**, ref `56651474`, public `0.910` | **Повышенный, но лучше проверенный по эмбрионам:** отдельное обучение на каждом исходном эмбрионе и перенос на другой дали reciprocal pooled175 `0.7488419`. E10 также победил E20 в заранее проведённой source-inner проверке `0.8114015 > 0.8068425`. Однако exact all199 checkpoint обучен на обоих эмбрионах и собственного holdout не имеет; public разрыв `0.045` с edge может сохраниться на private. |

Оба кандидата уже имеют scored LB refs; финальные отметки в Kaggle делает пользователь. Horaz all199 E20 ref `56661324` отправлен как отдельная заранее заявленная проверка и на момент этой записи PENDING. Новое явное правило пользователя: выбрать E20 при public LB >= 0.920, иначе E10. Оно заменяет прежний запрет выбора эпох по LB; публичный порог не является оценкой private CV. Финальный дедлайн — 2026-09-29 23:59 UTC.

**Сила свидетельств:** Horaz — единственная линия из этой пары с проверенным переносом по эмбрионам; у edge relink v2 нет reciprocal CV точной сборки. Это даёт больше оснований доверять Horaz как независимой private-страховке, чем следовало из одного public score. Число `0.7488419` относится к двум source-only fold-моделям, а не к all199 E10/E20: оно поддерживает выбор линии, но не задаёт численный прогноз private для финального checkpoint. Это historically exposed development estimate, а не новый нетронутый holdout.
