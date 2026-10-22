"""Independent scalar observer of saved completed-tick frames. No inference loop."""

def neighbor(p,direction,w,n):
    if direction==0:return p-1 if p%w else -1
    if direction==1:return p+1 if p%w<w-1 else -1
    if direction==2:return p-w if p>=w else -1
    return p+w if p+w<n else -1


def frame(block,ports,old,maze,p):
    r=[0]*64
    for k in range(8):r[k]=int(old[ports[k],p])
    r[8]=r[11]=1;r[9]=int(p==maze.start);r[10]=int(p==maze.goal)
    for gene in block:
        op,dst,a,b,c,_,gate=gene.row()
        if gate!=64 and not r[gate]:continue
        if op==0:r[dst]=r[a]
        elif op==1:r[dst]=a
        elif op==2:r[dst]=min(65535,r[a]+r[b])
        elif op==3:r[dst]=max(0,r[a]-r[b])
        elif op in (4,5,15,17):
            positive=[]
            for direction in range(4):
                q=neighbor(p,direction,maze.w,len(maze.cells))
                value=int(old[ports[a],q]) if q>=0 and maze.cells[q] else 0
                if value:positive.append((value,direction+1))
            smallest=min(positive,key=lambda x:x[0]) if positive else (0,0)
            r[dst]=len(positive) if op==17 else smallest[1] if op==5 else smallest[0]
        elif op in (6,7,14):
            q=neighbor(p,c if op==7 else b,maze.w,len(maze.cells))
            value=int(old[ports[a],q]) if q>=0 and maze.cells[q] else 0
            r[dst]=int(value==b) if op==7 else value
        elif op==8:r[dst]=int(r[a]==r[b])
        elif op==9:r[dst]=int(bool(r[a]) and bool(r[b]))
        elif op==10:r[dst]=int(bool(r[a]) or bool(r[b]))
        elif op==11:r[dst]=int(not r[a])
        elif op==12:r[dst]=r[b] if r[a] else r[c]
        elif op==16:r[dst]=int(bool(r[a])!=bool(r[b]))
        else:raise AssertionError(op)
    return r
