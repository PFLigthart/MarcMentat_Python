import pandas as pd


def extract_nodes_from_dat():
    """
    Extract the nodal locations from a dat file into a text file

    Args:
        None

    Returns:
        None: It only changes the file 'coordinates.txt
    """

    datFile = "testing_one_one_job1.dat"
    coordinatesFile = "coordinates.txt"
    marker1 = "coordinates"
    marker2 = "define              node                set                 apply1_nodes"

    with open(datFile, "r") as f1, open(coordinatesFile, "w") as f2:
        main = f1.read()
        start = main.find(marker1) + len(marker1)
        end = main.find(marker2)

        main = main[start:end]
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

    node_df = df.drop(0) # the top entry is wrong and should be removed.

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
        x_hat = row['x']
        x_hat = float(x_hat[:-2] + 'e' + x_hat[-2:])
        y_hat = row['y']
        y_hat = float(y_hat[:-2] + 'e' + y_hat[-2:])

        # Calculate the distance from the desired location
        distance = ((x - x_hat)**2 + (y - y_hat)**2)**0.5

        # check if distance is the smallest encountered so far
        if distance < min_distance:
            min_distance = distance
            node_id = row['Node']

    return (node_id, min_distance)


if __name__ == "__main__":
    extract_nodes_from_dat()
    node_df = get_node_coords_dataframe()
    (the_node, distance) = find_closest_node((30, 0, 0), node_df)
    print(f"The closest node is node {the_node} with a distance of {distance}")
