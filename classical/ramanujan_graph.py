"""Lubotzky-Phillips-Sarnak Ramanujan graphs — the combinatorial ground truth
for the roadmap Phase 2 qLDPC experiment.

This module is to Phase 2 what ``classical/ramanujan_series.py`` is to Phase 1:
exact, dependency-light, CPU-only mathematics that later stages are checked
*against* rather than a competitor to them. Nothing here touches CUDA or
CUDA-Q, and nothing here is timed — it builds a graph and proves the graph is
what it claims to be.

**Why this graph.** A ``k``-regular graph's adjacency spectrum always contains
the trivial eigenvalue ``k``. Alon-Boppana says the rest cannot all be small:
for large graphs the second-largest absolute eigenvalue is at least
``2*sqrt(k-1) - o(1)``. A graph that *attains* that bound —

    every non-trivial eigenvalue satisfies  |lambda| <= 2*sqrt(k-1)

— is called **Ramanujan**, and is an optimal spectral expander. LPS (1988)
gave the first explicit infinite family; the name honours Ramanujan because
the proof rests on the Ramanujan conjecture for Fourier coefficients of
modular forms, proved by Deligne. That is the thread this repo follows from
the 1914 series into quantum error correction: expansion is exactly the
property that makes a sparse parity-check matrix a *good* LDPC code.

**The construction.** For distinct primes ``p, q`` both congruent to 1 mod 4,
with ``q > 2*sqrt(p)``:

1. Jacobi's four-square theorem gives exactly ``p + 1`` integer solutions to
   ``a^2 + b^2 + c^2 + d^2 = p`` with ``a`` odd and positive and ``b, c, d``
   even. These are the generators.
2. Each solution becomes a 2x2 matrix over ``F_q`` using a square root ``i`` of
   ``-1`` mod ``q`` (which exists precisely because ``q = 1 mod 4``).
3. The Cayley graph of the group these matrices generate, inside ``PGL(2, q)``,
   is ``(p + 1)``-regular and Ramanujan.

Whether that group is ``PSL(2, q)`` or all of ``PGL(2, q)`` is decided by the
Legendre symbol ``(p|q)``: a quadratic residue gives the non-bipartite
``PSL(2, q)`` on ``q(q^2 - 1)/2`` vertices, a non-residue the bipartite
``PGL(2, q)`` on ``q(q^2 - 1)``. This module does not assume which — it
generates the subgroup by breadth-first search and then *checks* the order
against the predicted formula, so a construction bug surfaces as a failed
assertion rather than a subtly wrong graph.
"""

import math
from collections import deque
from typing import Any

import numpy as np
import numpy.typing as npt
from sympy import isprime

#: A projective 2x2 matrix over ``F_q``, row-major: ``(a, b, c, d)`` is
#: ``[[a, b], [c, d]]``. Elements are canonicalized by :func:`_canonical` so a
#: projective class has exactly one representative and can be a dict key.
Matrix = tuple[int, int, int, int]

#: Identity of ``PGL(2, q)``, already canonical for every ``q``.
IDENTITY: Matrix = (1, 0, 0, 1)


def _validate_primes(p: int, q: int) -> None:
    """Reject parameter pairs the LPS construction is not defined for.

    Each condition below is load-bearing, not defensive padding:
    ``p % 4 == 1`` is what makes the four-square count exactly ``p + 1``,
    ``q % 4 == 1`` is what makes ``sqrt(-1)`` exist mod ``q``, and
    ``q > 2*sqrt(p)`` is what keeps the Cayley graph simple — below it the
    generators can collide and produce multi-edges, which would silently
    invalidate the spectrum.
    """
    for name, value in (("p", p), ("q", q)):
        if not isprime(value):
            raise ValueError(f"{name} must be prime, got {value}")
        if value % 4 != 1:
            raise ValueError(f"{name} must be congruent to 1 mod 4, got {value}")
    if p == q:
        raise ValueError(f"p and q must be distinct, both are {p}")
    if q * q <= 4 * p:
        raise ValueError(f"need q > 2*sqrt(p) for a simple graph, got q={q}, p={p}")


