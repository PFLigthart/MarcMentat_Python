"""Script to create a singly unit of the soft actuator that will be optimised"""

import os
from scipy import optimize
from py_mentat import py_connect, py_disconnect, py_send, py_get_int, py_get_float
import time


def was_code_successfull(file_path, word, max_time=20):
    """Search status file to see if code ran successfully"""
    complete = False
    time_elapsed = 0
    start_time = time.time()

    while (complete == False) and (time_elapsed < max_time):
        with open(file_path, "r") as file:
            # read all content of a file
            content = file.read()
            # check if string present in a file
            if word in content:
                print("EXIT CODE - 3004")
                complete = True
            else:
                # pause for a short while
                time.sleep(0.1)
                time_elapsed = time.time() - start_time
    if complete == True:
        return True
    else:
        print("Ran Out of Time")
        return False


def does_file_exist(file_name, file_extension, max_time=15):
    """
    Check a file exits. Runs untill found or max time reached.

    Args:
        file_name: The file name.
        file_extension: The extension of the file, e.g. sts, t16, etc.
        max_time: The maximum ammount of time the model can run.
    """

    file_exists = False
    elapsed_time = 0
    start_time = time.time()

    # print(f"Looking for - {file_name}.{file_extension}")

    while (file_exists == False) and (elapsed_time < max_time):
        if os.path.isfile(f"{file_name}_job1.{file_extension}"):
            # print(f"Found: {file_name}.{file_extension}")
            file_exists = True
        else:
            # pause for a short ammount of time
            time.sleep(0.1)
            elapsed_time = time.time() - start_time

    return file_exists


def setup_geometry_and_mesh(N5XY, h, w, N6XY, N7XY, N8XY):
    # set analysis to planar
    py_send("*set_model_analysis_dimension planar")
    # create the geometry
    py_send("*set_solid_type sheet_rect")
    py_send(f"*add_solids 0 0 0 30 30 {N5XY[0]} {N5XY[1]} 0 {w} {h}")
    py_send("*solids_subtract 1 2 #")
    # create the four corner nodes.
    py_send("*add_nodes 0 0 0 30 0 0 30 30 0 0 30 0")
    # create the four internal corner nodes (these will be optimised)
    py_send(f"*add_nodes {N5XY[0]} {N5XY[1]} 0")
    py_send(f"*add_nodes {N6XY[0]} {N6XY[1]} 0")
    py_send(f"*add_nodes {N7XY[0]} {N7XY[1]} 0")
    py_send(f"*add_nodes {N8XY[0]} {N8XY[1]} 0")
    # Automesh
    py_send("@set($automesh_surface_desc,sheet)")
    py_send("@set($automesh_surface_family,quad)")
    py_send("*pt_set_target_element_size_method manual")
    py_send("*pt_set_global_element_size_sheet 1")
    py_send("*pt_mesh_sheet linear quad")
    py_send("solid1 #")
    # remove any duplicate nodes
    py_send("*sweep_nodes all_existing")

    return


def apply_boundary_conditions():
    """Apply the fixed boundary conditions and the required loads."""

    # fixed boundary condition.

    # select nodes in path from node 1-4
    py_send("*select_method_path *select_nodes 1 4 #")
    py_send("*new_apply *apply_type fixed_displacement")
    py_send("*apply_dof x *apply_dof_value x 0")
    py_send("*apply_dof y *apply_dof_value y 0")
    py_send("*add_apply_nodes")
    py_send("all_selected #")


def apply_loads(pressure_val):

    # Create the table
    py_send("*new_pre_defined_table linear_ramp_time")
    # egde pressure loads
    internal_edge_pairs = [[8, 5], [5, 6], [6, 7], [7, 8]]
    py_send("*select_clear_nodes")
    py_send("*select_clear_edges")
    for i in internal_edge_pairs:
        py_send(f"*select_edges {i[0]} {i[1]} #")

    py_send("*new_apply *apply_type edge_load *apply_option edge_load_mode:area")
    py_send("*apply_dof p *apply_dof_value p")
    py_send(f"*apply_dof_value p {pressure_val}")
    py_send("*apply_dof_table p linear_ramp_time1")
    py_send("*add_apply_edges all_selected #")


