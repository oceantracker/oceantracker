from os import path, remove
import traceback
from time import  perf_counter
from oceantracker.definitions import docs_base_url
import difflib
from time import sleep
import inspect

class OTerror(Exception):
    def __init__(self, message='-no error message given',hint=None):
        # Call the base class constructor with the parameters it needs
        msg= 'Error >> ' + message + '\n hint= ' + hint if hint is not None else ' Look at messages above or in .err file'
        super(OTerror, self).__init__(msg)

class OTfatal_error(OTerror): pass
class OTunexpected_error(OTerror): pass

class MessageLogger(object ):
    def __init__(self):


        self.reset()
        self.set_screen_tag('prelim')

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
        self.max_warnings = 25


    def settings(self, max_warnings=None):
        self.max_warnings = None if max_warnings is None else 25
    def set_screen_tag(self, screen_tag:str): self.screen_tag = screen_tag + ':'

    def set_max_warnings(self, n:int): self.max_warnings = n

    def set_up_files(self, run_output_dir, output_file_base, append=False):
        # log file

        log_file_name = output_file_base + '.txt'
        self.log_file_name = path.join(run_output_dir, log_file_name)

        self.log_file = open(self.log_file_name, 'w')

        # kill any old error file
        error_file_name = 'error_warnings.err'
        self.error_file_name = path.join(run_output_dir, error_file_name)
        if path.isfile(self.error_file_name ):
            remove(self.error_file_name)

        return  log_file_name, error_file_name

    def msg(self, msg_text, warning=False, note=False,
            hint=None, tag=None, tabs=0, crumbs='', link=None,caller=None,
            spell_check=None,possible_values=None,
            error=False, fatal_error=False, exception = None,
            traceback_str=None, dev=False):
        
        if exception is not None:
            fatal_error = True
        if fatal_error: error = True

        m = ''
        if dev: m +='Core developer:'
        # first line of message
        if error:
            m = self._append_message(m, '>>> Error: ' + msg_text, tabs)
            self.error_count += 1

        elif warning:
            m= self._append_message(m,'>>> Warning: ' + msg_text, tabs)
            self.warning_count += 1
            if self.warning_count > self.max_warnings: return

        elif note:
            m= self._append_message(m, '>>> Note: ' + msg_text, tabs)
            self.note_count += 1
            if self.note_count > self.max_warnings: return

        else:
            m = self._append_message(m, msg_text, tabs)

        if exception is not None:
            m = self._append_message(m, 'exception >>: ' + str(exception), tabs + 2)

        if traceback_str is not None:
            m = self._append_message(m, 'traceback >>: ' + str(traceback_str), tabs + 2)

        # first line complete
        if hint is not None:
            m = self._append_message(m, 'hint: ' + hint, tabs+2)

        # make crumb trail
        if crumbs is not None and crumbs != '':
            m =self._append_message(m, f'in: {crumbs}', tabs + 3)

        if caller is not None and (error or warning) :
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
            m = self._append_message(m, f'caller: {origin}', tabs + 3)

        if link is not None:
            m= self._append_message(m, 'see user documentation: ' + self.links[link], tabs + 3)

        pass
        # write message lines

        for l in  m.split('\n')[:-1]: # drop last \n
            ll = self.screen_tag + ' ' + l
            print(ll)
            if self.log_file is not None:
                self.log_file.write(ll + '\n')

        # keep list ond warnings errors etc to print at end
        if error:  self.errors_list.append(m)
                #self.build_stack()
        if warning: self.warnings_list.append(m)
        if note:self.notes_list.append(m)

        # todo add traceback to message?
        if fatal_error:
            raise OTerror('Fatal error cannot continue')
        pass
    def _append_message(self, m, msg, tabs):
        # append allowing  line breaks
        tab = '  '
        for n, s in enumerate(msg.split('\n')):
            m += (tabs + int(n > 0))*tab + s + '\n'
        return m

    def has_errors(self): return  self.error_count > 0

    def exit_if_prior_errors(self,msg, caller=None, crumbs=''):
        if self.has_errors():
            self.hori_line()
            self.msg(msg + '>>> Fatal errors, can not continue', crumbs= crumbs, caller=caller)
            for m in self.errors_list:
                self.msg(m)
            self.hori_line()
            sleep(1) # allow time for messages to print
            raise OTerror('Fatal error cannot continue >>> ' + msg if msg is not None else '', hint='Check above or run.err file for errors')

    def hori_line(self, text=None):
        n= 70
        if text is None:
            self.msg(n*'-')
        else:
            self.msg(f"--- {text} {(n-len(text) -5)*'-'}")

    def progress_marker(self, msg, tabs=0, start_time=None):
        tabs= tabs+1
        # add completion time if start given
        if start_time is not None:
            msg = f'{msg},\t  {perf_counter()-start_time:1.3f} sec'

        self.msg('- ' + msg, tabs=tabs)

    def show_all_warnings_and_errors(self):
        for t in [self.warnings_list, self.errors_list]:
            tt= list(set(t))
            for m in tt:
                for l in m.split('\n'):
                    print(self.screen_tag + ' ' + l)
                    if self.log_file is not None:
                        self.log_file.write(l + '\n')

    def write_error_log_file(self, e):
        sleep(.5)
        self.msg(str(e))
        tb = traceback.format_exc()
        self.msg(tb)

        with open(path.normpath(self.error_file_name),'w') as f:
            f.write('_____ Known warnings and Errors ________________________________\n')
            for t in [self.notes_list, self.warnings_list, self.errors_list]:
                for l in t:
                    f.write(self.screen_tag + ' ' + l + '\n')

            f.write('________Trace back_____________________________\n')
            f.write(str(e))
            f.write(tb)

    def spell_check(self, msg, key: str, possible_values: list,hint=None, **kwargs):
        ''' Makes suggestion by spell checking value against strings in list of possible_values'''

        if 'error' not in kwargs: kwargs['warning']= True
        if 'fatal_error' not in kwargs: kwargs['warning'] = True
        if 'tabs' not in kwargs: kwargs['tabs'] = 0


        if hint is None : hint= ''
        known = list(possible_values)
        if key not in known:
            # flag if unknown
            self.msg(msg, **kwargs)
            self.msg(f'Closest matches to "{key}" are :',tabs=kwargs['tabs']+5)
            for n ,t in enumerate(difflib.get_close_matches(key, known, cutoff=0.4)):
                self.msg(f'{n+1}: "{t}"',tabs=kwargs['tabs']+7)

        pass
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