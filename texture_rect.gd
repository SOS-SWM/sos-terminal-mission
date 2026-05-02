extends TextureRect

@onready var sub_viewport = $"../SubViewport"

func _unhandled_input(event: InputEvent):
	# Only forward keyboard events here
	if event is InputEventKey:
		sub_viewport.push_input(event)
