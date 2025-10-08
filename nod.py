def nod(a,b):
    if b == 0:
        return a
    return nod(b, a % b)

def nok(a, b):
    if a == 0 or b==0:
        return 0
    return abs(a*b)//nod(a, b)

def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

l = []
for i in range(7):
    l.append(fib(i))
print(l)

print(nod(21,49))
print(nok(21,49))