vlib work
vlog +define+VERILATOR ../rtl/rxuart.v ../rtl/txuart.v ../rtl/linetest.v ../sim/linetest_wave_tb.v
vsim -voptargs=+acc work.linetest_wave_tb

add wave -divider {Clock and UART Lines}
add wave sim:/linetest_wave_tb/i_clk
add wave sim:/linetest_wave_tb/i_uart_rx
add wave sim:/linetest_wave_tb/o_uart_tx

add wave -divider {RX Buffering}
add wave sim:/linetest_wave_tb/dut/rx_stb
add wave sim:/linetest_wave_tb/dut/rx_data
add wave sim:/linetest_wave_tb/dut/head
add wave sim:/linetest_wave_tb/dut/tail
add wave sim:/linetest_wave_tb/dut/nused
add wave sim:/linetest_wave_tb/dut/lineend
add wave sim:/linetest_wave_tb/dut/run_tx

add wave -divider {TX Handshake}
add wave sim:/linetest_wave_tb/dut/tx_stb
add wave sim:/linetest_wave_tb/dut/tx_data
add wave sim:/linetest_wave_tb/dut/tx_busy

add wave -divider {Echo Monitor}
add wave sim:/linetest_wave_tb/mon_wr
add wave sim:/linetest_wave_tb/mon_data

run 250 us
