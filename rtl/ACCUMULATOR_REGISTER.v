module ACCUMULATOR_REGISTER #(
    parameter REG_WIDTH = 8
)(
    input clk,
    input halt,
    input rst,
    input ALUI,
    input ALU,
    input load,
    input loadDecode,
    input ReadJalRegisters,

    // data bus inputs
    input [REG_WIDTH - 1 : 0] ALUOut,
    input [REG_WIDTH - 1 : 0] globalOut,
    input [REG_WIDTH - 1 : 0] ioOut,
    input [REG_WIDTH - 1 : 0] JALRegOut,

    // data bus outputs
    output [REG_WIDTH - 1 : 0] accOut
);

    wire cpu_enable = !halt;

    wire enable = ALUI | ALU | load | ReadJalRegisters;

    reg [REG_WIDTH - 1 : 0] acc;

    // Select which memory space supplies load data.
    wire [REG_WIDTH - 1 : 0] memoryOut =
        loadDecode ? ioOut : globalOut;

    // Select memory output for load instructions, otherwise ALU output.
    wire [REG_WIDTH - 1 : 0] mux1 =
        load ? memoryOut : ALUOut;

    // JAL/SRF register reads have final priority.
    wire [REG_WIDTH - 1 : 0] data =
        ReadJalRegisters ? JALRegOut : mux1;

    always @(posedge clk) begin
        if (rst)
            acc <= {REG_WIDTH{1'b0}};
        else if (enable && cpu_enable)
            acc <= data;
    end

    assign accOut = acc;

endmodule