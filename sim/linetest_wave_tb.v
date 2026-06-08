`timescale 1ns/1ps

module linetest_wave_tb;

	localparam [30:0] SETUP = 31'd32;

	reg         i_clk;
	reg         host_reset;
	reg         mon_reset;
	reg         src_stb;
	reg  [7:0]  src_data;
	wire        src_busy;
	wire        src_uart_tx;
	wire        o_uart_tx;
	wire        mon_wr;
	wire [7:0]  mon_data;
	wire        mon_break;
	wire        mon_parity_err;
	wire        mon_frame_err;
	wire        mon_ck_uart;

	linetest dut (
		.i_clk(i_clk),
		.i_setup(SETUP),
		.i_uart_rx(src_uart_tx),
		.o_uart_tx(o_uart_tx)
	);

	txuart host_tx (
		.i_clk(i_clk),
		.i_reset(host_reset),
		.i_setup(SETUP),
		.i_break(1'b0),
		.i_wr(src_stb),
		.i_data(src_data),
		.i_cts_n(1'b0),
		.o_uart_tx(src_uart_tx),
		.o_busy(src_busy)
	);

	rxuart monitor_rx (
		.i_clk(i_clk),
		.i_reset(mon_reset),
		.i_setup(SETUP),
		.i_uart_rx(o_uart_tx),
		.o_wr(mon_wr),
		.o_data(mon_data),
		.o_break(mon_break),
		.o_parity_err(mon_parity_err),
		.o_frame_err(mon_frame_err),
		.o_ck_uart(mon_ck_uart)
	);

	initial i_clk = 1'b0;
	always #5 i_clk = ~i_clk; // 100 MHz

	task send_byte;
		input [7:0] data;
		begin
			@(posedge i_clk);
			while (src_busy)
				@(posedge i_clk);
			src_data <= data;
			src_stb  <= 1'b1;
			@(posedge i_clk);
			src_stb  <= 1'b0;
		end
	endtask

	initial begin
		host_reset = 1'b1;
		mon_reset  = 1'b1;
		src_stb    = 1'b0;
		src_data   = 8'h00;

		repeat (8) @(posedge i_clk);
		host_reset = 1'b0;
		mon_reset  = 1'b0;

		// Wait long enough for DUT RX and monitor RX to synchronize
		// on the idle-high UART line.
		repeat (640) @(posedge i_clk);

		send_byte("A");
		send_byte("B");
		send_byte("C");
		send_byte(8'h0d); // carriage return triggers line send

		repeat (22000) @(posedge i_clk);
		$finish;
	end

	always @(posedge i_clk)
	if (dut.rx_stb)
		$display("%0t DUT RX byte = 0x%02x head=%0d", $time, dut.rx_data, dut.head);

	always @(posedge i_clk)
	if (dut.run_tx && dut.tx_stb && !dut.tx_busy)
		$display("%0t DUT TX byte = 0x%02x tail=%0d lineend=%0d", $time, dut.tx_data, dut.tail, dut.lineend);

	always @(posedge i_clk)
	if (mon_wr)
		$display("%0t Echo byte = 0x%02x", $time, mon_data);

endmodule
