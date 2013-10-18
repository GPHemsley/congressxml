from setuptools import setup

setup(name="CongressXML",
	version="0.1-dev",
	description="XML-to-HTML converter for HouseXML and CatoXML",
	url="http://github.com/GPHemsley/congressxml",
	author="Gordon P. Hemsley",
	author_email="me@gphemsley.org",
	license="Unlicense",
	packages=[ "congressxml" ],
	install_requires=[
		"lxml>=3.2.1",
	],
	zip_safe=False)