# nand2tetris

My solutions to the [nand2tetris](https://www.nand2tetris.org/) course on building a computer system, starting only with NAND logic gates and ending with a [working game of 2048](https://youtu.be/xZUWkpwCtUM):

<div align="center">
    <a href="https://youtu.be/xZUWkpwCtUM">
        <img 
            src="https://img.youtube.com/vi/xZUWkpwCtUM/hqdefault.jpg" 
            alt="Watch the video" 
        >
    </a>
</div>

## Projects
| Project | Title | Languages | Notable Work |
|---|---|---|---|
| 1<br>2<br>3 | Boolean Logic<br>Boolean Arithmetic<br>Sequential Logic | HDL | - [ALU](https://github.com/isnbh0/nand2tetris/blob/main/projects/02/ALU.hdl) |
| 4 | Machine Language | Hack assembly | - [Fill.asm](https://github.com/isnbh0/nand2tetris/blob/main/projects/04/fill/Fill.asm) |
| 5 | Computer Architecture | HDL | - [CPU](https://github.com/isnbh0/nand2tetris/blob/main/projects/05/CPU.hdl) |
| 6 | Assembler | Python | - [Assembler](https://github.com/isnbh0/nand2tetris/blob/main/projects/06/assemble.py) |
| 7<br>8 | VM I: Stack Arithmetic<br>VM II: Program Control | Python | - [VM translator](https://github.com/isnbh0/nand2tetris/blob/main/projects/08/vmtranslator.py)<br>- [Assembly code generation](https://github.com/isnbh0/nand2tetris/blob/main/projects/08/helpers.py) |
| 9 | High-Level Language | Jack | - [2048 game main loop](https://github.com/isnbh0/nand2tetris/blob/main/projects/09/2048/TwosGame.jack)<br>- [2048 game board manipulation and rendering](https://github.com/isnbh0/nand2tetris/blob/main/projects/09/2048/Board.jack) |
| 10<br>11 | Compiler I: Syntax Analysis<br>Compiler II: Code Generation | Python | - [VM compilation engine](https://github.com/isnbh0/nand2tetris/blob/main/projects/11/compiler/engine/vm_compilation_engine.py)<br>- [Jack tokenizer](https://github.com/isnbh0/nand2tetris/blob/main/projects/11/compiler/jack_tokenizer.py)<br>- [Symbol table](https://github.com/isnbh0/nand2tetris/blob/main/projects/11/compiler/symbol_table.py)<br>- [VM writer](https://github.com/isnbh0/nand2tetris/blob/main/projects/11/compiler/vm_writer.py)<br>- [Helper functions and utils](https://github.com/isnbh0/nand2tetris/blob/main/projects/11/compiler/utils/helpers.py) |
| 12 | Operating System | Jack | - [OS Memory module with basic defrag support](https://github.com/isnbh0/nand2tetris/blob/main/projects/12/Memory.jack) |

### Reference for languages used
| Language      | Extension | Description                                                                                                                                                       |
|---------------|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| HDL           | .hdl      | A hardware description language for describing circuits of logic gates.                                                                                           |
| Hack machine  | .hack     | A 16-bit machine language for the Hack computer, a von Neumann platform with CPU, instruction memory, data memory, and memory-mapped screen and keyboard for I/O. |
| Hack assembly | .asm      | A human-readable assembly language for the Hack machine language.                                                                                                 |
| VM            | .vm       | The language associated with the stack-based virtual machine as specified in The Elements of Computing Systems chapters 7 and 8.                                  |
| Jack          | .jack     | A high-level, object-based programming language inspired by languages like Java or C#.                                                                            |

## Note
The code (especially Python) may not be 100% polished and will trigger linters, with issues such as the following.
- inconsistency with case types when naming functions and attributes (e.g. [`compileClass`](https://github.com/isnbh0/nand2tetris/blob/4700bdd4999ee23faf0ce44e70277f7cf8ffdd96/projects/11/compiler/engine/vm_compilation_engine.py#L104) vs [`current_token`](https://github.com/isnbh0/nand2tetris/blob/4700bdd4999ee23faf0ce44e70277f7cf8ffdd96/projects/11/compiler/engine/vm_compilation_engine.py#L39))
- unused imports and names (e.g. [here](https://github.com/isnbh0/nand2tetris/blob/4700bdd4999ee23faf0ce44e70277f7cf8ffdd96/projects/06/assemble.py#L3) and [here](https://github.com/isnbh0/nand2tetris/blob/4700bdd4999ee23faf0ce44e70277f7cf8ffdd96/projects/06/assemble.py#L180))
- f-strings with no placeholders (e.g. [in here](https://github.com/isnbh0/nand2tetris/blob/4700bdd4999ee23faf0ce44e70277f7cf8ffdd96/projects/08/helpers.py))
- lines that have been commented out that will never be used (e.g. [here](https://github.com/isnbh0/nand2tetris/blob/4700bdd4999ee23faf0ce44e70277f7cf8ffdd96/projects/08/vmtranslator.py#L154))


---

Based on the [Nand2tetris Software Suite](https://www.nand2tetris.org/software).
