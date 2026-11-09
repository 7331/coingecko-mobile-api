from datetime import UTC, datetime

import matplotlib.figure
import matplotlib.patches

from coingecko_mobile_api.infrastructure.coingecko_api.schemas import OhlcPoint

UP_CANDLE_COLOR = "#2ebd85"
DOWN_CANDLE_COLOR = "#f6465d"
BACKGROUND_COLOR = "#141414"
PANEL_COLOR = "#1d1d20"
GRID_COLOR = "#2b2b2e"
TEXT_COLOR = "#d9d9d9"

_BODY_WIDTH_FRACTION = 0.62


def render_candlestick_chart(
    *, candles: list[OhlcPoint], coin_name: str, days_label: str, vs_currency: str, output_path: str
) -> None:
    figure = matplotlib.figure.Figure(figsize=(10.2, 5.6), dpi=150, facecolor=BACKGROUND_COLOR)
    axes = figure.add_subplot()
    axes.set_facecolor(PANEL_COLOR)

    highs = [candle.high_price for candle in candles]
    lows = [candle.low_price for candle in candles]
    highest = max(highs)
    lowest = min(lows)
    price_span = highest - lowest
    axes.set_ylim(lowest - price_span * 0.1, highest + price_span * 0.1)
    axes.set_xlim(-1, len(candles))

    for index, candle in enumerate(candles):
        color = UP_CANDLE_COLOR if candle.close_price >= candle.open_price else DOWN_CANDLE_COLOR
        axes.plot([index, index], [candle.low_price, candle.high_price], color=color, linewidth=1.1, zorder=2)
        body_bottom = min(candle.open_price, candle.close_price)
        body_height = abs(candle.close_price - candle.open_price) or price_span * 0.002
        axes.add_artist(
            matplotlib.patches.Rectangle(
                (index - _BODY_WIDTH_FRACTION / 2, body_bottom),
                _BODY_WIDTH_FRACTION,
                body_height,
                facecolor=color,
                edgecolor=color,
                linewidth=0.6,
                zorder=3,
            )
        )

    axes.grid(color=GRID_COLOR, linewidth=0.6)
    axes.tick_params(colors=TEXT_COLOR, labelsize=9)
    for spine in axes.spines.values():
        spine.set_color(GRID_COLOR)
    axes.yaxis.set_major_formatter(lambda value, _position: f"${value:,.2f}")
    label_step = max(1, len(candles) // 8)
    label_positions = list(range(0, len(candles), label_step))
    axes.set_xticks(label_positions, labels=[_candle_label(candles[position]) for position in label_positions])

    axes.annotate(
        f"${highest:,.2f}",
        (highs.index(highest), highest),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        color=TEXT_COLOR,
        fontsize=8.5,
    )
    axes.annotate(
        f"${lowest:,.2f}",
        (lows.index(lowest), lowest),
        xytext=(0, -14),
        textcoords="offset points",
        ha="center",
        color=TEXT_COLOR,
        fontsize=8.5,
    )

    axes.set_title(
        f"{days_label} {coin_name} Graph\nPrice: ${candles[-1].close_price:,.2f} {vs_currency.upper()}",
        loc="left",
        color=TEXT_COLOR,
        fontsize=11,
        fontweight="bold",
        pad=14,
    )
    figure.tight_layout()
    figure.savefig(output_path, facecolor=BACKGROUND_COLOR)


def _candle_label(candle: OhlcPoint) -> str:
    moment = datetime.fromtimestamp(candle.timestamp_unix_milliseconds / 1000, tz=UTC)
    return moment.strftime("%d %b %H:%M")
