module PC #(
    parameter WIDTH = 8,
    parameter SUBOP_WIDTH = 2
)(
    input clk,
    input rst,
    input halt,
    input beq,

    input [7:0] regOut,
    input [7:0] accOut,
    input [7:0] imm,
    input [SUBOP_WIDTH-1:0] SubopField,

    output [WIDTH-1:0] PCOut
);

    wire cpu_enable = !halt;

    wire equal =
        (regOut == accOut);

    wire not_equal =
        (regOut != accOut);

    wire less_than =
        ($signed(regOut) < $signed(accOut));

    reg condition;

    always @(*) begin
        case (SubopField)
            2'b00: condition = equal;
            2'b01: condition = not_equal;
            2'b10: condition = less_than;
            2'b11: condition = 1'b1;
            default: condition = 1'b0;
        endcase
    end

    reg [WIDTH-1:0] PC;

    always @(posedge clk) begin
        if (rst)
            PC <= 8'd0;

        else if (cpu_enable) begin
            if (beq && condition)
                PC <= PC + imm;
            else
                PC <= PC + 1'b1;
        end
    end

    assign PCOut = PC;

endmodule