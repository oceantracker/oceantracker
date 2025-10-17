import common_definitions as cd
from oceantracker.main import OceanTracker

def test001_schism_native3D():
    args = cd.get_args()
    ot = OceanTracker()
    ot.settings(**cd.base_settings(__name__)
                )
    ot.add_class('reader', **cd.reader_demo_schisim3D)
    ot.add_class('release_groups', **dict(cd.rg_P1,
                    points=cd.schism_demo['deep_point']))

    case_info_file = ot.run()
    # add assert   case_info_file is None


