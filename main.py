#!/usr/bin/env python3

# https://msdn.microsoft.com/en-us/library/windows/hardware/dn641604(v=vs.85).aspx
# https://docs.microsoft.com/en-us/windows-hardware/drivers/image/web-services-on-devices-reference

import zeep
# Override WS-Addressing namespace (use WS2006 instead of WS 1.1)
zeep.ns.WSA = 'http://schemas.xmlsoap.org/ws/2004/08/addressing'
import zeep.wsa, zeep.plugins

import papersize

import argparse
import datetime
import getpass
import platform
import sys

# == Arguments ==

parser = argparse.ArgumentParser(description='Interact with a network scanner using the Microsoft WSD (Web Services on Devices) WS-Scan protocol')
parser.add_argument('url', help='URL of the WS-Scan endpoint, e.g. http://192.168.0.2/ws2/')
parser.add_argument('--debug', action='store_true', help='Print debug information to stderr')
parser_operation = parser.add_subparsers(title='operation', dest='operation', help='The operation to perform')

must_honor = ['ColorProcessing', 'CompressionQualityFactor', 'ContentType', 'InputSize', 'InputSource', 'Resolution', 'ScanRegionWidth', 'ScanRegionHeight', 'ScanRegionXOffset', 'ScanRegionYOffset']

parser_scan = parser_operation.add_parser('scan', help='Scan a document')
parser_scan.add_argument('--name', default=datetime.datetime.now().strftime('Scan job at %Y-%m-%d %H:%M:%S'), help='Name of the scan job (JobName)')
parser_scan.add_argument('--user', default='{} on {}'.format(getpass.getuser(), platform.node()), help='Name of the originating user (JobOriginatingUserName)')
parser_scan.add_argument('--quality', default='100', help='Quality for lossless compression (CompressionQualityFactor, default "100")')
parser_scan.add_argument('--type', default='Auto', choices=['Auto', 'Text', 'Photo', 'Halftone', 'Mixed'], help='Type of scan (ContentType, default "Auto")')
parser_scan.add_argument('--format', default='exif', choices=['dib', 'exif', 'jbig', 'jfif', 'jpeg2k', 'pdf-a', 'png', 'tiff-single-uncompressed', 'tiff-single-g4', 'tiff-single-g3mh', 'tiff-single-jpeg-tn2', 'tiff-multi-uncompressed', 'tiff-multi-g4', 'tiff-multi-g3mh', 'tiff-multi-jpeg-tn2', 'xps'], help='Output file format (Format, default "exif")')
parser_scan.add_argument('--size', default='auto', help='Input paper size, either "auto", a size like "a4", or a measurement like "21cm x 29.7cm" (InputSize, default "auto")')
parser_scan.add_argument('--source', default='Auto', choices=['Auto', 'ADF', 'ADFDuplex', 'Film', 'Platen'], help='Output file format (InputSource, default "Auto")')
parser_scan.add_argument('--color', default=['Default'], choices=['Default', 'BlackAndWhite1', 'Grayscale4', 'Grayscale8', 'Grayscale16', 'RGB24', 'RGB48', 'RGBa32', 'RGBa64'], nargs='+', help='Color type, for front and optionally for back, (ColorProcessing)')
parser_scan.add_argument('--ppi', default=['Default'], nargs='+', help='Scan resolution, for front and optionally for back, in pixels per inch, e.g. "300x300" (Resolution)')
parser_scan.add_argument('--region', default=['Default'], nargs='+', help='Scan region, for front and optionally for back, "WxH+X,Y unit" (ScanRegion)')
parser_scan.add_argument('--optional', nargs='*', default=[], choices=must_honor, help='Space-separated list of settings which need not be honored (by default, all applicable settings are MustHonor)')

parser_shell = parser_operation.add_parser('shell', help='Initialise pyWSDscan and run a PDB shell')

args = parser.parse_args()

if args.operation is None:
	print(sys.argv[0] + ': error: you must specify an operation', file=sys.stderr)
	sys.exit(1)

# == End arguments ==

history = zeep.plugins.HistoryPlugin()
client = zeep.Client('data/ScanService/WSDScannerService.wsdl', plugins=[zeep.wsa.WsAddressingPlugin(), history])
service = client.create_service('{http://schemas.microsoft.com/windows/2006/08/wdp/scan}ScannerServiceBinding', args.url)

# Load some types
ScanTicket = client.get_type('ns0:ScanTicketType')

