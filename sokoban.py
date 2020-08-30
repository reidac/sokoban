# -*- python -*-


# A Sokoban solver, maybe.

# To start, a "board" is an arrangement of squares.  Squares can
# either be inaccessible, or accessible.  Accessible squares can be
# target squares or board squares.  Accessible squares can be occupied
# by crates or by the player.  There are special squares, typically
# adjacent to walls where there are no targets, which are "shadow",
# i.e. putting a crate there precludes a solution.

# There are quite a few combos, encoded into strings thus:

# 'X' or ' ' (space) Inaccessible
#
# 'p'  Shadow, board accessible to player but not to crate.
# 'P'  Shadow occupied by the player.
# 
#  .   Unoccupied board.
#  *   Player-occupied board.
#  %   Crate-occupied board.
#  
#  o   Unoccupied target.
#  +   Player-occupied target.
#  =   Crate-occupied target.

# Boards can be read in from files.  Boards can be converted to
# integers by assigning each accessible square a bit position, and
# setting the corresponding bit position to '1' if it's occupied and
# '0' otherwise.  The position of the player is part of state info for
# the purpose of detecting duplicates, but not for detecting whether
# the board is solved -- a board is solved when all the targets are
# occupied, and all of the crates are on targets, irrespective of the
# player position.

import bitarray
import sys

class State:
    # States are slightly smart. They know how many times they've been
    # compared, and can record how old they are.
    def __init__(self,data):
        self.data = data
        self.ccount = 0
        self.age = 0
    def __hash__(self):
        return hash(self.data[0].to01()) ^ hash(self.data[1])
    def __eq__(self,other):
        self.ccount += 1
        return self.data==other.data
    def __neq__(self,other):
        self.ccount += 1
        return self.data!=other.data
    def __repr__(self):
        return "%s.%s" % (str(self.data[0]), str(self.data[1]))
        
class Board:
    # The principal data structure, self.data, is a list of lists of
    # characters, read in according to the above scheme, but into
    # bitarray objects, one each for the player, the boxes, and the
    # targets.  There's also a mapping array that maps (r,c) pairs to
    # bit array indices.  Also an array for "shadow" spaces where
    # putting a box results in an unsolvable state, like in corners
    # or against walls with no targets.
    def __init__(self, fd):
        self.ppos = None
        self.boxes = bitarray.bitarray()
        self.targets = bitarray.bitarray()
        self.player = bitarray.bitarray()
        self.shadow = bitarray.bitarray()
        self.rctoline = {} # Indexed by rc tuples, values are ints.
        self.linetorc = [] # Eventually a list of rc tuples.
        if fd:
            count = 0
            row = 0
            for s in fd.xreadlines():
                if s[0]=='#':
                    continue # '#' is a comment character in the file.
                col = 0
                for c in s[:-1]:
                    if c in ' X':
                        col += 1 # Increment the column, but do nothing else.
                        continue # Don't care about inaccessible spaces.

                    if c in '*+P': # Player
                        self.ppos = (row,col)
                        self.player.append(True)
                    else:
                        self.player.append(False)

                    if c in '=%': # Crate
                        self.boxes.append(True)
                    else:
                        self.boxes.append(False)

                    if c in 'o=+': # Target
                        self.targets.append(True)
                    else:
                        self.targets.append(False)

                    if c in 'pP': # Shadow spaces where crates cannot go.
                        self.shadow.append(True)
                    else:
                        self.shadow.append(False)
                        
                    rc = (row,col)
                    self.rctoline[rc] = count
                    self.linetorc.append(rc)

                    col += 1
                    count += 1
                row += 1
        assert(len(self.targets)==len(self.boxes))
        assert(len(self.player)==len(self.boxes))
        assert(len(self.shadow)==len(self.boxes))

    def write(self, fd):
        # Get the bounds.
        lr = None; lc = None; hr = None; hc = None
        for k in self.rctoline.keys():
            if k[1] > hc or hc == None: hc = k[1]
            if k[1] < lc or lc == None: lc = k[1]
            if k[0] > hr or hr == None: hr = k[0]
            if k[0] < lr or lr == None: lr = k[0]

        for r in range(lr-1, hr+2):
            stro = ''
            for c in range(lc-1, hc+2):
                try:
                    idx = self.rctoline[ (r,c) ]
                except KeyError:
                    cr = 'X'
                else:
                    b = self.boxes[idx]
                    p = self.player[idx]
                    t = self.targets[idx]
                    s = self.shadow[idx]
                    # b and p are mutually exclusive.
                    if t:
                        if b:
                            cr = '='
                        elif p:
                            cr = '+'
                        else:
                            cr = 'o'
                    elif s: # s and b are mutually exclusive.
                        if p:
                            cr = 'P'
                        else:
                            cr = 'p'
                    else:
                        if b:
                            cr = '%'
                        elif p:
                            cr = '*'
                        else:
                            cr = '.'
                            
                stro += cr
            print >> fd, stro
                    


    def get_state(self):
        pcount = self.rctoline[self.ppos]
        st = (self.boxes[:],pcount)
        return State(st) 
        
    def set_state(self, st):
        self.boxes = st.data[0][:]
        self.ppos = self.linetorc[st.data[1]]
        self.player.setall(False)
        self.player[st.data[1]] = True

        
    def solved(self):
        return self.boxes == self.targets


    def move_up(self):
        pc = self.ppos
        tg = (self.ppos[0]-1,self.ppos[1])
        tg2 = (self.ppos[0]-2,self.ppos[1])

        return self._move(pc,tg,tg2)

    def move_down(self):
        pc = self.ppos
        tg = (self.ppos[0]+1,self.ppos[1])
        tg2 = (self.ppos[0]+2,self.ppos[1])

        return self._move(pc,tg,tg2)

    def move_left(self):
        pc = self.ppos
        tg = (self.ppos[0], self.ppos[1]-1)
        tg2 = (self.ppos[0], self.ppos[1]-2)

        return self._move(pc,tg,tg2)

    def move_right(self):
        pc = self.ppos
        tg = (self.ppos[0], self.ppos[1]+1)
        tg2 = (self.ppos[0], self.ppos[1]+2)
        
        return self._move(pc,tg,tg2)

    def _move(self, pc, tg, tg2):
        # Returns None if the move is rejected, True if it changes the
        # board state.  pc, tg, and tg2 are board-position tuples.
        pcx = self.rctoline[pc]
        try:
            tgx = self.rctoline[tg]
        except KeyError: # Adjacent space is inaccessible. Reject.
            return None
    
        if self.boxes[tgx]:
            try: # Adjacent space has a box. Look at next neighbor.
                tg2x = self.rctoline[tg2]
            except KeyError: # Next neighbor is inaccessible. Reject.
                return None
            
            if self.boxes[tg2x]:  # Next neighbor is a box. Reject.
                return None
            elif self.shadow[tg2x]: # Next neighbor is shadow, reject.
                return None
            else:
                self.boxes[tgx] = False
                self.boxes[tg2x] = True
                self.player[pcx] = False
                self.player[tgx] = True
                self.ppos = tg

                return True

        else: # Adjacent space is empty, just move the player.
            self.player[pcx] = False
            self.player[tgx] = True
            self.ppos = tg
            return True
            


