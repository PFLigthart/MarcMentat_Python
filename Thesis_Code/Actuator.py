"""Script to create a singly unit of the soft actuator that will be optimised"""

import os
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from py_mentat import py_connect, py_disconnect, py_get_float, py_get_int, py_send
from scipy import optimize


def plot_c(cube, col):
    x_s = [j for j in cube[0:4]]
    x_s.append(cube[0])
    y_s = [j for j in cube[4:]]
    y_s.append(cube[4])
    plt.plot(x_s, y_s, col, linestyle="--", alpha=0.8)


def get_angl_midpts(cube, side):
    """
    Calculate the absolute angle and midpoint of the provided side.

    Args:
        cube: The cube node locations [x1, .., x4, y1, .., y2]
        side: The side of interest, 41 or 34.

    Raises:
        ValueError: Incorrect side provided - must be 41 or 32.
            This is if the int passsed to the side argurment is not
            one of the two expected values.

    Returns:
        angl: The absolute angle in radians.
        midpts: The midpoint location.
    """

    if side == 41:
        pt_xa = cube[0]
        pt_ya = cube[4]
        pt_xb = cube[3]
        pt_yb = cube[7]
    elif side == 32:
        pt_xa = cube[1]
        pt_ya = cube[5]
        pt_xb = cube[2]
        pt_yb = cube[6]
    else:
        raise ValueError("Incorrect side provided - must be 41 or 32")

    del_x = pt_xb - pt_xa
    del_y = pt_yb - pt_ya

    if del_x == 0:
        if del_y == 0:
            m_grad = 0
        else:
            m_grad = 1e16  # large number to avoid nan.
    else:
        m_grad = (del_y) / (del_x)

    alpha = np.arctan(m_grad)  # angle between line and positive x direction

    # All iniqualities are "equal to" no sure if some should be without it.
    if del_x >= 0 and del_y >= 0:
        angl = (np.pi / 2) - abs(alpha)
    elif del_x >= 0 and del_y <= 0:
        angl = (np.pi / 2) + abs(alpha)
    elif del_x <= 0 and del_y >= 0:
        angl = ((3 * np.pi) / 2) + abs(alpha)
    elif del_x <= 0 and del_y <= 0:
        angl = ((3 * np.pi) / 2) - abs(alpha)

    # Rotations are applied about the midpoint of nodes 1 and 4.
    # Therefore the required translation is calculated about this point.
    midpts = np.array([[(pt_xa + pt_xb) / 2], [(pt_ya + pt_yb) / 2]])

    return (angl, midpts)


