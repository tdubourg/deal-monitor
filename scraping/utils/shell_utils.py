from subprocess import Popen, PIPE

DBG = True


def execute_shell_and_get_stdout(shell_command, args_list):
    if DBG:
        print "Going to execute command: ", shell_command, args_list
    command = [shell_command]
    command.extend(args_list)
    return Popen(command, stdout=PIPE, stderr=PIPE).communicate()[0] # [0] is stdout, [1] is stderr

def execute_shell_and_get_stdout_and_err(shell_command, args_list):
    if DBG:
        print "Going to execute command: ", shell_command, args_list
    command = [shell_command]
    command.extend(args_list)
    return Popen(command, stdout=PIPE, stderr=PIPE).communicate()
