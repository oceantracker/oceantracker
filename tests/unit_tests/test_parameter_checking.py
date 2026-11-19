"""Checks of user given parameter keys against class default params.

Unknown (eg misspelled) and obsolete parameters must stop a run at setup, deprecated ones must warn.
From v0.5.3.5 to v0.5.3.10 this check was silently switched off, so a misspelled
"max_count_per_particles" was ignored and the run used the default instead.
"""
import pytest

from oceantracker.main import OceanTracker
from oceantracker.shared_info import shared_info as si
from oceantracker.util.message_logger import MessageLogger, OTinput_error
from oceantracker.util.parameter_checking import (merge_params_with_defaults, check_param_keys,
                                                  ParamValueChecker as PVC)


def _defaults():
    return dict(
        name=PVC(None, str),
        max_count_per_particle=PVC(None, int),
        old_param=PVC(None, int, obsolete=True, doc_str='use "max_count_per_particle"'),
        dep_param=PVC(None, int, deprecated=True, doc_str='use "max_count_per_particle"'),
        nested=dict(a=PVC(1, int), b=PVC(2, int)),
        open_map=dict(control_key_allow_unknown_keys=True, a=PVC('x', str)),
    )


def _errors(ml):
    return '\n'.join(ml.msg_lists['error'])


# function level, using a real message logger
# ------------------------------------------------------------------
def test_known_keys_merge():
    ml = MessageLogger()
    p = merge_params_with_defaults(dict(max_count_per_particle=1, nested=dict(a=3)), _defaults(), ml)
    assert p['max_count_per_particle'] == 1 and p['nested'] == dict(a=3, b=2)
    assert 'control_key_allow_unknown_keys' not in p['open_map']
    assert len(ml.msg_lists['error']) == 0 and len(ml.msg_lists['strong_warning']) == 0


def test_unknown_key_is_an_error_with_suggestion():
    ml = MessageLogger()
    with pytest.raises(OTinput_error):
        merge_params_with_defaults(dict(max_count_per_particles=1), _defaults(), ml)
    err = _errors(ml)
    assert '"max_count_per_particles" is not recognised' in err
    assert '1: "max_count_per_particle"' in err


def test_suggestions_exclude_control_obsolete_and_deprecated_keys(monkeypatch):
    ml = MessageLogger()
    suggested = []
    real_spell_check = ml.spell_check

    def spy(msg, key, possible_values, **kwargs):
        suggested.extend(possible_values)
        return real_spell_check(msg, key, possible_values, **kwargs)

    monkeypatch.setattr(ml, 'spell_check', spy)
    with pytest.raises(OTinput_error):
        merge_params_with_defaults(dict(zzz=1), _defaults(), ml)
    assert set(suggested) == {'name', 'max_count_per_particle', 'nested', 'open_map'}


def test_unknown_nested_key_is_an_error():
    ml = MessageLogger()
    with pytest.raises(OTinput_error):
        merge_params_with_defaults(dict(nested=dict(c=1)), _defaults(), ml)
    assert 'Parameter "nested >> c" is not recognised' in _errors(ml)


def test_map_with_control_key_accepts_extra_keys():
    ml = MessageLogger()
    p = merge_params_with_defaults(dict(open_map=dict(my_field='temp')), _defaults(), ml)
    assert p['open_map']['my_field'] == 'temp'
    assert len(ml.msg_lists['error']) == 0


def test_user_given_control_key_is_an_error():
    for params in [dict(control_key_allow_unknown_keys=True, zzz=1),
                   dict(open_map=dict(control_key_allow_unknown_keys=False))]:
        ml = MessageLogger()
        with pytest.raises(OTinput_error):
            merge_params_with_defaults(params, _defaults(), ml)
        assert 'control_key_allow_unknown_keys" is not recognised' in _errors(ml)


def test_obsolete_key_is_an_error():
    ml = MessageLogger()
    with pytest.raises(OTinput_error):
        merge_params_with_defaults(dict(old_param=1), _defaults(), ml)
    assert '"old_param" is obsolete' in _errors(ml)


