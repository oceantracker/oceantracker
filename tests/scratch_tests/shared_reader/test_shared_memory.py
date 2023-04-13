from oceantracker.util import json_util, basic_util
from oceantracker import main
from os import path

params= json_util.read_JSON('../../../demos/demo_json/demo02_animation.json')

params['reader'].update({'share_reader': True, 'input_dir': path.join('../../..', 'demos', params['reader']['input_dir'])})

main.run(params)

pass
