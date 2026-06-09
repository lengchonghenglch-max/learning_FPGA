# Waveform Screenshot Notes

## Available Screenshots

### `uart_rx_false_start.png`

- 模块：`rxuart`
- 阶段：短低脉冲 / false start
- 结论：`i_uart_rx` 虽然短暂拉低，但 `half_baud_time` 没有形成有效起始位确认，接收状态机不会进入正常收数流程。

### `uart_rx_center_sampling.png`

- 模块：`rxuart`
- 阶段：有效起始位后的中心采样
- 结论：同步链稳定后，`half_baud_time` 先确认起始位中点，随后按位中心推进采样，说明该接收器不是沿边直接取样。

### `uart_rx_output_strobe.png`

- 模块：`rxuart`
- 阶段：字节输出
- 结论：`o_wr` 只在完整字节接收结束后拉高；结合本地仿真日志，已经成功收到 `0x55` 和 `0xA6`。

### `linetest_rx_stage.png`

- 模块：`linetest`
- 阶段：接收缓存阶段
- 结论：在 `140.500 us ~ 149.200 us` 窗口内，`dut.rx_stb` 依次确认收到 `0x41`、`0x42`，`dut.head` 随之递增，而 `dut.run_tx` 始终保持为 `0`，证明发送尚未启动。

### `linetest_lineend_trigger.png`

- 模块：`linetest`
- 阶段：回车触发行结束
- 结论：在 `151.715 us` 附近，`dut.rx_data` 变为 `0x0d`，`dut.head` 由 `3` 变 `4`，同时 `dut.lineend` 锁存为 `4`，`dut.run_tx` 拉高，随后 `dut.tx_stb` 开始请求发送。

### `linetest_tx_stage.png`

- 模块：`linetest`
- 阶段：整行发送阶段
- 结论：在 `151.700 us ~ 161.500 us` 窗口内，`dut.tx_stb` 持续有效，`dut.tail` 只在 `!dut.tx_busy` 的握手点前进，依次推进整行数据发送，`dut.lineend` 保持为 `4` 直到本轮发送结束。

## Naming Convention

推荐命名：

1. `linetest_rx_stage.png`
2. `linetest_lineend_trigger.png`
3. `linetest_tx_stage.png`
4. `uart_rx_false_start.png`
5. `uart_rx_center_sampling.png`
6. `uart_rx_output_strobe.png`

每张截图下方建议在工程日志里补 3 行说明：

1. 这是哪个模块、哪个阶段。
2. 你重点观察了哪些信号。
3. 这张图证明了什么结论。
