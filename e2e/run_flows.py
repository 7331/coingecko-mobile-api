from coin_flow import run_coin_flow
from flow_report import FlowCheckFailedError, FlowReport
from lookup_flow import run_lookup_flow
from markets_flow import run_markets_flow
from search_flow import run_search_flow


def main() -> None:
    report = FlowReport()
    for run_flow in (
        run_lookup_flow,
        run_markets_flow,
        run_coin_flow,
        run_search_flow,
    ):
        try:
            run_flow(report)
        except FlowCheckFailedError as failed:
            print(f"FLOW FAILED: {failed}", flush=True)
    print(f"\n{report.passed_check_count} passed, {report.failed_check_count} failed", flush=True)
    raise SystemExit(0 if report.has_passed() else 1)


if __name__ == "__main__":
    main()
