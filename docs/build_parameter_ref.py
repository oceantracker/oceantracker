# build full parm ref from dict and classes defaults
from os import path, mkdir, listdir
from glob import  glob
import inspect
import importlib

from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.parameter_checking import _ParameterBaseDataClassChecker, ParameterTimeChecker as PTC
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.shared_info import shared_info as si
si._setup()
si.class_importer._build_class_tree_ans_short_name_map()

from oceantracker import definitions

class RSTfileBuilder(object):
    def __init__(self, file_name, title):
        self.lines=[]
        self.toc_dict = {}
        self.file_name = file_name + '.rst'
        self.docs_dir= path.join(definitions.ot_root_dir,'docs','info','parameter_ref')
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
        file_name = path.join(self.docs_dir, self.file_name)
        print('writing:', path.basename(file_name))
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
                        if b is not None:
                            f.write(indent +'\t' + b +'\n')
                    f.write(indent + '\n')

    def add_new_toc_to_page(self, toc_name, indent=0, maxdepth=2, sort_body=False):
        self.lines.append({'type':'directive','direct_type': 'toctree','body': [],'sort_body': sort_body, 'indent':indent,'params': {'maxdepth': maxdepth}})
        self.toc_dict[toc_name] = self.lines[-1]

    def add_toc_link(self, toc_name, linked_toc):

        self.toc_dict[toc_name]['body'].append(linked_toc.file_name.replace('\\', '/'))

    def add_params_from_dict(self,params, indent=0, expert=False):

        if expert:
            p = {key: item for key, item in params.items() if isinstance(item,_ParameterBaseDataClassChecker) and item.expert}
            self.add_heading('Expert Parameters:', level=0)
        else:
            p = {key: item for key, item in params.items() if isinstance(item,_ParameterBaseDataClassChecker ) and not item.expert}
            self.add_heading('Parameters:', level=0)
        # loop over params
        dont_include= ['default','type', 'default_value', 'is_required', 'doc_str' ,'expert','obsolete']
        for key in sorted(p.keys()):
            item= p[key]

            if type(item) == dict:
                self.add_lines('* ``' + key + '``:' + ' nested parameter dictionary' , indent=indent+1)
                self.add_params_from_dict( item, indent=1,expert=False) # dont split expert for nested params
                continue

            if item.obsolete: continue  # dont write obsolete params

            if type(item) == PVC:
                self.add_lines('* ``' + key + '`` :   ``' + str(item.data_type) + '`` '
                               + ('  *<optional>*' if not item.is_required else '**<isrequired>**') , indent=indent+1)

                if item.doc_str is not None:
                    self.add_lines('Description: ' + str(item.doc_str.strip()), indent=indent+2)
                    self.add_lines()

                self.add_lines('- default: ``' + str(item.get_default()) + '``', indent=indent+2)

                for k, v in item.__dict__.items():
                    if k not in dont_include and v is not None:
                        self.add_lines('- ' + k + ': ``' + str(v) + '``', indent=indent+2)
                self.add_lines()

            elif type(item) == PTC:

                self.add_lines('* ``' + key + '`` :   ``' + str([x.__name__ for x in item.possible_types ]) + '`` '
                               + ('  *<optional>*' if not item.is_required else '**<isrequired>**') , indent=indent+1)

                if item.doc_str is not None:
                    self.add_lines('Description: ' + str(item.doc_str.strip()), indent=indent+2)
                    self.add_lines()

                self.add_lines('- default: ``' + str(item.get_default()) + '``', indent=indent+2)
                if hasattr(item,'possible_values')  and len(item.possible_values) > 0:
                    self.add_lines('- ' + 'possible_values' + ': ``' + str(v) + '``', indent=indent + 2)

                for k, v in item.asdict().items():
                    if (k not in dont_include and v is not None):
                        self.add_lines('- ' + k + ': ``' + str(v) + '``', indent=indent+2)

                self.add_lines()

            elif type(item) == PLC:

                self.add_lines('* ``' + key + '``:' + ('  *<optional>*' if not item.is_required else '**<isrequired>**'), indent=indent + 1)
                if item.doc_str is not None:
                    self.add_lines('Description: - ' + str(item.doc_str.strip()), indent=indent + 2)
                    self.add_lines()


                self.add_lines('- a list containing type:  ``' + str(item.possible_types) + '``', indent=indent+2)
                self.add_lines('- default list : ``'
                               + str(item.default) + '``', indent=indent+2)

                for k, v in item.asdict().items():
                    if k not in dont_include and v is not None:
                        self.add_lines('- ' + k + ': ``' + str(v) + '``', indent=indent+2)

                self.add_lines()
            else:
                self.add_lines()
                self.add_lines(key +': still working on display  of default params of  type ' + str(type(p[key])),indent=indent+0)
                self.add_lines()