def add_material_properties():
    """Add material properties to the geometry."""
    py_send("*new_mater standard *mater_option general:state:solid")
    py_send("*mater_option general:skip_structural:off")
    py_send("*mater_option structural:type:mooney")
    py_send("*mater_param structural:mooney_c10 80")
    py_send("*mater_param structural:mooney_c01 20")
    py_send("*add_mater_elements all_existing")


def create_geometric_properites(thickness):
    """
    Create geometric properties needed in planar analysis.

    Args:
        thickness: The thickness of the elements.
    """

    py_send("*new_geometry *geometry_type mech_planar_pstrain ")
    py_send(f"*geometry_param norm_to_plane_thick {thickness}")
    py_send("*add_geometry_elements all_existing")


def setup_loadcase():
    """Setup the required load case for the problem"""

    # Create the loadcase
    py_send("*new_loadcase *loadcase_type struc:static")
    py_send("*loadcase_option stepping:multicriteria")


def create_job():
    """Create a job - set up the job parameters"""
    py_send("*new_job structural")
    py_send("*add_job_loadcases lcase1")
    py_send("*job_option nod_quantities:manual")
    py_send("*add_post_nodal_quantity Displacement")
    py_send("*job_option strain:large")

    # create the element types
    py_send("*element_type 118 all_existing")


def run_the_model():
    py_send("*update_job")
    py_send("*save_model")
    py_send("*submit_job 1")


def delete_all(fname):
    """
    Deletes a model by deleting everything in the model and results files.

    Args:
        fname: Model file name
    """
    # close the results
    py_send("*post_close")

    # delete the job
    py_send("*edit_job job1 *remove_current_job")

    # delete the loadcase
    py_send("*edit_loadcase lcase1 *remove_current_loadcase")

    # delete the pressure loads
    py_send("*edit_apply apply2 *remove_current_apply")

    # delete the boundary conditions
    py_send("*edit_apply apply1 *remove_current_apply")

    # delete the table
    py_send("*edit_table linear_ramp_time1 *remove_current_table")

    # delete the geometric properties
    py_send("*edit_geometry geom1 *remove_current_geometry")

    # delete the material
    py_send("*edit_mater material1 *remove_current_mater")
    py_send("yes")

    # delete all elements
    py_send("*remove_elements all_existing #")

    # delete all nodes
    py_send("*remove_nodes all_existing #")

    # delete the solid
    py_send("*remove_solids 1 #")

    # delete the results files
    delete_file(file_name, ".log")
    delete_file(file_name, ".dat")
    delete_file(file_name, ".out")
    delete_file(file_name, ".sts")
    delete_file(file_name, ".t16")
    delete_file(file_name, "_b1.x_t")


def delete_file(file_name, file_extension):
    """
    Delete a file

    Args:
        file_name: The file name.
        file_extension: The file extension. This must inclulde the '.'

    Returns:
        None
    """

    file_path = file_name + "_job1" + file_extension
    if os.path.isfile(file_path):
        os.remove(file_path)
        # print("File has been deleted")
    else:
        print("File does not exist")

    return


def job_status_checks(file_name):
    """See if the job is completed and if successfully"""
    # does a status file exist
    does_file_exist(file_name, "sts", 15)
    path = os.path.abspath(os.getcwd())
    file_path = path + f"\\{file_name}_job1.sts"

    # was the run a success?
    success = was_code_successfull(file_path, "3004")

    return success


