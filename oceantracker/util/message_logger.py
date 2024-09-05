from os import path, remove
import traceback
from time import  perf_counter
from oceantracker.definitions import docs_base_url
import difflib
from time import sleep
import inspect

class GracefulError(Exception):
    def __init__(self, message='-no error message given',hint=None):
        # Call the base class constructor with the parameters it needs
        msg= 'Error >> ' + message + '\n hint= ' + hint if hint is not None else ' Look at messages above or in .err file'
        super(GracefulError, self).__init__(msg)



def msg_str(msg,tabs=0):
    tab = '  '
    m = ''
    for n in range(tabs): m += tab
    m +=  msg
    return m

class MessageLogger(object ):
    def __init__(self):


        self.reset()

        # build links lookup
        link_map= [['parameter_ref_toc', 'info/parameter_ref/parameter_ref_toc.html'],
                   ['release_groups', 'info/parameter_ref/release_groups_toc.html'],
                   ['howto_release_groups', 'info/how_to/C_release_groups.html']
                    ]
        self.links={}
        for l in link_map:
            self.links[l[0]]= docs_base_url + l[1]

    def reset(self):

        self.warnings_list=[]
        self.errors_list=[]
        self.notes_list = []
        self.log_file = None
        self.error_count = 0
        self.warning_count = 0
        self.note_count = 0
        self.screen_tag = 'prelim:'
        self.max_warnings = 25


    def settings(self, max_warnings=None):
        self.max_warnings = None if max_warnings is None else 25
    def set_screen_tag(self, screen_tag:str): self.screen_tag = screen_tag
    def set_max_warnings(self, n:int): self.max_warnings = n

    def set_up_files(self, run_output_dir, output_file_base, append=False):
        # log file

        log_file_name = output_file_base + '.txt'
        self.log_file_name = path.join(run_output_dir, log_file_name)

        self.log_file = open(self.log_file_name, 'w')

        # kill any old error file
        error_file_name = output_file_base+ '.err'
        self.error_file_name = path.join(run_output_dir, error_file_name)
        if path.isfile(self.error_file_name ):
            remove(self.error_file_name)

        return  log_file_name, error_file_name

    def msg(self, msg_text, warning=False, note=False,
            hint=None, tag=None, tabs=0, crumbs='', link=None,caller=None,
            spell_check=None,possible_values=None,
            fatal_error=False, exit_now=False, exception = None,
            traceback_str=None, dev=False):


        if exit_now : fatal_error = True
        if exception is not None:
            fatal_error = True
            exit_now = True


        m = ['']
        if dev: m[0] +='Core developer '
        # first line of message
        if fatal_error:
            m[0] += msg_str( '>>> Error: ', tabs)
            self.error_count += 1

        elif warning:
            m[0] += msg_str('>>> Warning: ' , tabs)
            self.warning_count += 1
        elif note:
            m[0] += msg_str('>>> Note: ', tabs)
            self.note_count += 1

        else:
            m[0] += msg_str('', tabs)

        if exception is not None:
            m[0] += msg_str('exception >>: ' + str(exception), tabs+2)

        if traceback_str is not None:
            m[0] += msg_str('traceback >>: ' + str(traceback_str), tabs + 2)

        m[0] +=  msg_text

        # first line complete
        if hint is not None:
            if '\n' in hint:
                # multi line hint
                for l in hint.split('\n'):
                    m.append(msg_str('hint: ' + l, tabs + 3))
            else:
                m.append(msg_str('hint: ' + hint, tabs + 3))

        if spell_check is not None:
           m.append(f'\n Closest matches to "{spell_check}" = {difflib.get_close_matches(spell_check, possible_values, cutoff=0.4)}')

        # make crumb trail
        if crumbs is not None and crumbs != '':
            m.append(msg_str(f'in: {crumbs}', tabs + 3))

        if caller is not None and (fatal_error or warning) :
            if hasattr(caller,'__class__'):
                origin=  f'Class = {caller.__class__.__name__} '
                if hasattr(caller,'info'):
                    # add internal name if not None
                    origin += f'role="{caller.info["class_role"]}"' if 'class_role' in caller.info else ''
                    origin +=  ' ' if 'name' not in caller.params or caller.params["name"] is None else f', name="{caller.params["name"]}"'
                    origin += f', instance #[{caller.info["instanceID"]}]'
                origin += f', class= {caller.__class__.__module__}.{caller.__class__.__name__} '

            else:
                origin = caller.__name__
            m.append(msg_str(f'caller: {origin}', tabs + 3))



        if link is not None:
            m.append(msg_str('see user documentation: ' + self.links[link], tabs + 3))

        # write message lines
        for l in m:
            ll = self.screen_tag + ' ' + l
            print(ll)
            if self.log_file is not None:
                self.log_file.write(ll + '\n')

            # keeplist ond warnings errors etc to print at end
            if fatal_error:
                    self.errors_list.append(l)
                    #self.build_stack()
            if warning :
                if len(self.warnings_list) <= self.max_warnings:
                    self.warnings_list.append(l)
            if note:
                if len(self.notes_list) <= self.max_warnings:
                    self.notes_list.append(l)

        # todo add traceback to message?
        if exit_now:
            raise GracefulError('Fatal error cannot continue')


    def has_fatal_errors(self): return  self.error_count > 0

    def exit_if_prior_errors(self,msg, caller=None, crumbs=''):
        if self.has_fatal_errors():
            self.print_line()
            self.msg(msg + '>>> Fatal errors, can not continue', crumbs= crumbs, caller=caller)
            for m in self.errors_list:
                self.msg(m)
            self.print_line()
            sleep(1) # allow time for messages to print
            raise GracefulError('Fatal error cannot continue >>> ' +msg if msg is not None else '', hint='Check above or run.err file for errors')

    def print_line(self, text=None):
        n= 70
        if text is None:
            self.msg(n*'-')
        else:
            self.msg(f"--- {text} {(n-len(text) -5)*'-'}")

    def progress_marker(self, msg, tabs=0, start_time=None):
        tabs= tabs+1
        # add completion time if start given
        if start_time is not None:
            msg = f' {msg},\t  {perf_counter()-start_time:1.3f} sec'
            tabs += 1

        self.msg('- ' + msg, tabs=tabs)

    def show_all_warnings_and_errors(self):

        for t in [self.notes_list, self.warnings_list, self.errors_list]:
            for l in t:
                print(self.screen_tag + ' ' + l)
                if self.log_file is not None:
                    self.log_file.write(l + '\n')

    def write_error_log_file(self, e,traceback_str):
        sleep(.5)
        with open(path.normpath(self.error_file_name),'w') as f:
            f.write('_____ Known warnings and Errors ________________________________\n')
            for t in [self.notes_list, self.warnings_list, self.errors_list]:
                for l in t:
                    f.write(self.screen_tag + ' ' + l + '\n')

            f.write('________Trace back_____________________________\n')
            f.write(str(e))
            f.write(traceback_str)


    def spell_check(self, msg, key: str, possible_values: list,hint=None, **kwargs):
        ''' Makes suggestion by spell checking value against strings in list of possible_values'''

        if 'fatal_error' not in kwargs: kwargs['warning']= True
        if 'exit_now' not in kwargs: kwargs['warning'] = True
        msg = msg + f', parameter "{key}" is not recognised, '
        if hint is None : hint= ''
        known = list(possible_values)
        if key not in known:
            # flag if unknown
            self.msg(msg,  hint=hint + f'\n Closest matches to "{key}" = {difflib.get_close_matches(key, known, cutoff=0.4)} ?? ',
                  **kwargs)

    def build_stack(self):

        #todo useful to print crumbs automatically?
        stack = inspect.stack(1)
        #stack = [l for l in stack if path.basename(l[1]) not in ['message_logger.py','main.py']]
        stack.reverse()
        stack = [l for l in stack if 'oceantracker' in path.dirname(l[1])]
        msg = ''
        for n, l in enumerate(stack[-6:-2]):
            msg +=  f'{path.basename(l[1])}#{l[2]}-.{l[3]}()>\n\t\t'+ n*'\t'
        self.msg('Traceback > '+ msg)
        pass

    def close(self):
        if self.log_file is not None:
            self.log_file.close()
            self.log_file = None