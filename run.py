import os
import re
import sys
import shutil
import random
import argparse
import subprocess
from string import Template

def to_binary_array(num):
    # Convert integer to binary array
    return list(map(int, list(''.join(str(1 & int(num) >> i) for i in range(8)[::-1]))))

def to_integer(bin_array):
    # Convert binary array to integer
    num = 0
    for bit in bin_array:
        num = (num << 1) | bit

    return num

def compute_result(tb_values):
    # Input bitmask and set mindist
    bitmask = to_binary_array(tb_values[0])
    mindist = 511

    # Calculate Manhattan distance
    for i in range(0, 8):
        if bitmask[i] == 1:
            distance = (abs(tb_values[9][0] - tb_values[8 - i][0]) +
                        abs(tb_values[9][1] - tb_values[8 - i][1])
                       )

            if distance < mindist:
                for j in range(0, i):
                    bitmask[j] = 0

                mindist = distance

            elif distance > mindist:
                bitmask[i] = 0

    return to_integer(bitmask)

def generate_input():
    tb_values = []

    # Random bitmask and random centroids
    tb_values.append(random.randint(0, 255))
    for _ in range(1, 10):
        tb_values.append([random.randint(0, 255), random.randint(0, 255)])

    # Create template dictionary
    d = {"BITMASK": tb_values[0],
         "XC1": tb_values[1][0], "YC1": tb_values[1][1],
         "XC2": tb_values[2][0], "YC2": tb_values[2][1],
         "XC3": tb_values[3][0], "YC3": tb_values[3][1],
         "XC4": tb_values[4][0], "YC4": tb_values[4][1],
         "XC5": tb_values[5][0], "YC5": tb_values[5][1],
         "XC6": tb_values[6][0], "YC6": tb_values[6][1],
         "XC7": tb_values[7][0], "YC7": tb_values[7][1],
         "XC8": tb_values[8][0], "YC8": tb_values[8][1],
         "X": tb_values[9][0], "Y": tb_values[9][1],
         "RESULT": compute_result(tb_values)
        }

    return d

def verilog_glbl_search():
    # Search for data\verilog\src\glbl.v
    print("Verilog glbl.v not found.")
    sys.stdout.write(r"Searching verilog glbl.v in C:\ ")
    sys.stdout.flush()

    # C:\ drive walk
    for root, _, files in os.walk(r"C:\\"):
        for name in files:
            if name == "glbl.v" and r"data\verilog\src\glbl.v" in os.path.abspath(os.path.join(root, name)):
                shutil.copyfile(os.path.abspath(os.path.join(root, name)), "lib/glbl.v")

                # Return success code if file found
                print("\n=> File found and copyed to working directory.")
                return 0

    # Return error code if file not found
    print("\n=> File not found.")
    return -1

def settings64_search():
    # Search for settings64 bat files
    print("Settings64 bat files not found.")
    sys.stdout.write(r"Searching settings64 bat files in C:\ ")
    sys.stdout.flush()

    found = 0

    # C:\ drive walk
    for root, _, files in os.walk(r"C:\\"):
        for name in files:
            if name == ".settings64-Vivado.bat":
                # Copy if doesn't already exists
                if not os.path.exists("lib/.settings64-Vivado.bat"):
                    shutil.copyfile(os.path.abspath(os.path.join(root, name)), "lib/.settings64-Vivado.bat")

                found += 1
            if name == ".settings64-DocNav.bat":
                # Copy if doesn't already exists
                if not os.path.exists("lib/.settings64-DocNav.bat"):
                    shutil.copyfile(os.path.abspath(os.path.join(root, name)), "lib/.settings64-DocNav.bat")

                found += 1
            if name == ".settings64-SDK_Core_Tools.bat":
                # Copy if doesn't already exists
                if not os.path.exists("lib/.settings64-SDK_Core_Tools.bat"):
                    shutil.copyfile(os.path.abspath(os.path.join(root, name)), "lib/.settings64-SDK_Core_Tools.bat")

                found += 1

            if found == 3:
                break

        if found == 3:
            break

    # Return success or error code
    if found == 3:
        print("\n=> Files found and copyed to working directory.")
    else:
        print("\n=> Files not found.")

    return found

def vivado_synthesis(args):
    # Create tcl file to run vivado
    create_tcl_file(args)

    sys.stdout.write(r"Post-synthesis simulation selected, running synthesis ")
    sys.stdout.flush()

    # Run synthesis with vivado batch mode
    bash = subprocess.getoutput(settings_call() +
                                "vivado -mode batch -source run.tcl"
                               )

    print("")

    # Printh synthesis warnings and errors
    for line in bash.split("\n"):
        if "WARNING" in line:
            print("    " + line)

        elif "ERROR" in line:
            print("    " + line)

    # Return error code if synthesis failed
    if "ERROR" in bash:
        print("=> Synthesis failed.\n")
        return -1

    # Return success code if synthesis succeeded
    print("=> Synthesis completed.")
    return 0

def settings_call():
    # Set settings64 batch calls
    return ("CALL ../lib/.settings64-Vivado.bat & " +
            "CALL ../lib/.settings64-DocNav.bat & " +
            "CALL ../lib/.settings64-SDK_Core_Tools.bat & "
           )

