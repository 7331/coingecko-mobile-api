from pydantic import BaseModel, ConfigDict, Field

from cli_runner import CliResult
from flow_report import FlowReport


class SearchResultsModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    coins: list[SearchCoinModel]
    rwas: list[object]
    nft_contracts: list[object] = Field(default=[], alias="nftContracts")
    markets: list[object]
    categories: list[object]


class SearchCoinModel(BaseModel):
    id: str
    symbol: str
    name: str
    data: SearchCoinDataModel


class SearchCoinDataModel(BaseModel):
    price: float | None
    price_change_percentage_24h: float | None


def run_search_flow(report: FlowReport) -> None:
    bitcoin = CliResult.run("search", "bitcoin", "--json")
    results = bitcoin.json_output(SearchResultsModel)
    top = results.coins[0] if results.coins else None
    report.require_check(
        "search bitcoin returns coins led by bitcoin",
        passed=bitcoin.exit_code == 0 and top is not None and top.id == "bitcoin",
        detail=f"exit {bitcoin.exit_code}, {len(results.coins)} coins, top {top.id if top else None}",
    )

    typo = CliResult.run("search", "bitcvoin")
    report.require_check(
        "typo search returns a valid empty payload",
        passed=typo.exit_code == 0 and typo.stdout.strip() != "",
        detail=f"exit {typo.exit_code}, stdout {typo.stdout.strip()[:60]!r}",
    )
