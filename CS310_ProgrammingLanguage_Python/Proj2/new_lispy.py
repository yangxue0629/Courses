#!/usr/bin/python

################ Lispy: Scheme Interpreter in Python

## (c) Peter Norvig, 2010; See http://norvig.com/lispy.html

################ Symbol, Env classes

from __future__ import division
import string

Symbol = str

class Env(dict):
    "An environment: a dict of {'var':val} pairs, with an outer Env."
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms,args))
        self.outer = outer
        #self.level = 0 if self.outer == None else outer.level + 1
        self.update(var = {})
    def find(self, var):
        "Find the innermost Env where var appears."
        return self if var in self else self.outer.find(var)

def add_globals(env):
    "Add some Scheme standard procedures to an environment."
    import math, operator as op
    env.update(vars(math)) # sin, sqrt, ...
    env.update(
     {'say': lambda x: say(x), 'quit' : goodbye,
      '+':op.add, '-':op.sub, '*':op.mul, '/':op.div, 'not':op.not_,
      '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '=':op.eq, 
      'equal?':op.eq, 'eq?':op.is_, 'length':len, 'cons':lambda x,y:[x]+y,
      'car':lambda x:x[0],'cdr':lambda x:x[1:], 'append':op.add,  
      'list':lambda *x:list(x), 'list?': lambda x:isa(x,list), 
      'null?':lambda x:x==[], 'symbol?':lambda x: isa(x, Symbol)})
    return env

def say(x): print x
def goodbye(): print ";; Bye."; quit()

global_env = add_globals(Env())

isa = isinstance

################ eval

def eval(x, env=global_env, depth = 0):
    "Evaluate an expression in an environment."
    if isa(x, Symbol):             # variable reference
        return env.find(x)[x]
    elif not isa(x, list):         # constant literal
        return x                
    elif x[0] == 'load':
      tmp = eval(x[1],env)
      return eload(tmp)
    elif  x[0] == 'quote' or  x[0] == "'":
        (_, exp) = x
        return exp
    elif x[0] == 'if':             # (if test conseq alt)
        (_, test, conseq, alt) = x
        return eval((conseq if eval(test, env) else alt), env)
    elif x[0] == 'set!':           # (set! var exp)
        (_, var, exp) = x
        env.find(var)[var] = eval(exp, env)
    elif x[0] == 'define':         # (define var exp)
        (_, var, exp) = x
        global_env['var'][var] = False
        env[var] = eval(exp, env)
    elif x[0] == 'lambda':         # (lambda (var*) exp)
        (_, vars, exp) = x
        return lambda *args: eval(exp, Env(vars, args, env))
    elif x[0] == 'begin':          # (begin exp*)
        for exp in x[1:]:
            val = eval(exp, env)
        return val
    elif x[0] == 'trace':          # (trace X)
        if len(x) > 1:
            var = x[1] 
            global_env['var'][var] = True
        if len(x) == 1:
            for k in global_env['var'].keys(): global_env['var'][k] = True
    elif x[1] == 'untrace':       # (untrace X)
        if len(x) > 1:
            var = x[1]
            global_env['var'][var] = False
    else:                         # (proc exp*)
        exps = [eval(exp, env, depth+1) for exp in x]
        head = [x[0]] + exps[1:]
        flage = False
        if x[0] in global_env['var'].keys() and global_env['var'][x[0]]: 
            flage = True
            print tabs(depth), depth, ':', to_string(head)
        proc = exps.pop(0)
        tmp = proc(*exps)
        if flage: print tabs(depth), depth, ': returned ', tmp
        depth += 1
        return tmp

################ parse, read, and user interaction

def read(s):
    "Read a Scheme expression from a string."
    return read_from(tokenize(s))

parse = read

def tokenize(s):
    "Convert a string into a list of tokens."
    return s.replace('(',' ( ').replace(')',' ) ').split()

def read_from(tokens):
    "Read an expression from a sequence of tokens."
    if len(tokens) == 0:
        raise SyntaxError('unexpected EOF while reading')
    token = tokens.pop(0)
    if '(' == token:
        L = []
        while tokens[0] != ')':
            L.append(read_from(tokens))
        tokens.pop(0) # pop off ')'
        return L
    elif ')' == token:
        raise SyntaxError('unexpected )')
    else:
        return atom(token)

def atom(token):
    "Numbers become numbers; every other token is a symbol."
    try: return int(token)
    except ValueError:
        try: return float(token)
        except ValueError:
            return Symbol(token)

def to_string(exp):
    "Convert a Python object back into a Lisp-readable string."
    return '('+' '.join(map(to_string, exp))+')' if isa(exp, list) else str(exp)

def repl(prompt='lis.py> '):
    "A prompt-read-eval-print loop."
    print ";; LITHP ITH LITHTENING ...(v0.1)"
    while True:
        val = eval(parse(raw_input(prompt)))
        if val is not None: print to_string(val)
        
tabs = lambda n: '  ' * n


def sexp(s) :
  level,keep = 0,""
  while s:
    if s[0] == ";":
      while s and s[0] != "\n": s=s[1:]
      if not s: break
    if s[0] == "(": level += 1
    if level > 0  : keep += s[0]
    if s[0] == ")":  
      level -= 1
      if level==0:
        yield keep
        keep=""
    s = s[1:]
  if keep:
    yield keep


def eload(f) :
  with open(f) as contents:
    code = contents.read()
  for part in  sexp(code):
    eval(parse(part))

import sys
if len(sys.argv) > 1:
  eload(sys.argv[1])
else:
  repl()
  quit()