def make_class_sub_pages(class_role, link_tag=''):
    # make doc pages from defaults of all python in named dir

    mods= si.class_importer.class_tree[class_role]

    toc = RSTfileBuilder(class_role+'_toc', class_role + link_tag)

    toc.add_new_toc_to_page(class_role, maxdepth=1,sort_body=True)
    instance = None
    for name, info in mods.items():
        #if name[0] == '_':   continue  # ignore internal/base classes flagged with underscore
        instance= info['class_obj']()
        p = RSTfileBuilder(name, name)
        doc_str = info["class_obj"].__doc__

        p.add_lines('**Doc:** ' + ('' if doc_str is None else doc_str.replace("\n","")) )
        p.add_lines()
        short_name = info["class_name"].split(".")[-1]
        p.add_lines(f'**short class_name:** {short_name}')
        p.add_lines()
        p.add_lines(f'**full class_name :** {info["class_name"]}')
        p.add_lines()

        if instance.development is not None or  short_name.lower().startswith('dev') :
            m = f'Class is under development may not yet work in all cases, if errors contact developer'

            p.add_directive('warning',body=m)

        # show inheritance
        parents=''
        for b in info['class_obj'].__mro__[:-2][::-1]:
            parents = parents  + '> ' + b.__name__

        p.add_lines(f'**Inheritance:** {parents}')
        p.add_lines()


        # write params
        params = instance.default_params
        p.add_params_from_dict(params,expert=False)
        p.add_lines()
        p.add_params_from_dict(params, expert=True)
        p.add_lines()

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
    settings_dict = si.settings.asdict()
    sp.add_heading('Top level settings/parameters', level=2)
    sp.add_params_from_dict(settings_dict,expert=False)
    sp.add_params_from_dict(settings_dict, expert=True)
    sp.write()

    page.add_heading('Top level settings', level=2)
    page.add_new_toc_to_page('Settings', maxdepth=1)
    page.add_toc_link('Settings',sp)

    # core classes
    page.add_heading('Core "class" roles',level=2)
    page.add_lines('Only one class in each role role. These have singular role names.')
    page.add_new_toc_to_page('core', maxdepth=1)
    for key in sorted(si.core_class_roles.possible_values()):
        toc = make_class_sub_pages(key)
        page.add_toc_link('core', toc)

    page.write()

    page.add_heading('Multiple classes for each role',level=2)
    page.add_lines('Can be many classes per role, each with a user given name as part of  dictionary for each role. These roles have plural names.')
    page.add_new_toc_to_page('roles_dict', maxdepth=1, sort_body=True)

    page.add_new_toc_to_page('user', maxdepth=1)
    for key in sorted(si.class_roles.possible_values()):
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



    dest = path.join( definitions.ot_root_dir, 'docs/info/how_to')
    work_dir = path.join( definitions.ot_root_dir, 'tutorials_how_to')
    chdir(work_dir)
    for f in glob( '*.ipynb'):
        subprocess.run('jupyter nbconvert '+ f + '  --to rst')
        #subprocess.run('jupyter nbconvert ' + f + '  --to script')
        print('converted', f)
        f_base = f.split('.')[0]
        print(f_base)
        f_base + '_files'
        old_fn = f_base +'.rst'
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

