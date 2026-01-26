from os import path, remove
from time import  perf_counter
from oceantracker.definitions import docs_base_url
import difflib
from time import sleep
import inspect
import shutil, traceback, inspect
from copy import deepcopy
import textwrap

class OTinput_error(Exception):
    def __init__(self, message='-no error message given',hint=None):
        # Call the base class constructor with the parameters it needs
        msg= 'Error >> ' + message + '\n hint= ' + hint if hint is not None else ' Look at messages above or in .err file'
        super(OTinput_error, self).__init__(msg)

class OTfatal_error(OTinput_error): pass
class OTunexpected_error(OTinput_error): pass

msg_types_template = dict(fatal_error=[],error=[],warning=[],  strong_warning=[],note=[],deprecated=[])
class MessageLogger(object ):
    def __init__(self):


        self.reset()
        self.set_screen_tag('prelim')
        self.error_file_name = 'error_warnings.err'
        self.line_length = 100
        self.hang_indent=2

    def reset(self):

        self.msg_lists = deepcopy(msg_types_template)

        self.log_file = None
        self.max_warnings = 25

    def settings(self, max_warnings=None):
        self.max_warnings = None if max_warnings is None else 25
    def set_screen_tag(self, screen_tag:str): self.screen_tag = screen_tag + ':'

    def set_max_warnings(self, n:int): self.max_warnings = n

    def set_up_files(self, si):
        # log file set up
        log_file_name = 'run_log.txt'
        self.log_file_name = path.join(si.output_files['run_output_dir'], log_file_name)

        if si.run_info.restarting or si.run_info.continuing:
            shutil.copyfile(si.saved_state_info['log_file'],self.log_file_name)
            self.log_file = open(self.log_file_name, 'a')
            self._print_msg('>>>> restarting log file')
        else:
            self.log_file = open(self.log_file_name, 'w')

        # kill any old error file
        error_file_name = path.join(si.output_files['run_output_dir'], self.error_file_name)
        if path.isfile(error_file_name ):
            remove(error_file_name)

        return  log_file_name, self.error_file_name

    def msg(self, msg_text, note=False,
            hint=None, tag=None, tabs=0, link=None,caller=None,wrap=False,
            warning=False,strong_warning=False, error=False, fatal_error=False,
            dev=False):

        error = error or fatal_error

        m = tabs*'\t' +''
        if dev: m +='Core developer:'

        # first line of message
        if error:
            m = self._build_msg(msg_text,msg_tag='Error', hint=hint,add_trace=True,caller=caller, wrap=True)
            self.msg_lists['error'].append(m)

        elif warning:
            if  len(self.msg_lists['warning']) > self.max_warnings: return
            m = self._build_msg(msg_text, msg_tag='Warning', hint=hint, add_trace=False,caller=caller, wrap=True)
            self.msg_lists['warning'].append(m)

        elif strong_warning:
            if len(self.msg_lists['warning']) > self.max_warnings: return
            m = self._build_msg(msg_text, msg_tag='Strong warning', hint=hint, add_trace=True,caller=caller, wrap=True)
            self.msg_lists['strong_warning'].append(m)

        elif note:
            if len(self.msg_lists['note']) > self.max_warnings: return
            m = self._build_msg(msg_text, msg_tag='Note', hint=hint, add_trace=False,caller=caller, wrap=True)
            self.msg_lists['note'].append(m)

        else:
            m = self._build_msg(msg_text, msg_tag=None, hint=hint, add_trace=False, wrap=wrap)


        # write message
        self._print_msg(m)

        if error: raise OTinput_error('Fatal error cannot continue')
        pass


    def hori_line(self, text=None):
        if text is None:
            self._print_msg(self.line_length *'-')
        else:
            self._print_msg(f"--- {text} {(self.line_length-len(text) -5)*'-'}")

    def progress_marker(self, msg, tabs=0, start_time=None):
        tabs= tabs+1
        # add completion time if start given
        if start_time is not None:
            msg = f'{msg},\t  {perf_counter()-start_time:1.3f} sec'

        self._print_msg(  tabs*'\t'+ '- ' + msg)

    def show_all_strong_warnings_and_errors(self):
        for m in self.msg_lists['strong_warning']+ self.msg_lists['error']+ self.msg_lists['fatal_error']:
            self._print_msg(m)

    def write_error_log_file(self, e, si):
        sleep(.5)
        self._print_msg(str(e))
        tb = traceback.format_exc()
        self._print_msg(tb)
        if si.run_info.run_output_dir is None: return # no folder to write to

        error_file_name = path.join(si.run_info.run_output_dir, self.error_file_name)
        with open(path.normpath(error_file_name),'w') as f:
            f.write('_____ Known warnings and Errors ________________________________\n')
            for l, ml in self.msg_lists.items():
                for m in ml:
                    f.write( m)
            f.write('________Trace back_____________________________\n')
            f.write(str(e))
            f.write(tb)

    def spell_check(self, msg, key: str, possible_values: list,hint=None, tabs=0, caller=None, link=None,
                    fatal_error=True):
        ''' Makes suggestion by spell checking value against strings in list of possible_values'''
        known = list(possible_values)
        if key in known : return

        m = 'Error >>>' + msg
        hand_indent = 2
        off = '\n' + 2 * hand_indent * '\t'
        if caller is not None:
            m += off + f'{self._get_caller_info(caller)}'


        # flag if unknown
        m += off + f'Closest matches to "{key}" are :'
        o = difflib.get_close_matches(key, known, cutoff=0.5, n=4)
        if len(o) > 0:
            for n ,t in enumerate(o):
                m += off + hand_indent*'\t'+ f'{n+1}: "{t}"'
        else:
            m += off+ f'>> None found'
            m += off + self._add_long_line(f'hint=Possible values = {str(known)}',
                                           tabs =2 * hand_indent,
                                           hand_indent=hand_indent)

        m = self._add_doc_html_link(m, caller, 2 * hand_indent)

        t = self._get_trace_back_str(tabs=3)
        m += '\n' + self._add_long_line(f'trace: {t}', tabs= 2 * hand_indent, hand_indent=hand_indent, wrap=True)

        self.msg_lists['error'].append(m)
        self._print_msg(m)
        self._input_error()

        pass


    def save_state(self,si,state_dir):
        self.log_file.close()
        # save log file
        state_log = path.join(state_dir,'log_file.txt')
        shutil.copyfile(path.join(si.run_info.run_output_dir, si.output_files['run_log']),
                        state_log)

        self.log_file = open(self.log_file_name, 'a')

        return state_log

    def close(self):
        if self.log_file is not None:
            self.log_file.close()
            self.log_file = None


    # utility code
    def _add_long_line(self,txt,tabs,wrap, hand_indent=2):
        #add wordrap if needed
        if not wrap: return txt

        if len(txt) == 0: return ''
        w= textwrap.wrap(txt, width=self.line_length,  initial_indent=tabs*'\t', subsequent_indent=(tabs+hand_indent)*'\t', expand_tabs=False,
                      replace_whitespace=True, fix_sentence_endings=False, break_long_words=True, drop_whitespace=True,
                      break_on_hyphens=True)
        m = ''
        for l in w[:-1]: m += l + '\n'
        m += w[-1]
        return m


    def _build_msg(self,msg, msg_tag=None,hint=None,add_trace=False,caller=None, wrap = False):

        m = f'{msg_tag} >>> ' if msg_tag is not None else ''
        m += self._add_long_line(msg,tabs=0, hand_indent=4, wrap= wrap)


        if caller is not None:
            m += '\n'+ 2*self.hang_indent*'\t' + f'{self._get_caller_info(caller)}'

        if hint is not None:
            m += '\n'+ self._add_long_line(f'hint: {hint}',tabs=4, hand_indent=4,wrap = True)

        m = self._add_doc_html_link(m, caller, 3)

        if add_trace:
            t = self._get_trace_back_str(tabs=3)
            m += '\n' + self._add_long_line(f'trace: {t}', tabs=6, hand_indent=2,wrap=True)
        return m

    def _print_msg(self,msg):
        # write message lines
        txt= f'{self.screen_tag} {msg}'
        print(txt)
        if self.log_file is not None:
            self.log_file.write(txt + '\n')

    def _get_caller_info(self,caller):
        if caller is not None:
            if hasattr(caller, '__class__'):
                origin = f'In:  role = "{caller.role_name if hasattr(caller, "role_name") else "??"}"'
                origin += f', class_name = "{caller.__class__.__name__}"'
                origin += f' \t   ({caller.__class__.__module__}.{caller.__class__.__name__})'
            else:
                origin = caller.__name__
            return  origin

    def _add_doc_html_link(self,m, caller,tabs):
        import requests
        if caller is  None or not  hasattr(caller, '__class__'):  return m

        role= caller.role_name if hasattr(caller, "role_name") else None
        name =  caller.__class__.__name__

        # https://oceantracker.github.io/oceantracker/documentation/api_ref/dispersion_toc.html
        # add class link
        url = f'{docs_base_url}/documentation/api_ref/{name}.html'
        response = requests.get(f'{docs_base_url}/documentation/api_ref/{name}.html' )
        if response.status_code == 200:
            m+= '\n' + tabs*'\t' + f'Docs for "{name}": {url}'

        url = f'{docs_base_url}/documentation/api_ref/{role}_toc.html'
        response = requests.get(f'{docs_base_url}/documentation/api_ref/{name}.html')
        if response.status_code == 200:
            m += '\n' + tabs * '\t' + f'Other classes in role "{role}": {url}'

        return m




    def _get_trace_back_str(self,tabs=0):

        s = inspect.stack()
        trail = []
        for l in list(s):
            d = dict(file_name=l.filename, line=l.lineno,function= l.function, )
            if 'oceantracker' in d['file_name']: trail.append(d)
        pass

        result=''
        for  count, f in enumerate(trail[3:-2]):
            if (count+1) % 7 == 0 :
                result +='\n' + ((count % 7))*'\t'
            result += f'{f["function"]} ({f["line"]}) < '

        return result

    def _input_error(self):
        raise( OTinput_error('Fatal input errors cannot continue'))










