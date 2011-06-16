#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import os
import cmd
import readline
import threading

import gobject
import dbus
from dbus.service import Object, BusName, signal, method
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop

def handle_hello_reply():
    print 'done'

def handle_hello_error(e):
    print "HelloWorld raised an exception! That's not meant to happen..."
    print "\t", str(e)


class Console(cmd.Cmd):

    def __init__(self, dsession, loop):
        cmd.Cmd.__init__(self)
        self.prompt = "=>> "
        self.intro  = "Welcome to console!"  ## defaults to None

        self.seq = dsession.get_object('es.ucm.Pontifex.Sequencer', '/')
        self.seq_if = dbus.Interface(self.seq, 
                                    dbus_interface='es.ucm.Pontifex.Sequencer.Console')
                                    

    def do_run(self, arg):
        """Run command"""
        self.seq_if.console('run %s' % arg, reply_handler=handle_hello_reply, error_handler=handle_hello_error)

    def do_startobsrun(self, arg):
        """Start observing run"""
        self.seq_if.console('startobsrun %s' % arg)

    def do_endobsrun(self, arg):
        """End observing run"""
        self.seq_if.console('endobsrun %s' % arg)

    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        print self._hist

    def do_exit(self, args):
        """Exits from the console"""
        return -1

    ## Command definitions to support Cmd object functionality ##
    def do_EOF(self, args):
        """Exit on system end of file character"""
        return self.do_exit(args)

    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'"""
        os.system(args)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   ## sets up command completion
        self._hist    = []      ## No history yet
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print "Exiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def emptyline(self):    
        """Do nothing on empty input line"""
        pass

    def default(self, line):       
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        try:
            exec(line) in self._locals, self._globals
        except Exception, e:
            print e.__class__, ":", e

if __name__ == '__main__':
    dbus_loop = DBusGMainLoop()
    dsession = SessionBus(mainloop=dbus_loop)

    loop = gobject.MainLoop()
    gobject.threads_init()
    #dbus.set_default_main_loop(loop)
    console = Console(dsession, loop)

    def fun():
        console.cmdloop()
        loop.quit()

    td = threading.Thread(target=fun)
    td.start()
    
    try:
        loop.run()
    except KeyboardInterrupt:
        console.do_exit(None)