def search_level(b, states):
    # The passed-in "states" is a dictionary of move lists keyed by
    # state objects.  For each state in the dictionary keys, make all
    # possible moves.  If the move gives a null result, discard it.
    # If we've already seen the move, discard it. Otherwise, add it to
    # the list of states for the next round.
    global allstates

    # print >> sys.stdout, "Searching a new level."
    ret = dict()
    for (s,m) in states.items():

        b.set_state(s)

        # print >> sys.stdout, "\nStarting state:"
        # b.write(sys.stdout)
        
        r = b.move_up()
        if r:
            # print >> sys.stdout, "\nUpward move:"
            # b.write(sys.stdout)
            n = b.get_state()
            if not n in allstates:
                # print >> sys.stdout, "New!"
                allstates.add(n)
                lst = m[:]
                lst.append('up')
                ret[n] = lst

        b.set_state(s)
        r = b.move_down()
        if r:
            # print >> sys.stdout, "\nDownward move:"
            # b.write(sys.stdout)
            n = b.get_state()
            if not n in allstates:
                # print >> sys.stdout, "New!"
                allstates.add(n)
                lst = m[:]
                lst.append('down')
                ret[n] = lst

        b.set_state(s)
        r = b.move_right()
        if r:
            # print >> sys.stdout, "\nRightward move:"
            # b.write(sys.stdout)
            n = b.get_state()
            if not n in allstates:
                # print >> sys.stdout, "New!"
                allstates.add(n)
                lst = m[:]
                lst.append('right')
                ret[n] = lst

        b.set_state(s)
        r = b.move_left()
        if r:
            # print >> sys.stdout, "\nLeftward move:"
            # b.write(sys.stdout)
            n = b.get_state()
            if not n in allstates:
                # print >> sys.stdout, "New!"
                allstates.add(n)
                lst = m[:]
                lst.append('left')
                ret[n] = lst

    return ret
    
                
    

if __name__=="__main__":
    b = Board(sys.stdin)
    allstates = set()

    start_s = b.get_state()

    allstates.add(start_s)
    states = {start_s:[]}

    b.write(sys.stdout)
    
    limit = 500
    solved = False
    levels = 0
    while(not solved and levels < limit):
        print "Level %d." % levels
        new_states = search_level(b, states)
        for (s,m) in new_states.items():
            b.set_state(s)
            if b.solved():
                print m
                solved = True
                sys.exit()
                
        states = new_states
        levels += 1

        print "States: ", len(allstates)
        print 
