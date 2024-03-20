# build full parm ref from dict and classes defaults
from os import path, mkdir, listdir
from glob import  glob
import inspect
import importlib

import oceantracker.common_info_default_param_dict_templates as common_info
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util import package_util

root_param_ref_dir = path.join(package_util.get_root_package_dir(),'docs', 'info', 'parameter_ref')


class RSTfileBuilder(object):
    def __init__(self, file_name, title):
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
        pass
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

                if item.info['obsolete'] is not None: continue # dont write obsolete params
                self.add_lines('* ``' + key + '`` :   ``' + str(item.info['type']) + '`` '
                               + ('  *<optional>*' if not item.info['is_required'] else '**<isrequired>**') , indent=indent+1)

                if item.info['doc_str'] is not None:
                    self.add_lines('Description: ' + str(item.info['doc_str'].strip()), indent=indent+2)
                    self.add_lines()

                self.add_lines('- default: ``' + str(item.get_default()) + '``', indent=indent+2)

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


def make_class_sub_pages(class_role, link_tag=''):
    # make doc pages from defaults of all python in named dir

    mod_name=package_util.get_package_name() + '.' + class_role

    mod = importlib.import_module( mod_name)

    package_dir= package_util.get_package_dir()

    toc = RSTfileBuilder(class_role+'_toc', class_role + link_tag)

    toc.add_lines('**Module:** ' + package_util.package_relative_file_name(mod.__name__).strip())
    toc.add_lines()

    toc.add_new_toc_to_page(class_role, maxdepth=1,sort_body=True)
    instance = None
    for f in glob(path.join( package_dir,class_role,'*.py')):

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
            p.add_lines('**class_name:** ' + c.__module__ + '.' + c.__name__)
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

            # get all defaults and wrte to yaml
            #instance.merge_with_class_defaults({},{})
            #write_YAML(name+'.yaml',instance.params)

            p.add_heading('Parameters:', level=0)

            p.add_params_from_dict(instance.default_params)

            p.write()
            toc.add_toc_link(class_role,p)

    # add role from last instance, as it derives from base class
    if instance is not None:
        toc.add_lines('**Role:** ' + (instance.docs['role'] if instance.docs['role'] is not None else ''))
        toc.add_lines()
    toc.write()
    return toc


def build_param_ref():
    # parameter ref  TOC

    page= RSTfileBuilder('parameter_ref_toc','Parameter details')
    page.add_lines('Links to details of parameter default values for settings and classes, acceptable values etc.')
    page.add_lines()

    # settings sub page
    sp = RSTfileBuilder('settings', 'Settings')
    settings_dict = common_info.shared_settings_defaults
    settings_dict.update(common_info.case_settings_defaults)
    sp.add_heading('Top level settings/parameters', level=2)
    sp.write_param_dict_defaults(settings_dict)

    page.add_heading('Top level settings', level=2)
    page.add_new_toc_to_page('Settings', maxdepth=1)
    page.add_toc_link('Settings',sp)


    # core classes
    page.add_heading('Core "class" roles',level=2)
    page.add_lines('Only one core class per role. These have singular role names.')
    page.add_new_toc_to_page('core', maxdepth=1)
    for key in sorted(common_info.core_class_list):
        toc = make_class_sub_pages(key)
        page.add_toc_link('core', toc)

    page.write()

    page.add_heading('Multiple classes for each role',level=2)
    page.add_lines('Can be many classes per role, each with a user given name as part of  dictionary for each role. These roles have plural names.')
    page.add_new_toc_to_page('class_dicts', maxdepth=1, sort_body=True)

    page.add_new_toc_to_page('user', maxdepth=1)
    for key in sorted(common_info.class_dicts_list):
        if key in ['nested_readers'] : continue
        toc = make_class_sub_pages(key)
        page.add_toc_link('user', toc)

    # write toc page at end
    page.write()

if __name__ == "__main__":

    build_param_ref()

    # convert ipyhton to
    import subprocess
    from os import  path, chdir, rename, remove
    import shutil
    from glob import  glob

    chdir(r'../tutorials_how_to')
    print('h')
    dest = r'../docs/info/how_to'
    for f in glob('*.ipynb'):
        subprocess.run('jupyter nbconvert '+ f + '  --to rst')
        subprocess.run('jupyter nbconvert ' + f + '  --to script')
        f_base = f.split('.')[0]
        print(f_base)
        f_base + '_files'
        old_fn = f_base+'.rst'
        new_fn = path.join(dest,old_fn)
        if path.isfile(new_fn):
            remove(new_fn)
        shutil.move(old_fn, dest)

        old_dir = f_base  +'_files'
        new_dir = path.join(dest, old_dir)
        print(old_dir,new_dir)
        if path.isdir(old_dir) :
            if path.isdir(new_dir): shutil.rmtree(new_dir, ignore_errors=True)
            shutil.move(old_dir, new_dir)

