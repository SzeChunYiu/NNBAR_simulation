"""Small command-line demonstration for event-selection cuts."""

from .event_selection import apply_selection_cuts
from .event_variables import EventVariables


if __name__ == "__main__":
    signal_ev = EventVariables(
        invariant_mass=1850.0,
        sphericity=0.65,
        total_energy=1900.0,
        scint_energy=400.0,
        lg_energy=1200.0,
        longitudinal_energy=300.0,
        transverse_energy=1500.0,
        top_bottom_asymmetry=0.1,
        forward_backward_asymmetry=0.05,
        n_charged=3,
        n_neutral=2,
        n_pions=4,
        n_protons=1,
        vertex_r=5.0,
        n_tracks_to_vertex=3,
    )

    background_ev = EventVariables(
        invariant_mass=300.0,
        sphericity=0.1,
        total_energy=500.0,
        scint_energy=100.0,
        lg_energy=50.0,
        longitudinal_energy=400.0,
        transverse_energy=100.0,
        top_bottom_asymmetry=0.9,
        forward_backward_asymmetry=0.8,
        n_charged=1,
        n_neutral=0,
        n_pions=0,
        n_protons=0,
        vertex_r=100.0,
        n_tracks_to_vertex=1,
    )

    print("Signal event selection:")
    result = apply_selection_cuts(signal_ev)
    print(f"  Result: {result}")
    for cut, passed in result.cut_results.items():
        status = "PASS" if passed else "FAIL"
        value = result.cut_values[cut]
        print(f"    {cut}: {status} (value={value:.2f})")

    print("\nBackground event selection:")
    result = apply_selection_cuts(background_ev)
    print(f"  Result: {result}")
    for cut, passed in result.cut_results.items():
        status = "PASS" if passed else "FAIL"
        value = result.cut_values[cut]
        print(f"    {cut}: {status} (value={value:.2f})")