def test_deprecated_key_warns_only_when_given_a_value():
    ml = MessageLogger()
    merge_params_with_defaults(dict(dep_param=1), _defaults(), ml)
    assert len(ml.msg_lists['strong_warning']) == 1
    assert '"dep_param" is deprecated' in ml.msg_lists['strong_warning'][0]

    # merged params hold deprecated keys set to None, merging them again must not warn
    ml = MessageLogger()
    merge_params_with_defaults(dict(dep_param=None), _defaults(), ml)
    assert len(ml.msg_lists['strong_warning']) == 0


def test_deferred_key_check():
    # as used when trying candidate readers, keys are checked later with check_param_keys
    ml = MessageLogger()
    given = dict(zzz=1, nested=dict(c=1))
    merge_params_with_defaults(dict(given), _defaults(), ml, check_keys=False)
    assert len(ml.msg_lists['error']) == 0

    with pytest.raises(OTinput_error):
        check_param_keys(given, _defaults(), ml)
    assert '"zzz" is not recognised' in _errors(ml)


# full runs, setup errors are caught by the runner, which then returns None
# ------------------------------------------------------------------
def _run(base_settings, reader, extra_settings={}, points=[[1594000, 5484200, -2]], **stats):
    ot = OceanTracker()
    ot.settings(**{**base_settings, 'max_run_duration': 3 * 3600, **extra_settings})
    ot.add_class('reader', **reader)
    ot.add_class('release_groups', name='p', class_name='PointRelease',
                 points=points, release_interval=3600, pulse_size=2)
    if stats:
        ot.add_class('particle_statistics', **stats)
    return ot.run()


def test_misspelled_class_param_stops_run(base_settings, reader_demo_schism3D, schism3D_release_locations):
    """The reported case: a typo in an age-based stats param was silently ignored."""
    stats = dict(name='age_stats', class_name='PolygonStats2D_ageBased',
                 polygon_list=schism3D_release_locations['polygons'],
                 update_interval=3600, max_age_to_bin=24 * 3600, age_bin_size=3600,
                 max_count_per_particles=1)
    assert _run(base_settings, reader_demo_schism3D, **stats) is None
    err = '\n'.join(si.msg_logger.msg_lists['error'])
    assert '"max_count_per_particles" is not recognised' in err
    assert '"max_count_per_particle"' in err.replace('"max_count_per_particles"', '')


def test_misspelled_reader_param_stops_run(base_settings, reader_demo_schism3D):
    # checked once the reader format has been detected
    assert _run(base_settings, {**reader_demo_schism3D, 'regrid_z_to_sigma_levelx': True}) is None
    err = '\n'.join(si.msg_logger.msg_lists['error'])
    assert '"regrid_z_to_sigma_levelx" is not recognised' in err
    assert '1: "regrid_z_to_sigma_levels"' in err


def test_obsolete_reader_param_stops_run(base_settings, reader_demo_schism3D):
    assert _run(base_settings, {**reader_demo_schism3D, 'time_buffer_size': 24}) is None
    assert '"time_buffer_size" is obsolete' in '\n'.join(si.msg_logger.msg_lists['error'])


def test_misspelled_reader_param_reported_when_format_not_detected(base_settings, reader_demo_schism3D):
    # forcing the wrong reader fails format detection, the typo must still be reported first
    reader = {**reader_demo_schism3D, 'class_name': 'ROMSreader', 'geographic_cords': True}
    assert _run(base_settings, reader) is None
    err = '\n'.join(si.msg_logger.msg_lists['error'])
    assert '"geographic_cords" is not recognised' in err
    assert '1: "geographic_coords"' in err


def test_obsolete_setting_stops_run(base_settings, reader_demo_schism3D):
    assert _run(base_settings, reader_demo_schism3D,
                extra_settings=dict(regrid_z_to_uniform_sigma_levels=True)) is None
    assert '"regrid_z_to_uniform_sigma_levels" is obsolete' in '\n'.join(si.msg_logger.msg_lists['error'])


def test_reader_specific_param_accepted_by_format_detection(base_settings, reader_schism3D_v5,
                                                            schism3Dv5_release_locations):
    """Detection tries ROMSreader before SCHISMreaderV5, ROMS does not know the SCHISM "hgrid_file_name"."""
    assert _run(base_settings, {**reader_schism3D_v5, 'hgrid_file_name': None},
                points=schism3Dv5_release_locations['point']) is not None
