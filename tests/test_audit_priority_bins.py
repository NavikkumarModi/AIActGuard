from aiactguard.audit_priority.bins import bin_index


def test_bin_index_covers_full_range():
    assert bin_index(0.0, n_bins=10) == 0
    assert bin_index(0.99, n_bins=10) == 9
    assert bin_index(1.0, n_bins=10) == 9  # clamped, not out of range


def test_bin_index_middle_values():
    assert bin_index(0.5, n_bins=10) == 5
    assert bin_index(0.45, n_bins=10) == 4


def test_bin_index_respects_n_bins():
    assert bin_index(0.5, n_bins=4) == 2
    assert bin_index(0.99, n_bins=4) == 3