def get_x_y_node_displacements():
    """
    Get the x y node displacements of the nodes of interest.

    Displacements are relative to staring positions.

    Args:
        None

    Returns:
        N2X: Node 2 x displacement.
        N2Y: Node 2 y displacement.
        N3X: Node 3 x displacement.
        N3Y: Node 3 y displacement.
    """

    py_send("*post_close")
    py_send("*post_open testing_one_one_job1.t16")
    # py_send("*post_next")
    py_send("*post_skip_to_last")

    # return 1
    # py_send("*fill_view")
    py_send("*post_contour_lines")
    py_send("*post_value Displacement X")
    # Node 2
    n_id = py_get_int("node_id(2)")
    N2X = py_get_float(f"scalar_1({n_id})")
    # Node 3
    n_id = py_get_int("node_id(3)")
    N3X = py_get_float(f"scalar_1({n_id})")

    # Tell marc we want displacement Y
    py_send("*post_value Displacement Y")
    # Node 2
    n_id = py_get_int("node_id(2)")
    N2Y = py_get_float(f"scalar_1({n_id})")
    # Node 3
    n_id = py_get_int("node_id(3)")
    N3Y = py_get_float(f"scalar_1({n_id})")

    n2xy = (N2X, N2Y)
    n3xy = (N3X, N3Y)

    return (n2xy, n3xy)


def get_cutaway_dimensions(t1, t2, t3, t4):
    """
    Get the required coordinates and dimensions of the cutaway in the element

    This function works on the assumption that the elements has dimensions
        30x30 mm.

    Args:
        t1: Thickness of bottom.
        t2: Thickness of right side.
        t3: Thickness of top.
        t4: Thickness of left side.

    Returns:
        N5XY: Node 5 x-y coordinates.
        h: Hight of the cutaway.
        w: With of the cutaway.
    """
    N5XY = (t4, t1)
    h = 30 - t3 - t1
    w = 30 - t2 - t4
    return (N5XY, h, w)


def get_nodes_6_7_8(t1, t2, t3, t4):
    """
    Get the nodal coordinates of nodes 6, 7, 8.

    Args:
        t1: Thickness of bottom.
        t2: Thickness of right side.
        t3: Thickness of top.
        t4: Thickness of left side.

    Returns:
        N6XY: Node 6 coordinates.
        N7XY: Node 7 coordinates.
        N8XY: Node 8 coordinates.
    """
    N6XY = (30 - t2, t1)
    N7XY = (30 - t2, 30 - t3)
    N8XY = (t4, 30 - t3)

    return (N6XY, N7XY, N8XY)


def model_setup(file_name, N5XY, h, w, N6XY, N7XY, N8XY):
    """Setting up the model"""
    # Save the model
    py_send(f'*set_save_formatted off *save_as_model "{file_name}" yes')
    setup_geometry_and_mesh(N5XY, h, w, N6XY, N7XY, N8XY)
    apply_boundary_conditions()
    add_material_properties()
    create_geometric_properites(thickness=2)
    apply_loads(20)
    setup_loadcase()
    create_job()
    return


def mentat_main(N5XY, h, w, N6XY, N7XY, N8XY):
    """
    Simulate a geometry and return the desired nodal displacements.

    Args:
        node_array: Array contaning the geometry node locations (1-8)

    Returns:
        N2X: Node 2 x displacements.
        N2Y: Node 2 y displacements.
        N3X: Node 3 x displacements.
        N3Y: Node 3 y displacements.
    """

    model_setup(file_name, N5XY, h, w, N6XY, N7XY, N8XY)
    run_the_model()
    success = job_status_checks(file_name)
    # Wait untill a .t16 results file has been made.
    proceed = does_file_exist(file_name, "t16", 15)  # if time runs out -> false
    if success and proceed:
        node_displacements = get_x_y_node_displacements()
        return node_displacements
    else:
        print("Problem encountered in code")
        return


def convert_displacements_to_coordinates(n2xy_d, n3xy_d):
    """
    Convert nodal displacements into nodal coodinates.

    This function assumes an element of shape 30x30mm.

    Args:
        n2xy: Original node 2 coordinates.
        n3xy: Original node 3 coordinates.
        n2xy_d: Node 2 x-y, displacements.
        n3xy_d: Node 3 x-y, displacements.

    Returns:
        n2xy: New node 2 coordinates.
        n3xy: New node 3 coordinates.
    """
    # Node 2
    n2x = 30 + n2xy_d[0]
    n2y = n2xy_d[1]

    # Node 3
    n3x = 30 + n3xy_d[0]
    n3y = 30 + n3xy_d[1]

    n2xy = (n2x, n2y)
    n3xy = (n3x, n3y)

    return (n2xy, n3xy)


