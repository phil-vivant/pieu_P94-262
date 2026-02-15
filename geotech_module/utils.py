import math
import numpy as np
from PyNite import FEModel3D


def max_list(list_of_float: list[float]) -> float:
    """
    Returns the maximum value in a list
    """
    maximum = -1 * math.inf
    for element in list_of_float:
        maximum = max(element, maximum)
    return maximum


def min_list(list_of_float: list[float]) -> float:
    """
    Returns the minimum value in a list
    """
    minimum = math.inf
    for element in list_of_float:
        minimum = min(element, minimum)
    return minimum


def trapezoidal_integration(cb_x: list[float], cb_y: list[float], x1: float, x2: float) -> float:
    """
    Retourne l'intégrale d'une courbe entre deux abscisses x1 et x2.
    """
    if rising_curve(cb_x) == True:
        xmin = x1
        xmax = x2
    else:
        cb_x = invert_list(cb_x)
        cb_y = invert_list(cb_y)
        xmin = x2
        xmax = x1

    y1 = np.interp(xmin, cb_x, cb_y)
    y2 = np.interp(xmax, cb_x, cb_y)
    x_acc = [xmin]
    y_acc = [y1]

    for idx, y in enumerate(cb_y):
        if cb_x[idx] < xmin:
            pass
        elif cb_x[idx] > xmax:
            pass
        else:
            x_acc.append(cb_x[idx])
            y_acc.append(cb_y[idx])

    x_acc.append(xmax)
    y_acc.append(y2)

    return np.trapz(y_acc, x_acc)


def mean_value(cb_x: list[float], cb_y: list[float], x1: float, x2: float) -> float:
    """
    Retourne la valeur moyenne d'une courbe entre deux abscisses x1 et x2.
    [Intégrale de la courbe entre x1 et x2] / [x2 - x1]
    """
    return trapezoidal_integration(cb_x, cb_y, x1, x2) / abs(x2 - x1)


def rising_curve(cb_x: list[float]) -> bool:
    """
    Vérifie que la liste de nombres est croissante.
    """
    test = 1
    x_i_moins_un = cb_x[0]
    for x_i in cb_x:
        if x_i >= x_i_moins_un:
            test *= 1
        else:
            test *= 0
    return test == 1


def invert_list(liste_a_inverser):
    """
    Renvoie la liste en ordre inverse
    """
    liste_acc = []
    for element in reversed(liste_a_inverser):
        liste_acc.append(element)
    return liste_acc


def calc_shear_modulus(nu: float, E: float) -> float:
    """
    Calculate the shear modulus from the Poisson's ratio and the elastic modulus
    @param: nu: Poisson's ratio
    @param : E: elastic modulus
    return the shear modulus
    """
    G = E / (2 * (1 + nu))
    return G


def get_nodes(locations: list) -> dict[str, float]:
    """
    Returns a dictionary listing the nodes in the structure
    """
    nodes = {}
    for idx, loc in enumerate(locations):
        nodes.update({f"N{idx}": loc})
    return nodes


def get_node_name_at_location(nodes: dict, location: float) -> str:
    """
    Returns the name of the node at a given location
    """
    for node, loc in nodes.items():
        if loc == location:
            return node


def skin_friction_law(s: float, qs: float, ks: float) -> float:
    """
    Loi de mobilisation du frottement latéral en fonction du déplacement vertical,
    proposée par Franc et Zhao - 1982
    La loi est symétrique (positive / négative).
    Lateral skin friction mobilisation, relative to the vertical displacement,
    proposed by Franc et Zhao - 1982
    """
    return np.sign(s) * tri_linear_law(abs(s), qs/2, ks, qs, ks/5)


def end_bearing_law(s: float, qp: float, kp: float) -> float:
    """
    Loi de mobilisation de l'effort de pointe en fonction du déplacement vertical,
    proposée par Franc et Zhao - 1982
    La loi renvoie 0 pour un déplacement négatif.
    End-bearing resistance mobilisation, relative to the vertical displacement,
    proposed by Franc et Zhao - 1982
    """
    return tri_linear_law(s, qp/2, kp, qp, kp/5)


