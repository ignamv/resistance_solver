from rsolver import Resistor, RNetwork
import pytest
import numpy.testing


def test_equality():
    assert Resistor(3, 0, 1) == Resistor(3, 1, 0)

def test_solve_series():
    net = RNetwork()
    net.add(Resistor(3, 0, 1))
    net.add(Resistor(3, 1, 2))
    net.add(Resistor(3, 2, 3))
    net.add(Resistor(3, 3, 4))
    assert net.solve_series()
    assert net.resistors == {Resistor(12, 0, 4)}
    assert not net.solve_series()


def test_solve_parallel():
    net = RNetwork()
    net.add(Resistor(4., 0, 1))
    net.add(Resistor(8., 1, 0))
    net.add(Resistor(8., 0, 1))
    assert net.solve_parallel()
    assert net.resistors == {Resistor(2., 0, 1)}
    assert not net.solve_parallel()


def test_wye_to_delta():
    net = RNetwork()
    r1 = net.add(Resistor(2., 0, 3))
    r2 = net.add(Resistor(4., 1, 3))
    r3 = net.add(Resistor(8., 2, 3))
    assert net.find_wye() == [r1,r2,r3]
    net.add_terminal(3)
    with pytest.raises(ValueError):
        net.find_wye()
    net.remove_terminal(3)
    net.convert_wye_to_delta(r1, r2, r3)
    assert net.resistors == {
        Resistor(28., 1, 2),
        Resistor(14., 2, 0),
        Resistor(7., 0, 1),
    }


solvecases = [
    # 2 || 2
    ([
        [2., 0, 1],
        [2., 0, 1],
    ], [0, 1], [[1.,-1.],[-1., 1.]]),
    # 3 + 5
    ([
        [3., 0, 1],
        [5., 1, 2],
    ], [0, 2], [[0.125,-0.125],[-0.125, 0.125]]),
    # 6 + (6 || 3)
    ([
        [6., 0, 1],
        [6., 1, 2],
        [3., 1, 2],
    ], [0, 2], [[0.125,-0.125],[-0.125, 0.125]]),
    # Triangle, one side has two series R
    ([
        [1., 0, 1],
        [.5, 1, 2],
        [.5, 2, 3],
        [1., 3, 0],
    ], [0, 1, 3], [[2.,-1.,-1.],[-1.,2.,-1.],[-1.,-1.,2.]]),
    # Bridge, requires Wye to Delta conversion
    ([
        [1., 0, 1],
        [1., 0, 2],
        [1., 1, 2],
        [1., 3, 1],
        [1., 3, 2],
    ], [0, 3], [[1., -1.], [-1., 1.]]),
    # 3 equal parallel branches of 3 resistors
    # Connections between them make no difference because balance ensures I=0
    ([
        # Branch 1
        [1., 0, 1],
        [1., 1, 2],
        [1., 2, 3],
        # Branch 2
        [1., 0, 4],
        [1., 4, 5],
        [1., 5, 3],
        # Branch 3
        [1., 0, 6],
        [1., 6, 7],
        [1., 7, 3],
        # Connect the ends of the first column of resistors
        [1., 1, 4],
        [1., 4, 6],
        # Connect the ends of the second column of resistors
        [1., 2, 5],
        [1., 5, 7],
    ], [0, 3], [[1., -1.], [-1., 1.]]),
]


@pytest.mark.parametrize('rs,terminals,ymatrix', solvecases)
def test_solve(rs, terminals, ymatrix):
    net = RNetwork()
    for res in rs:
        net.add(Resistor(*res))
    for terminal in terminals:
        net.add_terminal(terminal)
    net.solve()
    for ii, t1 in enumerate(terminals):
        for jj, t2 in enumerate(terminals):
            if ii == jj:
                continue
            rs = net.find_parallel(t1, t2)
            admittance = ymatrix[ii][jj]
            if admittance == 0:
                assert not rs
                continue
            assert len(rs) == 1
            numpy.testing.assert_almost_equal(list(rs)[0].r, -1 / admittance)