def create_tcl_file(args):
    # Create tcl file to run vivado
    tclfile = open("run.tcl", 'w')

    # Set synthetis tcl commands
    tcl_commands = ("read_vhdl ../" + args.filepath + "\n" +
                    "read_xdc ../vhd/constraints.xdc\n\n" +
                    "synth_design -top project_reti_logiche -part xc7a200tfbg484-1\n" +
                    "write_checkpoint -force post_synth\n\n"
                   )

    tclfile.write(tcl_commands)
    tclfile.write("open_checkpoint post_synth.dcp\n")

    # Set functional specific commands
    if args.synth == "functional":
        tclfile.write("write_vhdl -mode funcsim -force functional_simulation.vhd\n")

    # Set timing specific commands
    elif args.synth == "timing":
        tclfile.write("write_verilog -mode timesim -sdf_anno true -force timing_simulation.v\n")
        tclfile.write("write_sdf -force timing_simulation.sdf\n")

    tclfile.close()

    return

def simulation_commands(args):
    # GUI waveform enabled
    if args.gui:
        gui = "-gui"
        debug = "-debug all"
    # GUI waveform disabled
    else:
        gui = "-runall"
        debug = ""

    # Post-synthesis functional simulation commands
    if args.synth == "functional":
        return ("xvhdl project_tb.vhd & " +
                "xvhdl functional_simulation.vhd & "
                "xelab " + debug + " project_tb & " +
                "xsim work.project_tb " + gui
               )

    # Post-synthesis timing simulation commands
    if args.synth == "timing":
        return ("xvhdl project_tb.vhd & " +
                "xvlog timing_simulation.v & " +
                "xvlog ../lib/glbl.v & " +
                "xelab " + debug + " -L simprims_ver -L unisims_ver project_tb glbl & " +
                "xsim work.project_tb#work.glbl " + gui
               )

    # Behavioural simulation commands
    return ("xvhdl project_tb.vhd & " +
            "xvhdl ../" + args.filepath + " & " +
            "xelab " + debug + " project_tb & " +
            "xsim work.project_tb " + gui
           )

def run_end():
    os.chdir("..")

    if os.path.exists("log"):
        shutil.rmtree("log")

def main():
    # Argument parser
    parser = argparse.ArgumentParser(description=("Run behavioural, post-synthesis functional " +
                                                  "or post-synthesis timing simulation on a template " +
                                                  "testbench populated with random values."
                                                 )
                                    )
    parser.add_argument("filepath",
                        action="store",
                        help="vhd project file path to perform simulation with [vhd/filename.vhd]."
                       )
    parser.add_argument("-n",
                        action="store",
                        type=int,
                        default=1,
                        help="number of simulations [default = 1]."
                       )
    parser.add_argument('--synth',
                        default=None,
                        choices=["functional", "timing"],
                        help="post-synthesis functional or timing simulation [default = behavioural]"
                       )
    parser.add_argument("--gui",
                        action="store_true",
                        default=False,
                        help="enable GUI waveform simulation."
                       )

    args = parser.parse_args()

    # Lib directory, no glbl.v and settings64
    if not os.path.exists("lib"):
        os.makedirs("lib")

        if (settings64_search() != 3 or (args.synth == "timing" and verilog_glbl_search() == -1)):
            return run_end()
    else:
        # No settings64 bat files
        if (not os.path.exists("lib/.settings64-Vivado.bat") or
                not os.path.exists("lib/.settings64-DocNav.bat") or
                not os.path.exists("lib/.settings64-SDK_Core_Tools.bat")):
            if settings64_search() != 3:
                return run_end()

        # No verilog glbl.v
        if args.synth == "timing" and not os.path.exists("lib/glbl.v"):
            if verilog_glbl_search() == -1:
                return run_end()

    # Create log directory
    if not os.path.exists("log"):
        os.makedirs("log")
    os.chdir("log")

    # Testbench template file
    filein = open("../vhd/template_tb.vhd")
    template = Template(filein.read())
    filein.close()

    passed_simulations = 0

    # If functional or timing post-synthesis simulation
    if args.synth is not None:
        # Run synthesis
        if vivado_synthesis(args) == -1:
            return run_end()

    for i in range(0, args.n):
        # Temporary testbench file
        fileout = open("project_tb.vhd", 'w')

        print("\nSimulation ID: " + str(i + 1))

        # Generate input and create testbench
        tb_values = generate_input()
        fileout.write(template.substitute(tb_values))
        fileout.close()

        # Print expected return value
        print("    Expected return value: " + str(bin(tb_values.get("RESULT"))))
        sys.stdout.write("    Running simulation ")
        sys.stdout.flush()

        # Run simulation
        bash = subprocess.getoutput(settings_call() +
                                    simulation_commands(args)
                                   )

        # Parse bash output for result
        if not args.gui:
            if "passed" in bash:
                print("    RAM address 0b00010011: " +
                      str(bin(int(re.search(r"passed(\d+)", bash).group(1))))
                     )
                print("=> Simulation passed.")

                passed_simulations += 1
            else:
                for line in bash.split("\n"):
                    if "ERROR" in line:
                        print("    " + line)

                if "failed" in bash:
                    print("    RAM address 0b00010011: " +
                          str(bin(int(re.search(r"failed(\d+)", bash).group(1))))
                         )

                print("=> Simulation failed.")
        else:
            print("")

    # Number of passed simulations
    if not args.gui:
        print("\nNumber of passed simulations: " +
              str(passed_simulations) + '/' + str(args.n) +
              " (" + str((passed_simulations * 100) / args.n) + "%)"
             )

    return run_end()

if __name__ == "__main__":
    main()
