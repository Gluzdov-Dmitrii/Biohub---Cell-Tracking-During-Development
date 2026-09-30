"""Build the readable EXP225 P26 notebook without executing inference.

Core upstream cells 2--4 remain byte-identical when concatenating their sections.
Cell 5 changes only CSV coordinate serialization in write_test_submission.
The production edition freezes the historically selected tight55 postprocess,
omits runtime train-label inference/selection, and corrects diagnostic metadata.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "work/biohub_explainer_20260922/verified_public/biohub-p26-o01-exact-public-0947.ipynb"
DEFAULT_OUTPUT = ROOT / "kaggle_notebooks/exp225_p26_research"
NOTEBOOK_NAME = "biohub-exp225-p26-research.ipynb"
KERNEL_ID = "dmitriigluzdov/biohub-exp225-p26-research-and-frozen-inference"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source(cell: dict) -> str:
    value = cell.get("source", "")
    return "".join(value) if isinstance(value, list) else value


def markdown(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip().splitlines(keepends=True)}


def code(text: str, **metadata) -> dict:
    return {"cell_type": "code", "execution_count": None, "outputs": [],
            "metadata": metadata, "source": text.splitlines(keepends=True)}


# One entry marks a top-level AST boundary, followed by an explanation for readers.
# Functions and literal runtime patches are kept intact, so their scope cannot change.
SECTIONS = {
    0: [(1, "1. Frozen starting preset / Исходные параметры", "Исходный preset P26. Ниже отдельная короткая ячейка явно фиксирует исторически выбранный вариант `tight55`. При экспериментах меняйте параметры до чтения конфигурации и запускайте Restart & Run All.")],
    1: [(1, "1.1 Configuration guard / Защита параметров", "Проверка ключевых настроек прекращает запуск при случайном отклонении от исходного preset. Исторические печатные подписи обновлены; сами проверки сохранены.")],
    2: [
        (1, "2. Paths and configuration / Пути и конфигурация", "`TEST_DIR` указывает на реальный competition test во время запуска. Имена роликов будут обнаружены динамически; готовый публичный CSV не является входом."),
        (60, "2.1 Graph parameters / Параметры графа", "Параметры с суффиксом `_UM` измеряются в микрометрах. Координаты CSV остаются в voxel units; перевод происходит только при расчёте физических расстояний."),
        (151, "2.2 Resolved configuration / Фактическая конфигурация", "Снимок прочитанных значений полезен для сравнения запусков. Конфигурация читается один раз: изменение environment после этой ячейки не обновляет уже созданные Python-константы.")],
    3: [
        (1, "3. Offline dependencies / Окружение без Internet", "Пакеты устанавливаются из прикреплённых offline wheels при необходимости. Исходные ограничения версий и Docker image сохранены; Internet должен оставаться выключенным."),
        (75, "3.1 Locate support artifacts / Найти исходники и веса", "Support pack содержит inference repository и primary checkpoint. Проверяется manifest и ожидаемая структура, а не произвольный первый найденный `.pth`."),
        (160, "3.2 Dependency checks / Проверка зависимостей", "Эти функции подготавливают совместимые зависимости из локальных артефактов Kaggle."),
        (283, "3.3 Install offline dependencies / Подготовить пакеты", "Установка разрешена из прикреплённых файлов. Здесь сохранена исходная логика проверки импортов и восстановления окружения."),
        (370, "3.4 Materialize inference repository / Развернуть inference", "Копируются исходники и конфигурация в `/kaggle/working/tracking_repo`. Это копия кода для текущего запуска, а не файл с готовыми ответами."),
        (447, "3.5 Verify primary and DeepCenter / SHA моделей", "Сравниваются SHA256 исходного support-кода, primary-весов и DeepCenter. Несовпадение немедленно останавливает запуск до inference."),
        (571, "3.6 Secondary model / Вторая temporal model", "Второй seed добавляет свидетельства о детекциях и связях. Его identity также проверяется SHA256. Веса смешивания ниже являются частью воспроизводимого baseline.")],
    4: [
        (1, "4. GPU and detector TTA / GPU и аугментации", "Temporal UNet извлекает признаки из 3D-кадров. Spatial flips/rotations дают дополнительные представления; предсказания переводятся обратно в исходные координаты и усредняются."),
        (85, "4.1 Candidate-retention guard / Сохранение кандидатов", "Если смешивание двух детекторов теряет слишком много кандидатов кадра, используется primary. Минимальное отношение числа кандидатов — 0,90; решение записывается по каждому кадру."),
        (169, "4.2 Forward/reverse association / Двунаправленные связи", "Node transformer оценивает связи между кандидатами соседних кадров. Обратное время и harmonic-probability fusion добавляют проверку взаимного согласия."),
        (212, "4.3 Feature TTA / Аугментации признаков связей", "TTA применяется и к признакам для association; у secondary сила feature TTA равна 0,75. Большие строковые патчи оставлены целыми, чтобы не менять их точное содержимое."),
        (246, "4.4 Discover runtime test movies / Найти test", "Список `.zarr` строится из текущего `TEST_DIR`. Затем формируется временный split только для этих test movies и команда inference."),
        (292, "4.5 Two-GPU helpers / Работа двух GPU", "Один ролик обрабатывается одним worker. После окончания проверяются и объединяются GEFF-шарды. Модельные вызовы остаются в исходном проверенном predictor."),
        (414, "4.6 Run inference / Запуск моделей", "Это основной дорогой этап. Нужен Kaggle GPU T4 ×2; фактическое число устройств и время будут напечатаны. Время зависит от размеров runtime test, поэтому публичное время не гарантирует hidden runtime.")],
    5: [
        (1, "5. Graph and physical units / Граф и единицы", "Узел — клетка в кадре, ребро — её продолжение или деление в следующем кадре. Масштаб `(z,y,x)=(1.625,0.40625,0.40625)` мкм/voxel учитывает анизотропию изображения."),
        (117, "5.1 DeepCenter input / Центры клеток", "Отдельная 3D U-Net выдаёт heatmap центров. Она используется как veto/confirmation для некоторых восстановленных узлов и делений, а не как ground truth."),
        (271, "5.2 DeepCenter loading and scoring / Проверка центров", "Модель загружается из уже проверенного checkpoint. Небольшой cache ограничивает повторное чтение кадров и вычисление heatmaps."),
        (436, "5.3 Motion relinking / Пересвязывание по движению", "Hungarian assignment учитывает физическое расстояние, движение и learned edge probability. Именно `MOTION_RELINK_TIGHT_UM=5.5` заморожен из исторического победителя sweep."),
        (563, "5.4 Close missing-frame gaps / Пропущенные кадры", "Связывание через разрыв может добавить промежуточный узел. Его положение проверяется по исходному test изображению и DeepCenter, с ограничениями числа добавлений."),
        (832, "5.5 Strict gap recovery / Дополнительное восстановление", "Более строгая ветка восстановления использует локальный контекст и ограничения длины/частоты. Эта функция сохранена без изменений."),
        (996, "5.6 Division hypotheses / Деления клеток", "Дополнительные гипотезы делений ограничены геометрией parent/daughters, расхождением, взаимными соседями и квотами на кадр и ролик."),
        (1167, "5.7 Short-track filtering / Короткие треки", "Короткие компоненты удаляются; отдельная консервативная rescue-ветка сохраняет компоненты с сильными связями. Делящиеся компоненты имеют отдельное правило."),
        (1291, "5.8 Coordinate smoothing / Сглаживание", "Локальный line fit сглаживает позиции вдоль трека. Это постобработка координат после model inference, а не новый детектор."),
        (1365, "5.9 Full graph policy / Порядок постобработки", "Здесь собраны repair, gap closing, division, filtering и smoothing в исходном порядке. Порядок важен: даже одинаковые параметры в другой последовательности дадут иной граф."),
        (1580, "5.10 Serialize submission / Записать submission.csv", "Финальные узлы и рёбра записываются в один корневой `/kaggle/working/submission.csv`. Dataset IDs происходят из runtime test; число роликов не фиксировано.")],
    6: [(1, "6. Candidate retention and graph audit / Проверки результата", "Проверки исходного P26 сохранены; metadata отчёта исправлены на реальные параметры EXP225. Этот аудит проверяет форму и граф, но не оценивает качество hidden test.")],
    11: [(1, "7. Resolved pipeline manifest / Что реально запустилось", "Сводка фактически загруженных моделей и режимов. Runtime train-validator удалён: все решения о конфигурации приняты до запуска.")],
}


def split_sections(text: str, spec: list, original_index: int) -> list[dict]:
    lines = text.splitlines(keepends=True)
    nodes = ast.parse(text).body
    valid = {n.lineno for n in nodes}
    result = []
    for i, (start, title, explanation) in enumerate(spec):
        if start != 1 and start not in valid:
            raise ValueError(f"Cell {original_index}: unsafe boundary {start}")
        end = spec[i + 1][0] - 1 if i + 1 < len(spec) else len(lines)
        fragment = "".join(lines[start - 1:end])
        compile(fragment, f"upstream_cell_{original_index}_{start}", "exec")
        result.append(markdown(f"## {title}\n\n{explanation}"))
        result.append(code(fragment, upstream_cell=original_index,
                           upstream_start_line=start, upstream_end_line=end))
    if "".join(source(c) for c in result if c["cell_type"] == "code") != text:
        raise AssertionError("Split lost original text")
    return result


def replace_assignment(text: str, name: str, replacement: str) -> str:
    nodes = [n for n in ast.parse(text).body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(nodes) != 1:
        raise ValueError(f"Expected one assignment to {name}")
    node = nodes[0]
    lines = text.splitlines(keepends=True)
    return "".join(lines[:node.lineno - 1]) + replacement.rstrip() + "\n" + "".join(lines[node.end_lineno:])


def corrected_guard(text: str, upstream_sha: str) -> str:
    replacement = '''_guard_report = {
    "experiment": "EXP225_P26_FROZEN_TIGHT55",
    "status": "PASS_RETENTION_AND_BASIC_GRAPH_NOT_QUALITY_VALIDATION",
    "parent_experiment": "P26_O01_public_0.947_submission_56243810",
    "source_kernel": "zhehaoliang/biohub-p26-o01-exact-public-0947",
    "source_notebook_sha256": "UPSTREAM_SHA",
    "method_attribution": "P26 by zhehaoliang; Pilkwang model artifacts; upstream harmonic fusion attribution yusuketogashi/no-hack-biohub-cell-another-approch-3rd v18; upstream diagnostic lineage raykkretzschmar",
    "public_output_used": False,
    "runtime_train_labels_used": False,
    "historical_train_proxy_selected_configuration": True,
    "organizer_labels_used_for_configuration": True,
    "leaderboard_feedback_used_for_configuration": True,
    "exact_honest_oof_for_public_weights_available": False,
    "configuration": {
        "minimum_candidate_retention": float(os.environ["BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION"]),
        "fallback_scope": "individual_frame",
        "detector_threshold": DET_THRESHOLD,
        "secondary_detection_weight": float(os.environ["BIOHUB_SECONDARY_DETECTION_WEIGHT"]),
        "secondary_edge_weight": float(os.environ["BIOHUB_SECONDARY_EDGE_WEIGHT"]),
        "bidirectional_primary_weight": float(os.environ["BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT"]),
        "secondary_link_mode": os.environ["BIOHUB_SECONDARY_LINK_MODE"],
        "secondary_low_margin_max": float(os.environ["BIOHUB_SECONDARY_LOW_MARGIN_MAX"]),
        "edge_candidate_threshold": float(os.environ["BIOHUB_DUAL_SEED_EDGE_THRESHOLD"]),
        "ilp_appearance_weight": ILP_APPEARANCE_WEIGHT,
        "ilp_disappearance_weight": ILP_DISAPPEARANCE_WEIGHT,
        "gap_close_um": GAP_CLOSE_UM,
        "motion_relink_tight_um": MOTION_RELINK_TIGHT_UM,
        "deepcenter_gap_threshold": DEEPCENTER_GAP_THRESHOLD,
        "deepcenter_gap_confirm_min_span_um": DEEPCENTER_GAP_CONFIRM_MIN_SPAN_UM,
        "runtime_validator_enabled": False,
    },
    "hardware": {"visible_gpu_count": int(torch.cuda.device_count())},
    "diagnostics": {
        "rows": len(_guard_records),
        "fallback_frames": sum(bool(row["use_primary"]) for row in _guard_records),
        "by_movie": _guard_by_movie,
    },
    "submission": {"sha256": _guard_digest, "rows": len(_guard_frame), "datasets": _guard_datasets},
    "topology": _guard_topology,
    "quality_promotion": {
        "status": "requires_clean_run_final_audit_and_guarded_submission_receipt",
        "historical_parent_public_score": 0.947,
        "candidate_public_score": None,
    },
}'''.replace("UPSTREAM_SHA", upstream_sha)
    return replace_assignment(text, "_guard_report", replacement)


def bound_serialized_coordinates(text: str) -> str:
    old = '            for node_id in sorted(nodes_by_id):\n                node = nodes_by_id[node_id]\n                writer.writerow({'
    new = '''            # EXP225: round only at CSV serialization, then enforce runtime volume bounds.
            _output_shape = tuple(int(v) for v in json.loads(
                (TEST_DIR / f"{dataset}.zarr" / "0" / "zarr.json").read_text()
            )["shape"])
            if len(_output_shape) != 4 or any(size <= 0 for size in _output_shape):
                raise AssertionError(f"{dataset}: invalid runtime TZYX shape {_output_shape}")
            _output_zyx_max = tuple(size - 1 for size in _output_shape[1:])

            for node_id in sorted(nodes_by_id):
                node = nodes_by_id[node_id]
                writer.writerow({'''
    if text.count(old) != 1:
        raise AssertionError("Expected one CSV node serialization loop")
    text = text.replace(old, new, 1)
    for index, axis in enumerate("zyx"):
        old = f'"{axis}": max(0, int(round(float(node["{axis}"])))),'
        new = f'"{axis}": min(_output_zyx_max[{index}], max(0, int(round(float(node["{axis}"]))))),'
        if text.count(old) != 1:
            raise AssertionError(f"Expected one CSV {axis} serialization")
        text = text.replace(old, new, 1)
    return text


INTRO = """# Biohub EXP225 · P26 research notebook

