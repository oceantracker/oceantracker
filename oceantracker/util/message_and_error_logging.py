from os import path, remove
import traceback

import numpy as np

from oceantracker.util import json_util
import logging

class GracefulExitError(Exception):
    def __init__(self, message='-no error message given'):
        # Call the base class constructor with the parameters it needs
        super(GracefulExitError, self).__init__(message)

class FatalError(Exception):
    def __init__(self, message='-no error message given'):
        # Call the base class constructor with the parameters it needs
        super(FatalError, self).__init__(message)

class MessageClass():
    def __init__(self, msg, warning=False, note=False,  hint=None, tag=None, tabs=0, exception=None,traceback_str=None, crumbs=None):
        self.text = msg
        self.is_warning = warning
        self.is_note = note
        self.is_error = exception is not None
        self.hint = hint
        self.tag = tag
        self.tabs = tabs
        self.exception = exception
        self.traceback_str = traceback_str
        self.crumbs= crumbs



    def to_str(self):
        m=''
        tabs= '  '
        if self.tag is not None: m += self.tag
        if self.exception is not None: m += 'Error raised \n' + str(self.exception)    +'\n'

        for n in range(self.tabs): m = tabs + m
        if self.is_error:  m += '>>> Error: '

        if self.exception is not None:
            m += str(self.exception) +'\n'
            if self.traceback_str is not None:
                m += str(self.traceback_str) +'\n'
        if self.is_warning: m += '>>> Warning: '
        if self.is_note: m += '>>> Note: '
        m += self.text

        if self.hint is not None:
            m_add = ''
            for n in range(self.tabs+2): m_add = tabs + m_add
            m_add += 'Hint : ' + self.hint
            m += '\n' + m_add

        if self.crumbs is not None:
            m_add = ''
            for n in range(self.tabs+2): m_add = tabs + m_add
            m_add += 'Crumb trail: ' + self.crumbs
            m += '\n' + m_add

        return m

def append_message(msg_list, msg, warning=False,note=False, hint=None, tag=None, tabs=0,exception=None,traceback_str=None, crumbs=None):
    # give consistent messaging format
    if type(msg) != list: msg=[msg]
    for m in msg:
        if type(m) ==str:
            m = MessageClass(m, warning=warning, tag=tag,note=note,
                             exception=exception, traceback_str=traceback_str,
                             tabs=tabs, hint=hint, crumbs=crumbs)
        msg_list.append(m)

    if exception is not None:
        for m in msg:
            print('Fatal error >> ' + m)
            #todo add to log file
        #raise(FatalError)

    return msg_list

class MessageLogging(object):
    def __init__(self, screen_tag):
        self.msg_list = []
        self.error_list = []

        self.screen_tag = screen_tag
        self.max_warnings= 50
        self.log_file = None
        self.last_message_displayed= 0

    def set_up_log_file(self, log_dir, log_file_base_name, file_tag):
        if log_file_base_name is None:
            self.log_file = None
        else:
            self.log_file_name =path.join(log_dir, log_file_base_name + '_' + file_tag + '.txt')
            self.log_file= open( self.log_file_name, 'w')

        # kill any old error file
        self.error_file_name = path.join(log_dir, log_file_base_name + '.err')
        if path.isfile(self.error_file_name ):
            remove(self.error_file_name )

        self.debug_data_file_name= path.join(log_dir, log_file_base_name + '_debug_variables.json')
        self.debug_data= {} # dict to write data from

    def set_max_warnings(self,n_max): self.max_warnings=n_max

    def show_latest_messages(self):
        self.add_messages(self.msg_list[self.last_message_displayed:])
        self.last_message_displayed += len(self.msg_list)

    def check_messages_for_errors(self):
        if len(self.error_list) > 0:
            raise GracefulExitError()

    def add_msg(self, msg, raiseerrors = False):
        if msg is not None:
            self.add_messages( [msg], raiseerrors = raiseerrors)

    def add_messages(self, msg_list: list, raiseerrors=False):
        if msg_list is None : return
        if type(msg_list) != list : msg_list=[msg_list]
        if  len(msg_list) == 0 :return

        has_errors = False
        for m in msg_list:
            self._log(m)
            if (m.is_warning or m.is_note) and len(self.msg_list) < self.max_warnings: self.msg_list.append(m)
            if m.is_error:
                self.error_list.append(m)
                has_errors = True
        if has_errors and raiseerrors:
            raise FatalError('Messages contain a fatal error')

    def write_msg(self, msg_text, warning=False, note=False, hint=None, tag=None, tabs=0, crumbs=None, exception=None, traceback_str=None,raiseerrors=False):
        if msg_text is not None and len(msg_text) > 0:
            m = MessageClass(msg_text, warning=warning,note=note,  exception=exception, traceback_str=traceback_str, hint=hint, tag=tag, tabs=tabs, crumbs=crumbs)
            self.add_messages([m],raiseerrors=raiseerrors)

    def write_warning(self,msg, hint=None): self.write_msg(msg, warning=True,hint=hint)

    def write_note(self, msg, hint=None):
        self.write_msg(msg, note=True, hint=hint)

    def write_progress_marker(self, msg, tabs=0):  self.write_msg('- ' + msg, tabs=tabs+1)

    def show_all_warnings_and_errors(self):
        if len(self.msg_list) > 0 or len(self.error_list)> 0:
            self.insert_screen_line()
            for m in self.msg_list: self._log(m)
            for m in self.error_list:   self._log(m)

    def get_all_warnings_and_errors(self):
        # list of all unique warnings and strings as text
        text=[]
        for m in self.msg_list: text.append(m.to_str())
        for m in self.error_list: text.append(m.to_str())
        text=list(set(text))
        return text

    def write_error_log_file(self, e=None):

        if self.log_file is None : return

        with open(path.normpath(self.error_file_name),'w') as f:
            f.write('_____Warnings ________________________________\n')
            for w in self.msg_list:
                f.write(w.to_str() +'\n')
            f.write('_____Errors ________________________________\n')
            for w in self.error_list:
                f.write(w.to_str() + '\n')

            f.write('_____________________________________\n')

            if e is not None:
                f.write(str(e))
                self.write_msg(str(e))
                s = traceback.format_exc()
                f.write(s)
                self.write_msg(s)

    def insert_screen_line(self):
        self._log(MessageClass('--------------------------------------------------------------------------'))

    def _log(self, msg):
        if (msg.is_warning or msg.is_note) and len(self.msg_list) > self.max_warnings: return
        # form string
        m= msg.to_str()
        m = m.replace('\n', '\n' + self.screen_tag)
        m = self.screen_tag + ' ' + m
        print(m)

        if self.log_file is not None:
            self.log_file.write(m + '\n')

    def _append_debug_varaiable_data(self,varname, data):
        if varname not in self.debug_data:
            if isinstance(data, np.ndarray):
                self.debug_data[varname]= data
            else:
                self.debug_data[varname]=[]
        else:
            if isinstance(data,np.ndarray):
                self.debug_data[varname]= np.concatenate((self.debug_data[varname], data), axis=0)
            else:
                self.debug_data[varname].append(data)

    def close(self):
        if self.log_file is not None: self.log_file.close()

        # put out added debug data
        if len(self.debug_data) > 0:
            json_util.write_JSON(self.debug_data_file_name, self.debug_data)
