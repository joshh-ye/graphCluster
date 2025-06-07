import numpy as np
import time

array1 = np.array([1,2,3])
array2 = np.array([1,2,3])

startTime = time.time()
np.dot(array1, array2)
endtime = time.time()

print(endtime - startTime)