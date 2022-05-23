def clean_for_kindle(parser):
	parser = _remove_images(parser)
	parser = _remove_script(parser)
	return parser

"""
Kindles don't like images with svg extensions. That said, Kindles can't convert image urls into images anyway, so let's just remove all images.
"""
def _remove_images(parser):
	[img.extract() for img in parser.findAll('img')]
	return parser

def _remove_script(parser):
	[script.extract() for script in parser.findAll('script')]
	return parser