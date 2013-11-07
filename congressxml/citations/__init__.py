import urllib, json

def is_special_segment(entity_value_segment):
	return (entity_value_segment in [ "note", "etseq" ])

def add_special_segment(citation, entity_value_segment):
	if "special" not in citation:
		citation["special"] = entity_value_segment
	else:
		raise ValueError("Special segment already defined in citation")

	return citation

def parse_prefixed_segments(citation, entity_value_segments):
	prefix_map = {
		"d": "division",
		"t": "title",
		"st": "subtitle",
		"pt": "part",
		"spt": "subpart",
		"ch": "chapter",
		"sch": "subchapter",
		"s": "section",
		"ss": "subsection",
		"p": "paragraph",
		"sp": "subparagraph",
		"cl": "clause",
		"scl": "subclause",
		"i": "item",
		"si": "subitem",
	}

	for entity_value_segment in entity_value_segments:
		try:
			prefix, segment = entity_value_segment.split(":")

			if prefix_map[prefix] not in citation:
				citation[prefix_map[prefix]] = segment
			else:
				raise ValueError("Segment already defined in citation: %s" % ( prefix_map[prefix] ))
		except ValueError:
			if is_special_segment(entity_value_segment):
				add_special_segment(citation, entity_value_segment)
			else:
				if "extra" not in citation:
					citation["extra"] = []

				citation["extra"].append(entity_value_segment)

	return citation

def build_citation(entity_value_segments, entity_value_segment_names):
	citation = {}

	i = 0
	while len(entity_value_segments) > 0:
		entity_value_segment = entity_value_segments.pop(0)

		if is_special_segment(entity_value_segment):
			add_special_segment(citation, entity_value_segment)
		else:
			try:
				citation[entity_value_segment_names[i]] = entity_value_segment
			except IndexError:
				break

		i += 1

	citation = parse_prefixed_segments(citation, entity_value_segments)

	return citation

def segment_names_for(entity_type):
	segment_name_map = {
		"uscode": {
			# XXX: The CatoXML spec is not clear on what actually comes after 'subparagraph' for the 'usc' subtype.
			"usc": [ "subtype", "title", "section", "subsection", "paragraph", "subparagraph", "clause", "subclause", "item", "subitem" ],
			"usc-chapter": [ "subtype", "title", "chapter", "subchapter" ],
			"usc-appendix": [ "subtype", "title", "section" ],
		},
		"act": [ "act" ],
		"statute-at-large": [ "type", "volume", "page" ],
		"public-law": [ "type", "congress", "law" ],
	}

	if entity_type in segment_name_map:
		return segment_name_map[entity_type]

	return []

def entity_value_segments_from(entity_value):
	return entity_value.split("/")

def deepbills_citation_for(entity_type, entity_value, entity_ref_text, entity_proposed=False):
	entity_value_segment_names = segment_names_for(entity_type)
	entity_value_segments = entity_value_segments_from(entity_value)

	if entity_type in [ "uscode" ]:
		entity_subtype = entity_value_segments[0]

		citation = build_citation(entity_value_segments, entity_value_segment_names[entity_subtype])
	else:
		citation = build_citation(entity_value_segments, entity_value_segment_names)

	citation["type"] = entity_type
	citation["value"] = entity_value
	citation["proposed"] = True if entity_proposed else False

	import re
	citation["text"] = re.sub(r"(\s+)", " ", entity_ref_text)

	return citation
