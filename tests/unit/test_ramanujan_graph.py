import math

import numpy as np
import pytest

from classical import ramanujan_graph as rg
from classical.ramanujan_graph import (
    IDENTITY,
    _canonical,
    _multiply,
    _validate_primes,
    adjacency_matrix,
    cayley_graph,
    expected_order,
    four_square_solutions,
    is_quadratic_residue,
    lps_generators,
    ramanujan_bound,
    report,
    spectral_data,
    sqrt_minus_one,
)

#: The two smallest legal LPS pairs. ``(17, 13)`` is the quadratic-residue
#: case (non-bipartite PSL(2,13), 1092 vertices); ``(5, 13)`` is the canonical
#: textbook pair and the non-residue case (bipartite PGL(2,13), 2184).
PSL_PAIR = (17, 13)
PGL_PAIR = (5, 13)


def test_four_square_solution_count_matches_jacobi():
    for p in (5, 13, 17, 29):
        assert len(four_square_solutions(p)) == p + 1


def test_four_square_solutions_satisfy_the_constraints():
    for a, b, c, d in four_square_solutions(13):
        assert a > 0 and a % 2 == 1
        assert b % 2 == 0 and c % 2 == 0 and d % 2 == 0
        assert a * a + b * b + c * c + d * d == 13


def test_four_square_solutions_are_distinct():
    solutions = four_square_solutions(17)
    assert len(set(solutions)) == len(solutions)


def test_sqrt_minus_one_squares_to_minus_one():
    for q in (5, 13, 17, 29):
        root = sqrt_minus_one(q)
        assert (root * root + 1) % q == 0


def test_sqrt_minus_one_rejects_3_mod_4():
    # 7 is 3 mod 4, so -1 is a non-residue and no square root exists. This is
    # exactly the condition _validate_primes enforces upstream.
    with pytest.raises(ValueError, match="no square root"):
        sqrt_minus_one(7)


def test_quadratic_residue_decides_the_group():
    assert is_quadratic_residue(17, 13) is True
    assert is_quadratic_residue(5, 13) is False


def test_expected_order_halves_for_the_residue_case():
    full = 13 * (13 * 13 - 1)
    assert expected_order(17, 13) == full // 2
    assert expected_order(5, 13) == full


@pytest.mark.parametrize(
    ("p", "q", "message"),
    [
        (4, 13, "p must be prime"),
        (5, 12, "q must be prime"),
        (7, 13, "p must be congruent to 1 mod 4"),
        (5, 7, "q must be congruent to 1 mod 4"),
        (5, 5, "must be distinct"),
        (13, 5, r"q > 2\*sqrt\(p\)"),
    ],
)
def test_validate_primes_rejects_illegal_pairs(p, q, message):
    with pytest.raises(ValueError, match=message):
        _validate_primes(p, q)


def test_canonical_collapses_scalar_multiples():
    q = 13
    base = (1, 2, 3, 4)
    for scale in range(1, q):
        scaled = tuple(entry * scale % q for entry in base)
        assert _canonical(scaled, q) == _canonical(base, q)


def test_canonical_rejects_the_zero_matrix():
    with pytest.raises(ValueError, match="no projective class"):
        _canonical((0, 0, 0, 0), 13)


def test_canonical_leading_entry_is_one():
    assert _canonical((5, 0, 0, 5), 13) == IDENTITY
    # First nonzero entry is b, not a — the scan is row-major, not diagonal.
    assert _canonical((0, 3, 3, 0), 13)[1] == 1


def test_multiply_by_identity_is_a_no_op():
    for generator in lps_generators(*PGL_PAIR):
        assert _multiply(generator, IDENTITY, PGL_PAIR[1]) == generator
        assert _multiply(IDENTITY, generator, PGL_PAIR[1]) == generator


def test_generators_are_distinct_and_count_p_plus_one():
    for p, q in (PSL_PAIR, PGL_PAIR):
        generators = lps_generators(p, q)
        assert len(generators) == p + 1
        assert len(set(generators)) == p + 1


def test_generator_set_is_closed_under_inversion():
    # This is what makes the Cayley graph undirected: solution (a,b,c,d) and
    # (a,-b,-c,-d) give mutually inverse matrices, and both are in the set.
    p, q = PGL_PAIR
    generators = set(lps_generators(p, q))
    for generator in generators:
        a, b, c, d = generator
        determinant = (a * d - b * c) % q
        inverse_det = pow(determinant, q - 2, q)
        inverse = _canonical(
            (d * inverse_det % q, -b * inverse_det % q, -c * inverse_det % q, a * inverse_det % q),
            q,
        )
        assert inverse in generators


