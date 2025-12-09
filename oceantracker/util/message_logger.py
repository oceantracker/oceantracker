from os import path, remove
import traceback
from time import  perf_counter
from oceantracker.definitions import docs_base_url
import difflib
from time import sleep
import inspect
import shutil


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

        self.error_file_name = 'error_warnings.err'

    def reset(self):

        self.msg_lists = dict(fatal_error=[],error=[],warning=[],  strong_warning=[],note=[])

        self.log_file = None
        self.max_warnings = 25


    def settings(self, max_warnings=None):
        self.max_warnings = None if max_warnings is None else 25
    def set_screen_tag(self, screen_tag:str): self.screen_tag = screen_tag + ':'

    def set_max_warnings(self, n:int): self.max_warnings = n

    def set_up_files(self, si):
        # log file set up
        log_file_name = si.run_info['output_file_base'] + '_log.txt'
        self.log_file_name = path.join(si.run_info.root_output_dir, log_file_name)

        if si.run_info.restarting:
            shutil.copyfile(si.restart_info['log_file'],self.log_file_name)
            self.log_file = open(self.log_file_name, 'a')
            self.msg('>>>> restarting log file')
        else:
            self.log_file = open(self.log_file_name, 'w')

        # kill any old error file
        error_file_name = path.join(si.run_info.root_output_dir, self.error_file_name)
        if path.isfile(error_file_name ):
            remove(error_file_name)

        return  log_file_name, self.error_file_name

    def msg(self, msg_text, note=False,
            hint=None, tag=None, tabs=0, crumbs='', link=None,caller=None,
            possible_values=None, warning=False,strong_warning=False,
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
            self._add_to_msg_list('error', msg_text, hint, crumbs, caller)

        elif warning:
            m= self._append_message(m,'>>> Warning: ' + msg_text, tabs)
            if  len(self.msg_lists['warning']) > self.max_warnings: return
            self._add_to_msg_list('warning', msg_text, hint, crumbs, caller)
        elif strong_warning:
            m = self._append_message(m, '>>> Strong warning: ' + msg_text, tabs)
            if len(self.msg_lists['strong_warning']) > self.max_warnings: return
            self._add_to_msg_list('strong_warning', msg_text, hint, crumbs, caller)

        elif note:
            m= self._append_message(m, '>>> Note: ' + msg_text, tabs)
            if len(self.msg_lists['note']) > self.max_warnings: return
            self._add_to_msg_list('note', msg_text, hint, crumbs, caller)

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
                origin=  f'Class = "{caller.__class__.__name__}" '
                if hasattr(caller,'info'):
                    # add internal name if not None
                    origin += f'role="{caller.info["class_role"]}"' if 'class_role' in caller.info else ''
                    origin +=  ' ' if 'name' not in caller.params or caller.params["name"] is None else f', name="{caller.params["name"]}"'
                    origin += f', instance #[{caller.info["instanceID"]}]'
                origin += f', class= "{caller.__class__.__module__}.{caller.__class__.__name__}"'

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

        # todo add traceback to message?
        if fatal_error:
            self._add_to_msg_list('fatal_error', msg_text, hint, crumbs, caller)
            raise OTerror('Fatal error cannot continue')
        pass
    def _append_message(self, m, msg, tabs):
        # append allowing  line breaks
        tab = '  '
        for n, s in enumerate(msg.split('\n')):
            m += (tabs + int(n > 0))*tab + s + '\n'
        return m

    def has_errors(self): return  len(self.msg_lists['error']) > 0

    def exit_if_prior_errors(self,msg, caller=None, crumbs=''):
        if self.has_errors():
            self.hori_line()
            self.msg(msg + '>>> Fatal errors, can not continue', crumbs= crumbs, caller=caller)
            self.show_all_strong_warnings_and_errors()
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

    def show_all_strong_warnings_and_errors(self):
        for m in self.msg_lists['strong_warning']+ self.msg_lists['error']+ self.msg_lists['fatal_error']:

            self.msg(m['msg'],hint= m['hint'],caller=m['caller'],crumbs=m['crumbs'])


    def write_error_log_file(self, e, si):
        sleep(.5)
        self.msg(str(e))
        tb = traceback.format_exc()
        self.msg(tb)
        if si.run_info.root_output_dir is None: return # no folder to write to

        error_file_name = path.join(si.run_info.root_output_dir, self.error_file_name)
        with open(path.normpath(error_file_name),'w') as f:
            f.write('_____ Known warnings and Errors ________________________________\n')
            for l, ml in self.msg_lists.items():
                for m in ml:
                    f.write( f'{l} >>> {m["msg"]} \n')
                    f.write(f'\t\t hint  : {m["hint"]}\n')
                    f.write(f'\t\t crumbs: {m["crumbs"]} \n')
                    f.write(f'\t\t caller: {m["caller"]} \n')

            f.write('________Trace back_____________________________\n')
            f.write(str(e))
            f.write(tb)

    def spell_check(self, msg, key: str, possible_values: list,hint=None, tabs=0, crumbs='', caller=None, link=None):
        ''' Makes suggestion by spell checking value against strings in list of possible_values'''

        known = list(possible_values)
        if key not in known:
            # flag if unknown
            self.msg(msg)

            self.msg(f'Closest matches to "{key}" are :',tabs=tabs +5)
            o = difflib.get_close_matches(key, known, cutoff=0.5, n=4)
            if len(o) > 0:
                for n ,t in enumerate(o):
                    self.msg(f'{n+1}: "{t}"',tabs=tabs+7)
            else:
                self.msg(f'>> None found',tabs=tabs+7,
                         hint=f'Possible values = {str(known)}')
            self.msg('Unknown  values', hint=hint, fatal_error=True, tabs=tabs,crumbs=crumbs,caller=caller)

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

    def save_state(self,si,state_dir):
        self.log_file.close()
        # save log file
        state_log = path.join(state_dir,'log_file.txt')
        shutil.copyfile(path.join(si.run_info.root_output_dir, si.output_files['run_log']),
                        state_log)

        self.log_file = open(self.log_file_name, 'a')

        return state_log

    def close(self):
        if self.log_file is not None:
            self.log_file.close()
            self.log_file = None


    def _add_to_msg_list(self,msg_type,msg,hint,crumbs, caller):
        self.msg_lists[msg_type].append(
            dict(msg=msg, hint=hint, crumbs=crumbs, caller=str(caller))
        )