def four_square_solutions(p: int) -> list[tuple[int, int, int, int]]:
    """The ``p + 1`` generators from Jacobi's four-square theorem.

    Returns every integer solution of ``a^2 + b^2 + c^2 + d^2 = p`` with ``a``
    odd and positive and ``b, c, d`` even. Jacobi's theorem guarantees there
    are exactly ``p + 1`` of them for ``p = 1 mod 4``; the count is asserted by
    :func:`lps_generators` rather than assumed here.
    """
    limit = math.isqrt(p)
    # The even sweep must *start* even: range(-limit, limit + 1, 2) walks odd
    # values whenever limit is odd (p = 13 gives limit = 3, hence -3, -1, 1, 3
    # and zero solutions found). Rounding the bound down to even fixes the
    # parity of the whole range.
    even_limit = limit - limit % 2
    even_range = range(-even_limit, even_limit + 1, 2)

    solutions: list[tuple[int, int, int, int]] = []
    for a in range(1, limit + 1, 2):
        remainder_a = p - a * a
        for b in even_range:
            remainder_b = remainder_a - b * b
            if remainder_b < 0:
                continue
            for c in even_range:
                remainder_c = remainder_b - c * c
                if remainder_c < 0:
                    continue
                d = math.isqrt(remainder_c)
                if d * d != remainder_c:
                    continue
                # sorted() rather than a bare set so d == 0 contributes one
                # solution, not two, and iteration order stays deterministic.
                for signed_d in sorted({d, -d}):
                    if signed_d % 2 == 0:
                        solutions.append((a, b, c, signed_d))
    return sorted(solutions)


def sqrt_minus_one(q: int) -> int:
    """Smallest ``i`` with ``i^2 = -1 (mod q)``.

    Exists for every prime ``q = 1 mod 4``, which :func:`_validate_primes`
    has already enforced by the time this is reached.
    """
    for candidate in range(1, q):
        if (candidate * candidate + 1) % q == 0:
            return candidate
    raise ValueError(f"no square root of -1 mod {q}")


