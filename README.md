# FPGA-UART-Learning

UART + FIFO + Modbus 学习工程日志。

## Structure

- `rtl/`: RTL 源码
- `sim/`: 仿真文件
- `docs/`: 学习笔记与调试日志
- `waveform/`: 波形截图与导出文件

## Latest Results

### 2026-06-08

- `rxuart`：已经完成 3 组波形整理，验证了“短毛刺不会触发接收”“有效起始位需要半个 baud 确认”“`o_wr` 只在字节完成后拉高”。
- `linetest`：已经通过 testbench 日志验证 `A/B/C/\r` 会先缓存，再按顺序回发；对应的波形截图还需要补。

## Quick Links

- `rxuart` 结论整理：`docs/uart_rx.md`
- `linetest` 结论整理：`docs/linetest.md`
- 调试过程记录：`docs/debug_log.md`
- 波形截图说明：`waveform/README.md`
