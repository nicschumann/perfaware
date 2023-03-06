import os
import subprocess
from disassemble import disassemble

if __name__ == '__main__':
    testcases = [
        './testcases/single_register_mov',
        './testcases/many_register_mov',
    ]

    for testcase in testcases:
        binary = open(testcase, 'rb')

        prog = disassemble(binary)

        program_output_filename = f'{testcase}_prime.asm'
        binary_outfile_name = f'{testcase}_prime'

        outfile = open(program_output_filename, 'w+')
        outfile.write(prog)
        outfile.close()

        subprocess.call(['nasm', program_output_filename])

        binary_prime = open(binary_outfile_name, 'rb')
        binary.seek(0)

        binary_contents = binary.read()
        binary_prime_contents = binary_prime.read()

        
        print(binary_contents == binary_prime_contents)

        # Cleanup
        binary_prime.close()
        binary.close()

        os.remove(program_output_filename)
        os.remove(binary_outfile_name)



