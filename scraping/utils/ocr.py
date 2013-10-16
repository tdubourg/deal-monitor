from shell_utils import execute_shell_and_get_stdout

def ocr(image_filepath):
	# Running gocr with chars restricted to digits only and returning the result of the command
	return execute_shell_and_get_stdout("gocr", [image_filepath, "-C", "0-9"]).strip()