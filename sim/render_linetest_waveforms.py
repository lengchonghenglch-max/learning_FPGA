from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
VCD_PATH = ROOT / "sim" / "linetest_wave.vcd"
WAVEFORM_DIR = ROOT / "waveform"


TARGET_SIGNALS = {
    "linetest_wave_tb.src_uart_tx",
    "linetest_wave_tb.o_uart_tx",
    "linetest_wave_tb.mon_wr",
    "linetest_wave_tb.mon_data",
    "linetest_wave_tb.dut.rx_stb",
    "linetest_wave_tb.dut.rx_data",
    "linetest_wave_tb.dut.head",
    "linetest_wave_tb.dut.tail",
    "linetest_wave_tb.dut.lineend",
    "linetest_wave_tb.dut.run_tx",
    "linetest_wave_tb.dut.tx_stb",
    "linetest_wave_tb.dut.tx_data",
    "linetest_wave_tb.dut.tx_busy",
}


@dataclass
class VarDef:
    full_name: str
    width: int
    identifier: str
    bit_index: Optional[int] = None


@dataclass
class SignalTrack:
    width: int
    events: List[Tuple[int, str]]


def parse_vcd(vcd_path: Path) -> Dict[str, SignalTrack]:
    tracked_ids: Dict[str, VarDef] = {}
    split_bus_defs: Dict[str, Dict[int, str]] = {}
    direct_defs: Dict[str, VarDef] = {}
    scope: List[str] = []
    in_header = True

    with vcd_path.open("r", encoding="utf-8", errors="replace") as handle:
        lines = handle.readlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if in_header:
            if stripped.startswith("$scope"):
                parts = stripped.split()
                scope.append(parts[2])
                continue
            if stripped.startswith("$upscope"):
                scope.pop()
                continue
            if stripped.startswith("$var"):
                parts = stripped.split()
                width = int(parts[2])
                identifier = parts[3]
                ref_tokens = parts[4:-1]
                ref_name = " ".join(ref_tokens)
                base_name = ref_tokens[0]
                full_name = ".".join(scope + [base_name])
                if full_name not in TARGET_SIGNALS:
                    continue
                if width == 1 and len(ref_tokens) > 1 and ref_tokens[1].startswith("["):
                    bit_index = int(ref_tokens[1][1:-1])
                    split_bus_defs.setdefault(full_name, {})[bit_index] = identifier
                    tracked_ids[identifier] = VarDef(full_name, 1, identifier, bit_index)
                else:
                    direct_defs[identifier] = VarDef(full_name, width, identifier)
                    tracked_ids[identifier] = VarDef(full_name, width, identifier)
                continue
            if stripped == "$enddefinitions $end":
                in_header = False
                break

    signals: Dict[str, SignalTrack] = {}
    for var in direct_defs.values():
        signals[var.full_name] = SignalTrack(var.width, [])
    for full_name, bit_map in split_bus_defs.items():
        signals[full_name] = SignalTrack(max(bit_map) + 1, [])

    split_state: Dict[str, Dict[int, str]] = {
        full_name: {bit: "x" for bit in bit_map}
        for full_name, bit_map in split_bus_defs.items()
    }
    split_last: Dict[str, Optional[str]] = {full_name: None for full_name in split_bus_defs}
    direct_last: Dict[str, Optional[str]] = {var.full_name: None for var in direct_defs.values()}

    current_time = 0
    data_started = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if data_started is False:
            if stripped == "$enddefinitions $end":
                data_started = True
            continue
        if stripped.startswith("#"):
            current_time = int(stripped[1:])
            continue
        if stripped == "$dumpvars" or stripped == "$end":
            continue

        if stripped[0] in "01xz":
            value = stripped[0]
            identifier = stripped[1:]
        elif stripped[0] in "bBrR":
            parts = stripped.split()
            value = parts[0][1:]
            identifier = parts[1]
        else:
            continue

        if identifier not in tracked_ids:
            continue

        vdef = tracked_ids[identifier]
        if vdef.bit_index is None:
            track = signals[vdef.full_name]
            if direct_last[vdef.full_name] != value:
                track.events.append((current_time, value))
                direct_last[vdef.full_name] = value
        else:
            bus_bits = split_state[vdef.full_name]
            bus_bits[vdef.bit_index] = value
            merged = "".join(
                bus_bits[idx] for idx in sorted(bus_bits.keys(), reverse=True)
            )
            if split_last[vdef.full_name] != merged:
                signals[vdef.full_name].events.append((current_time, merged))
                split_last[vdef.full_name] = merged

    return signals


