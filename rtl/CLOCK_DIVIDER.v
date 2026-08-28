module CLOCK_DIVIDER #(
    parameter COUNTER_WIDTH = 24
)(
    input  wire clk,
    input  wire rst,
    output wire slow_clk
);

    reg [COUNTER_WIDTH-1:0] counter;

    always @(posedge clk or posedge rst) begin
        if (rst)
            counter <= {COUNTER_WIDTH{1'b0}};
        else
            counter <= counter + 1'b1;
    end

    assign slow_clk = counter[COUNTER_WIDTH-1];

endmodule