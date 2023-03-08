; reg
mov es, ax
mov bx, es
mov es, cx
mov dx, es

; disp: 8 bit signed
mov ss, [bx + di + 10]
mov [bx + di - 10], es

; disp: 16 bit signed

mov ds, [bx + si + 3223]
mov [bp + di - 3223], cs

; direct
mov ds, [2043]
mov [2043], cs