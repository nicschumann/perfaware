from dataclasses import dataclass


PRINT_DECODE = True

mov_rm_to_from_r_header = 0b100010
mov_imm_to_reg_mem = 0b1100011
mov_imm_to_reg = 0b1011


@dataclass
class Immediate:
    bytelength: int
    value: int | None = None

    def __repr__(self) -> str:
        return f'{self.value}'

@dataclass
class Register:
    name: str

    def __repr__(self) -> str:
        return self.name.lower()

@dataclass
class RegisterSum:
    left: Register
    right: Register

    def __repr__(self) -> str:
        return f'{self.left} + {self.right}'

@dataclass
class EffectiveAddress:
    register: Register | RegisterSum | None
    offset: Immediate | None

    def __repr__(self) -> str:
        offset_string = '' if self.offset is None or self.offset.value == 0 else f' + {self.offset}'
        return f'[{self.register}' + offset_string + ']'

@dataclass
class DirectAddress:
    offset: Immediate

    def __repr__(self) -> str:
        return f'[{self.offset}]'

@dataclass
class MovInstruction:
    dest: Register | EffectiveAddress
    source: Register | EffectiveAddress | Immediate

    def __repr__(self) -> str:
        length_flag = ''

        if (type(self.dest) == EffectiveAddress or type(self.dest) == DirectAddress) and type(self.source) == Immediate:
            length_flag = 'word ' if self.source.bytelength == 2 else 'byte '

        return f'mov {self.dest}, {length_flag}{self.source}'


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

EFFECTIVE_ADDRESS_TABLE = [
    
    EffectiveAddress(RegisterSum(Register('BX'), Register('SI')), None), # [BX + SI]
    EffectiveAddress(RegisterSum(Register('BX'), Register('DI')), None), # [BX + DI]
    EffectiveAddress(RegisterSum(Register('BP'), Register('SI')), None), # [BP + SI]
    EffectiveAddress(RegisterSum(Register('BP'), Register('DI')), None), # [BP + DI]

    EffectiveAddress(Register('SI'), None), # [SI]
    EffectiveAddress(Register('DI'), None), # [DI]
    DirectAddress(Immediate(2)), # [WORD 16]
    EffectiveAddress(Register('BX'), None), # [BX]

    EffectiveAddress(RegisterSum(Register('BX'), Register('SI')), Immediate(1)), # [BX + SI + BYTE 8]
    EffectiveAddress(RegisterSum(Register('BX'), Register('DI')), Immediate(1)), # [BX + DI + BYTE 8]
    EffectiveAddress(RegisterSum(Register('BP'), Register('SI')), Immediate(1)), # [BP + SI + BYTE 8]
    EffectiveAddress(RegisterSum(Register('BP'), Register('DI')), Immediate(1)), # [BP + DI + BYTE 8]

    EffectiveAddress(Register('SI'), Immediate(1)), # [SI + BYTE 8]
    EffectiveAddress(Register('DI'), Immediate(1)), # [DI + BYTE 8]
    EffectiveAddress(Register('BP'), Immediate(1)), # [BP + BYTE 8]
    EffectiveAddress(Register('BX'), Immediate(1)), # [BX + BYTE 8]

    EffectiveAddress(RegisterSum(Register('BX'), Register('SI')), Immediate(2)), # [BX + SI + WORD 16]
    EffectiveAddress(RegisterSum(Register('BX'), Register('DI')), Immediate(2)), # [BX + DI + WORD 16]
    EffectiveAddress(RegisterSum(Register('BP'), Register('SI')), Immediate(2)), # [BP + SI + WORD 16]
    EffectiveAddress(RegisterSum(Register('BP'), Register('DI')), Immediate(2)), # [BP + DI + WORD 16]

    EffectiveAddress(Register('SI'), Immediate(2)), # [SI + WORD 16]
    EffectiveAddress(Register('DI'), Immediate(2)), # [DI + WORD 16]
    EffectiveAddress(Register('BP'), Immediate(2)), # [BP + WORD 16]
    EffectiveAddress(Register('BX'), Immediate(2)), # [BX + WORD 16]
]

def decode_bytes(wide: int, instr_stream) -> int:
    data_bytes = instr_stream.read(1)
    data = int.from_bytes(data_bytes, byteorder="big")

    if wide == 1:
        data_h_bytes = instr_stream.read(1)
        data_h = int.from_bytes(data_h_bytes, byteorder="big")
        data = (data_h << 8) + data
    
    return data


