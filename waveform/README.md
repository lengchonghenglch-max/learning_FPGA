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

## Pending Screenshots

- `linetest_rx_stage.png`
- `linetest_lineend_trigger.png`
- `linetest_tx_stage.png`

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
