# build full parm ref from dict and classes defaults
from os import path, mkdir
from glob import  glob
import inspect
import importlib

from oceantracker.common_info_default_param_dict_templates import run_params_defaults_template, default_case_param_template, default_class_names
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util import package_util

root_param_ref_dir = path.join(package_util.get_root_package_dir(),'docs', 'info', 'parameter_ref')


class RSTfileBuilder(object):
    def __init__(self, file_name,title):
        self.lines=[]
        self.toc_dict = {}
        self.file_name = file_name + '.rst'

        self.add_lines((len(title)+1) * '#')
        self.add_lines(title)
        self.add_lines((len(title)+1)  * '#')
        self.add_lines()


    def add_lines(self,lines='', indent=0):
        if type(lines) != list: lines=[lines]

        for l in lines:
            self.lines.append( {'type': 'text', 'text': l, 'indent': indent})


    def add_heading(self,txt, level=0):
        self.add_lines()
        m='*=_^'
        self.add_lines(txt)
        self.add_lines(m[level]*(len(txt)+1))
        self.add_lines()

    def add_directive(self,direct_type, caption='', body=[], indent=0):
        if type(body) != list: body=[body]
        self.lines.append({'type': 'directive', 'direct_type': direct_type, 'body' : body, 'indent' :indent, 'params':{}})
        self.add_lines()
        self.add_lines()


    def collapsable_code(self,file_name):
        a=1
        '''
            ..raw:: html
        
            < details >
            < summary > code < / summary >
        
        ..literalinclude::../../../ demos / minimal_example.py
        :language: python
        :caption:
        
        ..raw:: html
        
        < / details >
        '''

    def write(self):
        file_name = path.join(root_param_ref_dir, self.file_name)
        with open(file_name ,'w') as f:
            for l in self.lines:
                indent=l['indent'] * '\t'
                if l['type'] == 'text':
                    f.write( indent  + l['text']+'\n')
                if l['type'] == 'directive':
                    f.write(indent + '\n')
                    f.write(indent+ '.. ' + l['direct_type'] + '::' +'\n')
                    for p,val in l['params'].items():
                        f.write(indent + '\t:' + p + ': ' +str(val) + '\n')
                    f.write(indent + '\n')
                    o = sorted(l['body']) if l['direct_type'] =='toctree' and l['sort_body'] else l['body']
                    for b in o:
                        f.write(indent +'\t' +b +'\n')
                    f.write(indent + '\n')

    def add_new_toc_to_page(self, toc_name, indent=0, maxdepth=2, sort_body=False):
        self.lines.append({'type':'directive','direct_type': 'toctree','body': [],'sort_body': sort_body, 'indent':indent,'params': {'maxdepth': maxdepth}})
        self.toc_dict[toc_name] = self.lines[-1]

    def add_toc_link(self, toc_name, linked_toc):

        self.toc_dict[toc_name]['body'].append(linked_toc.file_name.replace('\\', '/'))

    def write_param_dict_defaults(self, params):
        self.add_lines()
        #self.add_directive('warning', body='Lots more to add here and work on layout!!')

        self.add_heading('Parameters:', level=0)

        self.add_params_from_dict(params)

        self.write()

    def add_params_from_dict(self,params, indent=0):

        for key in sorted(params.keys()):
            item= params[key]

            if type(item) == dict:
                self.add_lines('* ``' + key + '``:' + ' nested parameter dictionary' , indent=indent+1)

                self.add_params_from_dict( item, indent=1)

                continue


            if type(item) == PVC:

                if item.info['obsolete'] is not None: continue
                self.add_lines('* ``' + key + '`` :   ``' + str(item.info['type']) + '`` '
                               + ('  *<optional>*' if not item.info['is_required'] else '**<isrequired>**') , indent=indent+1)

                if item.info['doc_str'] is not None:
                    self.add_lines('Description: - ' + str(item.info['doc_str'].strip()), indent=indent+2)
                    self.add_lines()

                self.add_lines('- default: ``' + str(item.get_default()) + '``', indent=indent+2)
                  # dont write obsolete params
                for k, v in item.info.items():
                    if k not in ['type', 'default_value', 'is_required', 'doc_str'] and v is not None:
                        self.add_lines('- ' + k + ': ``' + str(v) + '``', indent=indent+2)

                self.add_lines()

            elif type(item) == PLC:

                self.add_lines('* ``' + key + '``:' + ('  *<optional>*' if not item.info['is_required'] else '**<isrequired>**'), indent=indent + 1)
                if item.info['doc_str'] is not None:
                    self.add_lines('Description: - ' + str(item.info['doc_str'].strip()), indent=indent + 2)
                    self.add_lines()

                if  type(item.info['acceptable_types']) == dict or type(item.info['default_list']) == dict or type(item.info['default_value']) == dict:
                    self.add_lines()
                    self.add_lines(key + ': still working on display  of lists of dict, eg nested polygon list ', indent=indent+0)
                    self.add_lines()
                    continue

                self.add_lines('- a list containing type:  ``' + str(item.info['acceptable_types']) + '``', indent=indent+2)
                self.add_lines('- default list : ``'
                               + str(item.info['default_list']) + '``', indent=indent+2)

                for k, v in item.info.items():
                    if k not in ['default_list','acceptable_types', 'default_value', 'is_required', 'doc_str'] and v is not None:
                        self.add_lines('- ' + k + ': ``' + str(v) + '``', indent=indent+2)

                self.add_lines()
            else:
                self.add_lines()
                self.add_lines(key +': still working on display  of default params of  type ' + str(type(params[key])),indent=indent+0)
                self.add_lines()


