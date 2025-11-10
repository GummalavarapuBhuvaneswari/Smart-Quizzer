A = ["eat", "tea", "tan", "ate", "nat", "bat"]
for i in range(len(A)):
   for j in range(i + 1, len(A)):
       if sorted(A[i]) == sorted(A[j]):
           print(f'"{A[i]}" and "{A[j]}" are anagrams.')