def instruction_decode(instruction : int, instr_stream) -> MovInstruction:  
    
    if PRINT_DECODE:
        print(f'\nhead: {instruction:8b}' )

    if (instruction >> 1) == mov_imm_to_reg_mem: 
        instr_bytes = instr_stream.read(1)
        instr_addl = int.from_bytes(instr_bytes, byteorder="big")

        w = (instruction & 1)
        mod = instr_addl >> 6
        rem = instr_addl & 0b00000111
        disp = 0

        if mod == 1:
            disp = decode_bytes(0, instr_stream)
        
        elif mod == 2 or rem == 0b110:
            disp = decode_bytes(1, instr_stream)

        data = decode_bytes(w, instr_stream)

        ea_index = (mod*8) + rem

        dst = EFFECTIVE_ADDRESS_TABLE[ea_index]
        if dst.offset is not None: dst.offset.value = disp

        src = Immediate(w * 2, data)

        if PRINT_DECODE:
            print(f'inst: {(instruction << 8) + instr_addl:16b}' )
            print(f'   w: {w:8b}')
            print(f' mod: {mod:10b}')
            print(f' rem: {rem:16b}')

        return MovInstruction(dst, src)


    if (instruction >> 4) == mov_imm_to_reg:
        w = (instruction & 0b00001000) >> 3
        reg = instruction & 0b00000111
        reg_index = (w << 3) + reg

        data = decode_bytes(w, instr_stream)
        dest = REGISTER_TABLE[reg_index]

        if PRINT_DECODE:
                print(f'inst: {instruction:8b}' )
                print(f'   w: {w:5b}')
                print(f' reg: {reg:8b}')

        return MovInstruction(dest, Immediate(w * 2, data))
        
    
    if (instruction >> 2) == mov_rm_to_from_r_header:

        instr_uint8 = decode_bytes(0, instr_stream)
        instruction = (instruction << 8) + instr_uint8

        instr_data = (instruction & (2**10 - 1))
        dw = instr_data >> 8

        instr_data = (instr_data & (2**8 - 1))
        mod = instr_data >> 6

        instr_data = (instr_data & (2**6 - 1))
        reg = instr_data >> 3

        instr_data = (instr_data & (2**3 - 1))
        rem = instr_data

        if PRINT_DECODE:
            print(f'inst: {instruction:16b}' )
            print(f'  dw: {dw:8b}')
            print(f' mod: {mod:10b}')
            print(f' reg: {reg:13b}')
            print(f' rem: {rem:16b}')

        if mod == 3: # MOD = 0b11 = 3, register -> register
            reg_index = ((dw & 1) << 3) + reg
            rem_index = ((dw & 1) << 3) + rem
            reg_is_dst = (dw & 2) == 2
            dst = REGISTER_TABLE[reg_index if reg_is_dst else rem_index]
            src = REGISTER_TABLE[rem_index if reg_is_dst else reg_index]

            return MovInstruction(dst, src)
        
        elif mod == 2:
            # register <-> memory [expr + 16 bit displacement]

            d16 = decode_bytes(1, instr_stream)

            reg_index = ((dw & 1) << 3) + reg
            ea_index = (mod*8) + rem

            reg_val = REGISTER_TABLE[reg_index]
            ea_val = EFFECTIVE_ADDRESS_TABLE[ea_index]
            ea_val.offset.value = d16

            reg_is_dst = (dw & 2) == 2
            dst = reg_val if reg_is_dst else ea_val
            src = ea_val if reg_is_dst else reg_val

            return MovInstruction(dst, src)


        elif mod == 1:
            # register <-> memory [expr + 8 bit displacement]
            # expr + 8bit displacement
            d8 = decode_bytes(0, instr_stream)

            reg_index = ((dw & 1) << 3) + reg
            ea_index = (mod*8) + rem
            reg_val = REGISTER_TABLE[reg_index]
            ea_val = EFFECTIVE_ADDRESS_TABLE[ea_index]
            ea_val.offset.value = d8

            reg_is_dst = (dw & 2) == 2
            dst = reg_val if reg_is_dst else ea_val
            src = ea_val if reg_is_dst else reg_val

            return MovInstruction(dst, src)

        elif mod == 0:
            # register <-> memory [expr]
            # expr, no displacement
            reg_index = ((dw & 1) << 3) + reg
            ea_index = (mod*8) + rem
            reg_is_dst = (dw & 2) == 2
            reg_val = REGISTER_TABLE[reg_index]
            ea_val = EFFECTIVE_ADDRESS_TABLE[ea_index]

            dst = reg_val if reg_is_dst else ea_val
            src = ea_val if reg_is_dst else reg_val
            
            if rem == 0b110:
                disp = decode_bytes(1, instr_stream)
                ea_val.offset.value = disp

            return MovInstruction(dst, src)





def disassemble(file):
    program = 'bits 16\n\n'

    while instr_bytes := file.read(1):

        instruction = int.from_bytes(instr_bytes, byteorder="big")
        program += str(instruction_decode(instruction, file)) + '\n'

    return program
        

if __name__ == '__main__':
    filepath = './testcases/challenge_movs'
    file = open(filepath, 'rb')
    file.seek(0)

    prog = disassemble(file)

    print('\n\n')
    print(prog)