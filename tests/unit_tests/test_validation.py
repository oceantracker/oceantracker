from oceantracker.main import OceanTracker
from oceantracker.read_output.python import load_output_files

import pytest
import numpy as np
from os import path, makedirs

@pytest.fixture
def default_plot_output_path(request, default_root_output_dir):
    """Default output path for plots"""
    func_name = request.node.name
    return path.join(default_root_output_dir, func_name)

@pytest.fixture
def test_name(request):
    """Returns the name of the current test function"""
    return request.node.name


@pytest.mark.skip(reason="Not implemented yet")
def test_schism_resuspension():
    assert True


@pytest.mark.validation
def test_schism_validation_run_small(
    base_settings,
    reader_schism3D,
    basic_point_release,
    schism_release_locations,
    gridded_2D_timeBased,
    polygon_stats_timeBased_waterDepth,
    reference_data_dir,
    test_name,
    default_plot_output_path,
    create_reference_data_flag,
):
    ot = OceanTracker()
    ot.settings(
        **{**base_settings, "write_tracks": True},
        use_A_Z_profile=True, # do we need this for the base reference test?
    )
    ot.add_class(
        "tracks_writer",
        update_interval=3600,
        write_dry_cell_flag=False,
        turn_on_write_particle_properties_list=[
            "nz_cell",
            "z_fraction_water_velocity",
            "z_fraction",
        ],
    )
    ot.add_class("reader", **reader_schism3D, regrid_z_to_sigma_levels=True)
    ot.add_class(
        "release_groups",
        **{
            **(
                basic_point_release
                | {"name": "single_point_release", "release_interval": 0}
            ),
            "points": schism_release_locations["deep_point"],
            # "points": schism_release_locations["polygons"][0]["points"],
        },
    )
    # Add statistics
    ot.add_class("particle_statistics", **gridded_2D_timeBased)
    ot.add_class(
        "particle_statistics",
        **{
            **polygon_stats_timeBased_waterDepth,
            "polygon_list": schism_release_locations["polygons"],
        },
    )
    # Run the model
    case_info_file = ot.run()
    # and check if it ran
    assert case_info_file is not None

    # Compare or create reference tracks
    if not create_reference_data_flag:
        # check if reference data exists and throw a warning otherwise

        track_results = compare_tracks_with_reference(
            case_info_file, reference_data_dir, test_name, create_reference=False
        )

        # Assert tracks are within acceptable tolerances
        assert (
            track_results["x_max_diff"] < 1e-6
        ), f"Maximum position difference {track_results['x_max_diff']} exceeds tolerance"
        assert (
            abs(track_results["time_max_diff"]) < 1e-6
        ), f"Maximum time difference {abs(track_results['time_max_diff'])} exceeds tolerance"

        # Compare or create reference statistics
        stats_results = compare_stats_with_reference(
            case_info_file, reference_data_dir, test_name, create_reference=False
        )

        # Assert statistics are within acceptable tolerances
        for key, value in stats_results.items():
            if "count" in key:
                assert value == 0, f"Particle count difference {key}: {value}"
    else:
        compare_tracks_with_reference(
            case_info_file, reference_data_dir, test_name, create_reference=True
        )
        compare_stats_with_reference(
            case_info_file, reference_data_dir, test_name, create_reference=True
        )
    create_plots(case_info_file, default_plot_output_path, test_name)
    print_additional_validation_checks(case_info_file)

