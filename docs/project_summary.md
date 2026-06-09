# 项目状态

## 项目目标
围绕 `wbuart32` 中的 `rxuart` 和 `linetest` 模块，建立一套可复现、可截图、可沉淀结论的 UART 学习与仿真验证流程。

## 当前进度
- 已完成 `rxuart` 功能分析，整理了起始位确认、中心采样、`o_wr` 输出的学习文档。
- 已完成 `linetest` 功能分析，理清了 `rx_stb -> head -> lineend/run_tx -> tail -> tx_stb/tx_busy` 的整行缓存回显链路。
- 已完成 `uart_rx_wave_tb.v`、`linetest_wave_tb.v` 以及对应 `.do` 脚本，可在 ModelSim 和 Icarus Verilog 下复现实验。
- 已完成 `rxuart` 的 3 张波形截图整理，并把结果写入 `docs/debug_log.md`、`docs/uart_rx.md`、`waveform/README.md`。
- 已完成 `linetest` 的仿真日志验证，确认 `A/B/C/\r` 会先缓存，再按顺序回发。
- 已完成 `linetest` 的 3 张波形截图整理，并把结果写入 `docs/linetest.md`、`docs/debug_log.md`、`waveform/README.md`。
- 已完成 `docs/uart_rx.md` 与 `docs/linetest.md` 的 GitHub 图文展示排版，文档内可直接查看关键波形。
- 已完成本机 ModelSim 10.4 兼容性规则沉淀，记录在 `docs/toolchain_memory.md`。

## 核心架构
项目以 `rtl/` 中的 UART RTL 为分析对象，以 `sim/` 中的 testbench 和 `.do` 脚本为验证入口，以 `docs/` 中的学习记录和调试日志为知识沉淀，以 `waveform/` 中的截图为最终证据。

当前重点模块关系如下：

```text
rxuart
  -> 负责把串口位流还原为字节，重点验证起始位确认与中心采样

linetest
  -> 内部调用 rxuart/txuart
  -> 先把一行数据写入 buffer
  -> 收到回车/换行后锁存 lineend
  -> 再通过 txuart 按顺序回发整行
```

## 关键设计决策
- 用独立 testbench 而不是只看原始工程例程，保证每个学习点都能被单独刺激、单独观察、单独复现。
- `rxuart` 的验证重点放在 `half_baud_time`、`zero_baud_counter`、`state`、`o_wr`，而不是只看 `i_uart_rx` 电平。
- `linetest` 的验证重点放在 `head`、`tail`、`lineend`、`run_tx`、`tx_busy`，而不是只看最终 `o_uart_tx`。
- ModelSim 脚本统一使用 `vsim -voptargs=+acc`，避免层级优化导致内部信号不可见。
- 仿真结论同时要求“日志可复现 + 波形可截图”，避免只有口头结论没有证据链。

## 当前问题
- ModelSim 图形界面在关闭某些窗口后容易出现布局异常，需要继续固化恢复方法和临时文件处理方式。
- 当前 `linetest` 波形图是通过 VCD 自动渲染生成的，后续若继续扩展到其他模块，仍需要把这套流程再抽象和复用。
- 当前总结集中在 `rxuart` 和 `linetest`，后续如果扩展到 FIFO、Wishbone 或 Modbus，项目记忆文档还需要继续扩展。

## 下一步计划
- 视学习进度继续扩展下一个模块，优先考虑 FIFO 或更上层的 UART 系统接口行为。
- 如果继续做仿真文档化，优先把当前的 VCD 渲染方式推广到 FIFO 或更上层 UART 系统接口模块。
- 继续补充 ModelSim 图形界面异常时的恢复步骤和临时文件处理经验。
