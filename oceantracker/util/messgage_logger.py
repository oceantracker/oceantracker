from os import path, remove
import traceback
from time import  perf_counter
from oceantracker.common_info_default_param_dict_templates import docs_base_url
import difflib
from oceantracker.util.parameter_base_class import ParameterBaseClass
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

class MessageLogger(object):
    def __init__(self, screen_tag = 'T',max_warnings = 50):
        self.screen_tag = screen_tag + ':'
        self.max_warnings = max_warnings
        self.fatal_error_count = 0
        self.warnings_list=[]
        self.errors_list=[]
        self.notes_list = []
        self.log_file = None
        self.error_warning_count = 0

        # build links lookup
        link_map= [['parameter_ref_toc', 'info/parameter_ref/parameter_ref_toc.html'],
                   ['release_groups', 'info/parameter_ref/release_groups_toc.html'],
                   ['howto_release_groups', 'info/how_to/C_release_groups.html']
                    ]
        self.links={}
        for l in link_map:
            self.links[l[0]]= docs_base_url + l[1]


    def set_up_files(self,run_output_dir,output_file_base):

        # log file
        log_file_name = output_file_base + '_log.txt'
        self.log_file_name = path.join(run_output_dir, log_file_name)
        self.log_file= open(self.log_file_name, 'w')

        # kill any old error file
        error_file_name = output_file_base+ '.err'
        self.error_file_name = path.join(run_output_dir, error_file_name)
        if path.isfile(self.error_file_name ):
            remove(self.error_file_name)

        return  log_file_name, error_file_name

    #todo add abilty to return excecption/traceback?
    def msg(self, msg_text, warning=False, note=False,
            hint=None, tag=None, tabs=0, crumbs='', link=None,caller=None,
            fatal_error=False, exit_now=False, exception = None, traceback_str=None, dev=False):

        if exception is not None:
            fatal_error = True
            exit_now = True

        if fatal_error: self.fatal_error_count +=1

        m = ['']
        if dev: m[0] +='Core developer '
        # first line of message
        if fatal_error:
            m[0] += msg_str( '>>> Error: ', tabs)
            self.error_warning_count += 1

        elif warning:
            m[0] += msg_str('>>> Warning: ' , tabs)
            self.error_warning_count += 1
        elif note:
            m[0] += msg_str('>>> Note: ', tabs)
        else:
            m[0] += msg_str('', tabs)

        if exception is not None:
            m[0] += msg_str('exception >>: ' + str(exception), tabs+2)

        if traceback_str is not None:
            m[0] += msg_str('traceback >>: ' + str(traceback_str), tabs + 2)

        m[0] +=  msg_text

        # first line complete
        if hint is not None:
            m.append(msg_str('hint: ' + hint, tabs + 3))
        # make crumb trail
        if crumbs is not None and crumbs != '':
            m.append(msg_str(f'in: {crumbs}', tabs + 3))

        if fatal_error and caller is not None:
            if hasattr(caller,'__class__'):
                origin=  f' {caller.__class__.__name__}'
                if isinstance(caller,ParameterBaseClass):
                    # add internal name if not None
                    origin +=  ' ' if caller.info["name"] is None else f'"{caller.info["name"]}"'
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
            if warning :
                if len(self.warnings_list) <= self.max_warnings:
                    self.warnings_list.append(l)
            if note:
                if len(self.notes_list) <= self.max_warnings:
                    self.notes_list.append(l)

        # todo add traceback to message?
        if exit_now:
            raise GracefulError('Fatal error cannot continue')


    def has_fatal_errors(self): return  self.fatal_error_count > 0

    def exit_if_prior_errors(self,msg=None):
        if self.has_fatal_errors():
            self.print_line()
            self.msg('>>> Fatal errors, can not continue')
            for m in self.errors_list:
                self.msg(m)
            self.print_line()
            raise GracefulError('Fatal error cannot continue >>> ' +msg if msg is not None else '', hint='Check above or run.err file for errors')

    def print_line(self):
        self.msg('--------------------------------------------------------------------------')

    def progress_marker(self, msg, tabs=0, start_time=None):
        tabs= tabs+1
        # add completion time if start given
        if start_time is not None:
            msg = f' {msg},\t  {perf_counter()-start_time:1.3f} sec'
            tabs += 2

        self.msg('- ' + msg, tabs=tabs)

    def show_all_warnings_and_errors(self):

        for t in [self.notes_list, self.warnings_list, self.errors_list]:
            for l in t:
                print(self.screen_tag + ' ' + l)
                if self.log_file is not None:
                    self.log_file.write(l + '\n')

    def write_error_log_file(self, e=None):

        if self.log_file is None : return

        with open(path.normpath(self.error_file_name),'w') as f:
            f.write('_____ Known warnings and Errors ________________________________\n')
            for t in [self.notes_list, self.warnings_list, self.errors_list]:
                for l in t:
                    print(self.screen_tag + ' ' + l)
                    if self.log_file is not None:
                        self.log_file.write(l + '\n')


            f.write('________Trace back_____________________________\n')

            if e is not None:
                f.write(str(e))
                self.msg(str(e))
                s = traceback.format_exc()
                f.write(s)
                self.msg(s)

    def spell_check(self, msg, value: str, possible_values: list, **kwargs):
        ''' Makes suggestion by spell checking value against strings in list of possible_values'''

        if 'fatal_error' not in kwargs: kwargs['warning']= True
        if 'exit_now' not in kwargs: kwargs['warning'] = True
        msg = msg + f'. The "{value}" is not recognised, '
        self.msg(msg,
                 hint=f'"Closest matches to "{value}" = {difflib.get_close_matches(value, list(possible_values), cutoff=0.4)} ?? ',
                  **kwargs)

    def close(self):
        if self.log_file is not None: self.log_file.close()