def rotate_then_translate(points, theta, translation):
    """
    Move a quad-4 element in the coordinate plane.
    Rotations are counter-clockwise.
    Args:
        points: The node points of the element. [x1, .., x4, y1, .., y4]
        theta: The angle by which to rotate the element.
        translation: The translation matrix. [[x], [y]]
    Returns:
        new_points: The element points after rotation.
    """
    rotation_matrix = np.array(
        [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
    )

    mid_point = np.array(
        [
            [(points[3] + points[0]) / 2],
            [(points[7] + points[4]) / 2],
        ]
    )

    # first rotate about the mid point the side with verticies 1 and 4.
    new_points = np.zeros(points.shape[0])
    for i in range(int((points.shape[0]) / 2)):
        pt = [points[i], points[i + 4]]  # x, y values
        # shifts rotation point to be about the mid point
        rot_point = np.array([[pt[0] - mid_point[0, 0]], [pt[1] - mid_point[1, 0]]])
        rotated_point = rotation_matrix @ rot_point
        rot_translate_point = np.array(
            [
                [rotated_point[0, 0] + mid_point[0, 0]],
                [rotated_point[1, 0] + mid_point[1, 0]],
            ]
        )
        final_point = np.add(rot_translate_point, translation)
        new_points[i] = final_point[0, 0]
        new_points[i + 4] = final_point[1, 0]

    return new_points


def extract_nodes_from_dat():
    """
    Extract the nodal locations from a dat file into a text file

    Args:
        None

    Returns:
        None: It only changes the file 'coordinates.txt
    """

    datFile = "node_location.dat"
    coordinatesFile = "coordinates.txt"
    marker1 = "coordinates"
    marker2 = "define              node                set"

    with open(datFile, "r") as f1, open(coordinatesFile, "w") as f2:
        main = f1.read()
        start = main.find(marker1) + len(marker1)
        end = main.find(marker2)

        main = main[start:end]
        # time.sleep(1) # Testing if this needs to be here.
        f2.write(main)


def get_node_coords_dataframe():
    """
    Read the nodal coordinate data from a text file into a pandas df

    Args:
        None.

    Returns:
        node_df: The data frame containing the node numbers and coordinates.
    """

    df = pd.read_csv(
        "coordinates.txt",
        delim_whitespace=True,  # separator is whitespace
        header=None,  # no header
        names=["Node", "x", "y", "z"],
    )  # set columns names

    node_df = df.drop(0)  # the top entry is wrong and should be removed.

    return node_df


def find_closest_node(desired_location, node_df):
    """
    Find the closest node to the desired geometry location

    We are dealing with a planar analysis, therefore we ignore the z values

    Args:
        desired_location: The target location of the geometry - tuple.
        node_df: Data frame that contains all the node id's and locations.

    Returns:
        node_id: The id of the closest node.
        min_distance: The distance of the closest node.
    """

    x = desired_location[0]
    y = desired_location[1]

    # large number to ensure a result is found
    min_distance = 100

    for _, row in node_df.iterrows():

        # convert the string to the correct format then convert to float
        x_hat = row["x"]
        x_hat = float(x_hat[:-2] + "e" + x_hat[-2:])
        y_hat = row["y"]
        y_hat = float(y_hat[:-2] + "e" + y_hat[-2:])

        # Calculate the distance from the desired location
        distance = ((x - x_hat) ** 2 + (y - y_hat) ** 2) ** 0.5

        # check if distance is the smallest encountered so far
        if distance < min_distance:
            min_distance = distance
            node_id = row["Node"]

    return (node_id, min_distance)


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
                print("\t\t\tEXIT CODE - 3004")
                complete = True
            else:
                # pause for a short while
                time.sleep(0.1)
                time_elapsed = time.time() - start_time
    if complete == True:
        return True
    else:
        print("Ran out of Time - was_code_successfull")
        return False


def does_file_exist(file_name, file_extension, max_time=15):
    """
    Check a file exits. Runs until found or max time reached.

    Args:
        file_name: The file name.
        file_extension: The extension of the file, e.g. sts, t16, etc.
        max_time: The maximum amount of time the model can run.
    """

    file_exists = False
    elapsed_time = 0
    start_time = time.time()

    while (file_exists == False) and (elapsed_time < max_time):
        if os.path.isfile(f"{file_name}.{file_extension}"):
            file_exists = True
        else:
            # pause for a short ammount of time
            time.sleep(0.1)
            elapsed_time = time.time() - start_time

    return file_exists


def setup_geometry_and_mesh(N5XY, N6XY, N7XY, N8XY):
    # set analysis to planar
    py_send("*set_model_analysis_dimension planar")
    # create the geometry
    py_send("*set_solid_type sheet_rect")
    # Add the main solid
    py_send(f"*add_solids 0 0 0 90 30")
    # Add the cutaway solids
    py_send("*set_solid_type sheet_arb_poly")
    # add cutaway 1
    py_send("*add_solids")
    for i in (0, 30, 60):
        py_send(f"*add_solids")
        py_send(f"{N5XY[0] + i} {N5XY[1]} 0")
        py_send(f"{N6XY[0] + i} {N6XY[1]} 0")
        py_send(f"{N7XY[0] + i} {N7XY[1]} 0")
        py_send(f"{N8XY[0] + i} {N8XY[1]} 0 #")

    # Subtract the three cutouts
    py_send("*solids_subtract 1 2 #")
    py_send("*solids_subtract 1 3 #")
    py_send("*solids_subtract 1 4 #")
    create_nodes(N5XY, N6XY, N7XY, N8XY)
    # # Automesh
    py_send("@set($automesh_surface_desc,sheet)")
    py_send("@set($automesh_surface_family,quad)")
    py_send("*pt_set_target_element_size_method manual")
    py_send("*pt_set_global_element_size_sheet 1")
    py_send("*pt_mesh_sheet linear quad")
    py_send("solid1 #")
    # remove any duplicate nodes
    py_send("*sweep_nodes all_existing #")

    return


def create_nodes(N5XY, N6XY, N7XY, N8XY):
    """
    Create the required nodes for the application of boundary conditions.

    Args:
        N5XY: x-y coordinates for node 5.
        N6XY: x-y coordinates for node 6.
        N7XY: x-y coordinates for node 7.
        N8XY: x-y coordinates for node 8.

    Returns:
        None
    """

    # create the four corner nodes.
    py_send("*add_nodes 0 0 0 90 0 0 90 30 0 0 30 0")
    # create the four internal corner nodes. Cutout 1
    py_send(f"*add_nodes {N5XY[0]} {N5XY[1]} 0")

    py_send(f"*add_nodes {N6XY[0]} {N6XY[1]} 0")
    py_send(f"*add_nodes {N7XY[0]} {N7XY[1]} 0")
    py_send(f"*add_nodes {N8XY[0]} {N8XY[1]} 0")
    # create the four internal corner nodes. Cutout 2
    py_send(f"*add_nodes {N5XY[0] + 30} {N5XY[1]} 0")
    py_send(f"*add_nodes {N6XY[0] + 30} {N6XY[1]} 0")
    py_send(f"*add_nodes {N7XY[0] + 30} {N7XY[1]} 0")
    py_send(f"*add_nodes {N8XY[0] + 30} {N8XY[1]} 0")
    # create the four internal corner nodes. Cutout 2
    py_send(f"*add_nodes {N5XY[0] + 60} {N5XY[1]} 0")
    py_send(f"*add_nodes {N6XY[0] + 60} {N6XY[1]} 0")
    py_send(f"*add_nodes {N7XY[0] + 60} {N7XY[1]} 0")
    py_send(f"*add_nodes {N8XY[0] + 60} {N8XY[1]} 0")

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
    internal_edge_pairs = [
        [8, 5],
        [5, 6],
        [6, 7],
        [7, 8],
        [12, 9],
        [9, 10],
        [10, 11],
        [11, 12],
        [16, 13],
        [13, 14],
        [14, 15],
        [15, 16],
    ]
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
    py_send("*mater_param structural:mooney_c10 0.26056762")  # assuming MPa
    py_send("*mater_param structural:mooney_c01 0.09754981")  # assuming MPa
    py_send("*mater_param structural:mooney_c20 0.05750069")  # assuming MPa
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
    delete_file(file_name, "_job1.log")
    delete_file(file_name, "_job1.dat")
    delete_file(file_name, "_job1.out")
    delete_file(file_name, "_job1.sts")
    delete_file(file_name, "_job1.t16")
    delete_file(file_name, "_job1_b1.x_t")
    delete_file("node_location", ".dat")
    delete_file("node_location", "_b1.x_t")


def delete_file(file_name, file_extension):
    """
    Delete a file

    Args:
        file_name: The file name.
        file_extension: The file extension. This must inclulde the '.'

    Returns:
        None
    """

    file_path = file_name + file_extension
    if os.path.isfile(file_path):
        os.remove(file_path)
    else:
        print("File does not exist")

    return


def job_status_checks(file_name):
    """See if the job is completed and if successfully"""
    # does a status file exist
    does_file_exist(file_name + "_job1", "sts", 15)
    path = os.path.abspath(os.getcwd())
    file_path = path + f"\\{file_name}_job1.sts"

    # was the run a success?
    success = was_code_successfull(file_path, "3004")

    return success


def get_x_y_node_displacements(node_ids):
    """
    Get the x y node displacements of the nodes of interest.

    NB! Displacements are relative to staring positions.

    Args:
        node_ids: The node ids of interest. In the order,
            (node17_id, node18_id, node19_id, node20_id).

    Returns:
        n17xy: node 17 x-y coordinates passed as a tuple (x, y)
        n18xy: node 17 x-y coordinates passed as a tuple (x, y)
        n19xy: node 17 x-y coordinates passed as a tuple (x, y)
        n20xy: node 17 x-y coordinates passed as a tuple (x, y)
    """

    # Setup the post process environment
    py_send("*post_close")
    py_send("*post_open testing_one_one_job1.t16")
    py_send("*post_skip_to_last")
    py_send("*post_contour_lines")

    # Tell mark we want displacement X
    py_send("*post_value Displacement X")

    # Node 17
    n_id = py_get_int(f"node_id({node_ids[0]})")
    N17X = py_get_float(f"scalar_1({n_id})")
    # Node 18
    n_id = py_get_int(f"node_id({node_ids[1]})")
    N18X = py_get_float(f"scalar_1({n_id})")
    # Node 19
    n_id = py_get_int(f"node_id({node_ids[2]})")
    N19X = py_get_float(f"scalar_1({n_id})")
    # Node 20
    n_id = py_get_int(f"node_id({node_ids[3]})")
    N20X = py_get_float(f"scalar_1({n_id})")

    # Tell marc we want displacement Y
    py_send("*post_value Displacement Y")

    # Node 17
    n_id = py_get_int(f"node_id({node_ids[0]})")
    N17Y = py_get_float(f"scalar_1({n_id})")
    # Node 18
    n_id = py_get_int(f"node_id({node_ids[1]})")
    N18Y = py_get_float(f"scalar_1({n_id})")
    # Node 19
    n_id = py_get_int(f"node_id({node_ids[2]})")
    N19Y = py_get_float(f"scalar_1({n_id})")
    # Node 20
    n_id = py_get_int(f"node_id({node_ids[3]})")
    N20Y = py_get_float(f"scalar_1({n_id})")

    n17xy = (N17X, N17Y)
    n18xy = (N18X, N18Y)
    n19xy = (N19X, N19Y)
    n20xy = (N20X, N20Y)

    return (n17xy, n18xy, n19xy, n20xy)


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


def model_setup(file_name, N5XY, N6XY, N7XY, N8XY):
    """Setting up the model"""
    # Save the model
    py_send(f'*set_save_formatted off *save_as_model "{file_name}" yes')
    setup_geometry_and_mesh(N5XY, N6XY, N7XY, N8XY)
    apply_boundary_conditions()
    add_material_properties()
    create_geometric_properites(thickness=2)
    apply_loads(30)
    setup_loadcase()
    create_job()
    return


def mentat_main(N5XY, N6XY, N7XY, N8XY):
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

    model_setup(file_name, N5XY, N6XY, N7XY, N8XY)
    # Export at dat file to read node ids from
    py_send("*write_marc 'node_location.dat' yes")
    node_file = does_file_exist("node_location", "dat")
    if node_file == True:
        did_this_work = is_file_being_modified(file_name_and_exten="node_location.dat")
    else:
        print("Error in node file somewhere")
    extract_nodes_from_dat()
    node_df = get_node_coords_dataframe()
    node_targets = ((30, 0, 0), (60, 0, 0), (60, 30, 0), (30, 30, 0))
    node_ids = []
    for i in node_targets:
        (the_node_id, distance) = find_closest_node(i, node_df)
        node_ids.append(the_node_id)
        if distance > 0.01:
            print(f"\t\t\tDistance:\t{distance}")

    run_the_model()
    success = job_status_checks(file_name)
    # Wait untill a .t16 results file has been made.
    proceed = does_file_exist(
        file_name + "_job1", "t16", 15
    )  # if time runs out -> false
    if success and proceed:
        node_displacements = get_x_y_node_displacements(node_ids)
        return node_displacements
    else:
        print("Problem encountered in code")
        return


def is_file_being_modified(file_name_and_exten, max_time=15):
    """
    Runs infinitely until a file is no longer being modified

    Args:
        file_name_and_extension: The full file name and extension.
        max_time: The maximum time the function can run before termination.

    Returns:
        Success: True if file is no longer being modified.
            False if time runs out.
    """
    start_time = time.time()
    mod_time = time.ctime(os.path.getmtime(file_name_and_exten))
    last_mod_time = mod_time

    run_time = 0
    success = False

    while (success == False) and (run_time < max_time):
        print(f"\t\t\tMod time:\t{mod_time}")
        time.sleep(0.1)
        mod_time = time.ctime(os.path.getmtime(file_name_and_exten))
        if mod_time == last_mod_time:
            success = True
        else:
            last_mod_time = mod_time

    return success


def convert_displacements_to_coordinates(node_disps):
    """
    Convert nodal displacements into nodal coodinates.

    This function assumes an element of shape 30x30mm and that the element
        of interest is the second element stacked to the right.

    Args:
        node_disps: Nodes 17-20 nodal displacements. Each as a tuple

    Returns:
        n17xy: New node 17 coordinates.
        n18xy: New node 18 coordinates.
        n19xy: New node 19 coordinates.
        n20xy: New node 20 coordinates.
    """
    n17xy_d = node_disps[0]
    n18xy_d = node_disps[1]
    n19xy_d = node_disps[2]
    n20xy_d = node_disps[3]

    # Node 17
    n17x = 30 + n17xy_d[0]
    n17y = n17xy_d[1]

    # Node 18
    n18x = 60 + n18xy_d[0]
    n18y = n18xy_d[1]

    # Node 19
    n19x = 60 + n19xy_d[0]
    n19y = 30 + n19xy_d[1]

    # Node 20
    n20x = 30 + n20xy_d[0]
    n20y = 30 + n20xy_d[1]

    n17xy = (n17x, n17y)
    n18xy = (n18x, n18y)
    n19xy = (n19x, n19y)
    n20xy = (n20x, n20y)

    return (n17xy, n18xy, n19xy, n20xy)


def fitness_function(node_locations, return_node_locations=False):
    """
    The function that will be optimised

    Args:
        node_locations: List containing all the node locations for nodes 5-8.
        return_node_locations: True if final node locations should be returned.

    Returns
        fitness: Sum of the euclidian distances from target nodes.
    """

    N5XY = (node_locations[0], node_locations[1])
    N6XY = (node_locations[2], node_locations[3])
    N7XY = (node_locations[4], node_locations[5])
    N8XY = (node_locations[6], node_locations[7])

    node_disps = mentat_main(N5XY, N6XY, N7XY, N8XY)
    final_pos = convert_displacements_to_coordinates(node_disps)

    # convert the nodal displacements into the correct format
    x_lst = []
    y_lst = []
    for i in final_pos:
        x_lst.append(i[0])
        y_lst.append(i[1])

    coordinates = x_lst + y_lst

    (theta, _) = get_angl_midpts(coordinates, 41)

    np_coords = np.array(coordinates)
    coordinates = rotate_then_translate(
        np_coords, (theta), np.array([[-1 * x_lst[0]], [-1 * y_lst[0]]])
    )

    plt.show()

    fitness = determine_fitness_score(coordinates)

    delete_all(file_name)

    print(f"Fitness: {fitness}")

    if return_node_locations == True:
        print(f"The final positions: {final_pos}")
        return final_pos
    else:
        return fitness


def determine_fitness_score(node_points):
    """
    Determine the fitness of a solution.

    The fitness is the sum of the euclidian distances of all points from target

    Args:
        node_points: The node point positions of nodes 9-12 in the form,
            [x9, x10, x11, x12, y9, y10, y11, y12]

    Returns:
        score: The fitness score of the node point configuration.
    """

    # Target points
    t_1 = (0, 0)
    t_2 = (4.08612135e01, 6.56753218e-01)
    t_3 = (3.81125194e01, 3.03306614e01)
    t_4 = (0, 2.98009421e01)

    euclid_1 = ((t_1[0] - node_points[0]) ** 2 + (t_1[1] - node_points[4]) ** 2) ** 0.5
    euclid_2 = ((t_2[0] - node_points[1]) ** 2 + (t_2[1] - node_points[5]) ** 2) ** 0.5
    euclid_3 = ((t_3[0] - node_points[2]) ** 2 + (t_3[1] - node_points[6]) ** 2) ** 0.5
    euclid_4 = ((t_4[0] - node_points[3]) ** 2 + (t_4[1] - node_points[7]) ** 2) ** 0.5

    fitness = euclid_1 + euclid_2 + euclid_3 + euclid_4

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

    # Variable that controls if an optimisation is actually run.
    build_only = False

    # some general setup
    global file_name
    file_name = "testing_one_one"
    py_connect("", 40007)
    py_send('*change_directory "github\MarcMentat_Python\Thesis_Code"')

    # Optimiser code

    # Constraints
    con1 = {"type": "ineq", "fun": constraint_1}
    con2 = {"type": "ineq", "fun": constraint_2}
    con3 = {"type": "ineq", "fun": constraint_3}
    con4 = {"type": "ineq", "fun": constraint_4}
    con5 = {"type": "ineq", "fun": constraint_5}
    con6 = {"type": "ineq", "fun": constraint_6}
    cons = [con1, con2, con3, con4, con5, con6]

    # Bounds
    bd_1 = (2, 14)
    bd_2 = (2, 14)
    bd_3 = (16, 28)
    bd_4 = (2, 14)
    bd_5 = (16, 28)
    bd_6 = (16, 28)
    bd_7 = (2, 14)
    bd_8 = (16, 28)

    bnds = (bd_1, bd_2, bd_3, bd_4, bd_5, bd_6, bd_7, bd_8)

    # Initial guess. These are the node locations in oder as:
    # [N9X, N9Y, N10X, N10Y, N11X, N11Y, N12X, N12Y]
    x0 = [2, 2, 25, 8, 15, 15, 5, 25]

    if build_only == True:
        fitness_function(x0, True)
    else:
        # Run the optimiser
        solution = optimize.minimize(
            fitness_function, x0, method="Nelder-Mead", bounds=bnds
        )  # method="COBYLA",
        print(f"The best solution = {solution}")

        answer = fitness_function(solution.x, True)
        print(f"Final Nodal Parameters:\n\n\t\t{answer}")

    py_disconnect()