**Воспроизводимая отправная точка для LB и дальнейших экспериментов.** Inference основан на проверенном P26, который дал нашему аккаунту **public 0.947** (submission `56243810`). Это исторический результат родителя; score этой редакции появится только после её собственного запуска и submission.

**Что изменено:** код разбит на небольшие логические ячейки, добавлены пояснения, исправлены устаревшие подписи отчётов. Конфигурация исторического победителя `tight55` зафиксирована до inference: `MOTION_RELINK_TIGHT_UM=5.5`. Исходный runtime train-validator и подбор postprocess удалены. Детекторы, model inference, runtime patches, ILP и graph functions сохранены.

**Поправка сериализации v2:** после округления z/y/x ограничены диапазоном `0..dimension−1` фактического runtime test-объёма. Это предотвращает выход за верхнюю границу при округлении дробной позиции. Внутренние координаты графа, его рёбра, node IDs и время `t` не меняются.

Рабочая версия: [Biohub EXP225 — P26 Research and Frozen Inference](https://www.kaggle.com/code/dmitriigluzdov/biohub-exp225-p26-research-and-frozen-inference).

**Чтение:** сначала разделы 0–2, затем 4.4–4.6 и 5.9–7. Остальные блоки объясняют детали и позволяют локализовать изменения. Выполнение: **Restart & Run All**, строго сверху вниз.

## 0. Карта pipeline / Pipeline map

`runtime test .zarr → temporal 3D UNet ×2 + spatial/feature TTA → cell candidates → node-transformer edge scores → ILP → motion/gap/division repairs + DeepCenter confirmation → submission.csv → graph/bounds audit`

UNet находит клетки и признаки; transformer оценивает соответствия во времени; ILP выбирает согласованный граф; postprocess восстанавливает некоторые пропуски и деления. DeepCenter — дополнительная модель подтверждения центров. Все изображения берутся из test текущего запуска; frozen public CSV не читается.

## 0.1 Что говорят числа / Evidence, not interchangeable scores

| Результат | Значение | Что измерено |
|---|---:|---|
| P26, предыдущий результат нашего аккаунта | **0.947 public LB** | Родитель этого notebook; не local CV |
| EXP219, наш clean-fold production | **0.922 public LB** | Submission `56277173`; другой набор весов |
| Horaz selected 50/20, EXP223 | **0.7949879415** | Официальный scorer на 175 development movies; outer-fold selection bias |
| Наш EXP214 gapfix90 | **0.7427291486** | Та же 175-movie development cohort; development-adapted reciprocal embryo OOF |
| Horaz fixed-last50 control | **0.7386985046** | Та же 175 cohort/decoder; демонстрирует зависимость от выбора эпохи |

У публичных P26-весов здесь **нет доказанного точного честного OOF**. Исторический train proxy участвовал в выборе postprocess, а validation movies не доказаны исключёнными из обучения всех публичных моделей. Поэтому 0.947 LB, proxy-score и official development175 нельзя сравнивать как одну метрику. Отключение validator сейчас не делает исторический выбор независимым.

## 0.2 Запуск / Run recipe

Kaggle notebook, **GPU T4 ×2**, **Internet OFF**. Прикрепите competition и три dataset из `kernel-metadata.json`; сохранён исходный Docker image. Код проверит SHA support sources и checkpoints до inference. Не меняйте attached artifacts по похожему названию. Результат — ровно один корневой `submission.csv`; дополнительные JSON/CSV — diagnostics. После изменения параметров сначала выполните чистую версию и полный audit.

## 0.3 Основные ручки / Main edit points

| Параметр | Эта версия | Значение / место изменения |
|---|---:|---|
| `BIOHUB_DET_THRESHOLD` | 0.965 | Отсечение detector candidates, раздел 1 |
| `BIOHUB_SECONDARY_DETECTION_WEIGHT` | 0.80 | Смешивание detector logits, раздел 3.6 |
| `BIOHUB_SECONDARY_EDGE_WEIGHT` | 0.15 | Свидетельства secondary для association, раздел 3.6 |
| `BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT` | 0.15 | Обратное время для edge fusion, раздел 1 |
| `BIOHUB_SECONDARY_EDGE_FEATURE_TTA_WEIGHT` | 0.75 | Secondary feature TTA, раздел 4.3 |
| `BIOHUB_MOTION_RELINK_TIGHT_UM` | **5.5 µm** | Замороженный `tight55`, ячейка production override |
| `BIOHUB_GAP_CLOSE_UM` | 5.0 µm | Ограничение gap repair, раздел 1 |
| `BIOHUB_OUTPUT_MIN_TRACK_LEN` | 6 frames | Фильтр коротких треков, раздел 1 |
| `BIOHUB_VALIDATOR_ENABLE` | 0 | Runtime train selection удалён |

Меняйте один механизм на эксперимент. Для параметров, защищённых configuration guard, обновляйте и ожидаемое значение guard осознанно. Веса, их SHA и код загрузчика — единый контракт; новый checkpoint потребует отдельной проверки совместимости.

## 0.4 Авторы, зависимости и происхождение / Credits

- P26 reference: [zhehaoliang/biohub-p26-o01-exact-public-0947](https://www.kaggle.com/code/zhehaoliang/biohub-p26-o01-exact-public-0947).
- Primary/support code: [Pilkwang support pack](https://www.kaggle.com/datasets/pilkwang/biohub-tracking-support-pack-50ep-v1), checkpoint SHA `12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`.
- Secondary temporal seed314159: [Pilkwang temporal weights](https://www.kaggle.com/datasets/pilkwang/biohub-temporal-unet3d-seed314159-v1), SHA `9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f`.
- Center prior: [Pilkwang DeepCenter](https://www.kaggle.com/datasets/pilkwang/biohub-deepcenter-unet3d-center-prior-v1), SHA `8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0`.
- Upstream attribution retained: harmonic mutual-support association references [Yusuke Togashi, approach 3](https://www.kaggle.com/code/yusuketogashi/no-hack-biohub-cell-another-approch-3rd), v18; diagnostic lineage references Ray Kretzschmar. Original source strings remain in archived upstream evidence.
- Organizer architecture: [Royer lab competition repository](https://github.com/royerlab/kaggle-cell-tracking-competition). This edition documents and repackages the attributed pipeline; it does not claim authorship of its models.

Artifact slugs and notebook titles are labels, not proof of training split or epoch. Runtime SHA checks establish identity; separate training receipts are required to establish honest validation provenance.
"""

FUTURE = """## 8. Как развивать дальше / Next experiments

1. **Reproduction first.** Сохранить source SHA, версии dataset, полный output inventory, runtime dataset IDs, graph audit и CSV SHA. Сравнить эту frozen-версию с родителем; одинаковый рецепт ещё не доказывает одинаковый score.
2. **Separate a clean research branch.** Выбрать immutable embryo-level splits и source-only checkpoint selection до просмотра target labels. Horaz selected 50/20 — сильная development отправная точка, но её выбранные эпохи не дают unbiased outer test. P26 public pretrained models также не заменяют clean-fold модели для OOF.
3. **Improve one stage.** Detector misses, association errors и division errors считать раздельно официальным scorer на полной фиксированной когорте. Сначала небольшой парный pilot, потом full-cohort validation. Изменять модель/данные, узлы или linker по одной гипотезе; сохранять контрольную ветку.
4. **Promotion gate.** Положительный paired результат, стабильность по эмбрионам, отсутствие FP/division regression и успешный clean Internet-off run. Public LB improvement полезен для public track, но private-robust track требует собственной валидации или обоснованной независимости механизмов.

Notebook сам не отправляет результат в competition. В этом репозитории submission проходит только через протестированный `scripts/submit_code_file_once.py`, с preregistration, полным audit и проверкой API error/status/score после отправки. `COMPLETE` без score считается аномалией до диагностики.
"""


def build(args: argparse.Namespace) -> dict:
    upstream_bytes = args.source.read_bytes()
    upstream = json.loads(upstream_bytes)
    upstream_sha = sha256(upstream_bytes)
    original = {i: source(c) for i, c in enumerate(upstream["cells"]) if c["cell_type"] == "code"}
    cells = [markdown(INTRO)]
    overrides = {"BIOHUB_MOTION_RELINK_TIGHT_UM": "5.5", "BIOHUB_VALIDATOR_ENABLE": "0"}
    if args.runtime_overrides:
        extra = json.loads(args.runtime_overrides.read_text(encoding="utf-8"))
        if not isinstance(extra, dict) or any(not str(k).startswith("BIOHUB_") for k in extra):
            raise ValueError("Overrides must be an object with BIOHUB_ environment keys")
        overrides.update({str(k): str(v) for k, v in extra.items()})
    for i in (0, 1, 2, 3, 4, 5, 6, 11):
        text = original[i]
        if i == 1:
            text = text.replace('print("Baseline: fixed-90 dual-seed clean pipeline (public LB 0.913)")',
                                'print("Reference: P26 historical public LB 0.947; public weights, no exact honest OOF")')
            text = text.replace('print("Single model-level change: harmonic mutual-support association fusion")',
                                'print("EXP225 preserves P26 inference; historical tight55 frozen before configuration")')
            text = text.replace('print("Reverse-time association weight: 0.200")',
                                'print("Reverse-time association weight:", os.environ["BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT"])')
        elif i == 6:
            text = corrected_guard(text, upstream_sha)
        elif i == 5:
            text = bound_serialized_coordinates(text)
        elif i == 11:
            text = text.replace('print(f"Validator:               enabled={VALIDATOR_ENABLE}  "\n      f"held_out_samples={len(val_stems)}  match_radius={VALIDATOR_MATCH_RADIUS_UM}um")',
                                'print("Runtime train validator: disabled; historical tight55 frozen at 5.5 um")')
        cells.extend(split_sections(text, SECTIONS[i], i))
        if i == 1:
            cells.append(markdown("## 1.2 Production override / Заморозка выбранного варианта\n\nЭти значения применяются **до** чтения Python-констант. Исторический train-proxy sweep выбрал `tight55`; текущий запуск не читает train labels и не выбирает новые параметры. Исходные train-validation/sweep cells 7–10 сохранены только в reference notebook, а в production отсутствуют."))
            overlay = "# Explicit production differences from the upstream P26 notebook.\n"
            overlay += "\n".join(f"os.environ[{k!r}] = {v!r}" for k, v in sorted(overrides.items())) + "\n"
            overlay += 'BIOHUB_SCORE_AXIS = "historical P26 public 0.947; frozen tight55; no runtime train selection"\n'
            overlay += 'print(BIOHUB_SCORE_AXIS)\n'
            cells.append(code(overlay, exp225_role="production_overrides"))
    if args.append_audit:
        cells.append(markdown("## 7.1 Final runtime output audit / Полная проверка результата\n\nПроверка единственного root CSV, схемы, целочисленных идентификаторов, конечных значений, геометрических границ runtime test и инвариантов графа. Ошибка останавливает запуск."))
        cells.append(code(args.append_audit.read_text(encoding="utf-8"), exp225_role="final_runtime_audit"))
        cells.append(code(
            "EXP225_OUTPUT_AUDIT = run_exp225_output_audit(\n"
            "    TEST_DIR, WORKING_DIR,\n"
            "    source_evidence_status=(\n"
            "        'P26 model/code hashes checked; fixed historical tight55; '\n"
            "        'exact notebook Kaggle source identity verified externally; '\n"
            "        'no fresh private OOF'\n"
            "    ),\n"
            ")\n"
            "print(json.dumps(EXP225_OUTPUT_AUDIT, indent=2, sort_keys=True))\n",
            exp225_role="run_final_runtime_audit"))
    cells.append(markdown(FUTURE))
    metadata = copy.deepcopy(upstream.get("metadata", {}))
    metadata.pop("papermill", None)
    metadata["title"] = "Biohub EXP225 - P26 Research and Frozen Inference"
    metadata.setdefault("kaggle", {})["isInternetEnabled"] = False
    metadata["kaggle"]["isGpuEnabled"] = True
    metadata["exp225_provenance"] = {"upstream_sha256": upstream_sha,
        "upstream_kernel": "zhehaoliang/biohub-p26-o01-exact-public-0947",
        "runtime_train_selection": False, "historical_proxy_selection": True,
        "current_kernel": KERNEL_ID,
        "preserved_core_cells": [2, 3, 4], "modified_functions": ["write_test_submission"],
        "serialization_change": "clip rounded zyx to actual runtime shape; preserve graph/t/IDs/edges",
        "omitted_reference_cells": [7, 8, 9, 10]}
    notebook = {"cells": cells, "metadata": metadata, "nbformat": 4, "nbformat_minor": 5}
    for index, cell in enumerate(cells):
        cell["id"] = f"exp225-{index:03d}"
        if cell["cell_type"] == "code":
            compile(source(cell), f"exp225_cell_{index}", "exec")
    parity = {}
    for index in (0, 2, 3, 4):
        rebuilt = "".join(source(c) for c in cells if c.get("metadata", {}).get("upstream_cell") == index)
        if rebuilt != original[index]:
            raise AssertionError(f"Core source changed in original cell {index}")
        if ast.dump(ast.parse(rebuilt), include_attributes=False) != ast.dump(ast.parse(original[index]), include_attributes=False):
            raise AssertionError(f"AST mismatch in original cell {index}")
        parity[str(index)] = {"byte_text_equal": True, "ast_equal": True, "sha256": sha256(rebuilt.encode())}
    graph_source = "".join(source(c) for c in cells if c.get("metadata", {}).get("upstream_cell") == 5)
    original_graph_ast = ast.parse(original[5])
    revised_graph_ast = ast.parse(graph_source)
    if len(original_graph_ast.body) != len(revised_graph_ast.body):
        raise AssertionError("Graph cell top-level statement count changed")
    changed_functions = []
    for original_node, revised_node in zip(original_graph_ast.body, revised_graph_ast.body):
        if ast.dump(original_node, include_attributes=False) != ast.dump(revised_node, include_attributes=False):
            if not isinstance(original_node, ast.FunctionDef) or original_node.name != "write_test_submission":
                raise AssertionError("Graph logic changed outside write_test_submission")
            changed_functions.append(original_node.name)
    if changed_functions != ["write_test_submission"]:
        raise AssertionError("Expected exactly the serialization function to change")
    parity["5"] = {"byte_text_equal": False, "ast_equal": False,
        "changed_functions": changed_functions, "all_other_top_level_ast_equal": True,
        "change": "runtime shape read and clipping of rounded zyx at CSV output only",
        "sha256": sha256(graph_source.encode())}
    # Prove changing receipt metadata did not change the retention/graph checks.
    def without_report(text):
        tree = ast.parse(text)
        tree.body = [n for n in tree.body if not (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_guard_report" for t in n.targets))]
        return ast.dump(tree, include_attributes=False)
    guard = "".join(source(c) for c in cells if c.get("metadata", {}).get("upstream_cell") == 6)
    if without_report(guard) != without_report(original[6]):
        raise AssertionError("Upstream validation logic changed")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    nb_path = args.output_dir / NOTEBOOK_NAME
    nb_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    kernel = json.loads(args.source_metadata.read_text(encoding="utf-8"))
    kernel.pop("id_no", None)
    kernel.update(id=KERNEL_ID, title=metadata["title"],
                  code_file=NOTEBOOK_NAME, is_private=True, enable_gpu=True, enable_internet=False)
    (args.output_dir / "kernel-metadata.json").write_text(json.dumps(kernel, indent=2) + "\n", encoding="utf-8")
    report = {"status": "PASS_STATIC_BUILD_NO_INFERENCE_EXECUTED", "upstream_source_sha256": upstream_sha,
        "notebook_sha256": sha256(nb_path.read_bytes()), "code_cells": sum(c["cell_type"] == "code" for c in cells),
        "markdown_cells": sum(c["cell_type"] == "markdown" for c in cells),
        "maximum_code_cell_lines": max(len(source(c).splitlines()) for c in cells if c["cell_type"] == "code"),
        "core_source_parity": parity, "guard_logic_ast_preserved": True,
        "runtime_overrides": overrides, "kernel_id": KERNEL_ID,
        "serialization_bounds_fix": True, "omitted_reference_cells": [7, 8, 9, 10],
        "audit_source_sha256": sha256(args.append_audit.read_bytes()) if args.append_audit else None,
        "inference_executed_locally": False, "candidate_score": None}
    (args.output_dir / "build_receipt.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    readme = f'''# EXP225 P26 research notebook

Open `{NOTEBOOK_NAME}`. Russian explanations and English identifiers describe the full model-to-graph pipeline.
Kaggle kernel: [Biohub EXP225](https://www.kaggle.com/code/{KERNEL_ID}). Use this exact slug for updates; Kaggle derives it from the title.

This is a frozen production derivative of [P26](https://www.kaggle.com/code/zhehaoliang/biohub-p26-o01-exact-public-0947), historical account public score **0.947**, submission **56243810**. EXP225 has no score until its own checked execution and submission. Public weights do not have exact honest OOF here. Horaz selected development175 **0.7949879415** and our EXP214 **0.7427291486** are separate, development-adapted evidence; clean-fold EXP219 public **0.922** is also a different model bundle.

## Run

Kaggle T4 ×2, Internet **OFF**, the competition and three attached datasets from `kernel-metadata.json`. Use Restart & Run All. The original Docker digest and notebook dataset-version metadata are retained; embedded SHA256 guards pin materialized sources/checkpoints. Final output: `/kaggle/working/submission.csv`.

## Changes and provenance

- Upstream file SHA256: `{upstream_sha}`.
- Core original cells 2–4 (configuration reading, dependencies and GPU inference) retain exact source text and AST, split only at top-level boundaries. In original cell 5, every top-level AST is unchanged except `write_test_submission`.
- v2 fixes only CSV z/y/x serialization: read the actual runtime TZYX shape, round the coordinate, then clip to `0..dimension-1`. Internal graph coordinates, edge endpoints, node IDs and t remain unchanged. v1 artifacts were backed up to `work/exp225_20260922/v1/` before this correction.
- Frozen `BIOHUB_MOTION_RELINK_TIGHT_UM=5.5`, `BIOHUB_VALIDATOR_ENABLE=0` before configuration reading; removed original train-validator/sweep cells 7–10. This preserves the historical selected setting but does not erase its train-proxy selection bias.
- Retention/graph audit logic is unchanged. Diagnostic metadata now records resolved values, P26 parent and historical label/proxy selection accurately.
- Empty outputs and execution counts intentionally avoid presenting an old run as this candidate's result.
- {report['code_cells']} code cells; {report['markdown_cells']} explanatory cells; maximum {report['maximum_code_cell_lines']} code lines per cell. Original large runtime-patch string literals remain intact.
- Models and original method authors are credited in notebook section 0.4. Primary, secondary and DeepCenter are inference inputs, not new training products of this notebook.

## Rebuild / Review

From repository root: `python scripts/build_exp225_notebook.py`.
Append the separately reviewed final audit with `--append-audit scripts/exp225_output_audit.py`.
Optional `--runtime-overrides path.json` is an explicit experimental environment overlay; changing it creates a new candidate requiring fresh validation.

`build_receipt.json` records static compilation, source/AST parity and hashes. This builder never executes GPU inference or sends a Kaggle submission. Runtime success and submission audits are separate gates.

For further work: preregister one hypothesis, use clean source-only checkpoint selection with embryo-level heldout inference, compare complete paired predictions with the official scorer, then run an Internet-off production version. Keep public leaderboard and private-robust evidence distinct.
'''
    (args.output_dir / "README.md").write_text(readme, encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--source-metadata", type=Path, default=DEFAULT_SOURCE.parent / "kernel-metadata.json")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--runtime-overrides", type=Path)
    parser.add_argument("--append-audit", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args), indent=2))


if __name__ == "__main__":
    main()
