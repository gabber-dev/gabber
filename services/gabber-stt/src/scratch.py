import numpy as np

a = np.array([1, 2, 3], dtype=np.int16).reshape(1, -1)
b = np.array([4, 5, 6], dtype=np.int16).reshape(1, -1)
e = np.empty((0,), dtype=np.int16)

c = np.concatenate((a, b))

print(c)

print(e)