def tri_linear_law(
        s: float, q1: float, k1: float, q2: float|None=None, k2: float|None=None
) -> float:
    """
    Loi de comportement du type tri-linéaire. Elle est par exemple utilisée par
    Franc et Zhao - 1982 et recommandée par la NF P94-262.
    Remarque: il est possible d'obtenir une loi bi-linéaire. Il suffit pour cela
    de ne pas renseigner q2 et k2.
    Tri-linear behavior law proposed by Franc and Zhao - 1982 and recommended by
    NF P94-262.
    Note: it is possible to get a bi-linear law. Simply leave q2 and k2 blank.
    """
    try:
        s1 = q1 / k1
    except ZeroDivisionError:
        raise ZeroDivisionError('k1 doit être non nul!')
    
    if k2 is None:
        q2 = q1
        k2 = 1

    try:
        s2 = s1 + (q2-q1) / k2
    except ZeroDivisionError:
        raise ZeroDivisionError('k2 doit être non nul!')

    if s <= 0.:
        return 0.
    if s <= s1:
        return s * k1
    elif s <= s2:
        return q1 + (s - s1) * k2
    else:
        return q2


def build_pile(
        pile_data: dict,
        slices,
        horizontal_force,
        bending_moment,
        situation,
) -> FEModel3D:
    """
    Returns a pile finite element model for the data passed to the function.
    It is assumed to be a vertical pile, loaded on top, with continuous horizontal spring supports.
    Les données d'entrée pour définir le modèle PyNite sont les suivantes:
        - La définition du pieu :   pieu.data_pieu
        - La liste des sols:        pieu.lithology = [Soil]
        - La liste des slices :     pieu.slices = [TranchePieu]
        - horizontal_force :        effort horizontal appliqué en tête
        - bending_moment :          moment fléchissant appliqué en tête
        - situation :               ['court terme', 'long terme', 'elu', 'sismique']
    """
    E = pile_data["E"]
    B = pile_data["B"]
    Iz = pile_data["Iz"]
    Iy = pile_data["Iy"]
    A = pile_data["A"]
    J = pile_data["J"]
    nu = pile_data["nu"]
    rho = pile_data["rho"]

    # Création du modèle 3D
    pile_model = FEModel3D()

    # Création du matériau de la poutre
    G = calc_shear_modulus(nu, E)
    pile_model.add_material('pile_material', E, G, nu, rho)

    # Définition des NOEuds
    node_locations = [slices[0].z_top]
    linear_springs = [0]
    for slice in slices:
        node_locations.append(slice.z_middle)
        linear_springs.append(slice.linear_spring(B, situation))
    node_locations.append(slices[-1].z_bottom)
    linear_springs.append(0)
    nodes = get_nodes(node_locations)
    first_node = get_node_name_at_location(nodes, slices[0].z_top)
    last_node = get_node_name_at_location(nodes, slices[-1].z_bottom)
    for node, loc in nodes.items():
        pile_model.add_node(node, loc, 0, 0)

    # Création des appuis
    idx = 0
    for node_name, location in nodes.items():
        if node_name == first_node:
            pile_model.def_support(node_name=node_name, support_DX = True)
        elif node_name == last_node:
            pile_model.def_support(node_name, support_DZ = True, support_DX = True, support_RX = True)
        else:
            spring = linear_springs[idx]
            pile_model.def_support_spring(node_name, 'DY', spring, direction = None)
        idx +=1

    # Création de la barre
    pile_model.add_member(name='pile', i_node=first_node, j_node=last_node, material_name='pile_material', Iy=Iy, Iz=Iz, J=J, A=A)

    # Création des cas de charges
    pile_model.add_member_pt_load(Member='pile', Direction='Fy', P=horizontal_force, x=0.)
    pile_model.add_member_pt_load(Member='pile', Direction='Mz', P=bending_moment, x=0.)

    return pile_model


def get_model_curves(fem_model: FEModel3D, top_level: float=0, step: float=0.01) -> list[list[float]]:
    """
    Returns the curves data for the bending moment, the shear forces and the deflection along the pile.
    """
    height_pile = model_length(fem_model)
    moment = []
    shear = []
    deflection = []
    abscisse = []
    x = 0
    z = top_level
    while z >= top_level - height_pile:
        mx = fem_model.Members['pile'].moment('Mz', x, 'Combo 1')
        vx = fem_model.Members['pile'].shear('Fy', x, 'Combo 1')
        fx = fem_model.Members['pile'].deflection('dy', x, 'Combo 1')
        moment.append(mx)
        shear.append(vx)
        deflection.append(fx)
        abscisse.append(z)
        x += step
        z -= step
    return abscisse, moment, shear, deflection

def get_soil_pressure(fem_model: FEModel3D) -> list[list[float]]:
    """
    Returns the pressure on the soil along the pile axis
    """
    pression = []
    abscisse_p = []
    for node in fem_model.Nodes:
        pression.append(fem_model.Nodes[str(node)].RxnFY)
    return abscisse_p, pression

def model_length(fem_model: FEModel3D) -> float:
    """
    Returns the length of a specified member in a FEModel3D.
    The length is calculated from the x coordinates of the node.
    """
    return fem_model.Members['pile'].L()
