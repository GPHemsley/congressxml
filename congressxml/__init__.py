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

	html_attributes = { "class": [ xml_tag ] }

	for ( name, value ) in xml_element.items():
		html_attributes["data-%s" % ( name )] = value

	catoxml_ns = "{http://namespaces.cato.org/catoxml}"
	if xml_tag.startswith(catoxml_ns):
		xml_tag_name = xml_tag[len(catoxml_ns):]
		html_attributes["class"][html_attributes["class"].index(xml_tag)] = xml_tag_name

		if xml_tag_name in [ "entity-ref" ]:
			html_tag = "a"

			href = url_fn(xml_element)
			if href:
				html_attributes["href"] = href
		else:
			html_tag = "span"
	else:
		# Sections
		if xml_tag in [ "bill", "resolution", "amendment-doc" ]:
			html_tag = "article"
		elif xml_tag in [ "form", "action", "legis-body", "resolution-body", "division", "subdivision", "title", "subtitle", "chapter", "subchapter", "part", "subpart", "section", "subsection", "paragraph", "subparagraph", "clause", "subclause", "item", "subitem", "quoted-block", "attestation", "attestation-group", "endorsement", "amendment-form", "amendment-body", "amendment", "amendment-block", "non-statutory-material", "toc", "account", "subaccount", "subsubaccount", "subsubsubaccount", "committee-appointment-paragraph", "preamble", "whereas", "constitution-article", "rule", "rules-clause", "rules-paragraph", "rules-subparagraph", "rules-subdivision", "rules-item", "rules-subitem", "table" ]:
			html_tag = "section"
		elif xml_tag in [ "header", "ttitle" ]:
			html_tag = "h1"
		elif xml_tag in [ "subheader", "rules-clause-header" ]:
			html_tag = "h2"

		# Grouping content
		elif xml_tag in [ "distribution-code", "amend-num", "calendar", "purpose", "current-chamber", "congress", "session", "legis-num", "official-title", "enrolled-dateline", "associated-doc", "action-date", "action-desc", "action-instruction", "legis-type", "official-title-amendment", "text", "attestation-date", "attestor", "proxy", "role", "amendment-instruction", "para", "instructive-para", "graphic", "formula", "toc-entry", "quoted-block-continuation-text", "after-quoted-block", "tdesc" ]:
			html_tag = "p"
		elif xml_tag in [ "pagebreak" ]:
			html_tag = "hr"
		elif xml_tag in [ "list" ]:
			list_type = xml_element.get("list-type")

			# Determine appropriate HTML tag name
			if list_type in [ "numbered", "lettered" ]:
				html_tag = "ol"
			else: # "none"
				html_tag = "ul"

			# Determine appropriate list style type.
			if list_type == "numbered":
				html_attributes["type"] = "1"
			elif list_type == "lettered":
				html_attributes["type"] = "a"
		elif xml_tag in [ "list-item" ]:
			html_tag = "li"

		# Text-level semantics
		elif xml_tag in [ "external-xref", "internal-xref", "footnone-ref" ]:
			html_tag = "a"

			href = url_fn(xml_element)
			if href:
				html_attributes["href"] = href

			if xml_tag in [ "external-xref" ]:
				if "rel" not in html_attributes:
					html_attributes["rel"] = []

				html_attributes["rel"].append("external")
		elif xml_tag in [ "quote" ]:
			html_tag = "q"
		elif xml_tag in [ "term" ]:
			html_tag = "dfn"
		elif xml_tag in [ "subscript" ]:
			html_tag = "sub"
		elif xml_tag in [ "superscript" ]:
			html_tag = "sup"
		elif xml_tag in [ "italic" ]:
			html_tag = "i"
		elif xml_tag in [ "bold" ]:
			html_tag = "b"
		elif xml_tag in [ "linebreak" ]:
			html_tag = "br"

		# Edits
		elif xml_tag in [ "added-phrase" ]:
			html_tag = "ins"
		elif xml_tag in [ "deleted-phrase" ]:
			html_tag = "del"

		# Tabular data
		elif xml_tag in [ "tgroup" ]:
			html_tag = "table"
		elif xml_tag in [ "colspec" ]:
			html_tag = "colgroup"

			# TODO: Process <colspec> attributes into <colgroup> attributes and <col> elements.
		elif xml_tag in [ "thead" ]:
			html_tag = "thead"
		elif xml_tag in [ "tbody" ]:
			html_tag = "tbody"
		elif xml_tag in [ "row" ]:
			html_tag = "tr"
		elif xml_tag in [ "entry" ]:
			html_tag = "td"

			# TODO: Process <entry> attributes.

		# Fallback (everything else)
		# XXX: These appropriations elements are strange and are not documented outside the XSD.
		#      I think their end tags are in the wrong place.
		elif xml_tag in [ "appropriations-major", "appropriations-intermediate", "appropriations-small" ]:
			html_tag = "div"
		else:
			html_tag = "span"

	# Collapse token sets
	for html_attribute in html_attributes:
		# Space-separated tokens
		if html_attribute.lower() in [ "accept-charset", "accesskey", "class", "dropzone", "for", "headers", "itemprop", "itemref", "itemtype", "ping", "rel", "sandbox", "sizes", "sorted" ]:
			html_attributes[html_attribute] = " ".join(html_attributes[html_attribute])
		# Comma-separated tokens
		elif html_attribute.lower() in [ "accept", "srcset" ]:
			html_attributes[html_attribute] = ",".join(html_attributes[html_attribute])

	html_element = etree.Element(html_tag, attrib=html_attributes)

	empty_elements = [ "area", "base", "br", "col", "embed", "hr", "img", "input", "keygen", "link", "menuitem", "meta", "param", "source", "track", "wbr" ]
	html_element.text = "" if xml_element.text is None and html_tag.lower() not in empty_elements else xml_element.text

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
