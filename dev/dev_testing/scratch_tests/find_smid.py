def asm(func):
    t =func.inspect_asm()
    lines= list(t.values())[0].split('\n')
    simd_keywords = ["addps", "addpd", "vaddps", "vaddpd", "mulps", "mulpd",
                     "movups","xmm","ymm","zmm"]
    code=[]
    for n, l in enumerate(lines):
        num = len([ key for key in simd_keywords if key in l])
        if num > 0:
            code.append(l)
            print(func.__name__,f'{n} \t', l)
    print('smid lines=', len(code))