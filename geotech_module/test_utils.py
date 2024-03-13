import math
import utils

def test_is_courbes_croissantes():
    a = [0.0, -1.0, -1.0, -8.0, -8.0, -12.0, -12.0, -20.0]
    b = [0.0, 0.0, 1.2, 1.2, 0.8, 0.8, 1.8, 1.8]
    assert utils.rising_curve(a) == False
    assert utils.rising_curve(b) == True

def test_inverser_liste():
    a = [0.0, -1.0, -1.0, -8.0, -8.0, -12.0, -12.0, -20.0]
    b = [0.0, 0.0, 1.2, 1.2, 0.8, 0.8, 1.8, 1.8]
    a_inverse = [-20.0, -12.0, -12.0, -8.0, -8.0, -1.0, -1.0, 0.0]
    b_inverse = [1.8, 1.8, 0.8, 0.8, 1.2, 1.2, 0.0, 0.0]
    assert utils.invert_list(a) == a_inverse
    assert utils.invert_list(b) == b_inverse

def test_integrale_courbe():
    a = [0.0, -1.0, -1.0, -8.0, -8.0, -12.0, -12.0, -20.0]
    b = [0.0, 0.0, 1.2, 1.2, 0.8, 0.8, 1.8, 1.8]
    x1 = 0.0
    x2 = -20.0
    expected = 26.0
    actual = utils.trapezoidal_integration(a, b, x1, x2)
    assert expected == actual

def test_valeur_moyenne():
    a = [0.0, -1.0, -1.0, -8.0, -8.0, -12.0, -12.0, -20.0]
    b = [0.0, 0.0, 1.2, 1.2, 0.8, 0.8, 1.8, 1.8]
    x1 = 0.0
    x2 = -20.0
    expected = 1.3
    actual = utils.mean_value(a, b, x1, x2)
    assert expected == actual

def test_loi_frottement_lateral():
    qs = 0.200
    Kt = 4.0
    assert utils.skin_friction_law(-0.010, qs, Kt) == 0.000
    assert utils.skin_friction_law(0.0125, qs, Kt) == 0.050
    assert utils.skin_friction_law(0.0875, qs, Kt) == 0.150
    assert utils.skin_friction_law(0.2000, qs, Kt) == 0.200


def test_loi_effort_pointe():
    qp = 0.200
    Kp = 4.0
    assert utils.end_bearing_law(-0.010, qp, Kp) == 0.000
    assert utils.end_bearing_law(0.0125, qp, Kp) == 0.050
    assert utils.end_bearing_law(0.0875, qp, Kp) == 0.150
    assert utils.end_bearing_law(0.2000, qp, Kp) == 0.200


def test_loi_frottement_lateral():
    assert math.isclose(utils.skin_friction_law(-0.01, 200, 5000), 0)
    assert math.isclose(utils.skin_friction_law(0.01, 200, 5000), 50)
    assert math.isclose(utils.skin_friction_law(0.07, 200, 5000), 150)
    assert math.isclose(utils.skin_friction_law(0.15, 200, 5000), 200)


def test_loi_effort_pointe():
    assert math.isclose(utils.end_bearing_law(-0.01, 200, 5000), 0)
    assert math.isclose(utils.end_bearing_law(0.01, 200, 5000), 50)
    assert math.isclose(utils.end_bearing_law(0.07, 200, 5000), 150)
    assert math.isclose(utils.end_bearing_law(0.15, 200, 5000), 200)
