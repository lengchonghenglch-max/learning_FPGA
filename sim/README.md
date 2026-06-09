# Simulation Guide

## Files

1. `uart_rx_wave_tb.v`
   Observe `rxuart` start-bit confirmation, center sampling, and `o_wr`.
2. `linetest_wave_tb.v`
   Observe `linetest` buffering, line-end trigger, TX handshake, and echo result.
3. `uart_rx_wave.do`
   Open the `rxuart` waveform in ModelSim.
4. `linetest_wave.do`
   Open the `linetest` waveform in ModelSim.
5. `render_linetest_waveforms.py`
   Render `linetest` screenshots from `linetest_wave.vcd` without manual GUI capture.
6. `../docs/toolchain_memory.md`
   Persistent note for this machine's ModelSim 10.4 compatibility rules.

## ModelSim Usage

Open ModelSim, switch to the `sim/` directory in Transcript, then run:

```tcl
cd D:/wbuart32-master/wbuart32-master/master-learn/FPGA-UART-Learning/sim
do uart_rx_wave.do
do linetest_wave.do
```

Notes:

1. `do ...` and `quit -sim` are ModelSim Transcript commands, not PowerShell commands.
2. The `.do` files already use `vsim -voptargs=+acc` to preserve waveform visibility.
3. If relative paths fail, first check whether the current directory is `FPGA-UART-Learning/sim`.

## Icarus Verilog Quick Commands

### UART RX

```powershell
iverilog -g2012 -o sim\uart_rx_wave_tb.out rtl\rxuart.v sim\uart_rx_wave_tb.v
vvp sim\uart_rx_wave_tb.out
```

### linetest

```powershell
iverilog -g2012 -DVERILATOR -o sim\linetest_wave_tb.out rtl\rxuart.v rtl\txuart.v rtl\linetest.v sim\linetest_wave_tb.v
vvp sim\linetest_wave_tb.out
```

## Auto-Render linetest Screenshots

The current reproducible flow is:

1. Use ModelSim to export `sim/linetest_wave.vcd` with internal DUT signals.
2. Run:

```powershell
python sim\render_linetest_waveforms.py
```

This generates:

- `../waveform/linetest_rx_stage.png`
- `../waveform/linetest_lineend_trigger.png`
- `../waveform/linetest_tx_stage.png`

## Current Status

1. `uart_rx_wave_tb.v`: verified that a short glitch does not trigger reception.
2. `uart_rx_wave_tb.v`: verified center sampling and byte-complete `o_wr` output with screenshots in `../waveform/`.
3. `linetest_wave_tb.v`: verified that echo starts only after carriage return, based on local simulation logs.
4. `linetest_wave_tb.v`: waveform screenshots have been generated and stored in `../waveform/`.
5. `linetest.v`: ModelSim 10.4 requires explicit net types on ANSI-style ports, so `i_uart_rx` is now declared as `input wire`.

## This Machine's Special Constraints

This PC uses `ModelSim SE-64 10.4`. The following rules are mandatory:

1. If a signal is driven by `assign`, the left-hand signal must be `wire`, not `reg`.
2. With ``default_nettype none`` enabled, module ports should declare `wire` explicitly.
3. Waveform scripts must use:

```tcl
vsim -voptargs=+acc work.top_name
```

4. Do not assume `add wave sim:/top/*` will always work. Prefer explicit signal names.

## Extra Note for linetest

`linetest` internally instantiates `txuart/rxuart` with default `INITIAL_SETUP=868`, so its power-on wait is much longer than the external `i_setup=32` used in the testbench.

That means:

1. `linetest` needs a longer simulation window than `uart_rx`.
2. In ModelSim, it is reasonable to run to about `250 us` before taking screenshots.
