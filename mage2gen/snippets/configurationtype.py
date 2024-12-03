# A Magento 2 module generator library
# Copyright (C) 2016 Maikel Martens
#
# This file is part of Mage2Gen.
#
# Mage2Gen is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import os, locale
from .. import Module, Phpclass, Phpmethod, Xmlnode, StaticFile, Snippet, SnippetParam, utils, Readme

class ConfigurationTypeSnippet(Snippet):
	snippet_label = 'Configuration Type'

	def add(self, config_name, node_name, field_name, extra_params=None):
		config_class_name = ''.join(utils.upperfirst(w) for w in config_name.split('_'))
		
		# Create XSD
		config_xsd = Xmlnode('xs:schema',xsd=True, attributes={'attributeFormDefault':"unqualified", "elementFormDefault":"qualified", "xmlns:xs":"http://www.w3.org/2001/XMLSchema"}, nodes=[
			Xmlnode('xs:element', attributes={'name': 'config'}, nodes=[
				Xmlnode('xs:complexType', nodes=[
					Xmlnode('xs:choice', attributes={'maxOccurs': 'unbounded'}, nodes=[
						Xmlnode('xs:element', attributes={'name': node_name, 'type': '{}Type'.format(node_name), 'maxOccurs': 'unbounded', 'minOccurs': '0'})
					])
				])
			]),
			Xmlnode('xs:complexType', attributes={'type': '{}Type'.format(node_name)}, nodes=[
				Xmlnode('xs:sequence', nodes=[
					Xmlnode('xs:element', attributes={'name': field_name, 'type': 'xs:string'})
				])
			])	
		])
		self.add_xml('etc/{}.xsd'.format(config_name), config_xsd)

		# create merge XSD
		config_merged_xsd = Xmlnode('xs:schema', attributes={'xmlns:xs':'http://www.w3.org/2001/XMLSchema'}, nodes=[
			Xmlnode('xs:include', attributes={'schemaLocation': 'urn:magento:module:{}:etc/{}.xsd'.format(self.module_name, config_name)})
		])
		self.add_xml('etc/{}_merged.xsd'.format(config_name), config_merged_xsd)

		# Create SchemaLocator
		schema_locator_class = Phpclass('Config\\{}\\SchemaLocator'.format(config_class_name), 
            implements=['\\Magento\\Framework\\Config\\SchemaLocatorInterface'],
            attributes=[
                'private ?string $schema;',
                'private ?string $perFileSchema;'
            ],
            dependencies=['Magento\\Framework\\Module\\Dir\\Reader']
        )

		schema_locator_class.add_method(Phpmethod('__construct', params=['private Reader $moduleReader'], body="""
$etcDir = $moduleReader->getModuleDir(Dir::MODULE_ETC_DIR, 'Experius_Test');
$this->schema = $etcDir . '/example_merged.xsd';
$this->perFileSchema = $etcDir . '/example.xsd';
"""))

		schema_locator_class.add_method(Phpmethod('getSchema', return_type='?string', body="""
return $this->schema;
"""))

		schema_locator_class.add_method(Phpmethod('getPerFileSchema', return_type='?string', body="""
return $this->perFileSchema;
"""))

		self.add_class(schema_locator_class)

		# Create Converter
		converter_class = Phpclass('Config\\{}\\Converter'.format(config_class_name), implements=['\\Magento\\Framework\\Config\\ConverterInterface'])

		converter_class.add_method(Phpmethod('convert', params=['DOMDocument $source'], return_type='array', docstring=[
				'Convert dom node tree to array',
				'',
				'@param DOMDocument $source',
				'@return array',
			],
			body="""
$output = [];
$xpath = new DOMXPath($source);
$nodes = $xpath->evaluate('/config/example');

/** @var DOMNode $node */
foreach ($nodes as $node) {
    $nodeId = $node->attributes->getNamedItem('id')->nodeValue;

    $data = [];
    $data['id'] = $nodeId;
    foreach ($node->childNodes as $childNode) {
        if ($childNode->nodeType !== XML_ELEMENT_NODE) {
            continue;
        }

        $data[$childNode->nodeName] = $childNode->nodeValue;
    }
    $output['example'][$nodeId] = $data;
}

return $output;
		"""))

		self.add_class(converter_class)

		# Create Reader
		reader_class = Phpclass('Config\\{}\\Reader'.format(config_class_name), 
			extends='\\Magento\\Framework\\Config\\Reader\\Filesystem',
			attributes=[
				'protected array $_idAttributes = [',
				"    '/config/example' => 'id',",
				'];'
			],
			dependencies=[
				'Magento\\Framework\\Config\\FileResolverInterface',
				'Converter',
				'SchemaLocator',
				'Magento\\Framework\\Config\\ValidationStateInterface',
				'Magento\\Framework\\Config\\Dom'
			]
		)

		reader_class.add_method(Phpmethod('__construct', params=[
			'private FileResolverInterface $fileResolver',
			'private Converter $converter',
			'private SchemaLocator $schemaLocator',
			'private ValidationStateInterface $validationState',
			'private string $fileName = \'example.xml\'',
			'private array $idAttributes = []',
			'private string $domDocumentClass = Dom::class',
			'private string $defaultScope = \'global\''
		], body="""
parent::__construct(
    $fileResolver,
    $converter,
    $schemaLocator,
    $validationState,
    $fileName,
    $idAttributes,
    $domDocumentClass,
    $defaultScope
);
		"""))

		self.add_class(reader_class)

		self.add_static_file(
			'.',
			Readme(
				specifications=" - Configuration Type\n\t- {}".format(config_name),
			)
		)
		

	@classmethod
	def params(cls):
		 return [
			 SnippetParam(
				name='config_name',
				description='XML config filename', 
				required=True,
				regex_validator= r'^[a-z_]+$',
				error_message='Only lower case alphabet and underscore characters',
				repeat=True),
			 SnippetParam(
				name='node_name',
				description='Repeating XML node name',
				required=True,  
				regex_validator= r'^[a-z_]+$',
				error_message='Only lower case alphabet and underscore characters',
				repeat=True),
			 SnippetParam(
				name='field_name',
				description='Configuration field name',
				required=True,  
				regex_validator= r'^[a-z_]+$',
				error_message='Only lower case alphabet and underscore characters'),
		]