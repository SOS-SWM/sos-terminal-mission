extends Terminal


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	write("YUKI .N> ")
	await get_tree().create_timer(0.5).timeout
	var text = "HELLO WORLD!"
	for c in text:
		await get_tree().create_timer(0.1).timeout
		write(c)

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass
