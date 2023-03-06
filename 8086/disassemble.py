from dataclasses import dataclass


PRINT_DECODE = False

mov_rm_to_from_r_header = 0b100010

@dataclass
class Register:
    name: str

    def __repr__(self) -> str:
        return self.name.lower()

@dataclass
class Instruction:
    mnemonic: str
    dest: Register
    source: Register

    def __repr__(self) -> str:
        return f'{self.mnemonic} {self.dest}, {self.source}'


REGISTER_TABLE = [
    Register('AL'),
    Register('CL'),
    Register('DL'),
    Register('BL'),
    Register('AH'),
    Register('CH'),
    Register('DH'),
    Register('BH'),
    Register('AX'),
    Register('CX'),
    Register('DX'),
    Register('BX'),
    Register('SP'),
    Register('BP'),
    Register('SI'),
    Register('DI'),
]


def instruction_decode(instr_uint16 : int) -> Instruction:    
    if (instr_uint16 >> 10) == mov_rm_to_from_r_header:
        instr_data = (instr_uint16 & (2**10 - 1))
        dw = instr_data >> 8

        instr_data = (instr_data & (2**8 - 1))
        mm = instr_data >> 6

        instr_data = (instr_data & (2**6 - 1))
        reg = instr_data >> 3

        instr_data = (instr_data & (2**3 - 1))
        rem = instr_data

        if PRINT_DECODE:
            print(f'inst: {instr_uint16:16b}' )
            print(f'  dw: {dw:8b}')
            print(f'  mm: {mm:10b}')
            print(f' reg: {reg:13b}')
            print(f' rem: {rem:16b}')

        if mm == 3: # register -> register
            reg_index = ((dw & 1) << 3) + reg
            rem_index = ((dw & 1) << 3) + rem
            reg_is_dst = (dw & 2) == 2
            dst = reg_index if reg_is_dst else rem_index
            src = rem_index if reg_is_dst else reg_index

            return Instruction('mov', REGISTER_TABLE[dst], REGISTER_TABLE[src])


def disassemble(file):
    program = 'bits 16\n\n'

    while instr_bytes := file.read(2):
        instr_uint16 = int.from_bytes(instr_bytes, byteorder="big")
        program += str(instruction_decode(instr_uint16)) + '\n'

    return program
        

if __name__ == '__main__':
    filepath = './testcases/many_register_mov'
    file = open(filepath, 'rb')
    file.seek(0)

    prog = disassemble(file)

    print(prog)