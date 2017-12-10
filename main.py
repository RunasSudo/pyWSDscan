#!/usr/bin/env python3

# https://msdn.microsoft.com/en-us/library/windows/hardware/dn641604(v=vs.85).aspx
# https://docs.microsoft.com/en-us/windows-hardware/drivers/image/web-services-on-devices-reference

import zeep

# Override WS-Addressing namespace (use WS2006 instead of WS 1.1)
zeep.ns.WSA = 'http://schemas.xmlsoap.org/ws/2004/08/addressing'

import zeep.wsa

client = zeep.Client('data/ScanService/WSDScannerService.wsdl', plugins=[zeep.wsa.WsAddressingPlugin()])
service = client.create_service('{http://schemas.microsoft.com/windows/2006/08/wdp/scan}ScannerServiceBinding', 'http://192.168.0.8:9867/ws2/')

import pdb; pdb.set_trace()
