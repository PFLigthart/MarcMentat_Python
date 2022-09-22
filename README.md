# MarcMentat_Python
Code to run finite element analysis in [MarcMentat](https://www.mscsoftware.com/product/marc) using python scripts. This allows for an optimisation loop to be setup with a finite element analysis within the loop.

## Contents
[Virtual Environment](https://github.com/PFLigthart/MarcMentat_Python#how-to-setup-the-conda-virtual-environment-and-add-the-required-libraries)

* Instructions for how to setup a conda virtual environment in windows and to add the required libraries is provided.

[Note on Marc and Mentat](https://github.com/PFLigthart/Marc-Mentat)

[Create Python Script](https://github.com/PFLigthart/Setup-python-script-to-interface-with-Marc-and-Mentat)
* Instructions for how to setup a python script that can interface with MarcMentat is provided.

[Run Python Script from the terminal](https://github.com/PFLigthart/Run-the-python-script-from-the-termianl)

* Instructions for how to run the python script from the conda prompt *(terminal is also provided.

[Example](https://github.com/PFLigthart/Example-from-thesis)

* My personal files used for my masters thesis are included and can be used as an example. A short discription of what my code is designed for is also provided.

## How to install marc (For students at Stellenbosch University)
1. Obtain the software from the ftp server. You have to be connected to the network to access the server. If you are not on campus you will need to use the vpn. (Ask your supervisor or check your research group wiki for the address and passcode.)
2. Copy the files onto your machine. At the time of writing 2021.4 was the latest version the university had access to.
    * marc_2021.4_windows64
    * marc_2021.4_windows_doc
3. First install 'marc_2021.4_windows'. This is the program.
    * Double clicking on the file to start the installation.
    * When prompted, enter 'Stellenbosch University' as the company name.
    * When prompted, Do a complete install. Marc and Marc Mentat.
    * When prompted, enter '1700@license2.stb.sun.ac.za' for the License.
4. Finally install 'marc_2021.4_windows_doc'. This is the documentation.
    * Double click the file to start the installation.
    * When prompted, enter 'Stellenbosch University' as the company name.

Marc should now be installed and can be used when connect to the University Network.


## How to setup the conda virtual environment and add the required libraries.
The libraries required cannot be installed using either Pip or Conda. These libraries are part of the propriatary software and hence need to be copied into the virtual environment.
I use [miniconda](https://docs.conda.io/en/latest/miniconda.html) to setup my virtual environements.It is "a small, bootstrap version of [Anaconda](https://www.anaconda.com/)".

Here is a step by step procedure.

1. Open the anaconda terminal.
    * This can be found by seaching 'Anaconda Prompt' in the windows menu.
2. Create a virtual environemnt using conda
    * conda create --name Apex_Mentat_Pip python=3.8
	    * It is not recommended to mix conda and pip package intalls. Therefor the 'Pip' was appended to name to deonte that all packages within the environemnet should be installed using pip
3. Activate the environment.
	* conda activate Apex_Mentat_Pip
4. Install the required packages using pip (numpy and scipy) however, the installation of scipy will also install numpy.
	* pip install scipy
5. Move py_mentat and py_post files into virtual environmnet.
	* Files are located at: C:\Program Files\MSC.Software\Marc\2021.4.0\mentat2021.4\shlib\win64
		py_mentat.py
		py_post.py
    * Move files into the conda virtual environment.
	    * (Thanks to SB Chung for the following steps.)
	    * Depending on what environment you are using, the following steps may vary. However, if a conda environment is being used the following can be done
            1. Open the anaconda terminal.
            2. Activate the environment.
                * conda activate Apex_Mentat_Pip]
            3. type: python
	        4. type: import sys.
            5. type: sys.path
                * Different paths will be displayed. Look for the path that shows were the DLLs are stored.
                    * e.g.
                C:\\\Users\\\\\<your username>\\\miniconda3\\\envs\\\Apex_mentat_pip\\\DLLs
            6. If present, remove the double '\\\' to be only a single '\\', as shown below:
                * C:\Users\<your username>\miniconda3\envs\Apex_mentat_pip\DLLs
        * Place the py_mentat and py_post files into this directory. 
* The virtual environment should now be able to use these libraries.

## Marc Mentat
This guide assumes the user has some experience in MSC Marc. Here is a link to the official [Marc and Mentat Documentation](https://simcompanion.hexagon.com/customers/s/article/Marc-Documentation-Release-2021)

## Setup python script to interface with Marc and Mentat

TODO

## Run the python script from the termianl

TODO

## Example from thesis

TODO