def compare_tracks_with_reference(
    case_info_file, reference_data_dir, test_name, create_reference=False
):
    """
    Compare current run tracks with reference data or create reference data

    Args:
        case_info_file: Path to case info file from current run
        reference_data_dir: Directory containing reference data
        test_name: Name of the test (used for reference file naming)
        create_reference: If True, save current run as reference data

    Returns:
        dict: Dictionary of comparison metrics
    """
    # Load current run data
    tracks = load_output_files.load_track_data(case_info_file)

    reference_file = path.join(reference_data_dir, f"{test_name}_tracks.npz")

    if create_reference:
        # Save current run as reference data
        makedirs(reference_data_dir, exist_ok=True)

        # Save key track data
        np.savez(
            reference_file,
            x=tracks["x"],
            time=tracks["time"],
            status=tracks["status"],
            water_depth=tracks["water_depth"],
            age=tracks["age"],
            # Add any other key variables to compare
        )
        print(f"Created reference data: {reference_file}")
        return None

    # Load reference data for comparison
    if not path.exists(reference_file):
        raise FileNotFoundError(
            f"Reference file not found: {reference_file}\n"
            f"Run with --create-reference flag to create it"
        )

    tracks_ref = np.load(reference_file)

    # Compare positions
    dx = np.abs(tracks["x"] - tracks_ref["x"])

    results = {
        "x_min_diff": np.nanmin(dx),
        "x_mean_diff": np.nanmean(dx),
        "x_max_diff": np.nanmax(dx),
        "time_min_diff": np.nanmin(tracks["time"] - tracks_ref["time"]),
        "time_max_diff": np.nanmax(tracks["time"] - tracks_ref["time"]),
    }

    # Print comparison results
    print(f'\n(x,y,z) differences from reference run: "{test_name}"')
    print(f'\t min  : {results["x_min_diff"]}')
    print(f'\t mean : {results["x_mean_diff"]}')
    print(f'\t max  : {results["x_max_diff"]}')
    print(
        f'times, \t  min/max diff: {results["time_min_diff"]}, {results["time_max_diff"]}'
    )

    return results


def compare_stats_with_reference(
    case_info_file, reference_data_dir, test_name, create_reference=False
):
    """
    Compare particle statistics with reference data or create reference data

    Args:
        case_info_file: Path to case info file from current run
        reference_data_dir: Directory containing reference data
        test_name: Name of the test
        create_reference: If True, save current run as reference data

    Returns:
        dict: Dictionary of comparison metrics
    """
    case_info = load_output_files.read_case_info_file(case_info_file)

    reference_file = path.join(reference_data_dir, f"{test_name}_stats.npz")

    if create_reference:
        # Save statistics as reference data
        makedirs(reference_data_dir, exist_ok=True)

        stats_data = {}
        stats_params = case_info["working_params"]["class_roles"].get(
            "particle_statistics", {}
        )

        for name, params in stats_params.items():
            if name not in case_info["output_files"].get("particle_statistics", {}):
                continue
            stats = load_output_files.load_stats_data(case_info_file, name=name)

            # Save key statistics
            stats_data[f"{name}_count"] = stats["count"]
            stats_data[f"{name}_count_all_alive"] = stats["count_all_alive_particles"]

            # Save particle property sums if present
            if "particle_property_list" in params:
                for prop_name in params["particle_property_list"]:
                    if prop_name in stats:
                        prop_sum = f"sum_{prop_name}"
                        if prop_sum in stats:
                            stats_data[f"{name}_{prop_sum}"] = stats[prop_sum]
                        stats_data[f"{name}_{prop_name}"] = stats[prop_name]

        np.savez(reference_file, **stats_data)
        print(f"Created reference statistics: {reference_file}")
        return None

    # Load and compare with reference
    if not path.exists(reference_file):
        raise FileNotFoundError(
            f"Reference statistics file not found: {reference_file}\n"
            f"Run with --create-reference flag to create it"
        )

    stats_ref = np.load(reference_file)

    results = {}
    stats_params = case_info["working_params"]["class_roles"].get(
        "particle_statistics", {}
    )

    for name, params in stats_params.items():
        if name not in case_info["output_files"].get("particle_statistics", {}):
            continue

        stats = load_output_files.load_stats_data(case_info_file, name=name)

        # Compare counts
        ref_key = f"{name}_count"
        if ref_key in stats_ref:
            diff = np.max(np.abs(stats["count"] - stats_ref[ref_key]))
            results[f"{name}_count_max_diff"] = diff
            count_ref = stats_ref[ref_key].sum()
            count_new = stats["count"].sum()
            print(f'\nStats "{name}":')
            print(f'\t counts ref/new: {count_ref}, {count_new}')
            print(f"\t max diff counts: {diff}")

        # Compare alive particle counts
        ref_key = f"{name}_count_all_alive"
        if ref_key in stats_ref:
            diff = np.max(
                np.abs(stats["count_all_alive_particles"] - stats_ref[ref_key])
            )
            results[f"{name}_count_all_alive_max_diff"] = diff
            caa_ref = stats_ref[ref_key].sum()
            caa_new = stats["count_all_alive_particles"].sum()
            print(f'\t count_all_alive ref/new: {caa_ref}, {caa_new}')
            print(f"\t max diff count_all_alive: {diff}")

        # Compare particle properties
        if "particle_property_list" in params:
            for prop_name in params["particle_property_list"]:
                prop_sum = f"sum_{prop_name}"
                ref_key = f"{name}_{prop_sum}"

                if ref_key in stats_ref and prop_sum in stats:
                    dc = np.abs(stats[prop_sum] - stats_ref[ref_key])
                    diff = np.max(dc[np.isfinite(dc)])
                    results[f"{name}_{prop_sum}_max_diff"] = diff
                    print(f'\t Property sum "{prop_sum}" max diff: {diff}')

    return results


