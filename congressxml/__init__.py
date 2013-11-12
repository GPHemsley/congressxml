from lxml import etree

catoxml_ns = "{http://namespaces.cato.org/catoxml}"

def url_for_us_code(citation):
	def is_range(segment):
		# XXX: This is a quick-and-dirty range finder.
		return (".." in segment)

	def get_range_start(segment):
		return segment[:segment.index("..")]

	# Citations of proposed documents won't follow the same URL format.
	if citation["proposed"]:
		# XXX: We should probably support same-page URLs for these.
		return None

	if "title" not in citation:
		return None

	subpath = citation["title"]

	if citation["subtype"] == "usc-appendix":
		subpath += "a"

	if citation["subtype"] == "usc-chapter":
		if "chapter" in citation:
			subpath += "/chapter-%s" % ( citation["chapter"] )

			if "subchapter" in citation:
				subpath += "/subchapter-%s" % ( citation["subchapter"] )
	else:
		if "section" in citation:
			if is_range(citation["section"]):
				subpath += "/%s" % ( get_range_start(citation["section"]) )
			else:
				subpath += "/%s" % ( citation["section"] )

				if "subsection" in citation:
					if is_range(citation["subsection"]):
						fragment = get_range_start(citation["subsection"])
					else:
						fragment = citation["subsection"]

						for segment in [ "paragraph", "subparagraph", "clause", "subclause", "item", "subitem" ]:
							if segment in citation:
								# Sometimes a segment is empty, so we just skip it.
								if citation[segment] != "":
									if is_range(citation[segment]):
										segment_range_start = get_range_start(citation[segment])
										fragment += segment_range_start if fragment == "" else "_%s" % ( segment_range_start )
										break
									else:
										fragment += citation[segment] if fragment == "" else "_%s" % ( citation[segment] )
							else:
								break

					if fragment != "":
						subpath += "#%s" % ( fragment )

	# convert en-dashes to hyphens
	subpath = subpath.replace(u"\u2013", "-")

	return "http://www.law.cornell.edu/uscode/text/%s" % ( subpath )

def url_for_statute_at_large(citation):
	# Citations of proposed documents won't follow the same URL format.
	if citation["proposed"]:
		# XXX: We should probably support same-page URLs for these.
		return None

	try:
		# An en-dash indicates a page range, but link to just the first page in the range.
		page = citation["page"].split(u"\u2013")[0]
		url = "http://www.gpo.gov/fdsys/search/citation2.result.STATUTE.action?publication=STATUTE&statute.volume=%d&statute.pageNumber=%s" % ( int(citation["volume"]), page)
	except KeyError:
		url = None

	return url

def url_for_public_law(citation):
	# Citations of proposed documents won't follow the same URL format.
	if citation["proposed"]:
		# XXX: We should probably support same-page URLs for these.
		return None

	try:
		url = "https://www.govtrack.us/search?q=P.L.+%d-%d" % ( int(citation["congress"]), int(citation["law"]) )
	except KeyError:
		url = None
	except ValueError:
		# either the congress or the law number was not an integer (maybe blank), not sure why it occurrs but we'll just silently ignore
		url = None

	return url

def url_for_act(citation):
	# Citations of proposed documents won't follow the same URL format.
	if citation["proposed"]:
		# XXX: We should probably support same-page URLs for these.
		return None

	try:
		url = "https://www.govtrack.us/congress/bills/browse?congress=__ALL__&sort=relevance&text=%s" % ( citation["act"] )
	except KeyError:
		url = None

	return url