def value_at(events: List[Tuple[int, str]], when: int) -> str:
    current = events[0][1] if events else "x"
    for time_ps, value in events:
        if time_ps > when:
            break
        current = value
    return current


def segments(events: List[Tuple[int, str]], start_ps: int, end_ps: int) -> List[Tuple[int, int, str]]:
    if start_ps >= end_ps:
        raise ValueError("start_ps must be smaller than end_ps")
    points = [(time_ps, value) for time_ps, value in events if start_ps <= time_ps <= end_ps]
    current = value_at(events, start_ps)
    all_points = [(start_ps, current)] + points + [(end_ps, points[-1][1] if points else current)]

    compact: List[Tuple[int, str]] = []
    for time_ps, value in all_points:
        if compact and compact[-1][0] == time_ps:
            compact[-1] = (time_ps, value)
        elif compact and compact[-1][1] == value:
            continue
        else:
            compact.append((time_ps, value))

    result: List[Tuple[int, int, str]] = []
    for idx, (time_ps, value) in enumerate(compact[:-1]):
        next_time = compact[idx + 1][0]
        result.append((time_ps, next_time, value))
    if not result:
        result.append((start_ps, end_ps, current))
    elif result[-1][1] < end_ps:
        result.append((result[-1][1], end_ps, compact[-1][1]))
    return result


