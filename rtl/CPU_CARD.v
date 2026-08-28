module CPU_CARD #(
    parameter DATA_WIDTH     = 8,
    parameter ADDR_WIDTH     = 8,
    parameter IMM_WIDTH      = 8,
    parameter REG_ADDR_WIDTH = 3,
    parameter SUBOP_WIDTH    = 2
)(
    input  wire       rst,

    output wire [7:0] LED
);

	 wire internal_clk;
	 wire cpu_clk;
	 
	 wire loadDecode;

	 wire storeGlobal;
	 wire storeIO;
	 
	 internal u0 (
		  .oscena(1'b1),
		  .clkout(internal_clk)
	 );

	 CLOCK_DIVIDER #(
		  .COUNTER_WIDTH(17)
	 ) cpu_clock_divider (
		  .clk(internal_clk),
		  .rst(cpu_reset),
		  .slow_clk(cpu_clk)
	 );

    // ============================================================
    // CPU CONTROL
    // ============================================================

    // No halt hardware on the stripped-down card yet.
    wire halt = 1'b0;


    // ============================================================
    // INSTRUCTION FIELDS
    // ============================================================

    wire [ADDR_WIDTH-1:0]     PCOut;
    wire [IMM_WIDTH-1:0]      imm;
    wire [REG_ADDR_WIDTH-1:0] regField;
    wire [SUBOP_WIDTH-1:0]    SubopField;


    // ============================================================
    // OPCODE CONTROL LINES
    // ============================================================

    wire jal;
    wire ALUI;
    wire ALU;
    wire tty;
    wire copy;
    wire beq;
    wire load;
    wire store;


    // ============================================================
    // COPY SUBOP CONTROL
    // ============================================================

    wire COPYSTD;
    wire RINT_unused;


    // ============================================================
    // DATAPATH
    // ============================================================

    wire [DATA_WIDTH-1:0] accOut;
    wire [DATA_WIDTH-1:0] regOut;
    wire [DATA_WIDTH-1:0] ALUOut;
    wire [DATA_WIDTH-1:0] globalOut;
	 
	 // ============================================================
	 // POWER-ON RESET
	 // ============================================================

 	 reg [7:0] startup_counter = 8'h00;
    reg       startup_reset   = 1'b1;

	 always @(posedge internal_clk) begin
		  if (startup_counter != 8'hFF) begin
			   startup_counter <= startup_counter + 1'b1;
			   startup_reset   <= 1'b1;
		  end
		  else begin
		 	   startup_reset <= 1'b0;
		  end
	 end

	 // Manual reset button OR automatic startup reset
	 wire cpu_reset = rst | startup_reset;


    // ============================================================
    // INSTRUCTION MEMORY / DECODER
    // ============================================================

    INSTRUCTION_RAM #(
        .WIDTH(16),
        .ADDR_WIDTH(7),
        .IMM_WIDTH(IMM_WIDTH),
        .REG_FIELD_WIDTH(REG_ADDR_WIDTH),
        .OP_CODE_WIDTH(3),
        .SUB_OP_WIDTH(SUBOP_WIDTH)
    ) instruction_ram_inst (
        .clk(cpu_clk),

        .PCOut(PCOut),

        .imm(imm),
        .regField(regField),
        .SubopField(SubopField),

        .jal(jal),
        .ALUI(ALUI),
        .ALU(ALU),
        .tty(tty),
        .copy(copy),
        .beq(beq),
        .load(load),
        .store(store)
    );


    // ============================================================
    // COPY INSTRUCTION SUBOP DECODER
    // ============================================================

    COPY_SUBOP_CONTROL #(
        .SUBOP_WIDTH(SUBOP_WIDTH)
    ) copy_subop_control_inst (
        .copy(copy),
        .SubopField(SubopField),

        .COPYSTD(COPYSTD),
        .RINT(RINT_unused)
    );


    // ============================================================
    // PROGRAM COUNTER
    // ============================================================

    PC #(
        .WIDTH(ADDR_WIDTH),
        .SUBOP_WIDTH(SUBOP_WIDTH)
    ) pc_inst (
        .clk(cpu_clk),
        .rst(cpu_reset),
        .halt(halt),
        .beq(beq),

        .regOut(regOut),
        .accOut(accOut),
        .imm(imm),
        .SubopField(SubopField),

        .PCOut(PCOut)
    );


    // ============================================================
    // ALU
    // ============================================================
    //
    // Your ALU already handles both ALUI and ALU correctly:
    //
    // ALU = 0:
    //     second operand = immediate
    //
    // ALU = 1:
    //     second operand = accumulator
    //
    // Therefore:
    //
    // ALUI instruction -> ALU signal is 0 -> immediate arithmetic
    // ALU  instruction -> ALU signal is 1 -> register/ACC arithmetic
    //

    ALU #(
        .REG_WIDTH(DATA_WIDTH),
        .SUBOP_WIDTH(SUBOP_WIDTH)
    ) alu_inst (
        .ALU(ALU),

        .SubopField(SubopField),
        .regOut(regOut),
        .imm(imm),
        .accOut(accOut),

        .ALUOut(ALUOut)
    );


    // ============================================================
    // ACCUMULATOR
    // ============================================================
    //
    // The full CPU accumulator still has ports for IO and JAL.
    // Those features don't exist on the card, so tie them off.
    //

    ACCUMULATOR_REGISTER #(
        .REG_WIDTH(DATA_WIDTH)
    ) accumulator_inst (
        .clk(cpu_clk),
        .halt(halt),
        .rst(cpu_reset),

        .ALUI(ALUI),
        .ALU(ALU),
        .load(load),

        // No IO memory on card
        .loadDecode(loadDecode),

        // No JAL/SRF readback on card
        .ReadJalRegisters(1'b0),

        .ALUOut(ALUOut),
        .globalOut(globalOut),

        // Removed peripherals
        .ioOut({DATA_WIDTH{1'b0}}),
        .JALRegOut({DATA_WIDTH{1'b0}}),

        .accOut(accOut)
    );


    // ============================================================
    // GENERAL PURPOSE REGISTER FILE
    // ============================================================

    REGISTER_FILE #(
        .REG_WIDTH(DATA_WIDTH),
        .REG_COUNT(8),
        .REG_ADDR_WIDTH(REG_ADDR_WIDTH)
    ) register_file_inst (
        .rst(cpu_reset),
        .clk(cpu_clk),
        .halt(halt),

        .COPYSTD(COPYSTD),

        .accOut(accOut),
        .regField(regField),

        .regOut(regOut)
    );


    // ============================================================
    // GLOBAL DATA MEMORY
    // ============================================================

    GLOBAL_MEMORY #(
        .WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(4)
    ) global_memory_inst (
        .clk(cpu_clk),
        .halt(halt),

        .store(storeGlobal),

        .imm(imm),
        .accOut(accOut),

        .globalOut(globalOut)
    );
	 
	 LOAD_SUBOP_CONTROL #(
		 .SUBOP_WIDTH(SUBOP_WIDTH)
	 ) load_subop_control_inst (
		 .load(load),
		 .SubopField(SubopField),

		 .loadDecode(loadDecode)
	 );
	 
	 STORE_SUBOP_CONTROL #(
		 .SUBOP_WIDTH(SUBOP_WIDTH)
	 ) store_subop_control_inst (
		 .store(store),
		 .SubopField(SubopField),

		 .storeGlobal(storeGlobal),
		 .storeIO(storeIO)
	 );


   // ============================================================
	// LED OUTPUT REGISTER
	// ============================================================

	reg [DATA_WIDTH-1:0] led_reg;

	always @(posedge cpu_clk) begin
		 if (cpu_reset)
			  led_reg <= {DATA_WIDTH{1'b0}};
		 else if (storeIO)
			  led_reg <= accOut;
	end

	assign LED = led_reg;

endmodule