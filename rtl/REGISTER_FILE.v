module REGISTER_FILE #(
	parameter REG_WIDTH = 8,
	parameter REG_COUNT = 8,
	parameter REG_ADDR_WIDTH = 3
)(
	input rst,
	input clk,
	input halt,
	input COPYSTD,
	
	// databus inputs
	input [REG_WIDTH - 1 : 0] accOut,
	input [REG_ADDR_WIDTH - 1 : 0] regField,
	
	// databus outputs
	output [REG_WIDTH - 1 : 0] regOut
);

	wire cpu_enable = !halt;

	reg [REG_WIDTH - 1 : 0] registers [0 : REG_COUNT - 1]; // 8 x 8 bit registers
	
	integer i; // for reset logic
	
	always @(posedge clk) begin
		if(rst)
			begin
				for(i = 0; i < REG_COUNT; i = i + 1)
					registers[i] <= {REG_WIDTH{1'b0}}; // reset to 0
			end
		else if(cpu_enable && COPYSTD) begin
			registers[regField] <= accOut;
		end
	end
	
	assign regOut = registers[regField];

endmodule 