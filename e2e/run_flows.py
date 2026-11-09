from pathlib import Path
import tempfile

from coin_flow import run_coin_flow
from flow_report import FlowCheckFailedError, FlowReport
from lookup_flow import run_lookup_flow
from markets_flow import run_markets_flow
from search_flow import run_search_flow


def main() -> None:
    report = FlowReport()
    with tempfile.TemporaryDirectory(prefix="coingecko-e2e-") as work_directory:
        flows = (
            (run_lookup_flow, {}),
            (run_markets_flow, {}),
            (run_coin_flow, {"work_directory": Path(work_directory)}),
            (run_search_flow, {}),
        )
        for run_flow, keyword_arguments in flows:
            try:
                run_flow(report, **keyword_arguments)
            except FlowCheckFailedError as failed:
                print(f"FLOW FAILED: {failed}", flush=True)
    print(f"\n{report.passed_check_count} passed, {report.failed_check_count} failed", flush=True)
    raise SystemExit(0 if report.has_passed() else 1)


if __name__ == "__main__":
    main()
