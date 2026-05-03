extends TextureRect

@onready var sub_viewport = $"../SubViewport"

func _unhandled_input(event: InputEvent):
	if event is InputEventKey:
		if event.keycode == KEY_Q and event.ctrl_pressed:
			return
		sub_viewport.push_input(event)
