import ast, astor, codegen, dis


# def f(x):
#     return 1+2+3+4+x

# def g(x):
#     return x+1+2+3+4

def part_a(source):
    '''
    Breaking compilation into pieces - Part A
    '''
    print('\n\n# ---------------------------- PART A ----------------------------')

    # -- STEP 1: parse code into AST
    node = ast.parse(source, mode='eval')
    print('\n# -------------- STEP 1: parse code into AST')
    print(ast.dump(node))

    # -- STEP 2: compile into a code object
    compiled = compile(node, '<string>', mode='eval')
    print('\n# -------------- STEP 2: compile into a code object')
    print(compiled)
    print('co_varnames', compiled.co_varnames)
    print('co_consts', compiled.co_consts)
    print('co_argcount', compiled.co_argcount)
    print('co_code', compiled.co_code)

    # -- STEP 3: run the code object
    print('\n# -------------- STEP 3: run the code object')
    print(eval(compiled))


def part_b(source):
    '''
    Part A, but with more data.
    Breaking compilation into pieces, diving deeper.
    '''
    print('\n\n# ---------------------------- PART B ----------------------------')

    # -- STEP 1: parse code into AST
    node = ast.parse(source, mode='eval')
    print('\n# -------------- STEP 1: parse code into AST')
    print(ast.dump(node))

    # -- STEP 2: compile into a code object
    compiled = compile(node, '<string>', mode='eval')
    print('\n# -------------- STEP 2: compile into a code object')
    print(compiled)
    print('co_varnames', compiled.co_varnames)
    print('co_consts', compiled.co_consts)
    print('co_argcount', compiled.co_argcount)
    print('co_code', compiled.co_code)

    # -- STEP 2B: view the bytecode in a (slightly) more friendly manner
    print('\n# -------------- STEP 2B: view the bytecode in a (slightly) more friendly manner')
    print([b for b in compiled.co_code])

    # -- STEP 2C: dive into bytecode using dis
    print('\n# -------------- STEP 2C: dive into bytecode using dis')
    print(dis.dis(compiled))

    # -- STEP 3: run the code object
    print('\n# -------------- STEP 3: run the code object')
    print(eval(compiled))

    # # -- Reverse it:
    # # -- STEP 4:
    # print(codegen.to_source(node))


def part_c():
    '''
    Example of constant folding!
    '''
    pass


def main():
    # ---- Oddity: bytecode differs here.
    # ---- Does the AST differ as well?
    # dis.dis(f)
    # dis.dis(g)
    # tree = ast.parse('print("hello world")')
    # print(astor.dump_tree(tree, indentation='    '))

    source_with_cf = '3 * 2'
    source = 'print("may the force be with you")'
    part_a(source)
    part_b(source)
    part_b(source_with_cf)
    part_c()


    # OTHA STUFF:
    # import ast, dis
    # # def iffer(condition):
    # #     if condition:
    # #         return 3
    # #     else:
    # #         return 10
    # # print(dis.dis(iffer))
    # # print(ast.parse(iffer), mode='eval')
    # dis.dis("print('hello world')")
    # tree = ast.parse("print('hello world')")
    # print('tree', tree)
    # dump = ast.dump(tree)
    # print('dump', dump)



if __name__ == '__main__':
    main()
