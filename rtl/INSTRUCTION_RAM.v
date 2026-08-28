module INSTRUCTION_RAM #(
	parameter WIDTH = 16,
	parameter ADDR_WIDTH = 7,
	
	// instruction format widths 
	parameter IMM_WIDTH = 8,
	parameter REG_FIELD_WIDTH = 3,
	parameter OP_CODE_WIDTH = 3,
	parameter SUB_OP_WIDTH = 2
	
)(

	input clk,
	
	// databus inputs
	
	input [ADDR_WIDTH - 1 : 0] PCOut,
	
	// databus outputs
	output [IMM_WIDTH - 1 : 0] imm,
	output [REG_FIELD_WIDTH - 1 : 0] regField,
	output [SUB_OP_WIDTH - 1 : 0] SubopField,
	
	// individual control lines
	output jal,
	output ALUI,
	output ALU,
	output tty,
	output copy,
	output beq,
	output load,
	output store
);

	reg [WIDTH - 1 : 0] memory [0 : (1 << ADDR_WIDTH) - 1];
	
	wire [WIDTH - 1 : 0] instruction;
	wire [OP_CODE_WIDTH - 1 : 0] op_code;
	
	initial begin
        $readmemh("instruction_ram.hex", memory);
   end
	
	
	assign instruction = memory[PCOut];
	
	assign op_code = instruction[2:0];
	assign regField = instruction[5:3];
	assign SubopField = instruction[7:6];
	assign imm = instruction[15:8];
	
	assign jal   = op_code == 3'b000;
	assign ALUI  = op_code == 3'b001;
	assign ALU   = op_code == 3'b010;
	assign tty   = op_code == 3'b011;
	assign copy  = op_code == 3'b100;
	assign beq   = op_code == 3'b101;
	assign load  = op_code == 3'b110;
	assign store = op_code == 3'b111;

endmodule 