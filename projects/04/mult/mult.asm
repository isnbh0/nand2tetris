// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// Put your code here.

// R2 = 0; i = 0
@R2
M=0
@i
M=0

(LOOP)
// branch: if i gte R1, goto END
@i
D=M
@R1
D=D-M
@END
D;JGE

// R2 = R2 + R0
@R0
D=M
@R2
M=M+D

// i++
@i
M=M+1

// goto LOOP
@LOOP
0;JMP

// end
(END)
@END
0;JMP
