from collections import namedtuple
import random
import itertools


class Resistor(namedtuple('Resistor', ['r','n1','n2'])):
    @property
    def nodes(self):
        return self[1:3]

    def __eq__(self, other):
        return self.r == other.r and set(self.nodes) == set(other.nodes)

    def __hash__(self):
        return hash((self.r, tuple(sorted(self.nodes))))


def otherthan(x, y1, y2):
    """Return whichever one of y1, y2 that differs from x"""
    if x == y1:
        return y2
    elif x == y2:
        return y1
    else:
        raise Exception()
        

class RNetwork(object):
    def __init__(self):
        self.nodes = {}
        self.resistors = set()
        self.terminals = set()
        
    def add(self, res):
        self.nodes.setdefault(res.n1, []).append(res)
        self.nodes.setdefault(res.n2, []).append(res)
        self.resistors.add(res)
        return res
        
    def remove(self, res):
        for node in [res.n1, res.n2]:
            self.nodes[node].remove(res)
            if not self.nodes[node]:
                del self.nodes[node]
        self.resistors.discard(res)

    def add_terminal(self, node):
        self.terminals.add(node)

    def remove_terminal(self, node):
        self.terminals.discard(node)
        
    def find_parallel(self, n1, n2):
        """Resistors connected between n1 and n2"""
        return [r for r in self.nodes[n1]
                if n2 in r.nodes]

    def usage(self, node):
        """How many resistors/terminals touch node"""
        return len(self.nodes[node]) + (node in self.terminals)
    
    def find_series(self, startnode):
        """Longest chain of series resistors passing through node
        
        Return resistors, first node, last node"""
        if self.usage(startnode) != 2 or startnode in self.terminals:
            return [], startnode, startnode
        ret = list(self.nodes[startnode])
        lastnode = startnode
        # Search forward
        while True:
            node = otherthan(lastnode, *ret[-1].nodes)
            if self.usage(node) != 2 or node in self.terminals:
                lastnode = node
                break
            ret.append(otherthan(ret[-1], *self.nodes[node]))
            lastnode = node
        firstnode = startnode
        # Search backward
        while True:
            node = otherthan(firstnode, *ret[0].nodes)
            if self.usage(node) != 2 or node in self.terminals:
                firstnode = node
                break
            ret.insert(0, otherthan(ret[0], *self.nodes[node]))
            firstnode = node
        return ret, firstnode, lastnode
    
    def join_parallel(self, branches):
        if len(branches) == 1:
            return
        conductance = 0
        for branch in branches:
            conductance += 1 / branch.r
            self.remove(branch)
        self.add(Resistor(1 / conductance, branch.n1, branch.n2))
        
    def join_series(self, resistors, firstnode, lastnode):
        r = 0
        for resistor in resistors:
            r += resistor.r
            self.remove(resistor)
        self.add(Resistor(r, firstnode, lastnode))
        
    @staticmethod
    def wye_to_delta(r1, r2, r3):
        rp = r1 * r2 + r2 * r3 + r3 * r1
        return rp / r1, rp / r2, rp / r3
        
    @staticmethod
    def delta_to_wye(r1, r2, r3):
        rs = r1 + r2 + r3
        return r2 * r3 / rs, r3 * r1 / rs, r1 * r2 / rs
        
    def convert_wye_to_delta(self, r1, r2, r3):
        center = set(r1.nodes) & set(r2.nodes) & set(r3.nodes)
        assert len(center) == 1
        center = list(center)[0]
        n1 = otherthan(center, *r1.nodes)
        n2 = otherthan(center, *r2.nodes)
        n3 = otherthan(center, *r3.nodes)
        ra, rb, rc = self.wye_to_delta(r1.r, r2.r, r3.r)
        self.remove(r1)
        self.remove(r2)
        self.remove(r3)
        self.add(Resistor(ra, n2, n3))
        self.add(Resistor(rb, n3, n1))
        self.add(Resistor(rc, n1, n2))

    def free_node(self):
        for ii in itertools.count(len(self.nodes)):
            if ii not in self.nodes:
                return ii

    def convert_delta_to_wye(self, ra, rb, rc):
        center = self.free_node()
        r1, r2, r3 = self.delta_to_wye(ra.r, rb.r, rc.r)
        nodes = {node for r in (ra, rb, rc) for node in r.nodes}
        assert len(nodes) == 3
        self.remove(ra)
        self.remove(rb)
        self.remove(rc)
        self.add(Resistor(r1, center, next(iter(nodes - set(ra.nodes)))))
        self.add(Resistor(r2, center, next(iter(nodes - set(rb.nodes)))))
        self.add(Resistor(r3, center, next(iter(nodes - set(rc.nodes)))))
        
    def solve_series(self):
        found = False
        for node in list(self.nodes):
            if node not in self.nodes:
                continue
            rs, first, last = self.find_series(node)
            if not rs:
                continue
            self.join_series(rs, first, last)
            found = True
        return found
            
    def solve_parallel(self):
        found = False
        resistors = self.resistors.copy()
        for resistor in resistors:
            if resistor not in self.resistors:
                continue
            rs = self.find_parallel(*resistor.nodes)
            if len(rs) == 1:
                continue
            self.join_parallel(rs)
            found = True
        return found
    
    def find_wye(self):
        """Find and return 3 resistors forming a Wye"""
        # TODO: check no resistors are in parallel?
        for node, resistors in self.nodes.items():
            if len(resistors) == 3 and node not in self.terminals:
                return resistors[:3]
        raise ValueError('No wyes found')

    def find_delta(self):
        """Find and return 3 resistors forming a delta. Randomized."""
        resistors = list(self.resistors)
        random.shuffle(resistors)
        for r1 in resistors:
            nodes1 = {node for res_ in self.nodes[r1.n1] 
                           if res_ != r1
                           for node in res_.nodes
                           if node not in r1.nodes}
            nodes2 = {node for res_ in self.nodes[r1.n2] 
                           if res_ != r1
                           for node in res_.nodes
                           if node not in r1.nodes}
            #import pdb; pdb.set_trace()
            intersection = nodes1 & nodes2
            if not intersection:
                continue
            node = random.choice(list(intersection))
            r2 = next(iter(set(self.nodes[r1.n1]) & set(self.nodes[node])))
            r3 = next(iter(set(self.nodes[r1.n2]) & set(self.nodes[node])))
            return r1, r2, r3
        raise ValueError("No deltas found")

    def prune_dangling(self):
        """Remove non-terminal nodes with only 1 resistor"""
        nodes = list(self.nodes)
        for node in nodes:
            resistors = self.nodes[node]
            if node not in self.terminals and len(resistors) == 1:
                self.remove(resistors[0])

    def solve(self):
        while True:
            self.prune_dangling()
            while self.solve_parallel() or self.solve_series():
                pass
            try:
                rs = self.find_wye()
                self.convert_wye_to_delta(*rs)
            except ValueError:
                # No wyes. Are we done?
                if set(self.nodes) == self.terminals:
                    # Yes
                    break
                # Stuck, convert a random delta to a Wye
                rs = self.find_delta()
                self.convert_delta_to_wye(*rs)
