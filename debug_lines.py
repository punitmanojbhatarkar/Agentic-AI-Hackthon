lines = open('agents/critic.py').readlines()
for i in range(300, 320):
    print(f'{i+1:3d}: {repr(lines[i][:80])}')
