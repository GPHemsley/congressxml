from lxml import etree

def convert_element(e):
	xml_tag = e.tag

	html_attributes = { "class": xml_tag }

	for ( name, value ) in e.items():
		html_attributes["data-%s" % ( name )] = value

	catoxml_ns = "{http://namespaces.cato.org/catoxml}"
	if xml_tag.startswith(catoxml_ns):
		xml_tag = xml_tag[len(catoxml_ns):]
		html_attributes["class"] = xml_tag

		if xml_tag in [ "entity-ref" ]:
			import urllib

			html_tag = "a"
			html_attributes["href"] = "#%s" % ( urllib.quote(e.get("value", e.get("entity-id", e.get("entity-parent-id", "")))) )
		else:
			html_tag = "span"
	else:
		if xml_tag in [ "bill", "resolution", "amendment-doc" ]:
			html_tag = "article"
		elif xml_tag in [ "form", "action", "legis-body", "division", "subdivision", "title", "subtitle", "chapter", "subchapter", "part", "subpart", "section", "subsection", "paragraph", "subparagraph", "clause", "subclause", "item", "subitem", "quoted-block", "attestation", "attestation-group", "endorsement", "amendment-form", "amendment-body", "amendment", "amendment-block", "non-statutory-material" ]:
			html_tag = "section"
		elif xml_tag in [ "distribution-code", "calendar", "congress", "session", "enrolled-dateline", "legis-num", "associated-doc", "current-chamber", "action-date", "action-desc", "action-instruction", "legis-type", "official-title", "official-title-amendment", "text", "attestation-date", "attestor", "proxy", "role", "amendment-instruction", "para", "graphic", "formula" ]:
			html_tag = "p"
		else:
			html_tag = "span"

	html_element = etree.Element(html_tag, attrib=html_attributes)
	html_element.text = e.text #"\n\t"
	html_element.tail = e.tail #"\n"

	return html_element

def build_html_tree(xml_tree):
	xml_tree_root = xml_tree.getroot()
	html_tree = convert_element(xml_tree_root)

	for e in xml_tree_root.getchildren():
		# Ignore certain subtrees.
		if e.tag in [ "metadata" ]:
			continue

		html_tree.append(build_html_tree(etree.ElementTree(e)))

	return html_tree

def convert_xml(xml_file_path, html_file_path):
	xml_tree = etree.parse(xml_file_path)

	html_tree = etree.ElementTree(build_html_tree(xml_tree))

	html_tree.write(html_file_path)
