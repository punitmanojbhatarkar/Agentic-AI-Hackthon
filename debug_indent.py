lines = open('agents/critic.py').readlines()
for i in range(300, 320):
    indent = len(lines[i]) - len(lines[i].lstrip())
    print(f'{i+1:3d} [indent={indent:2d}]: {lines[i].rstrip()[:70]}')