def fitness_function(t1234_ls, return_node_locations=False):
    """
    The function that will be optimised

    Args:
        t1: Thickness 1
        t2: Thickness 2
        t3: Thickness 3
        t4: Thickness 4

    Returns
        fitness: Sum of the euclidian distances from target nodes.
    """

    t1 = t1234_ls[0]
    t2 = t1234_ls[1]
    t3 = t1234_ls[2]
    t4 = t1234_ls[3]

    N5XY, h, w = get_cutaway_dimensions(t1, t2, t3, t4)
    N6XY, N7XY, N8XY = get_nodes_6_7_8(t1, t2, t3, t4)
    node_disps = mentat_main(N5XY, h, w, N6XY, N7XY, N8XY)
    n2xy, n3xy = convert_displacements_to_coordinates(node_disps[0], node_disps[1])
    optimum = (n2xy, n3xy)

    n2_target = (40, -10)
    n3_target = (40, 40)

    euclid_2 = ((n2_target[0] - n2xy[0]) ** 2 + (n2_target[1] - n2xy[1]) ** 2) ** 0.5
    euclid_3 = ((n3_target[0] - n3xy[0]) ** 2 + (n3_target[1] - n3xy[1]) ** 2) ** 0.5

    fitness = euclid_2 + euclid_3

    delete_all(file_name)

    print(f"Fitness: {fitness}")

    if return_node_locations == True:
        return optimum
    else:
        return fitness


def constraint_1(t1234_ls):
    """
    Esure there is at least a 1mm gap vertically

    Args:
        t1234_ls: All wall thicknesses passed as a list

    Returns:
        constraint_eval: The evaluated constraint.
    """

    constraint_eval = 29 - t1234_ls[0] - t1234_ls[2]

    return constraint_eval


def constraint_2(t1234_ls):
    """
    Esure there is at least a 1mm gap vertically

    Args:
        t1234_ls: All wall thicknesses passed as a list

    Returns:
        constraint_eval: The evaluated constraint.
    """

    constraint_eval = 29 - t1234_ls[1] - t1234_ls[3]

    return constraint_eval


def constraint_3(t1234_ls):
    """
    Ensure a minimum wall thickness of 2mm

    Args:
        t1234_ls: All wall thicknesses passed as a list
    """

    return t1234_ls[0] - 2


def constraint_4(t1234_ls):
    """
    Ensure a minimum wall thickness of 2mm

    Args:
        t1234_ls: All wall thicknesses passed as a list
    """

    return t1234_ls[1] - 2


def constraint_5(t1234_ls):
    """
    Ensure a minimum wall thickness of 2mm

    Args:
        t1234_ls: All wall thicknesses passed as a list
    """

    return t1234_ls[2] - 2


def constraint_6(t1234_ls):
    """
    Ensure a minimum wall thickness of 2mm

    Args:
        t1234_ls: All wall thicknesses passed as a list
    """

    return t1234_ls[3] - 2


if __name__ == "__main__":

    # create a global optimum variable for easy retrival

    # some general setup
    global file_name
    file_name = "testing_one_one"
    py_connect("", 40007)
    py_send('*change_directory "my_marc_2"')

    # Optimiser code

    # Constraints
    con1 = {"type": "ineq", "fun": constraint_1}
    con2 = {"type": "ineq", "fun": constraint_2}
    con3 = {"type": "ineq", "fun": constraint_3}
    con4 = {"type": "ineq", "fun": constraint_4}
    con5 = {"type": "ineq", "fun": constraint_5}
    con6 = {"type": "ineq", "fun": constraint_6}
    cons = [con1, con2, con3, con4, con5, con6]

    # Initial guess
    x0 = [2.0, 7.53576963, 2.0, 4.37180637]

    # Run the optimiser
    solution = optimize.minimize(
        fitness_function, x0, method="COBYLA", constraints=cons
    )
    print(f"The best solution = {solution}")

    answer = fitness_function(solution.x, True)
    print(f"Final Nodal Parameters")

    py_disconnect()