def is_quadratic_residue(p: int, q: int) -> bool:
    """Legendre symbol ``(p|q) == 1``, by Euler's criterion.

    Decides the whole shape of the output graph: residue means the generated
    subgroup is ``PSL(2, q)`` and the graph is non-bipartite; non-residue means
    ``PGL(2, q)`` and bipartite.
    """
    return pow(p % q, (q - 1) // 2, q) == 1


def expected_order(p: int, q: int) -> int:
    """Predicted vertex count: ``|PSL(2,q)|`` or ``|PGL(2,q)|`` per ``(p|q)``."""
    full = q * (q * q - 1)
    return full // 2 if is_quadratic_residue(p, q) else full


def _canonical(matrix: Matrix, q: int) -> Matrix:
    """Unique representative of a matrix's projective class in ``PGL(2, q)``.

    Scales so the first nonzero entry (row-major) is 1. Two matrices differing
    by a scalar therefore canonicalize identically, which is what makes a
    projective group element usable as a dict key during the search.
    """
    for entry in matrix:
        if entry % q:
            inverse = pow(entry, q - 2, q)
            a, b, c, d = matrix
            return (a * inverse % q, b * inverse % q, c * inverse % q, d * inverse % q)
    raise ValueError(f"zero matrix has no projective class: {matrix}")


def _multiply(left: Matrix, right: Matrix, q: int) -> Matrix:
    """Matrix product mod ``q``, canonicalized."""
    a1, b1, c1, d1 = left
    a2, b2, c2, d2 = right
    return _canonical(
        (
            (a1 * a2 + b1 * c2) % q,
            (a1 * b2 + b1 * d2) % q,
            (c1 * a2 + d1 * c2) % q,
            (c1 * b2 + d1 * d2) % q,
        ),
        q,
    )


def lps_generators(p: int, q: int) -> list[Matrix]:
    """The ``p + 1`` LPS generator matrices in ``PGL(2, q)``.

    Solution ``(a, b, c, d)`` maps to ``[[a + b*i, c + d*i], [-c + d*i, a - b*i]]``
    mod ``q``, whose determinant is ``a^2 + b^2 + c^2 + d^2 = p`` — nonzero mod
    ``q`` because ``p`` and ``q`` are distinct primes, so every generator is
    genuinely invertible.

    The set is closed under inversion (solutions come in ``±`` pairs), which is
    what makes the resulting Cayley graph undirected.
    """
    _validate_primes(p, q)
    solutions = four_square_solutions(p)
    if len(solutions) != p + 1:
        raise ValueError(f"expected {p + 1} four-square solutions for p={p}, found {len(solutions)}")

    root = sqrt_minus_one(q)
    generators = [
        _canonical(
            (
                (a + b * root) % q,
                (c + d * root) % q,
                (-c + d * root) % q,
                (a - b * root) % q,
            ),
            q,
        )
        for a, b, c, d in solutions
    ]
    if len(set(generators)) != p + 1:
        raise ValueError(f"generators collided mod q={q} for p={p}; the q > 2*sqrt(p) bound was too weak")
    return generators


def cayley_graph(p: int, q: int) -> tuple[list[Matrix], list[list[int]]]:
    """Build the LPS Cayley graph, returning ``(vertices, adjacency)``.

    Breadth-first search from the identity generates exactly the subgroup the
    LPS matrices span, so the vertex set never has to be enumerated and then
    filtered for subgroup membership — the search finds it. The order is then
    checked against :func:`expected_order`, which is what turns "the group
    theory says PSL or PGL" from a comment into a test.

    ``adjacency[i]`` lists the neighbours of vertex ``i``, one per generator,
    so the graph is ``(p + 1)``-regular by construction.
    """
    generators = lps_generators(p, q)

    index: dict[Matrix, int] = {IDENTITY: 0}
    vertices: list[Matrix] = [IDENTITY]
    queue: deque[Matrix] = deque([IDENTITY])
    while queue:
        current = queue.popleft()
        for generator in generators:
            neighbour = _multiply(current, generator, q)
            if neighbour not in index:
                index[neighbour] = len(vertices)
                vertices.append(neighbour)
                queue.append(neighbour)

    order = expected_order(p, q)
    if len(vertices) != order:
        raise ValueError(f"generated subgroup has {len(vertices)} elements, expected {order} for p={p}, q={q}")

    adjacency = [[index[_multiply(vertex, generator, q)] for generator in generators] for vertex in vertices]
    return vertices, adjacency


def adjacency_matrix(adjacency: list[list[int]]) -> npt.NDArray[np.float64]:
    """Dense symmetric adjacency matrix from the neighbour lists."""
    size = len(adjacency)
    matrix = np.zeros((size, size), dtype=np.float64)
    for vertex, neighbours in enumerate(adjacency):
        for neighbour in neighbours:
            matrix[vertex, neighbour] = 1.0
    return matrix


def ramanujan_bound(degree: int) -> float:
    """The Alon-Boppana / Ramanujan threshold ``2*sqrt(k - 1)``."""
    return 2.0 * math.sqrt(degree - 1)


def spectral_data(p: int, q: int) -> dict[str, Any]:
    """Diagonalize the graph and report whether it is Ramanujan.

    The trivial eigenvalues are excluded before the bound is applied: every
    ``k``-regular graph has ``+k``, and a bipartite one also has ``-k``. Which
    case applies is not guessed — it follows from ``(p|q)``, the same quantity
    that already decided the vertex count, so the two agree or the build fails.

    Eigenvalues come from ``eigvalsh`` (symmetric solver), so they are real by
    construction rather than by discarding an imaginary part.
    """
    vertices, adjacency = cayley_graph(p, q)
    degree = p + 1
    bipartite = not is_quadratic_residue(p, q)

    eigenvalues = np.linalg.eigvalsh(adjacency_matrix(adjacency))
    trivial = 2 if bipartite else 1
    # eigvalsh returns ascending order: the trivial +k is last, and -k (if the
    # graph is bipartite) is first. Strip exactly those.
    non_trivial = eigenvalues[1:-1] if bipartite else eigenvalues[:-1]
    second_largest = float(np.max(np.abs(non_trivial)))
    bound = ramanujan_bound(degree)

    return {
        "p": p,
        "q": q,
        "vertices": len(vertices),
        "degree": degree,
        "bipartite": bipartite,
        "group": "PGL(2,q)" if bipartite else "PSL(2,q)",
        "edges": len(vertices) * degree // 2,
        "largest_eigenvalue": float(eigenvalues[-1]),
        "trivial_eigenvalues": trivial,
        "second_largest_abs_eigenvalue": second_largest,
        "ramanujan_bound": bound,
        # Tolerance absorbs LAPACK's floating-point error only. A graph that is
        # genuinely not Ramanujan misses this by an O(1) margin, not by 1e-9.
        "is_ramanujan": bool(second_largest <= bound + 1e-9),
        "spectral_gap": float(eigenvalues[-1] - eigenvalues[-2]),
    }


def report(p: int = 5, q: int = 13) -> dict[str, Any]:
    """Diagnostic for ``python -m classical.ramanujan_graph``.

    Defaults to ``(p, q) = (5, 13)``, the canonical worked example in the LPS
    literature: 5 is a non-residue mod 13, so this is the bipartite
    ``PGL(2, 13)`` graph on 2184 vertices, 6-regular.

    Note that ``q`` must be ``1 mod 4`` for ``sqrt(-1)`` to exist, which rules
    out every prime between 5 and 13 — 13 is the smallest legal partner for
    ``p = 5``, not merely a convenient one.
    """
    return spectral_data(p, q)


if __name__ == "__main__":
    for key, value in report().items():
        print(f"{key}: {value}")