def create_plots(case_info_file, plot_output_dir, test_name):
    """
    Create and save plots from test run

    Args:
        case_info_file: Path to case info file
        plot_output_dir: Directory to save plots
        test_name: Name of test (used for plot filenames)
    """
    from matplotlib import pyplot as plt
    from oceantracker.plot_output import plot_tracks

    makedirs(plot_output_dir, exist_ok=True)

    tracks = load_output_files.load_track_data(case_info_file)

    # Create track animation
    movie_file = path.join(plot_output_dir, f"{test_name}_tracks.mp4")
    plot_tracks.animate_particles(
        tracks,
        show_grid=True,
        show_dry_cells=True,
        axis_labels=True,
        movie_file=movie_file,
    )
    print(f"Saved track animation: {movie_file}")

    # Create comparison plots
    n_pulse = 0
    n_release = 0

    sel = np.logical_and(
        tracks["IDpulse"] == n_pulse, tracks["IDrelease_group"] == n_release
    )
    x = tracks["x"][:, sel, :]
    x0 = x[0, :].T
    time = (tracks["time"] - tracks["time"][0]) / 3600 / 24

    # Plot tracks in 2D
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.plot(x[:, :, 0], x[:, :, 1])
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title(f"{test_name} - Particle Tracks")
    ax.grid(True)
    plt.savefig(path.join(plot_output_dir, f"{test_name}_tracks_2d.png"), dpi=150)
    plt.close()

    # Plot displacement over time
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(time, x[:, :, 0] - x0[0])
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("X displacement (m)")
    ax.set_title(f"{test_name} - East Displacement")
    ax.grid(True)
    plt.savefig(path.join(plot_output_dir, f"{test_name}_displacement.png"), dpi=150)
    plt.close()

    # Plot status and vertical position over time
    fig, axs = plt.subplots(4, 1, figsize=(12, 10))

    axs[0].plot(time, tracks["status"][:, sel])
    axs[0].set_ylabel("Status")
    axs[0].set_title(f"{test_name} - Particle Status and Vertical Info")
    axs[0].grid(True)

    if "nz_cell" in tracks:
        axs[1].plot(time, tracks["nz_cell"][:, sel])
        axs[1].set_ylabel("nz_cell")
        axs[1].grid(True)

    if "z_fraction_water_velocity" in tracks:
        axs[2].plot(time, tracks["z_fraction_water_velocity"][:, sel])
        axs[2].set_ylabel("z_fraction_water_velocity")
        axs[2].grid(True)

    axs[3].plot(time, x[:, :, 2])
    if "tide" in tracks:
        axs[3].plot(time, tracks["tide"][:, sel], "--")
    axs[3].set_ylabel("Z (m)")
    axs[3].set_xlabel("Time (days)")
    axs[3].grid(True)

    plt.tight_layout()
    plt.savefig(path.join(plot_output_dir, f"{test_name}_vertical.png"), dpi=150)
    plt.close()

    print(f"Saved plots to: {plot_output_dir}")



def print_additional_validation_checks(case_info_file):
    # Additional validation checks (always run)
    tracks = load_output_files.load_track_data(case_info_file)

    # Check z fractions are in valid range
    if "z_fraction" in tracks:
        z_fraction = tracks["z_fraction"]
        sel = np.logical_or(z_fraction < -0.01, z_fraction > 1.01)
        assert not np.any(
            sel
        ), f"z_fraction out of range [0,1]: {np.count_nonzero(sel)} instances"

    if "z_fraction_water_velocity" in tracks:
        z_fraction_wv = tracks["z_fraction_water_velocity"]
        sel = np.logical_or(z_fraction_wv < -0.01, z_fraction_wv > 1.01)
        assert not np.any(
            sel
        ), f"z_fraction_water_velocity out of range [0,1]: {np.count_nonzero(sel)} instances"