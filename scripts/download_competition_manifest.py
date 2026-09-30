from __future__ import annotations

import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.competitions.types.competition_api_service import ApiDownloadDataFileRequest


COMPETITION = "biohub-cell-tracking-during-development"
THREAD_LOCAL = threading.local()


def get_client():
    if not hasattr(THREAD_LOCAL, "api"):
        api = KaggleApi()
        api.authenticate()
        THREAD_LOCAL.api = api
        THREAD_LOCAL.client_context = api.build_kaggle_client()
        THREAD_LOCAL.client = THREAD_LOCAL.client_context.__enter__()
    return THREAD_LOCAL.api, THREAD_LOCAL.client


def download_one(
    item: dict[str, object],
    destination: Path,
    retry_delays: tuple[int, ...],
    request_delay_seconds: float,
) -> tuple[str, int]:
    name = str(item["name"])
    expected = int(item["size"])
    target = destination / Path(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.stat().st_size == expected:
        return name, expected
    for attempt in range(len(retry_delays) + 1):
        try:
            if request_delay_seconds:
                time.sleep(request_delay_seconds)
            api, client = get_client()
            request = ApiDownloadDataFileRequest()
            request.competition_name = COMPETITION
            request.file_name = name
            response = client.competitions.competition_api_client.download_data_file(request)
            api.download_file(response, str(target), client.http_client(), quiet=True, resume=True)
            break
        except Exception as exc:
            detail = repr(exc)
            retryable = any(
                marker in detail
                for marker in ("429", "500", "502", "503", "504", "timed out", "ConnectionError")
            )
            if not retryable or attempt >= len(retry_delays):
                raise
            delay = retry_delays[attempt]
            print(
                f"retryable_download_error file={name} attempt={attempt + 1} "
                f"sleep_seconds={delay} error={detail}",
                flush=True,
            )
            time.sleep(delay)
    actual = target.stat().st_size
    if actual != expected:
        raise RuntimeError(f"size mismatch for {name}: expected {expected}, got {actual}")
    return name, actual


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--holdout", choices=("44b6", "6bba"), required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--request-delay-seconds",
        type=float,
        default=0.0,
        help="Delay before each network request; already verified files are skipped without delay.",
    )
    parser.add_argument(
        "--retry-delays-seconds",
        default="120,300,600",
        help="Comma-separated backoff after retryable download failures.",
    )
    parser.add_argument(
        "--movie-limit",
        type=int,
        default=None,
        help="Download only the first N lexicographic movie stems for this holdout.",
    )
    args = parser.parse_args()
    retry_delays = tuple(int(value) for value in args.retry_delays_seconds.split(",") if value)
    if any(value <= 0 for value in retry_delays):
        parser.error("--retry-delays-seconds values must be positive")
    if args.request_delay_seconds < 0:
        parser.error("--request-delay-seconds must be nonnegative")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = [item for item in manifest["files"] if Path(str(item["name"])).parts[1].startswith(args.holdout)]
    if args.movie_limit is not None:
        stems = sorted({Path(str(item["name"])).parts[1].rsplit(".", 1)[0] for item in entries})
        selected = set(stems[: args.movie_limit])
        entries = [
            item
            for item in entries
            if Path(str(item["name"])).parts[1].rsplit(".", 1)[0] in selected
        ]
    args.destination.mkdir(parents=True, exist_ok=True)
    failures: list[dict[str, str]] = []
    completed = 0
    if args.workers == 1:
        for item in entries:
            try:
                download_one(item, args.destination, retry_delays, args.request_delay_seconds)
                completed += 1
                if completed % 100 == 0:
                    print(f"completed_files={completed}/{len(entries)}", flush=True)
            except Exception as exc:
                failures.append({"name": str(item["name"]), "error": repr(exc)})
                break
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = []
            for item in entries:
                future = pool.submit(
                    download_one,
                    item,
                    args.destination,
                    retry_delays,
                    args.request_delay_seconds,
                )
                future.biohub_name = str(item["name"])
                futures.append(future)
            for future in as_completed(futures):
                try:
                    future.result()
                    completed += 1
                    if completed % 100 == 0:
                        print(f"completed_files={completed}/{len(entries)}", flush=True)
                except Exception as exc:
                    failures.append({"name": getattr(future, "biohub_name", "unknown"), "error": repr(exc)})
    receipt = {
        "competition": COMPETITION,
        "holdout": args.holdout,
        "file_count": len(entries),
        "total_bytes": sum(int(item["size"]) for item in entries),
        "movie_limit": args.movie_limit,
        "movie_stems": sorted({Path(str(item["name"])).parts[1].rsplit(".", 1)[0] for item in entries}),
        "completed_files": completed,
        "retry_delays_seconds": retry_delays,
        "request_delay_seconds": args.request_delay_seconds,
        "fail_fast_sequential": args.workers == 1,
        "failures": failures,
        "destination": str(args.destination),
    }
    receipt_path = args.destination / f"download_receipt_{args.holdout}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