if args.operation == 'scan':
	def make_mediaside(side):
		if side > 0:
			side0 = make_mediaside(0)
		
		return {
			'ColorProcessing': side0['ColorProcessing'] if len(args.color) <= side else None if args.color[side] == 'Default' else args.color[side],
			'Resolution': (
				side0['Resolution'] if len(args.ppi) <= side else
				None if args.ppi[side] == 'Default' else
				{
					'Width': args.ppi[side].split('x')[0],
					'Height': args.ppi[side].split('x')[1] if 'x' in args.ppi[side] else args.ppi[side]
				}
			),
			'ScanRegion': (
				side0['ScanRegion'] if len(args.region) <= side else
				None if args.region[side] == 'Default' else
				{
					'ScanRegionWidth': int(papersize.convert_length(float(args.region[side].split('x')[0]), args.region[side].split(' ')[1], 'in')*1000),
					'ScanRegionHeight': int(papersize.convert_length(float(args.region[side].split('x')[1].split('+')[0]), args.region[side].split(' ')[1], 'in')*1000),
					'ScanRegionXOffset': int(papersize.convert_length(float(args.region[side].split('+')[1].split(',')[0]), args.region[side].split(' ')[1], 'in')*1000),
					'ScanRegionYOffset': int(papersize.convert_length(float(args.region[side].split(',')[1].split(' ')[0]), args.region[side].split(' ')[1], 'in')*1000)
				}
			)
		}
	
	# Prepare ticket
	scan_ticket = ScanTicket(
		JobDescription={
			'JobName': args.name,
			'JobOriginatingUserName': args.user
		},
		DocumentParameters={
			'CompressionQualityFactor': args.quality,
			'ContentType': args.type,
			'Format': args.format,
			'InputSize': (
				{'DocumentSizeAutoDetect': {}} if args.size == 'auto' else
				{'InputMediaSize': {
					'Width': int(papersize.parse_papersize(args.size, 'in')[0]*1000),
					'Height': int(papersize.parse_papersize(args.size, 'in')[1]*1000)
				}}
			),
			'InputSource': None if args.source == 'Auto' else args.source,
			'MediaSides': {
				'MediaFront': make_mediaside(0),
				'MediaBack': make_mediaside(1) if args.source == 'ADFDuplex' else None
			}
		}
	)
	
	# Set MustHonour flags
	for x in ['CompressionQualityFactor', 'ContentType', 'Format', 'InputSize', 'InputSource']:
		if x not in args.optional:
			val = getattr(scan_ticket.DocumentParameters, x)
			if val is not None:
				val.MustHonor = 'true'
	
	for y in ['MediaFront', 'MediaBack']:
		side = getattr(scan_ticket.DocumentParameters.MediaSides, y)
		if side is not None:
			if 'ColorProcessing' not in args.optional:
				if side.ColorProcessing is not None:
					side.ColorProcessing.MustHonor = 'true'
			if 'Resolution' not in args.optional:
				if side.Resolution is not None:
					side.Resolution.MustHonor = 'true'
			if side.ScanRegion is not None:
				for x in ['ScanRegionWidth', 'ScanRegionHeight', 'ScanRegionXOffset', 'ScanRegionYOffset']:
					if x not in args.optional:
						getattr(side.ScanRegion, x).MustHonor = 'true'
	
	if args.debug:
		print('=== Scan ticket:', file=sys.stderr)
		print(scan_ticket, file=sys.stderr)
		print(file=sys.stderr)
	
	# Confusingly, my printer doesn't honour validity and just says "Yes!" all the time…
	print('Validating scan ticket...', file=sys.stderr)
	validate_result = service.ValidateScanTicket(scan_ticket)
	
	if args.debug:
		print(file=sys.stderr)
		print('=== ValidateScanTicket result:', file=sys.stderr)
		print(validate_result, file=sys.stderr)
		print(file=sys.stderr)
	
	if not validate_result.ValidTicket._value_1:
		print('Error: Scan parameters not supported', file=sys.stderr)
		sys.exit(1)
	
	print('Creating new scan job...', file=sys.stderr)
	create_result = service.CreateScanJob(ScanTicket=scan_ticket)
	
	if args.debug:
		print(file=sys.stderr)
		print('=== CreateScanJob result:', file=sys.stderr)
		print(create_result, file=sys.stderr)
		print(file=sys.stderr)
	
	print('Retrieving image data...', file=sys.stderr)
	try:
		retrieve_result = service.RetrieveImage(
			JobId=create_result.JobId,
			JobToken=create_result.JobToken,
			DocumentDescription={
				'DocumentName': args.name
			}
		)
	except zeep.exceptions.Fault as ex:
		print('Error: Scan failed', file=sys.stderr)
		print(ex, file=sys.stderr)
		sys.exit(1)
	
	sys.stdout.buffer.write(retrieve_result._value_1)
	
elif args.operation == 'shell':
	print('You may use the PDB shell to interact with the scanner, e.g. service.GetJobHistory()', file=sys.stderr)
	import pdb; pdb.set_trace()
