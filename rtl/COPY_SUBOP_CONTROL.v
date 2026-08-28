module COPY_SUBOP_CONTROL #(
	parameter SUBOP_WIDTH = 2
)(
	input copy,
	
	// databus inputs
	input [SUBOP_WIDTH - 1 : 0] SubopField,
	
	output COPYSTD,
	output RINT
);

	reg [3 : 0] decoder_out;

	always @(*) begin
		case(SubopField)
			2'b00 : decoder_out = 4'b0001;
			2'b01 : decoder_out = 4'b0010;
			2'b10 : decoder_out = 4'b0100;
			2'b11 : decoder_out = 4'b1000;
			default: decoder_out = 4'b0000;
		endcase
	end
	
	assign COPYSTD = copy & decoder_out[0];
	assign RINT = copy & decoder_out[1];

endmodule 