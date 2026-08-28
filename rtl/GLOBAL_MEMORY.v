module GLOBAL_MEMORY #(
    parameter WIDTH = 8,
    parameter ADDR_WIDTH = 4
)(
    input clk,
    input halt,
    input store,

    input [ADDR_WIDTH-1:0] imm,
    input [WIDTH-1:0] accOut,

    output [WIDTH-1:0] globalOut
);

    wire cpu_enable = !halt;

    reg [WIDTH-1:0] global_mem [0:(1 << ADDR_WIDTH)-1];

    initial begin
        $readmemh("global_memory.hex", global_mem);
    end

    always @(posedge clk) begin
        if (cpu_enable && store)
            global_mem[imm] <= accOut;
    end

    assign globalOut = global_mem[imm];

endmodule