def is_prime(n):
    """Return True if n is prime, False otherwise."""
    # BUG: for n < 2 this returns True, but 0 and 1 are not prime
    if n < 2:
        return True
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
