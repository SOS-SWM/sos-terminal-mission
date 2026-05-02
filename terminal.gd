extends Terminal

@onready var pty = $PTY

func _ready() -> void:
	#pty.fork("cd Engine")
	var shell = "sh"
	var args = ["-c", "cd Engine/ && uv run haruhi-rpg"]
	
	if OS.get_name() == "Windows":
		shell = "cmd.exe"
		args = ["/c", "cd Engine && uv run haruhi-rpg"]
		
	pty.fork(shell, args)
	grab_focus()
	grab_focus.call_deferred()
