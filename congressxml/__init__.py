from lxml import etree

def create_link_url(xml_element):
	# This tag is from the office XML file.
	if xml_element.tag == "external-xref":
		val = xml_element.get("parsable-cite")
		if xml_element.get("legal-doc") == "usc":
			usc, title, sec = val.split("/")
			return "http://www.law.cornell.edu/uscode/text/" + title + "/" + sec
		elif xml_element.get("legal-doc") == "usc-chapter": # added by Cato Deepbills
			return None # not easy to convert to a Cornell LII link
		elif xml_element.get("legal-doc") == "public-law":
			pl, congress, num = val.split("/")
			return "http://www.govtrack.us/search?q=P.L.+%d-%d" % (int(congress), int(num))
		elif xml_element.get("legal-doc") == "statute-at-large":
			return None
		elif xml_element.get("legal-doc") == "bill":
			return None
		elif xml_element.get("legal-doc") == "act":
			return None
		else:
			return None
		# there are some others that we really don't know how to interpret

	# It's a Cato Deepbills entity-ref tag.
	else:
		val = xml_element.get("value")

		if xml_element.get("entity-type") == "uscode":
			ref = val.split("/")
			if ref[0] == "usc":
				if len(ref) >= 3: ref[2] = ref[2].split("..")[0]
				return "http://www.law.cornell.edu/uscode/text/" + ref[1] + ("/" + ref[2] if len(ref) >= 3 else "")
			elif ref[0] == "usc-chapter":
				return None # not easy to convert to a Cornell LII link
			elif ref[0] == "usc-appendix":
				if len(ref) >= 3: ref[2] = ref[2].split("..")[0]
				return "http://www.law.cornell.edu/uscode/text/" + ref[1] + "a" + ("/" + ref[2] if len(ref) >= 3 else "")
		elif xml_element.get("entity-type") == "statute-at-large":
			sal, volume, page = val.split("/")
			page = page.split("..")[0] # page may be a range
			return "http://www.gpo.gov/fdsys/search/citation2.result.STATUTE.action?statute.volume=%d&statute.pageNumber=%s&publication=STATUTE" % (int(volume), int(page))
		elif xml_element.get("entity-type") == "public-law":
			pl, congress, num = val.split("/")[0:3]
			return "http://www.govtrack.us/search?q=P.L.+%d-%d" % (int(congress), int(num))


def convert_element(xml_element, url_fn=create_link_url):
	xml_tag = xml_element.tag

	html_attributes = { "class": xml_tag }

	for ( name, value ) in xml_element.items():
		html_attributes["data-%s" % ( name )] = value

	catoxml_ns = "{http://namespaces.cato.org/catoxml}"
	if xml_tag.startswith(catoxml_ns):
		xml_tag = xml_tag[len(catoxml_ns):]
		html_attributes["class"] = xml_tag

		html_tag = "span"
		if xml_tag in [ "entity-ref" ]:
			href = url_fn(xml_element)
			if href:
				html_tag = "a"
				html_attributes["href"] = href

	elif xml_tag == "external-xref":
		href = url_fn(xml_element)
		html_tag = "span"
		if href:
			html_tag = "a"
			html_attributes["href"] = href
			
	else:
		if xml_tag in [ "bill", "resolution", "amendment-doc" ]:
			html_tag = "article"
		elif xml_tag in [ "form", "action", "legis-body", "resolution-body", "division", "subdivision", "title", "subtitle", "chapter", "subchapter", "part", "subpart", "section", "subsection", "paragraph", "subparagraph", "clause", "subclause", "item", "subitem", "quoted-block", "attestation", "attestation-group", "endorsement", "amendment-form", "amendment-body", "amendment", "amendment-block", "non-statutory-material", "appropriations-small", "toc" ]:
			html_tag = "section"
		elif xml_tag in [ "distribution-code", "calendar", "congress", "session", "enrolled-dateline", "legis-num", "associated-doc", "current-chamber", "action-date", "action-desc", "action-instruction", "legis-type", "official-title", "official-title-amendment", "text", "attestation-date", "attestor", "proxy", "role", "amendment-instruction", "para", "graphic", "formula", "toc-entry", "after-quoted-block" ]:
			html_tag = "p"
		else:
			html_tag = "span"

	html_element = etree.Element(html_tag, attrib=html_attributes)
	html_element.text = "" if xml_element.text is None else xml_element.text
	html_element.tail = "" if xml_element.tail is None else xml_element.tail

	return html_element

def build_html_tree(xml_tree, url_fn=create_link_url):
	xml_tree_root = xml_tree.getroot()
	html_tree = convert_element(xml_tree_root, url_fn)

	for xml_element in xml_tree_root.getchildren():
		# Ignore certain subtrees.
		if xml_element.tag in [ "metadata" ]:
			continue

		html_tree.append(build_html_tree(etree.ElementTree(xml_element)))

	return html_tree

def convert_xml(xml_file_path, url_fn=create_link_url):
	xml_tree = etree.parse(xml_file_path)

	return etree.ElementTree(build_html_tree(xml_tree, url_fn))

# XXX: Is this even necessary? You can just call the write() method on the output of convert_xml()...
def write_html(html_tree, html_file_path):
	return html_tree.write(html_file_path)
