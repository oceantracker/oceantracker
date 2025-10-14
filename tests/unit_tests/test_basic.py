import ut_def
from oceantracker.main import OceanTracker

def test001_schism_native3D():
    args = ut_def.setup()
    ot = OceanTracker()

    ot.add_class('reader',**ut_def.reader_demo_schisim3D)
    ot.add_class('release_group',**dict(ut_def.rg_basic,points=ut_def.schism_data['deep_point']))

    ot.run()


