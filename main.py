"""q1729 status check: classical series sanity + CUDA-Q and NIM availability."""

from analysis import narrator
from classical.ramanujan_series import correct_digits, pi_approximation, series_term
from quantum import backend


def main() -> None:
    print("--- q1729: status ---")

    print(f"Ramanujan series term 0: {series_term(0)}")
    print(f"pi from 2 terms: {pi_approximation(2, precision=20)} ({correct_digits(2)} digits correct)")

    for key, value in backend.report().items():
        print(f"cudaq {key}: {value}")

    for key, value in narrator.report().items():
        print(f"nim {key}: {value}")


if __name__ == "__main__":
    main()