def format_value(signal_name: str, value: str) -> str:
    if any(ch in value.lower() for ch in ("x", "z")):
        return value
    if signal_name.endswith(("rx_data", "tx_data", "mon_data")):
        return f"0x{int(value, 2):02x}"
    return str(int(value, 2))


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/consolab.ttf",
        "C:/Windows/Fonts/DejaVuSansMono.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def render_waveform(
    output_path: Path,
    title: str,
    start_ps: int,
    end_ps: int,
    signal_order: List[Tuple[str, str]],
    parsed: Dict[str, SignalTrack],
) -> None:
    width = 1800
    left = 220
    right = 50
    top = 90
    row_h = 82
    bottom = 70
    height = top + bottom + row_h * len(signal_order)

    image = Image.new("RGB", (width, height), "#10151c")
    draw = ImageDraw.Draw(image)

    title_font = load_font(28)
    label_font = load_font(20)
    value_font = load_font(18)

    draw.text((left, 28), title, fill="#f3f6fa", font=title_font)
    time_span_us = (end_ps - start_ps) / 1_000_000.0
    draw.text(
        (left, 58),
        f"Window: {start_ps / 1_000_000:.3f} us .. {end_ps / 1_000_000:.3f} us   Span: {time_span_us:.3f} us",
        fill="#9db1c7",
        font=value_font,
    )

    plot_left = left
    plot_right = width - right
    plot_width = plot_right - plot_left

    for idx in range(6):
        tick_x = plot_left + plot_width * idx / 5.0
        tick_time = start_ps + (end_ps - start_ps) * idx / 5.0
        draw.line((tick_x, top - 8, tick_x, height - bottom + 10), fill="#273241", width=1)
        label = f"{tick_time / 1_000_000:.3f} us"
        draw.text((tick_x - 40, height - bottom + 18), label, fill="#7f95ab", font=value_font)

    bit_color = "#47d18c"
    bus_color = "#f9c74f"
    accent = "#5fa8ff"
    low_fill = "#18222d"
    high_fill = "#1b3026"

    for row, (signal_name, label) in enumerate(signal_order):
        y_top = top + row * row_h
        y_mid = y_top + row_h // 2
        y_high = y_top + 16
        y_low = y_top + row_h - 16

        draw.text((24, y_mid - 10), label, fill="#d9e2ec", font=label_font)
        draw.line((plot_left, y_mid, plot_right, y_mid), fill="#1e2833", width=1)

        track = parsed[signal_name]
        signal_segments = segments(track.events, start_ps, end_ps)

        if track.width == 1:
            for start_t, stop_t, value in signal_segments:
                x0 = plot_left + (start_t - start_ps) * plot_width / (end_ps - start_ps)
                x1 = plot_left + (stop_t - start_ps) * plot_width / (end_ps - start_ps)
                if value == "1":
                    draw.rectangle((x0, y_high, x1, y_low), fill=high_fill)
                    level_y = y_high
                elif value == "0":
                    draw.rectangle((x0, y_high, x1, y_low), fill=low_fill)
                    level_y = y_low
                else:
                    level_y = y_mid
                draw.line((x0, level_y, x1, level_y), fill=bit_color, width=3)
            for (start_t, _, value), (_, stop_t, next_value) in zip(signal_segments, signal_segments[1:]):
                x = plot_left + (stop_t - start_ps) * plot_width / (end_ps - start_ps)
                y0 = y_high if value == "1" else y_low if value == "0" else y_mid
                y1 = y_high if next_value == "1" else y_low if next_value == "0" else y_mid
                draw.line((x, y0, x, y1), fill=bit_color, width=2)
        else:
            for start_t, stop_t, value in signal_segments:
                x0 = plot_left + (start_t - start_ps) * plot_width / (end_ps - start_ps)
                x1 = plot_left + (stop_t - start_ps) * plot_width / (end_ps - start_ps)
                draw.line((x0, y_mid, x1, y_mid), fill=bus_color, width=3)
                draw.rectangle((x0, y_mid - 10, x1, y_mid + 10), outline=accent, width=1)
                label_text = format_value(signal_name, value)
                if x1 - x0 > 42:
                    text_box = draw.textbbox((0, 0), label_text, font=value_font)
                    text_x = x0 + max(4, (x1 - x0 - (text_box[2] - text_box[0])) / 2)
                    draw.text((text_x, y_mid - 11), label_text, fill="#f4f7fb", font=value_font)
            for _, stop_t, _ in signal_segments[:-1]:
                x = plot_left + (stop_t - start_ps) * plot_width / (end_ps - start_ps)
                draw.line((x, y_mid - 14, x, y_mid + 14), fill=accent, width=1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def main() -> None:
    parsed = parse_vcd(VCD_PATH)

    render_waveform(
        WAVEFORM_DIR / "linetest_rx_stage.png",
        "linetest RX stage: bytes are buffered while run_tx stays low",
        140_500_000,
        149_200_000,
        [
            ("linetest_wave_tb.src_uart_tx", "src_uart_tx"),
            ("linetest_wave_tb.dut.rx_stb", "dut.rx_stb"),
            ("linetest_wave_tb.dut.rx_data", "dut.rx_data"),
            ("linetest_wave_tb.dut.head", "dut.head"),
            ("linetest_wave_tb.dut.run_tx", "dut.run_tx"),
        ],
        parsed,
    )

    render_waveform(
        WAVEFORM_DIR / "linetest_lineend_trigger.png",
        "linetest line-end trigger: carriage return latches lineend and starts TX",
        151_600_000,
        151_820_000,
        [
            ("linetest_wave_tb.src_uart_tx", "src_uart_tx"),
            ("linetest_wave_tb.dut.rx_stb", "dut.rx_stb"),
            ("linetest_wave_tb.dut.rx_data", "dut.rx_data"),
            ("linetest_wave_tb.dut.head", "dut.head"),
            ("linetest_wave_tb.dut.lineend", "dut.lineend"),
            ("linetest_wave_tb.dut.run_tx", "dut.run_tx"),
            ("linetest_wave_tb.dut.tx_stb", "dut.tx_stb"),
        ],
        parsed,
    )

    render_waveform(
        WAVEFORM_DIR / "linetest_tx_stage.png",
        "linetest TX stage: tail advances only on TX handshake",
        151_700_000,
        161_500_000,
        [
            ("linetest_wave_tb.o_uart_tx", "o_uart_tx"),
            ("linetest_wave_tb.dut.run_tx", "dut.run_tx"),
            ("linetest_wave_tb.dut.tx_stb", "dut.tx_stb"),
            ("linetest_wave_tb.dut.tx_busy", "dut.tx_busy"),
            ("linetest_wave_tb.dut.tx_data", "dut.tx_data"),
            ("linetest_wave_tb.dut.tail", "dut.tail"),
            ("linetest_wave_tb.dut.lineend", "dut.lineend"),
            ("linetest_wave_tb.mon_wr", "mon_wr"),
            ("linetest_wave_tb.mon_data", "mon_data"),
        ],
        parsed,
    )


if __name__ == "__main__":
    main()
