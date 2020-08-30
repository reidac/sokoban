# Sokoban Solver

This repo contains a brute-force, breadth-first search based Sokoban
solver, which I wrote because I got stuck on a Sokoban level
( [this one](https://sokoban.info/?8_1) ) and couldn't figure it out.

It's Python 2, and doesn't require anything especially 
fancy in terms of dependencies, although it does make some
use of the `bitarray` module, with the idea of storing board-state
data efficiently.

It has two major abstractions, the "board", which is mostly geometry,
mapping (x,y) coordinates to the index of sites on the board which
can in principle be occupied, along with the location of the
targets, and the "state" of a board, which is the position of the 
player and all of the crates.  The `Board` class has rules for
evolving the state in response to moves.

The search is straightforward -- there is a list of all the states
that have already been seen, and the algorithm is, at each level,
for each state in the prior level, try all possible moves.  For
each move that generates a new, previously unseen state, add that 
state to the current level, and to the list of states that have 
been seen.  Invalid moves or moves that generate previously-seen
states are discarded. 

The loop continues until either the iteration limit is reached,
or one of the states is the solved state -- in the latter case,
the list of moves that gave rise to the state is dumped.

Input boards are read from standard input, and have a file format
as follows:

```
 'X' or ' ' (space) Inaccessible

 'p'  Shadow, board accessible to player but not to crate.
 'P'  Shadow occupied by the player.
 
  .   Unoccupied board.
  *   Player-occupied board.
  %   Crate-occupied board.
  
  o   Unoccupied target.
  +   Player-occupied target.
  =   Crate-occupied target.
``` 

The "shadow" spaces are optional, but they greatly increase the
efficiency of the algorithm.

Speaking of which, it's pretty inefficient, it uses a lot of memory
stumbling around in stupid parts of the search space.

A smarter algorithm would focus on crate pushes, rather than
player moves, and search over the space of allowable pushes,
which is smaller and more relevant than the space of 
allowable moves.
