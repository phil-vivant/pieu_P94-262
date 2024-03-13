import math
import soil

courbe_x = [0, 2, 4, 6, 8, 10]
courbe_y = [3, 2, 5, 4, 6, 2]

def test_integrale_courbe():
    assert math.isclose(soil.trapezoidal_integration(courbe_x, courbe_y, 3, 8), 23.25)
    assert math.isclose(soil.trapezoidal_integration(courbe_x, courbe_y, 0, 10), 39.)
    assert math.isclose(soil.trapezoidal_integration(courbe_x, courbe_y, 4, 4.1), 0.4975)

def test_valeur_moyenne():
    assert math.isclose(soil.mean_value(courbe_x, courbe_y, 3, 8), 4.65)
    assert math.isclose(soil.mean_value(courbe_x, courbe_y, 0, 10), 3.9)
    assert math.isclose(soil.mean_value(courbe_x, courbe_y, 4, 4.1), 4.975)

sol_1 = soil.Soil("Remblais",               0.0, -1.00, 'Q1', 0.0, 0.0, 5., 2/3, 'fin')
sol_2 = soil.Soil("Argiles",               -1.0, -8.00, 'Q2', 0.8, 1.2, 8., 2/3, 'fin')
sol_3 = soil.Soil("Argiles d'altérations", -8.0, -12.0, 'Q3', 0.6, 0.8, 6., 2/3, 'granulaire')
sol_4 = soil.Soil("Argiles carbonatées",  -12.0, -20.0, 'Q4', 1.3, 1.8, 10, 2/3, 'granulaire')

def test_check_courbe_frottement():
    assert sol_1.check_courbe_frottement() == True
    assert sol_2.check_courbe_frottement() == True
    assert sol_3.check_courbe_frottement() == True
    assert sol_4.check_courbe_frottement() == True
    AssertionError(sol_4.check_courbe_frottement())

def test_alpha_pieu_sol():
    assert sol_1.alpha_pieu_sol(19) == 2.7
    assert sol_2.alpha_pieu_sol(19) == 2.9
    assert sol_3.alpha_pieu_sol(19) == 2.4
    assert sol_4.alpha_pieu_sol(19) == 2.4

def test_kp_max():
    assert sol_1.kp_max(8) == 1.15
    assert sol_2.kp_max(8) == 1.10
    assert sol_3.kp_max(8) == 1.45
    assert sol_4.kp_max(8) == 1.45

def test_a_parameter():
    assert sol_1._a_parameter == 0.003
    assert sol_2._a_parameter == 0.010
    assert sol_3._a_parameter == 0.007
    assert sol_4._a_parameter == 0.008

def test_b_parameter():
    assert sol_1._b_parameter == 0.04
    assert sol_2._b_parameter == 0.06
    assert sol_3._b_parameter == 0.07
    assert sol_4._b_parameter == 0.08

def test_c_parameter():
    assert sol_1._c_parameter == 3.5
    assert sol_2._c_parameter == 1.2
    assert sol_3._c_parameter == 1.3
    assert sol_4._c_parameter == 3.0

def test_fonction_fsol():
    pass

def test_frottement_maxi():
    assert sol_1.frottement_maxi(19) == 0.200
    assert sol_2.frottement_maxi(19) == 0.380
    assert sol_3.frottement_maxi(19) == 0.320
    assert sol_4.frottement_maxi(19) == 0.320

def test_module_kt():
    assert math.isclose(sol_1.module_kt(0.25), 40.0)
    assert math.isclose(sol_2.module_kt(0.25), 64.0)
    assert math.isclose(sol_3.module_kt(0.25), 19.2)
    assert math.isclose(sol_4.module_kt(0.25), 32.0)

def test_module_kq():
    assert math.isclose(sol_1.module_kq(0.25), 220.0)
    assert math.isclose(sol_2.module_kq(0.25), 352.0)
    assert math.isclose(sol_3.module_kq(0.25), 115.2)
    assert math.isclose(sol_4.module_kq(0.25), 192.0)

def test_module_kf():
    assert math.isclose(round(sol_1.module_kf(0.80), 2), 20.09)
    assert math.isclose(round(sol_2.module_kf(0.80), 2), 32.14)
    assert math.isclose(round(sol_3.module_kf(0.80), 2), 24.11)
    assert math.isclose(round(sol_4.module_kf(0.80), 2), 40.18)
