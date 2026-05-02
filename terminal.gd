extends Terminal

@onready var pty = $PTY

func _ready() -> void:
	pty.fork()
	grab_focus()
	grab_focus.call_deferred()
