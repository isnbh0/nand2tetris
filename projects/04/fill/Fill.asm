// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed.
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

// initialize screen_limit to KBD addr
@KBD
D=A
@screen_limit
M=D

// initialize isblack=0
@isblack
M=0

// key press detect loop
(IDLE)
@KBD
D=M  // get current keycode

// if pressed, go to PRESSED
@PRESSED
D;JGT
@NONPRESSED
0;JMP

(PRESSED) // if isblack==0, go to BLACKEN
@isblack
D=M
@BLACKEN
D;JEQ
@FINALLY
0;JMP

(NONPRESSED) // if isblack==1, go to WHITEN
@isblack
D=M-1
@WHITEN
D;JEQ
@FINALLY
0;JMP

(FINALLY)
@IDLE
0;JMP


// blacken
// black every pixel
(BLACKEN)
@SCREEN
D=A
@addr
M=D

(BLACKEN_LOOP)
@addr
D=M
@screen_limit
D=D-M
@BLACKEN_END
D;JGE
@addr
A=M
M=-1
@1
D=A
@addr
M=D+M
@BLACKEN_LOOP
0;JMP

(BLACKEN_END)
// set isblack=1
@isblack
M=1
// go back to IDLE
@IDLE
0;JMP


// whiten
// white every pixel
(WHITEN)
@SCREEN
D=A
@addr
M=D

(WHITEN_LOOP)
@addr
D=M
@screen_limit
D=D-M
@WHITEN_END
D;JGE
@addr
A=M
M=0
@1
D=A
@addr
M=D+M
@WHITEN_LOOP
0;JMP

(WHITEN_END)
// set isblack=0
@isblack
M=0
// go back to IDLE
@IDLE
0;JMP
