import math

import pieu
import soil

sol_1 = soil.Soil("Argile", 0.0, -1.0, 'Q1', 0.5, 1., 5., 2/3)

data_pieu = {
    'Categorie': 19,
    'Eb': 20_000,
    'Dp': 0.15,
    'Ds': 0.25,
}

troncon = pieu.SlicePile(
    z_top=0.,
    delta_h=0.1,
    soil=sol_1,
    data_pieu=data_pieu,
)

troncon.set_Q_bott(0.500)
troncon.set_dz_bott(0.01)
troncon.set_dz_middle(0.011)


def test_set_Q_bott():
    assert troncon.Q_bott == 0.500

def test_set_dz_bott():
    assert troncon.dz_bott == 0.01

def test_set_dz_middle():
    assert troncon.dz_middle == 0.011

def test_categorie_pieu():
    assert troncon.pile_category == 19

def test_Eb():
    assert troncon.Eb == 20_000

def test_Dp():
    assert troncon.Dp == 0.15

def test_Ds():
    assert troncon.Ds == 0.25

def test_qs_max():
    pass

def test_qs_lim():
    pass

def test_module_kt():
    pass

def test_module_kq():
    pass

def test_section_pointe():
    expected = 0.0176715
    actual = round(troncon.section_pointe, 7)
    assert math.isclose(expected, actual)

def test_perimetre():
    expected = 0.785398
    actual = round(troncon.perimetre, 6)
    assert math.isclose(expected, actual)

def test_ksi_a():
    pass

def test_ksi_b():
    assert math.isclose(troncon.ksi_b, 2.77777777778e-6)