def make_sub_pages(class_type):
    # make doc pages from defaults of all python in named dir

    if class_type in default_class_names:
        mod_name= default_class_names[class_type].rsplit('.', maxsplit=2)[0]
    else:
        mod_name=package_util.get_package_name()+ '.' +class_type

    mod = importlib.import_module( mod_name)

    package_dir= package_util.get_package_dir()

    toc = RSTfileBuilder(class_type+'_toc', class_type)

    toc.add_lines('**Module:** ' + package_util.package_relative_file_name(mod.__name__).strip())
    toc.add_lines()

    toc.add_new_toc_to_page(class_type, maxdepth=1,sort_body=True)
    instance = None
    for f in glob(path.join( package_dir,class_type,'*.py')):

        mod_str= path.splitext(f)[0].split(package_util.get_root_package_dir() +'\\')[-1].replace('\\','.')
        mod = importlib.import_module(mod_str)
        package_util.get_package_name()

        for name, c in  inspect.getmembers(mod):
            if not inspect.isclass(c) : continue
            #print(name)
            if name[0] == '_':   continue  # ignore internal/base classes flagged with underscore

            if not issubclass(c, ParameterBaseClass): continue
            if c.__module__ !=  mod.__name__ : continue  # only work on locally declared claseses
            instance= c()


            p = RSTfileBuilder(name, name)

            p.add_lines('**Description:** ' + (instance.docs['description'] if instance.docs['description'] is not None else '' ) )
            p.add_lines()
            p.add_lines('**Class:** ' + c.__module__ + '.' + c.__name__)
            p.add_lines()

            p.add_lines('**File:** ' + package_util.package_relative_file_name(mod.__file__))
            p.add_lines()

            # show pinhertince
            parents=''
            for b in inspect.getmro(c)[1:]:
                #print(b.__name__, parents)
                if b.__name__ in ['object',  'ParameterBaseClass'] :continue
                parents = b.__name__ + '> ' + parents

            p.add_lines('**Inheritance:** ' + parents + c.__name__)
            p.add_lines()

            internal_name = instance.default_params['name'].get_default() if instance.default_params['name'].get_default() is not None else 'not given in defaults'
            p.add_lines('**Default internal name:** ``"' + internal_name.strip() + '"``' )
            p.add_lines()

            # get all defaults and wrte to yaml
            #instance.merge_with_class_defaults({},{})
            #write_YAML(name+'.yaml',instance.params)

            p.add_heading('Parameters:', level=0)

            p.add_params_from_dict(instance.default_params)

            p.write()
            toc.add_toc_link(class_type,p)

    # add role from last instance, as it derives from base class
    if instance is not None:
        toc.add_lines('**Role:** ' + (instance.docs['role'] if instance.docs['role'] is not None else ''))
        toc.add_lines()
    toc.write()
    return toc


def build_param_ref():
    # parameter ref  TOC

    page= RSTfileBuilder('parameter_ref_toc','Parameter details')


    page.add_lines('Links to details of parameter default values, acceptable values etc.')
    page.add_lines()
    page.add_directive('note',body= 'Lots more to add here!!')

    page.add_heading('Top level parameters',level=1)
    sp = RSTfileBuilder('shared_params', 'shared_params')
    sp.write_param_dict_defaults(run_params_defaults_template['shared_params'])

    page.add_new_toc_to_page('top', maxdepth=1)
    page.add_toc_link('top', sp)

    # look at readers
    toc= make_sub_pages('reader')
    page.add_toc_link('top', toc)

    page.add_heading('Case parameters',level=1)

    page.add_new_toc_to_page('case', maxdepth=1, sort_body=True)

    rp = RSTfileBuilder('run_params', 'run_params')
    rp.write_param_dict_defaults(default_case_param_template['run_params'])
    page.add_toc_link('case',rp)

    page.add_heading('Core classes',level=2)
    page.add_new_toc_to_page('core', maxdepth=1)
    for key in sorted(default_case_param_template.keys()):
        if key in ['run_params'] or  type(default_case_param_template[key])==list: continue

        toc = make_sub_pages(key)
        page.add_toc_link('core', toc)

    page.add_heading('User added classes',level=2)
    page.add_new_toc_to_page('user', maxdepth=1)
    for key in sorted(default_case_param_template.keys()):
        if type(default_case_param_template[key]) != list: continue
        toc = make_sub_pages(key)
        page.add_toc_link('user', toc)

    # write toc page at end
    page.write()

if __name__ == "__main__":
    build_param_ref()