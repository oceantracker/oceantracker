import time
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
        self.hint = hint
        self.tag = tag
        self.tabs = tabs
        self.exception = exception
        self.traceback_str = traceback_str
        self.crumbs= crumbs

    def to_str_list(self):
        m=[]
        t = self.tabs
        if self.exception is not None:
            append_msg_str(m,'>>> Error: ' + self.text , t)
        elif self.is_warning:
            append_msg_str(m,'>>> Warning: '+ self.text, t)
        elif self.is_note:
            append_msg_str(m,'>>> Note: ' + self.text, t)
        else:
            append_msg_str(m,self.text,t)

        if self.crumbs is not None:
            append_msg_str(m, 'In: ' + self.crumbs, t + 1)

        if self.hint is not None:
            append_msg_str(m, 'Hint: ' + self.hint , t+2)

        if self.exception is not None:
            if self.exception == GracefulExitError:
                append_msg_str(m, ' Graceful exit error =' + str(self.exception), t+1)
            else:
                append_msg_str(m, '>>> Fatal Error', t + 2)
                for s in traceback.format_list(traceback.extract_stack())[:-2]:
                    ss=s.split(' line ')
                    append_msg_str(m, ss[0].replace('\n',''), t+2)
                    append_msg_str(m, '  line ' +ss[-1].replace('\n',''),t+3)
        return m

def append_msg_str(msg_list,text, tabs=0):
    tab = '  '
    m = ''
    for n in range(tabs): m += tab
    return msg_list.append(m + text)

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
        self.warning_list = []

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
        #todo is this needed if fatal erroes trapped in add_mssages
        if len(self.error_list) > 0:
            raise GracefulExitError()

    def add_messages(self, msg_list):
        if msg_list is None: return
        if type(msg_list) != list : msg_list=[msg_list]
        if  len(msg_list) == 0 :return

        has_fatal_errors = False
        for m in msg_list:
            self._log(m)
            if (m.is_warning or m.is_note) and len(self.msg_list) < self.max_warnings:
                self.msg_list.append(m)
                self.warning_list.append(m)
            if m.exception is not None:
                self.error_list.append(m)
                if m.exception != GracefulExitError:  has_fatal_errors = True

        if has_fatal_errors:
            time.sleep(.5)
            traceback.print_stack()
            raise FatalError('Messages contain a fatal error')

    def write_msg(self, msg_text, warning=False, note=False, hint=None, tag=None, tabs=0, crumbs=None, exception=None, traceback_str=None):
        if msg_text is not None and len(msg_text) > 0:
            m = MessageClass(msg_text, warning=warning,note=note,  exception=exception, traceback_str=traceback_str, hint=hint, tag=tag, tabs=tabs, crumbs=crumbs)
            self.add_messages([m])

    def write_progress_marker(self, msg, tabs=0):
        self.write_msg('- ' + msg, tabs=tabs+1)

    def show_all_warnings_and_errors(self):
        if len(self.msg_list) > 0 or len(self.error_list)> 0:
            self.insert_screen_line()
            for m in self.warning_list: self._log(m)
            for m in self.error_list:   self._log(m)

    def get_all_warnings_and_errors(self):
        # list of all unique warnings and strings as text
        text=[]
        for m in self.warning_list:
            for l in m.to_str_list():
                text += l +'\n'
        for m in self.error_list:
            for l in m.to_str_list():
                text += l + '\n'
        text=list(set(text))
        return text

    def write_error_log_file(self, e=None):

        if self.log_file is None : return

        with open(path.normpath(self.error_file_name),'w') as f:
            f.write('_____Warnings ________________________________\n')
            for w in self.warning_list:
                for l in w.to_str_list():
                    f.write(l + '\n')
            f.write('_____Errors ________________________________\n')
            for w in self.error_list:
                for l in w.to_str_list():
                    f.write(l + '\n')

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
        for m in msg.to_str_list():
            print(self.screen_tag + ' ' + m)
            if self.log_file is not None:
                self.log_file.write(m + '\n')

    def close(self):
        if self.log_file is not None: self.log_file.close()

        # put out added debug data
        if len(self.debug_data) > 0:
            json_util.write_JSON(self.debug_data_file_name, self.debug_data)
