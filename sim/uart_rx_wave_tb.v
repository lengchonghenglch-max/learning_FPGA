`timescale 1ns/1ps

module uart_rx_wave_tb;

	localparam [30:0] SETUP = 31'd32;

	reg         i_clk;
	reg         i_reset;
	reg         i_uart_rx;
	wire        o_wr;
	wire [7:0]  o_data;
	wire        o_break;
	wire        o_parity_err;
	wire        o_frame_err;
	wire        o_ck_uart;

	rxuart dut (
		.i_clk(i_clk),
		.i_reset(i_reset),
		.i_setup(SETUP),
		.i_uart_rx(i_uart_rx),
		.o_wr(o_wr),
		.o_data(o_data),
		.o_break(o_break),
		.o_parity_err(o_parity_err),
		.o_frame_err(o_frame_err),
		.o_ck_uart(o_ck_uart)
	);

	initial i_clk = 1'b0;
	always #5 i_clk = ~i_clk; // 100 MHz

	task hold_line;
		input value;
		input integer cycles;
		integer n;
		begin
			i_uart_rx = value;
			for (n = 0; n < cycles; n = n + 1)
				@(posedge i_clk);
		end
	endtask

	task send_byte;
		input [7:0] data;
		integer k;
		begin
			hold_line(1'b1, 32);
			hold_line(1'b0, 32); // start bit
			for (k = 0; k < 8; k = k + 1)
				hold_line(data[k], 32);
			hold_line(1'b1, 32); // stop bit
		end
	endtask

	initial begin
		i_reset   = 1'b1;
		i_uart_rx = 1'b1;

		repeat (8) @(posedge i_clk);
		i_reset = 1'b0;
		hold_line(1'b1, 640);

		// Short glitch: low pulse shorter than half a baud.
		hold_line(1'b0, 4);
		hold_line(1'b1, 40);

		// Normal bytes for center-sampling observation.
		send_byte(8'h55);
		hold_line(1'b1, 48);
		send_byte(8'ha6);
		hold_line(1'b1, 48);

		$finish;
	end

	always @(posedge i_clk)
	if (o_wr)
		$display("%0t RX byte = 0x%02x", $time, o_data);

endmodule