def test_generators_raise_when_jacobi_count_is_wrong(monkeypatch):
    monkeypatch.setattr(rg, "four_square_solutions", lambda p: [(1, 0, 0, 0)])
    with pytest.raises(ValueError, match="expected 6 four-square solutions"):
        lps_generators(*PGL_PAIR)


def test_generators_raise_when_they_collide(monkeypatch):
    # q > 2*sqrt(p) is what keeps the generators distinct mod q. Bypass the
    # validator to prove the collision guard behind it actually fires rather
    # than being dead code protected by an earlier check.
    #
    # (29, 5) is a pair that genuinely collides, found by sweeping rather than
    # assumed: violating the bound is necessary but not sufficient for a
    # collision — (13, 5) and (17, 5) are illegal yet still yield p + 1
    # distinct generators, so the guard is a real second line of defence.
    monkeypatch.setattr(rg, "_validate_primes", lambda p, q: None)
    with pytest.raises(ValueError, match="generators collided"):
        lps_generators(29, 5)


def test_cayley_graph_is_regular_and_has_the_predicted_order():
    for p, q in (PSL_PAIR, PGL_PAIR):
        vertices, adjacency = cayley_graph(p, q)
        assert len(vertices) == expected_order(p, q)
        assert len(set(vertices)) == len(vertices)
        assert all(len(neighbours) == p + 1 for neighbours in adjacency)


def test_cayley_graph_edges_are_symmetric():
    p, q = PSL_PAIR
    _, adjacency = cayley_graph(p, q)
    neighbour_sets = [set(neighbours) for neighbours in adjacency]
    for vertex, neighbours in enumerate(neighbour_sets):
        for neighbour in neighbours:
            assert vertex in neighbour_sets[neighbour]


def test_cayley_graph_raises_when_the_subgroup_order_is_unexpected(monkeypatch):
    monkeypatch.setattr(rg, "expected_order", lambda p, q: 7)
    with pytest.raises(ValueError, match="expected 7"):
        cayley_graph(*PGL_PAIR)


def test_adjacency_matrix_is_symmetric_and_correctly_weighted():
    _, adjacency = cayley_graph(*PSL_PAIR)
    matrix = adjacency_matrix(adjacency)
    assert np.array_equal(matrix, matrix.T)
    assert set(np.unique(matrix)) <= {0.0, 1.0}
    assert np.all(matrix.sum(axis=1) == PSL_PAIR[0] + 1)


def test_ramanujan_bound_is_two_root_k_minus_one():
    assert ramanujan_bound(6) == pytest.approx(2.0 * math.sqrt(5))
    assert ramanujan_bound(18) == pytest.approx(2.0 * math.sqrt(17))


def test_psl_graph_is_ramanujan_and_not_bipartite():
    data = spectral_data(*PSL_PAIR)
    assert data["group"] == "PSL(2,q)"
    assert data["bipartite"] is False
    assert data["vertices"] == 1092
    assert data["degree"] == 18
    assert data["edges"] == 1092 * 18 // 2
    assert data["trivial_eigenvalues"] == 1
    # The trivial eigenvalue of a k-regular graph is exactly k.
    assert data["largest_eigenvalue"] == pytest.approx(18.0)
    assert data["is_ramanujan"] is True
    assert data["second_largest_abs_eigenvalue"] <= data["ramanujan_bound"]


def test_pgl_graph_is_ramanujan_and_bipartite():
    data = spectral_data(*PGL_PAIR)
    assert data["group"] == "PGL(2,q)"
    assert data["bipartite"] is True
    assert data["vertices"] == 2184
    assert data["degree"] == 6
    assert data["trivial_eigenvalues"] == 2
    assert data["largest_eigenvalue"] == pytest.approx(6.0)
    assert data["is_ramanujan"] is True
    assert data["second_largest_abs_eigenvalue"] <= data["ramanujan_bound"]


def test_spectral_gap_is_positive():
    assert spectral_data(*PSL_PAIR)["spectral_gap"] > 0.0


def test_report_defaults_to_the_canonical_pair():
    data = report()
    assert (data["p"], data["q"]) == PGL_PAIR
    assert data["is_ramanujan"] is True
