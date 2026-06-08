vlib work
vlog ../rtl/rxuart.v ../sim/uart_rx_wave_tb.v
vsim -voptargs=+acc work.uart_rx_wave_tb

add wave -divider {Clock and Line}
add wave sim:/uart_rx_wave_tb/i_clk
add wave sim:/uart_rx_wave_tb/i_reset
add wave sim:/uart_rx_wave_tb/i_uart_rx

add wave -divider {Synchronizer}
add wave sim:/uart_rx_wave_tb/dut/q_uart
add wave sim:/uart_rx_wave_tb/dut/qq_uart
add wave sim:/uart_rx_wave_tb/dut/ck_uart
add wave sim:/uart_rx_wave_tb/dut/chg_counter
add wave sim:/uart_rx_wave_tb/dut/half_baud_time

add wave -divider {RX State}
add wave sim:/uart_rx_wave_tb/dut/state
add wave sim:/uart_rx_wave_tb/dut/baud_counter
add wave sim:/uart_rx_wave_tb/dut/zero_baud_counter
add wave sim:/uart_rx_wave_tb/dut/data_reg
add wave sim:/uart_rx_wave_tb/o_data
add wave sim:/uart_rx_wave_tb/o_wr
add wave sim:/uart_rx_wave_tb/o_break
add wave sim:/uart_rx_wave_tb/o_parity_err
add wave sim:/uart_rx_wave_tb/o_frame_err

run 30 us
