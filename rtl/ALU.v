module ALU #(
	parameter REG_WIDTH = 8,
	parameter SUBOP_WIDTH = 2
)(
	input ALU,
	
	// databus inputs
	input [SUBOP_WIDTH - 1 : 0] SubopField,
	input [REG_WIDTH - 1 : 0] regOut,
	input [REG_WIDTH - 1 : 0] imm,
	input [REG_WIDTH - 1 : 0] accOut,
	
	// databus outputs
	output [REG_WIDTH - 1 : 0] ALUOut
);
	
	wire [REG_WIDTH - 1 : 0] second_value = ALU ? accOut : imm;
	
	reg [REG_WIDTH - 1 : 0] mux2;

	always @(*) begin
		case(SubopField)
			2'b00   : mux2 = regOut + second_value;
         2'b01   : mux2 = regOut - second_value;
         2'b10   : mux2 = regOut * second_value;
         2'b11   : mux2 = regOut / second_value;
         default : mux2 = {REG_WIDTH{1'b0}};
		endcase
	end
	
	assign ALUOut = mux2;
endmodule 