def create_link_url(xml_element):
	import citations

	link_url = None

	xml_tag = xml_element.tag

	if xml_tag.startswith(catoxml_ns):
		xml_tag_name = xml_tag[len(catoxml_ns):]

		if xml_tag_name in [ "entity-ref" ]:
			entity_type = xml_element.get("entity-type")
			entity_value = xml_element.get("value")
			entity_proposed = True if ( xml_element.get("proposed", "false") == "true" ) else False

			if entity_value is not None:
				citation = citations.deepbills_citation_for(entity_type, entity_value, xml_element.text, entity_proposed)

				if citation["type"] == "uscode":
					link_url = url_for_us_code(citation)
				elif citation["type"] == "statute-at-large":
					link_url = url_for_statute_at_large(citation)
				elif citation["type"] == "public-law":
					link_url = url_for_public_law(citation)
				elif citation["type"] == "act":
					link_url = url_for_act(citation)
				else:
					# Unexpected citation type.
					pass
	else:
		if xml_tag == "external-xref":
			legal_doc = xml_element.get("legal-doc")
			parsable_cite = xml_element.get("parsable-cite")

			# XXX: Workaround for citations.deepbills_citation_for().
			if legal_doc == "usc":
				legal_doc = "uscode"

			citation = citations.deepbills_citation_for(legal_doc, parsable_cite, xml_element.text)

#			if citation["type"] == "usc":
			if citation["type"] == "uscode":
				link_url = url_for_us_code(citation)
			elif citation["type"] == "statute-at-large":
				link_url = url_for_statute_at_large(citation)
			elif citation["type"] == "public-law":
				link_url = url_for_public_law(citation)
			elif citation["type"] == "act":
				link_url = url_for_act(citation)
			elif citation["type"] == "executive-order":
				pass
			elif citation["type"] == "regulation":
				pass
			elif citation["type"] == "bill":
				pass
			elif citation["type"] == "senate-rule":
				pass
			elif citation["type"] == "treaty-ust":
				pass
			elif citation["type"] == "treaty-tias":
				pass
			else:
				# Unexpected document type
				pass
		elif xml_tag == "internal-xref":
			idref = xml_element.get("idref")
			legis_path = xml_element.get("legis-path")
		elif xml_tag == "footnote-ref":
			idref = xml_element.get("idref")
		else:
			# Unexpected XML tag.
			pass

	return link_url

def can_be_link(xml_element):
	xml_tag = xml_element.tag

	if xml_tag.startswith(catoxml_ns):
		pass
	else:
		# Favor CatoXML references, because they tend to be more specific.
		# XXX: This is probably enough, but we might want to check for other nested link elements.
		entity_ref_tag_name = "{%s}entity-ref" % ( catoxml_ns )
		if xml_element.iterdescendants(entity_ref_tag_name) or xml_element.iterancestors(entity_ref_tag_name):
			return False

	return True

def convert_element(xml_element, url_fn=create_link_url):
	xml_tag = xml_element.tag

	html_attributes = { "class": [ xml_tag ] }

	for ( name, value ) in xml_element.items():
		html_attributes["data-%s" % ( name )] = value

	if xml_tag.startswith(catoxml_ns):
		xml_tag_name = xml_tag[len(catoxml_ns):]
		html_attributes["class"][html_attributes["class"].index(xml_tag)] = xml_tag_name

		if xml_tag_name in [ "entity-ref" ]:
			# We aren't allowed to have nested links.
			if can_be_link(xml_element):
				html_tag = "a"

				href = url_fn(xml_element)
				if href:
					html_attributes["href"] = href
			else:
				html_tag = "span"
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
			# We aren't allowed to have nested links.
			if can_be_link(xml_element):
				html_tag = "a"

				href = url_fn(xml_element)
				if href:
					html_attributes["href"] = href

				if xml_tag in [ "external-xref" ]:
					if "rel" not in html_attributes:
						html_attributes["rel"] = []

					html_attributes["rel"].append("external")
			else:
				html_tag = "span"
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

def build_html_tree(node, url_fn=create_link_url):
	html_tree = convert_element(node, url_fn)

	for xml_element in node.getchildren():
		# Ignore certain subtrees and processing instructions
		if xml_element.tag in [ "metadata" ] or not isinstance(xml_element.tag, basestring):
			continue

		html_tree.append(build_html_tree(xml_element))

	return html_tree

def convert_xml(xml_file_path, url_fn=create_link_url):
	xml_tree = etree.parse(xml_file_path, etree.XMLParser(recover=True))

	return etree.ElementTree(build_html_tree(xml_tree.getroot(), url_fn))

# XXX: Is this even necessary? You can just call the write() method on the output of convert_xml()...
def write_html(html_tree, html_file_path):
	return html_tree.write(html_file_path)
