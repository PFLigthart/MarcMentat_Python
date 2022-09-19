"""Script to create a singly unit of the soft actuator that will be optimised"""

import os
from py_mentat import py_connect, py_disconnect, py_send
from my_mentat_library import does_status_file_exist, was_code_successfull


def setup_geometry_and_mesh():
    # set analysis to planar
    py_send("*set_model_analysis_dimension planar")
    # create the geometry
    py_send("*set_solid_type sheet_rect")
    py_send("*add_solids 0 0 0 30 30 5 5 0 20 20")
    py_send("*solids_subtract 1 2 #")
    # create the four corner nodes.
    py_send("*add_nodes 0 0 0 30 0 0 30 30 0 0 30 0")
    # create the four internal corner nodes (these will be optimised)
    py_send("*add_nodes 5 5 0 25 5 0 25 25 0 5 25 0")
    # Automesh
    py_send("@set($automesh_surface_desc,sheet)")
    py_send("@set($automesh_surface_family,quad)")
    py_send("*pt_set_target_element_size_method manual")
    py_send("*pt_set_global_element_size_sheet 1")
    py_send("*pt_mesh_sheet linear quad 1 #")
    # remove any duplicate nodes
    py_send("*sweep_nodes all_existing")

    return


def apply_boundary_conditions(pressure_val):
    """
    Apply the fixed boundary conditions and the required loads.

    Args:
        pressure_val: The pressure value to be applied to the edges."""

    # fixed boundary condition.

    # select nodes in path from node 1-4
    py_send("*select_method_path *select_nodes 1 4 #")
    py_send("*new_apply *apply_type fixed_displacement")
    py_send("*apply_dof x *apply_dof_value x 0")
    py_send("*apply_dof y *apply_dof_value y 0")
    py_send("*add_apply_nodes")
    py_send("all_selected #")

    # egde pressure loads
    internal_edge_pairs = [[8, 5], [5, 6], [6, 7], [7, 8]]
    py_send("*select_clear_nodes")
    py_send("*select_clear_edges")
    for i in internal_edge_pairs:
        py_send(f"*select_edges {i[0]} {i[1]} #")
    py_send("*new_apply *apply_type edge_load *apply_option edge_load_mode:area")
    py_send("*apply_dof p")
    py_send(f"*apply_dof_value p {pressure_val}")
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

    # Create the table
    py_send("*new_pre_defined_table linear_ramp_time")
    # Create the loadcase
    py_send("*new_loadcase *loadcase_type struc:static")
    # py_send("*loadcase_option stepping:multicriteria")
    py_send("*loadcase_option stepping:table_defined")
    py_send("*set_loadcase_stepping_table linear_ramp_time1")


def create_job():
    """Create a job - set up the job parameters"""
    py_send("*new_job structural")
    py_send("*add_job_loadcases lcase1")
    py_send("*add_post_tensor strain")
    py_send("*add_post_var von_mises")
    py_send("*job_option strain:large")

    # create the element types
    py_send("*element_type 118 all_existing")


def model_setup(file_name):
    """Setting up the model"""
    # Save the model
    py_send(f'*set_save_formatted off *save_as_model "{file_name}" yes')
    setup_geometry_and_mesh()
    apply_boundary_conditions(50)
    add_material_properties()
    create_geometric_properites(thickness=2)
    setup_loadcase()
    create_job()
    return


def run_the_model():
    py_send("*update_job")
    py_send("*save_model")
    py_send("*submit_job 1")


def job_status_checks(file_name):
    """See if the job is completed and if successfully"""
    does_status_file_exist(file_name, 15)
    path = os.path.abspath(os.getcwd())
    file_path = path + f"\\{file_name}_job1.sts"
    print(file_path)
    was_code_successfull(file_path, "3004")


def main():
    file_name = "does_this_work"
    model_setup(file_name)
    run_the_model()
    job_status_checks(file_name)


if __name__ == "__main__":

    py_connect("", 40007)
    main()
    py_disconnect()
