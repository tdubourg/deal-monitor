from subprocess import Popen, PIPE

DBG = False


def execute_shell_and_get_stdout(shell_command, args_list):
    if DBG:
        print "Going to execute command: ", shell_command, args_list
    command = [shell_command]
    command.extend(args_list)
    return Popen(command, stdout=PIPE, stderr=PIPE).communicate()
