# Toolchain Memory

## Current Environment

- OS: Windows
- Terminal: PowerShell
- Simulator: ModelSim SE-64 10.4
- Backup simulator: Icarus Verilog

This file exists to preserve the constraints of this machine, so future simulation files can be written against the right rules from the start.

## ModelSim 10.4 Compatibility Rules

### 1. `assign` left-hand side must be `wire`

On this ModelSim version, a signal declared as `reg` should not also be driven by continuous assignment.

Wrong:

```verilog
reg [27:0] break_condition;
assign break_condition = {r_setup[23:0], 4'h0};
```

Right:

```verilog
wire [27:0] break_condition;
assign break_condition = {r_setup[23:0], 4'h0};
```

### 2. Always use `+acc` in `.do` scripts

To make internal signals visible to `add wave`, use:

```tcl
vsim -voptargs=+acc work.top_name
```

Do not default to:

```tcl
vsim work.top_name
```

Otherwise ModelSim may report:

```text
No objects found matching ...
```

### 3. Run `.do` scripts from the `sim/` directory

Current scripts use relative paths like:

```tcl
vlog ../rtl/xxx.v ../sim/yyy_tb.v
```

So the correct Transcript flow is:

```tcl
cd D:/wbuart32-master/wbuart32-master/master-learn/FPGA-UART-Learning/sim
do uart_rx_wave.do
```

### 4. `quit -sim` is a ModelSim command, not a PowerShell command

- `PS D:\...>`: PowerShell
- `VSIM ...>`: ModelSim Transcript

Only the ModelSim side accepts:

```tcl
quit -sim
```

### 5. Prefer explicit waveform signal lists

Do not rely on:

```tcl
add wave sim:/top/*
```

Prefer explicit signals:

```tcl
add wave sim:/uart_rx_wave_tb/i_clk
add wave sim:/uart_rx_wave_tb/i_uart_rx
add wave sim:/uart_rx_wave_tb/o_wr
add wave sim:/uart_rx_wave_tb/dut/state
```

## Naming Convention in This Repo

### Testbench files

- `sim/<module>_wave_tb.v`

Examples:

- `sim/uart_rx_wave_tb.v`
- `sim/linetest_wave_tb.v`

### ModelSim scripts

- `sim/<module>_wave.do`

Examples:

- `sim/uart_rx_wave.do`
- `sim/linetest_wave.do`

### Top-level module names

The top-level module name should match the testbench filename when practical:

```tcl
vsim -voptargs=+acc work.uart_rx_wave_tb
```

## Common Errors on This Machine

### Error 1

```text
Register is illegal in left-hand side of continuous assignment
```

Fix:

Check whether the signal on the left side of `assign` was mistakenly declared as `reg`. If yes, change it to `wire`.

### Error 2

```text
No objects found matching ...
```

Fix:

1. Confirm `vsim` successfully loaded the top module.
2. Confirm `.do` uses `-voptargs=+acc`.
3. Confirm the current Transcript directory is `sim/`.
4. Confirm the hierarchy path matches the real top-level name.

### Error 3

```text
quit : 无法将“quit”项识别为 cmdlet
```

Fix:

That means the command was typed in PowerShell instead of ModelSim Transcript.

## Default Strategy for Future Sim Work

For future simulation work in this repo, default to these five rules:

1. Every `.do` file uses `vsim -voptargs=+acc`
2. Every `.do` file is designed to run from `sim/`
3. Check `wire/reg` type before using `assign`
4. Use explicit wave signal lists instead of broad wildcards
5. Run one local compile check before asking the user to open ModelSim
