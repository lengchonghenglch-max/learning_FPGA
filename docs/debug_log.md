# Debug Log

## Template

### [YYYY-MM-DD] 问题标题
- 问题描述：
- 现象：
- 原因分析：
- 解决方法：
- 验证结果：

### [2026-06-08] linetest 中为什么不是收到字节就立刻回显
- 问题描述：区分 `linetest` 和 `echotest` 的行为差异，弄清楚 `linetest` 为什么需要缓存。
- 现象：观察源码后发现 `linetest` 不会在每个字节到达时立即触发发送，而是等回车、换行或长度超过阈值后再发送。
- 原因分析：`linetest` 的目标不是单字节回显，而是“整行缓存后回显”。因此它需要 `buffer/head/tail/lineend/run_tx` 这组控制信号来锁定一行数据边界。
- 解决方法：从 `rx_stb -> head -> lineend/run_tx -> tail -> tx_stb/tx_busy` 的完整链路分析模块行为，而不是只看 `i_uart_rx` 和 `o_uart_tx`。
- 验证结果：已经确认 `linetest` 的核心机制是“行缓存 + 发送握手”，后续用波形截图继续验证。

### [2026-06-08] UART RX 为什么不能检测到低电平就直接采样
- 问题描述：弄清楚 `rxuart` 为什么不在 `i_uart_rx` 第一次拉低时就当作 `bit0` 开始采样。
- 现象：源码中先经过同步链，再等待 `half_baud_time`，之后才进入正式位接收状态。
- 原因分析：刚出现的低电平可能只是毛刺，且边沿附近采样最不稳定。UART RX 需要先确认有效起始位，再在位中心采样。
- 解决方法：把分析重点放到 `ck_uart`、`half_baud_time`、`state`、`zero_baud_counter` 和 `o_wr` 上，而不是只盯着原始串口线。
- 验证结果：理论分析已经闭环，后续通过“短毛刺 + 正常字节”两段波形验证该结论。

### [2026-06-08] linetest 波形分析准备
- 问题描述：需要用波形证明 `linetest` 是“先收一整行，再开始发送”。
- 现象：如果只看 `o_uart_tx`，只能看到最终发出的串口帧，无法直接解释缓存边界和发送启动条件。
- 原因分析：`linetest` 的关键行为发生在内部指针和握手信号上，包括 `head`、`tail`、`lineend`、`run_tx`、`tx_busy`。
- 解决方法：编写 `sim/linetest_wave_tb.v`，重点观察 `dut.rx_stb`、`dut.head`、`dut.lineend`、`dut.run_tx`、`dut.tail`、`dut.tx_busy`。
- 验证结果：已生成 testbench 和 ModelSim 脚本，等待实际跑波形并补截图。

### [2026-06-08] UART RX 波形分析准备
- 问题描述：需要用波形证明 `rxuart` 采用了起始位中点确认和位中心采样。
- 现象：单看 `i_uart_rx` 只能看到线电平变化，无法说明状态机何时认定有效起始位。
- 原因分析：真正关键的是 `half_baud_time`、`state`、`zero_baud_counter`、`data_reg`、`o_wr` 之间的因果关系。
- 解决方法：编写 `sim/uart_rx_wave_tb.v`，加入“短低脉冲毛刺”和“完整字节”两种刺激，进行对比分析。
- 验证结果：已生成 testbench 和 ModelSim 脚本，等待实际跑波形并补截图。

### [2026-06-08] linetest 仿真中为什么迟迟看不到回显
- 问题描述：`linetest_wave_tb.v` 初版中已经收到了输入字节，但短时间内看不到发送回显，容易误判为发送逻辑有问题。
- 现象：内部 `dut.rx_stb` 可以收到 `A/B/C/0D`，但在较短仿真窗口内看不到 `dut.tx_stb` 和回显字节。
- 原因分析：`linetest` 内部实例化的 `txuart` 使用默认参数 `INITIAL_SETUP=868`，上电后会先经历较长的内部等待时间，和 testbench 里外部设置的 `i_setup=32` 不同。
- 解决方法：把 `linetest` 仿真运行时长拉长到约 `250 us`，并在 testbench 中打印 `dut.rx_stb`、`dut.tx_stb`、`mon_wr` 进行交叉验证。
- 验证结果：已经成功观察到 `A/B/C/0D` 被缓存后依次回发，终端打印出了完整的 `DUT TX` 和 `Echo byte` 日志。

### [2026-06-08] ModelSim 10.4 兼容性要求需要固化
- 问题描述：同样的 Verilog 和 `.do` 脚本在 Icarus Verilog 可运行，但在当前机器的 ModelSim 10.4 上出现额外兼容性问题，导致重复排查。
- 现象：先后遇到了 `Register is illegal in left-hand side of continuous assignment` 和 `No objects found matching ...` 两类错误。
- 原因分析：当前 ModelSim 版本较老，对 `assign` 左值类型要求更严格；同时默认优化模式不会保留足够的层级可见性，导致 `add wave` 找不到对象。
- 解决方法：建立 `docs/toolchain_memory.md`，固定记录本机规则：`assign` 左边检查 `wire/reg` 类型、`.do` 脚本统一使用 `vsim -voptargs=+acc`、所有脚本从 `sim/` 目录执行。
- 验证结果：`rxuart.v` 已修正 `break_condition` 类型，`uart_rx_wave.do` 和 `linetest_wave.do` 已加入 `+acc`，后续仿真将按这份规则执行。

### [2026-06-08] UART RX 波形截图已经补齐
- 问题描述：把 `rxuart` 的理论分析落到实际波形图上，确认“毛刺过滤”和“中心采样”不是停留在代码阅读阶段。
- 现象：已补 3 张截图，分别覆盖短毛刺、有效起始位后的中心采样，以及字节完成后的 `o_wr` 输出阶段。
- 原因分析：单看控制台打印只能证明收到了字节，不能证明它是如何判定起始位、如何选取采样时刻的。
- 解决方法：按 `uart_rx_false_start.png`、`uart_rx_center_sampling.png`、`uart_rx_output_strobe.png` 三个阶段整理截图，并与 testbench 日志交叉验证。
- 验证结果：Icarus 仿真打印出了 `RX byte = 0x55` 和 `RX byte = 0xa6`；配合截图可确认短毛刺未触发接收，真正的字节只在起始位确认后按位中心被采样。

### [2026-06-08] linetest 回显链路已通过仿真日志验证
- 问题描述：需要确认 `linetest` 是否真的是“先缓存一整行，再按顺序发送”，而不是误以为发送逻辑卡死。
- 现象：仿真日志显示 `DUT RX` 依次收到了 `0x41`、`0x42`、`0x43`、`0x0d`，随后 `DUT TX` 和 `Echo byte` 又按同样顺序输出。
- 原因分析：如果只盯着较短时间窗口里的波形，很容易因为 `txuart` 默认参数带来的启动等待而误判为“没有回显”。
- 解决方法：延长仿真运行时间，并同时打印 `dut.rx_stb`、`dut.tx_stb` 与外部监视器 `mon_wr` 的结果。
- 验证结果：日志中已经出现 `DUT TX byte = 0x41/0x42/0x43/0x0d` 与对应的 `Echo byte = 0x41/0x42/0x43/0x0d`，确认 `linetest` 的整行缓存回显链路成立。
