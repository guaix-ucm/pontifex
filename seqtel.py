import corre

class TestObsModParser:
    def bias(self, args):
        return 'test', 'bias', 0, None, int(args[0])
    def dark(self, args):
        return 'test', 'dark', float(args[0]), None, int(args[1])

ot = TestObsModParser()

def run_obsmode(args):
    repeat = 0
    argslist = args.split()
    assert len(argslist) > 2

    fun = getattr(ot, argslist[1])

    pars = fun(argslist[2:])
    corre.exec_obsmode(*pars)
